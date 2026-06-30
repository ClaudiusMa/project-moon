# Coaching Playbook

Engine B's second ritual, run **after** the weekly reflection. An agentic tool (or a
thoughtful human) follows this playbook to read the week's real data and the person's
own reflection, then give honest, specific, **grounded** advice for the week ahead. It
is **tool-agnostic**.

The job is to be a coach, not a cheerleader: kind, direct, and always tied to the
numbers and the person's own stated intentions — never generic life advice.

## Inputs (all read-only — never modify them)

- `Moon/weeks/<ISO-week>/time-report.md` — the mirror: cognitive hours and **share %**
  for all eight identities, plus **Trash time** and **Invisible (unallocated)**.
- `Moon/weeks/<ISO-week>/events.json` — the actual schedule: event titles, times, and
  which identity each was scheduled under.
- `Moon/weeks/<ISO-week>/reflection.md` — the person's own answers (plan, how it went,
  stressors, future-self).
- `Moon/config/categories.md` and `categories.yaml` — what each identity *means* and its
  **core question** (the one-line test for "did this hour fund this identity?").
- `Moon/trends.csv` *(if it spans multiple weeks)* — the trajectory: is an identity
  rising or fading over time?

## Procedure

1. **Read everything above** for the target week (confirm the week first).
2. **Intention vs reality.** Put the reflection's *"What's your plan?"* and *"How did it
   go?"* next to the actual **share %**. Did the hours go where they said they wanted?
3. **Find what stands out — grounded in the data.** Look for:
   - The **underfunded** identities — especially any at **0%** (name them).
   - **Trash time** — energy-draining, negative time. Always nudge toward *reducing* it,
     even from a low number; never normalize it.
   - **Invisible %** — chores / low-return time with no clear purpose. Some is fine, but
     call it out when it *surges* and crowds the identities (compare to a typical week).
   - **Avoidance dressed as virtue** — e.g. lots of `reliable_man` admin while `builder`
     stalls, or `exceptional_people` networking standing in for real `loyal_friend` time.
   - Each funded identity against its **core question** from `categories.md`.
   - **Recall vs reality** — compare their unaided Q4 *"what did you do this week?"*
     against `events.json`. What they spotlighted, forgot, or weighted differently from
     the calendar reveals what actually holds their attention — and where memory and the
     schedule diverge. Reflect this back gently; it's a mirror, not a gotcha.
   - A **trend** if `trends.csv` has history (an identity quietly fading week over week).
4. **Give 2–4 concrete moves for next week.** Specific and schedulable, tied to *their*
   stated plan — e.g. "block 2h Sunday for `grateful_son`: call your parents" — not
   "spend more time on family." Prefer moves that convert Trash/Invisible hours into an
   underfunded identity.
5. **Write `Moon/weeks/<ISO-week>/coaching.md`** from the template, and read the key
   points back to the person.

## Rules

- **Ground every claim in the data.** Cite real hours, percentages, or event titles. No
  invented activities, no inferring beyond what's on the calendar.
- **Respect that category = intention.** Don't re-litigate how they categorized an event
  (that was their scheduling-time choice). You *may* flag when Trash/Invisible is large
  or an identity is starved — that's the point of the mirror.
- **Honest but kind.** Name the hard thing plainly, then give a path. One paragraph of
  praise is fine; don't bury the signal in it.
- **Concise.** A coaching note is a half-page, not an essay. Specific beats comprehensive.
- **Side-effect free.** Read the inputs; write only `coaching.md`. Never touch
  `events.json`, the report, or the reflection.

## Output template

```markdown
---
week: <ISO-week>
date: <YYYY-MM-DD>
type: coaching
---

# Coaching — <ISO-week>

## The mirror this week

<2–4 lines: the headline allocation — top-funded, underfunded/0%, Trash + Invisible %.>

## Intention vs reality

<Did the hours match what you said mattered in the reflection? Cite the gap or the match.>

## What stands out

- <grounded observation, with the number/event behind it>
- <avoidance-dressed-as-virtue or an identity failing its core question, if any>
- <a trend from trends.csv, if there's history>

## Moves for next week

1. <concrete, schedulable move tied to their plan>
2. <ideally converts Trash/Invisible time into an underfunded identity>
3. <optional third>
```

## Iterating this playbook

This playbook improves over time. When the person gives feedback in any session about the
coaching — what landed, what missed, what they want more or less of, or a new way they
think about an identity or a bucket — fold it into **Learned preferences** below so the
next session reflects it. Keep entries short and dated; let them accumulate.

## Learned preferences

- 2026-06-30 — **Trash time** is energy-draining/negative time: always coach to *reduce*
  it. **Invisible** is chores / low-return time: some is fine, but flag it when it
  *surges*.

## Degraded mode

- **No reflection yet** — run the reflection playbook first; coaching needs the person's
  own intentions to compare against.
- **No `trends.csv` history** — skip the trend observation; coach on this week alone.
- **A missing input** — proceed with what's present and say which signal you couldn't use.
