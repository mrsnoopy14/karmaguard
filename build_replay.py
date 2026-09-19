import json
import sys
from pathlib import Path

import agents
from server import BASE_VERSIONS, PROMPTS, SESSION_FILE, list_versions

ROOT = Path(__file__).parent
OUT = ROOT / "replay" / "index.html"


def main():
    session = Path(sys.argv[1]) if len(sys.argv) > 1 else SESSION_FILE
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    if not session.exists():
        sys.exit("No session.json yet. Run the dashboard once (for example v1: Run guard, then Auto-fix) and try again.")
    events = json.loads(session.read_text(encoding="utf-8"))
    if not any(e["path"] == "/api/runs" for e in events):
        sys.exit("session.json has no completed runs yet.")

    fixed = {e["response"]["id"] for e in events if e["path"] == "/api/fix"}
    tested = {int(e["body"]["version"]) for e in events if e["path"] == "/api/test"}
    needed = set(range(1, BASE_VERSIONS + 1)) | (tested - fixed)
    versions = [v for v in list_versions() if v["id"] in needed]
    missing = needed - {v["id"] for v in versions}
    if missing:
        sys.exit(f"Prompt files for versions {sorted(missing)} are missing in {PROMPTS}.")

    data = {
        "recordedAt": events[0]["at"],
        "state": {"versions": versions, "models": agents.MODELS, "categories": agents.CATEGORIES, "runs": []},
        "events": [{k: e[k] for k in ("path", "body", "response")} for e in events],
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    html = html.replace("<title>KarmaGuard</title>", "<title>KarmaGuard replay</title>", 1)
    html = html.replace("\n<script>\n", f"\n<script>window.KG_REPLAY = {payload};</script>\n<script>\n", 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    runs = sum(e["path"] == "/api/runs" for e in events)
    print(f"Wrote {out} ({len(html) // 1024} KB, {runs} runs, {len(fixed)} fixes)")


if __name__ == "__main__":
    main()
