# Project Moon (登月计划)

Turn your calendar into a weekly record of where your attention actually went, and
pair each week with a short guided reflection. Moon reads **per-category Google
calendars**, converts them into **cognitive hours** (whole-hour attention blocks, not
stopwatch minutes), and tracks the trend over time.

It's **tool-agnostic and local-first**: a deterministic Python core plus markdown
playbooks. Any agentic coding tool (Claude Code, Codex, …) or a plain shell + a human
can run it. Your calendar URLs and your weekly data never leave your machine.

## How it works

- **Category = the calendar an event lives on.** One Google calendar per category —
  `Learn, Build, Career, Habit, Workout, Social, Exploration, Trash`. Event titles are
  free-form; they're never parsed to guess a category. Same calendars → same numbers,
  every time.
- **Cognitive hours.** Within a category, overlapping/adjacent events merge into a
  block and each block rounds **up** to whole hours. A 45-minute focus block costs one
  cognitive hour, because the leftover minutes aren't really reusable.
- **Weekly reflection.** Six questions, asked one at a time, lightly proofread, saved
  per week. The "what did you do this week?" answer is auto-drafted from your event
  titles, so you start from a recap rather than a blank page.

## Setup

1. **Calendars.** In Google Calendar, make one calendar per category and put each event
   on the matching one. For each calendar, copy its **"Secret address in iCal format"**
   (Calendar settings → *Integrate calendar*).
2. **Config.** Copy the template and fill in your eight secret URLs:
   ```bash
   cp Moon/config/feeds.example.yaml Moon/config/feeds.yaml
   # edit Moon/config/feeds.yaml — it's gitignored and never committed
   ```
3. **Dependencies.** Python 3.9+ and:
   ```bash
   pip install -r Moon/scripts/requirements.txt
   ```

## Run it

```bash
# 1. Compute the last completed week (deterministic, no input needed)
./Moon/scripts/moon-weekly

# 2. Reflect (interactive): run Moon/playbooks/reflection.md with your agent, or by hand
```

This writes `Moon/weeks/<ISO-week>/` (events, time report, reflection) and appends to
`Moon/trends.csv`. See [`AGENTS.md`](AGENTS.md) for the full operating guide and
[`Moon/README.md`](Moon/README.md) for the directory layout.

## Privacy

`Moon/config/feeds.yaml` (your secret calendar URLs) and `Moon/weeks/` (your event data
and personal reflections) are **gitignored** — they stay local and are never committed.
Only `Moon/trends.csv` (aggregate cognitive hours per category per week) is tracked.

## License

See [LICENSE](LICENSE).
