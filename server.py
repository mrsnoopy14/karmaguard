import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import agents

ROOT = Path(__file__).parent
PROMPTS = ROOT / "prompts"
RUNS_FILE = ROOT / "runs.jsonl"
SESSION_FILE = ROOT / "session.json"
RECORDED = {"/api/attacks", "/api/test", "/api/fix", "/api/runs"}
session_lock = threading.Lock()


def record(path, body, result):
    with session_lock:
        events = json.loads(SESSION_FILE.read_text(encoding="utf-8")) if SESSION_FILE.exists() else []
        events.append({"path": path, "body": body, "response": result, "at": time.time()})
        SESSION_FILE.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
INDEX = ROOT / "static" / "index.html"
PORT = int(os.environ.get("KG_PORT", 8765))
BASE_VERSIONS = 2


def list_versions():
    versions = []
    for path in PROMPTS.glob("bot_v*.txt"):
        num = int(re.search(r"bot_v(\d+)", path.name).group(1))
        changes_path = PROMPTS / f"bot_v{num}.changes.json"
        changes = json.loads(changes_path.read_text(encoding="utf-8")) if changes_path.exists() else []
        versions.append({"id": num, "prompt": path.read_text(encoding="utf-8"), "changes": changes})
    return sorted(versions, key=lambda v: v["id"])


def load_prompt(version):
    return (PROMPTS / f"bot_v{int(version)}.txt").read_text(encoding="utf-8")


def meta(res):
    return {k: res[k] for k in ("cost", "latency_ms", "tokens", "model")}


def api_state(_):
    runs = []
    if RUNS_FILE.exists():
        runs = [json.loads(line) for line in RUNS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {
        "versions": list_versions(),
        "models": agents.MODELS,
        "categories": agents.CATEGORIES,
        "policy": agents.POLICY,
        "runs": runs[-20:],
    }


def api_attacks(body):
    attacks, res = agents.generate_attacks(int(body.get("count", 12)), body.get("focus"))
    return {"attacks": attacks, "meta": meta(res)}


def api_test(body):
    bot_res = agents.ask_bot(load_prompt(body["version"]), body["message"])
    verdict, judge_res = agents.judge(
        body["message"], bot_res["text"], body.get("test_id", ""), body.get("expected", ""))
    return {"reply": bot_res["text"], "verdict": verdict, "bot": meta(bot_res), "judge": meta(judge_res)}


def api_fix(body):
    fixed, res = agents.fix_prompt(load_prompt(body["version"]), body["failures"])
    new_id = max(v["id"] for v in list_versions()) + 1
    (PROMPTS / f"bot_v{new_id}.txt").write_text(fixed["prompt"], encoding="utf-8")
    (PROMPTS / f"bot_v{new_id}.changes.json").write_text(
        json.dumps(fixed["fixes"], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"id": new_id, "prompt": fixed["prompt"], "changes": fixed["fixes"], "meta": meta(res)}


def api_save_run(body):
    body["at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with RUNS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(body, ensure_ascii=False) + "\n")
    return {"ok": True}


BROWSERS = [
    shutil.which("chrome"), shutil.which("msedge"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    shutil.which("google-chrome"), shutil.which("chromium"),
]


def api_report_pdf(body):
    browser = next((b for b in BROWSERS if b and Path(b).exists()), None)
    if not browser:
        raise RuntimeError("No Chrome or Edge found to render the PDF")
    work = Path(tempfile.mkdtemp(dir=agents.SANDBOX))
    html_path, pdf_path = work / "report.html", work / "report.pdf"
    html_path.write_text(body["html"], encoding="utf-8")
    try:
        subprocess.run([
            browser, "--headless=new", "--disable-gpu", "--no-first-run",
            f"--user-data-dir={work / 'profile'}",
            "--no-pdf-header-footer", "--print-to-pdf-no-header",
            f"--print-to-pdf={pdf_path}", html_path.as_uri(),
        ], capture_output=True, timeout=90)
        if not pdf_path.exists():
            raise RuntimeError("Browser did not produce a PDF")
        return pdf_path.read_bytes(), "application/pdf"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def api_reset(_):
    for path in PROMPTS.glob("bot_v*"):
        if int(re.search(r"bot_v(\d+)", path.name).group(1)) > BASE_VERSIONS:
            path.unlink()
    RUNS_FILE.unlink(missing_ok=True)
    with session_lock:
        SESSION_FILE.unlink(missing_ok=True)
    return {"ok": True}


ROUTES = {
    ("GET", "/api/state"): api_state,
    ("POST", "/api/attacks"): api_attacks,
    ("POST", "/api/test"): api_test,
    ("POST", "/api/fix"): api_fix,
    ("POST", "/api/runs"): api_save_run,
    ("POST", "/api/reset"): api_reset,
    ("POST", "/api/report.pdf"): api_report_pdf,
}


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        is_text = content_type.startswith("text/") or content_type == "application/json"
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if is_text else content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_route(self, method):
        if method == "GET" and self.path in ("/", "/index.html"):
            return self.send(200, INDEX.read_bytes(), "text/html")
        route = ROUTES.get((method, self.path))
        if not route:
            return self.send(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            result = route(body)
            if self.path in RECORDED:
                record(self.path, body, result)
            if isinstance(result, tuple):
                self.send(200, *result)
            else:
                self.send(200, result)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            traceback.print_exc()
            self.send(500, {"error": str(e)})

    def do_GET(self):
        self.handle_route("GET")

    def do_POST(self):
        self.handle_route("POST")

    def log_message(self, fmt, *args):
        if "/api/" in self.path:
            sys.stderr.write(f"{self.command} {self.path} {args[1] if len(args) > 1 else ''}\n")


if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    print(f"KarmaGuard running at {url}")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
