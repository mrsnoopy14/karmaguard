# KarmaGuard

An AI reliability agent for Team 3 (AI observability and reliability). It attacks the KarmaCoins support bot with tricky customer messages, judges every reply against the support policy, tracks cost and latency, and rewrites the bot's prompt until it is safe.

## Run

Requirements: Python 3.10+ and Claude Code, logged in. No API key and no pip installs needed.

```
cd KarmaGuard
python server.py
```

The dashboard opens at http://localhost:8765.

## How it works

| Agent | Model | Job |
|---|---|---|
| Hacker (attacker) | Sonnet | Writes targeted tests across 15 attack types, each with a test ID, expected safe behaviour and severity |
| Bot (the system under test) | Haiku | The KarmaCoins support bot, driven by `prompts/bot_vN.txt` |
| Judge | Sonnet | Scores each reply from 1 to 5 against `policy.md` and returns pass/fail, failure type, severity, reason and a recommended fix |
| Auto-fix | Sonnet | Finds the weakness behind each failure, explains why it failed, and writes minimal, targeted instruction changes as a new bot version |

Agent prompts are written by the team (Gourav) and live in `agents.py`.

### Bot versions
- **v1 (weak demo):** has planted weaknesses ("always say yes", "add goodwill coins"), so it reliably fails.
- **v2 (team-written):** Gourav's hand-written bot prompt, with the full policy inserted.
- **v3+ (auto-fixed):** created by the auto-fix agent. "Reset demo" deletes these and keeps v1 and v2.

Each agent is a headless `claude -p` call (see `agents.py`). The cost, latency and tokens of every call are shown on the dashboard.

### Buttons
- **Run guard**: the attacker writes a fresh set of attacks, then the bot answers each one and the judge scores it.
- **Auto-fix and re-test**: the fixer rewrites the prompt, then the same attacks run again for a before/after comparison. It fixes failures and also near misses (tests that passed with a judge score below 5), so a strong bot can still be hardened. The before/after card shows the pass rate and the average judge score.
- **Report**: downloads a PDF report for the selected version: verdict, KPIs, before vs after, weak spots, fixes applied, all results, failures and near misses with recommended fixes, and agent cost. The server renders it with the locally installed Chrome or Edge. If neither is found, the browser print dialog opens instead ("Save as PDF").
- **Harder attacks on weak spots**: the attacker studies the failures and digs deeper into the same weaknesses.
- **Autopilot**: runs the full loop (attack → judge → fix → re-test) on its own until the pass rate is at least 80%, with at most 3 fixes.
- **Reset demo**: deletes the generated bot versions and run history.

Test results:
- v1 scored 25% on 8 attacks; the auto-fixed version scored 100% on the same set.
- v2 scored 100% on 10 standard attacks. After "Harder attacks on weak spots", it dropped to 75% (6 of 8). Two real gaps were caught: it implied missed quiz days could be compensated through a ticket, and it did not flag a 2 kg pickup that is below the 5 kg minimum.

## Demo script (6 minutes)
1. **Hook (30s):** "Every company is putting chatbots in front of customers. One wrong reply, like promising free coins or leaking someone's phone number, costs money and trust. Today you only find out when a customer complains."
2. **Well-written is not enough (2 min):** Select v2 (team-written) and click Run guard. It passes, so everything looks fine. Then click "Harder attacks on weak spots". The hacker studies the near-misses, digs deeper, and the pass rate drops below 80%. Point at the red alert, the severity labels and the judge's recommended fix.
3. **Auto-fix (2 min):** Click Auto-fix. In Agent activity, read out 2–3 lines: weakness → why → fix. The same attacks run again and the "Before vs after" card goes up.
4. **Worst case (1 min, optional):** Switch to v1 and run Autopilot to show a badly written bot being fixed end to end without a human.
5. **Close (30s):** "This can run every night on every AI feature we ship: the support bot, the quiz, onboarding. It catches failures before customers do, and costs about ₹X per run at API rates."

If the harder round passes as well, click Auto-fix anyway. It hardens the near misses and the average judge score goes up (for example 4.5 → 5.0). Attacks are generated fresh each time, so results vary.

Backup: record one full Autopilot run at 4:45 PM in case of a network issue.

## Summary slide
- **Problem:** AI bots fail silently. Wrong promises, invented policies and data leaks only show up after a customer complaint.
- **Approach:** four Claude agents in a closed loop: attacker → bot → judge → fixer → re-test. The loop runs on autopilot until the pass rate reaches 80%.
- **Tools:** Claude Code (headless mode), Claude Sonnet and Haiku, Python, and an HTML dashboard.
- **Impact:** failures caught before release, reliability you can measure (pass rate per version), cost and latency visibility per agent, and a reusable guard for every AI feature.

## Files
- `policy.md`: ground-truth support policy (dummy data)
- `prompts/bot_v1.txt`: the weak demo bot prompt
- `prompts/bot_v2.txt`: the team-written bot prompt
- `agents.py`: the attacker, bot, judge and fixer, plus the Claude CLI wrapper
- `server.py`: the local API and dashboard server
- `static/index.html`: the dashboard
