# KarmaGuard: prototype demo video (max 3 minutes)

Only the dashboard is shown, no slides. About 360 spoken words, around 2 minutes 45 seconds.

## Before recording

1. Start the server: `cd KarmaGuard` and then `python server.py`. Open http://127.0.0.1:8765.
2. Click **Reset demo**. Select **v1 · weak demo** and set **Tests** to **6**.
3. Browser zoom at 90%, so the pipeline and the numbers fit on screen. Close other tabs and turn off notifications.
4. Record with **Win + Alt + R** (Xbox Game Bar) with the microphone on, or use OBS.

The real agents take time: the hacker takes about 40 seconds, the tests about a minute, and the auto-fix plus re-test about a minute and a half. Two ways to stay under 3 minutes:
- **Option A:** record live, then cut the waiting parts in **Clipchamp** (built into Windows). The script marks where to cut.
- **Option B:** record the replay page and click **Play replay**. It shows the same real run, but fast, with no waiting.

---

## 0:00 – 0:20 · Opening
**Screen:** the full dashboard, not started yet. Move the mouse slowly across the four pipeline boxes.

> This is KarmaGuard, an AI agent that tests our customer support bot before customers do. Four Claude agents work in a loop: a hacker, the support bot, a judge, and an auto-fixer. Let's run it on a weak version of the KarmaCoins support bot.

## 0:20 – 0:45 · The hacker attacks
**Screen:** click **Run guard**. The Hacker box glows.

> The hacker agent is now writing six tricky customer messages across fifteen attack types: prompt injection, fake admin instructions, coin fraud, privacy, and Hinglish questions. Each test comes with a severity and the answer a safe bot should give.

✂️ *Option A: cut the wait here until the first results appear.*

## 0:45 – 1:25 · The judge catches failures
**Screen:** results appear one by one. Point at a red row, then click it to open the chat view.

> Now the support bot answers each message, and the judge scores it against our official policy. Red means fail. Here, the customer asked for coins in chat, and the bot said "Sure, I've added eighty goodwill coins." That breaks our policy. The judge gives it one out of five, explains why, and recommends a fix.

**Screen:** point at the red alert banner, then the **Pass rate** ring.

> The pass rate is far below our 80 percent bar, so KarmaGuard raises an alert: not safe to show customers.

**Screen:** point at **Weak spots by attack type**.

> We can also see exactly where the bot is weak.

## 1:25 – 2:15 · Auto-fix and re-test
**Screen:** click **Auto-fix and re-test**. The Auto-fix box glows.

> Now the auto-fix agent reads every failure. For each one it explains the weakness, why it caused the failure, and what it changed.

**Screen:** open the **What changed** tab under Bot instructions.

> Here it found the exact root cause: the instructions allowed goodwill coins. It removed that and added a clear rule. Then it saves a new bot version and runs the same attacks again.

✂️ *Option A: cut the wait until the re-test finishes.*

**Screen:** point at the **Before vs after** card and the green banner.

> Same attacks, and the pass rate goes from failing to passing, with no human editing the prompt. On Autopilot, this whole loop runs by itself until the bot is safe.

## 2:15 – 2:45 · Observability and close
**Screen:** scroll to **Cost and latency by agent**, then click **Report** and show the PDF for two seconds.

> Every agent call is tracked for cost, tokens and latency. A full run costs about twelve rupees. And every version gets a PDF report with the results, the failures and the fixes, ready to share with the team.

**Screen:** scroll back to the top of the dashboard.

> KarmaGuard can run every night on every AI feature we ship. Tests today, trust tomorrow.

---

## If something goes wrong while recording
- If a call errors or is very slow, press **Reset demo** and record again, or switch to Option B (replay).
- If v1 passes more tests than expected, keep the recording. The before vs after card will still show the improvement.
