# Project Moon (登月计划)

Turn your calendar into a weekly record of which **identities** your time actually
funded, and pair each week with a short guided reflection and coaching. Moon reads
**per-identity Google calendars** — one per part of the person you're trying to become —
converts them into **cognitive hours** (whole-hour attention blocks, not stopwatch
minutes), and tracks the trend over time.

It's **tool-agnostic and local-first**: a deterministic Python core plus markdown
playbooks. Any agentic coding tool (Claude Code, Codex, …) or a plain shell + a human
can run it. Your calendar URLs and your weekly data never leave your machine.

## How it works

- **One calendar per identity.** Each calendar is an identity account you're investing
  in — *I support myself and family, I am a designer with exceptional taste, I'm a
  builder, I am a helpful man, I am surrounded by exceptional people, I am a superman,
  I am a loyal friend, I am a grateful son* (full definitions and tie-breakers in
  [`Moon/config/categories.md`](Moon/config/categories.md)). You choose an event's
  identity when you **schedule** it — by which calendar you put it on, never by parsing
  its title. Same calendars → same numbers, every time.
- **Cognitive hours.** Within an identity, overlapping/adjacent events merge into a
  block and each block rounds **up** to whole hours. A 45-minute focus block costs one
  cognitive hour, because the leftover minutes aren't really reusable.
- **An honest mirror.** The report shows every identity's share of your week as a
  percentage — *all eight, even the ones at 0%*, so an underfunded identity stays
  visible. Two non-identity slices keep it honest:
  - **Trash time** — energy-draining, negative time you'd rather not repeat. Surfaced so
    you can see it and **reduce** it.
  - **Invisible (unallocated)** — chores, errands, low-return time with no clear purpose.
    Some is unavoidable; the signal is **don't let it surge**.
- **Weekly reflection + coaching.** After the numbers, a short reflection (bare
  questions, answered from memory — you review *last week* and plan *next week*), then a
  **coach** reads your answers against the actual schedule and gives grounded advice for
  the week ahead.

## Setup

1. **Calendars.** In Google Calendar, make one calendar per identity (see
   [`Moon/config/categories.md`](Moon/config/categories.md)) and put each event on the
   one that matches *why* you scheduled it. Optionally add a **Trash** calendar
   (energy-draining time) and use your everyday/primary as **Invisible**.
2. **Get each feed.** For every calendar, copy its **"Secret address in iCal format"**
   (Calendar settings → *Integrate calendar*). These URLs auto-refresh, so your data
   never goes stale — and Moon flags it whenever a calendar's name changes.
3. **Private feed list.** Create your `Astronaut/` workspace and a `rocket.md` from the
   template, then paste your URLs:
   ```bash
   mkdir -p Astronaut
   cp Moon/config/feeds.example.md Astronaut/rocket.md
   # edit Astronaut/rocket.md — map each identity id to its secret iCal URL
   # (a local .ics path also works); add `- trash_time:` and `- invisible:` lines too.
   ```
   Everything under `Astronaut/` is gitignored, so your URLs and data stay on your
   machine.
4. **Dependencies.** Python 3.9+ and:
   ```bash
   pip install -r Moon/scripts/requirements.txt
   ```

## Run it

```bash
# 1. Compute the most recent completed week (deterministic, no input needed)
./Moon/scripts/moon-weekly
#    ...or a specific week:  ./Moon/scripts/moon-weekly --week 2026-W26

# 2. Reflect, then coach: run Moon/playbooks/reflection.md, then
#    Moon/playbooks/coaching.md with your agent (or by hand)
```

Run it after a week closes — a mid-week run only sees a partial week. It writes
`Moon/weeks/<ISO-week>/` (events, time report, reflection, coaching) and appends to
`Moon/trends.csv`. See [`AGENTS.md`](AGENTS.md) for the full operating guide and
[`Moon/README.md`](Moon/README.md) for the directory layout.

## Privacy

Your private data is gitignored and never committed:
- `Astronaut/` — your feed list (`rocket.md`, with secret URLs) and any local calendar exports.
- `Moon/weeks/` — per-week events, reflections, and coaching notes.
- `Moon/trends.csv` — weekly per-identity aggregates (they reveal personal patterns).

Only the **product** (`Moon/` scripts, playbooks, and committed config templates) is
tracked. Back up `Astronaut/` and `Moon/weeks/` yourself (iCloud, a private repo, etc.).

## License

See [LICENSE](LICENSE).
