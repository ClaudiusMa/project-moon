# Project Moon (登月计划)

**Is your calendar funding the person you're trying to become?** Project Moon turns your
Google Calendar into a weekly mirror of that question — not "what did I do this week," but
"which version of myself did my time fund."

Tool-agnostic and local-first: a deterministic Python core plus markdown playbooks. Any
agentic coding tool (Claude Code, Codex, …) or a plain shell + a human can run it. Your
calendars and weekly data never leave your machine.

## 1. The philosophy

- **A category is an identity account — a person you're choosing to become.** Not an
  activity bucket ("work," "exercise"), but an identity ("a builder," "a present
  parent," "an athlete"). **You define your own.** They're personal; there is no fixed
  list — the set in this repo is *one example*, and yours will be different.
- **You choose the identity when you schedule, not after.** Each identity is its own
  Google calendar, and putting an event on it is you declaring *why* you're spending the
  time. The same coffee is *"surrounded by exceptional people"* if it's a mentor, or
  *"a loyal friend"* if it's your closest friend — you decide which when you schedule it.
  Moon never guesses from the title, so the same calendars always produce the same numbers.
- **Cognitive hours, not minutes.** Within an identity, overlapping/adjacent events merge
  into a block and round **up** to whole hours — a 45-minute focus block costs one
  cognitive hour, because the leftover isn't really reusable. The unit models attention,
  not stopwatch time.
- **The weekly report is an honest mirror.** It shows each identity's *share* of your week
  as a percentage. An identity you say matters but funded 2% is the signal that matters.
- **Reflection + coaching close the loop.** After the numbers, you reflect from memory,
  then a coach reads your answers against the actual schedule and advises the week ahead.

The goal isn't a perfect taxonomy — it's a weekly check on whether your hours are making
your desired self real.

## 2. An example (one person's setup)

Here's how the maintainer uses it — an **illustration, not a prescription.** They keep one
calendar per identity they're investing in:

> *I support myself and family · I'm a builder · I am a designer with exceptional taste ·
> I am surrounded by exceptional people · I am a superman · I am a loyal friend · I am a
> grateful son · I am a helpful man*

…plus two non-identity calendars they find useful: a **Trash time** calendar for
energy-draining hours they want to *cut*, and their default calendar treated as
**Invisible** (chores / low-return time — fine in small doses, worth watching when it
surges).

A week then comes back like this *(synthetic numbers, to show the shape)*:

| Identity (this person's) | Cognitive hours | Share |
| --- | ---: | ---: |
| I am a superman | 8 | 22% |
| I'm a builder | 7 | 19% |
| I support myself and family | 6 | 17% |
| I am a loyal friend | 5 | 14% |
| I am surrounded by exceptional people | 3 | 8% |
| I am a designer with exceptional taste | 2 | 6% |
| I am a helpful man | 1 | 3% |
| I am a grateful son | 0 | 0% |
| _Trash time_ | 1 | 3% |
| _Invisible (unallocated)_ | 3 | 8% |

The mirror talks: *"builder is my stated priority but landed behind hobbies; grateful-son
was 0% again; Trash time is creeping up."* **Your identities, and what you learn from
them, will be your own.**

## 3. Set it up (make it yours)

1. **Name your identities.** Pick the few people you're trying to become — 3–8 is plenty
   (a parent, a writer, an athlete, a founder… whatever *you're* investing in). Optionally
   add a **Trash** calendar for time you want to cut, and use your default calendar as
   **Invisible**.
2. **Create one Google Calendar per identity.** For each, copy its **"Secret address in
   iCal format"** (Calendar settings → *Integrate calendar*). The URL auto-refreshes, so
   your data never goes stale.
3. **Define them for Moon.** Edit [`Moon/config/categories.yaml`](Moon/config/categories.yaml)
   — an `id`, a `display_name`, and a one-line core question per identity — and the human
   notes in [`Moon/config/categories.md`](Moon/config/categories.md). It ships with the
   example set above; **replace it with yours.**
4. **Point Moon at your calendars.** Copy the template and paste your secret URLs, keyed by
   your ids:
   ```bash
   mkdir -p Astronaut
   cp Moon/config/feeds.example.md Astronaut/rocket.md
   # edit Astronaut/rocket.md — one `- <id>: <secret iCal URL>` per identity,
   # plus optional `- trash_time:` / `- invisible:` lines.
   ```
   Everything under `Astronaut/` is gitignored — your URLs and data stay local.
5. **Install and run:**
   ```bash
   pip install -r Moon/scripts/requirements.txt
   ./Moon/scripts/moon-weekly            # most recent completed week
   ```
   Then run the reflection and coaching playbooks in `Moon/playbooks/` with your agent (or
   by hand).
6. **Then just live in your calendar.** Schedule each event on the identity it's *for*, and
   run Moon once a week. It even flags it when you rename a calendar.

See [`AGENTS.md`](AGENTS.md) for the full operating guide and
[`Moon/README.md`](Moon/README.md) for the directory layout.

## Privacy

Gitignored, never committed: `Astronaut/` (your `rocket.md` + any local calendar files),
`Moon/weeks/` (events, reflections, coaching), and `Moon/trends.csv` (weekly aggregates).
Only the product code, playbooks, and the *example* config are tracked. Back up
`Astronaut/` and `Moon/weeks/` yourself (iCloud, a private repo, etc.).

## License

See [LICENSE](LICENSE).
