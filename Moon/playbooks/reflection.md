# Reflection Playbook

Engine B's weekly ritual. An agentic tool (or a human) follows this playbook to run
a short guided reflection and save it as the week's `reflection.md`. It is
**tool-agnostic** — nothing here depends on a specific assistant.

## Cadence

The review is done the **following week**, looking back at the week that just closed —
so the framing is "last week." The review also sets the plan for the week ahead, which
carries forward: this reflection's *"What do you plan to do this week?"* becomes the next
reflection's *"What's your plan?"*, so each week you see plan versus reality.

## Purpose

Rewind the week before asking for reflection. First show the exact calculated time spent
in every identity and non-identity bucket, then give a short, factual recap of what was
on the calendar. This re-anchors the person's memory before they answer the bare
questions in one pass. Happiness is a free list. *"What's your plan?"* is **carried in**
from last week (not asked).

## Inputs (read-only)

- **Target week** — the just-completed ISO week to review (default: most recent
  completed week). Resolve it before beginning and state it in the rewind.
- **Time report** — read `Moon/weeks/<ISO-week>/time-report.md` for Engine A's exact
  cognitive hours, share percentages, and full category list.
- **Events** — read `Moon/weeks/<ISO-week>/events.json` for calendar titles, times, and
  their scheduling-time identity.
- **Previous reflection** — read only to carry its *"What do you plan to do this week?"*
  forward into this reflection's *"What's your plan?"*. If there's none, that section is
  "No plan from last week."

The report and events are **read-only**. This playbook writes nothing except the
reflection file.

## Output

- **`Moon/weeks/<ISO-week>/reflection.md`** — written from the template at the bottom.
  Gitignored (personal) and dated: do **not** overwrite an existing reflection without
  explicit confirmation.

## Procedure

1. **Pick the week** (the completed week to review) and state it. With no explicit week,
   use the most recent completed ISO week; do not ask a week-selection question before
   showing the rewind.
2. **Read the computed week.** Read that week's `time-report.md` and `events.json`. Never
   calculate, estimate, re-round, or correct a number yourself; all numbers must be
   copied from Engine A's report.
3. **Carry the plan.** Read the previous reflection's *"What do you plan to do next
   week?"* and place it in this reflection's *"What's your plan?"* (verbatim). If there's
   no prior reflection, use "No plan from last week."
4. **Present the week rewind before asking anything.** Use the exact format and rules in
   **Week rewind output** below. Finish the entire rewind before presenting intake.
5. **Present the bare questions all at once** — exactly as written below, nothing added
   between them. Show the carried plan as context. Let the person answer in one pass.
6. **Proofread each answer** under the rule below.
7. **Write the file** from the template and read it back.

## Week rewind output

Present this block before the six questions:

1. `# Week rewind — <ISO-week>` and the report's date range.
2. `## Time by category` followed by the report's **entire Summary table verbatim** —
   every configured identity, including 0h rows, plus Trash, Invisible, any unexpected
   bucket, and Total. Do not recalculate or selectively omit rows.
3. `## What was on your calendar` followed by a concise factual recap (normally 3–7
   bullets) made from `events.json`:
   - Lead with the largest allocations using the report's exact hours and shares.
   - Group calendar titles into useful memory cues by identity and/or day; mention real
     titles, and preserve the calendar's identity assignment.
   - Name identities at 0h and report Trash/Invisible exactly as shown, even when 0h.
   - `events.json` retains Invisible events from 12:00 a.m.–7:00 a.m. even though Engine
     A excludes that interval. They may be mentioned as schedule context, but never imply
     that the excluded portion contributed to the report's Invisible hours or share.
   - `events.json` also retains the full interval for timed events lasting at least
     24 hours even though Engine A removes their 12:00 a.m.–7:00 a.m. windows. Never
     imply that those excluded overnight portions contributed to an identity's hours.
   - Describe these as **scheduled activities**, not proof that they happened.
   - Do not coach, judge the allocation, infer intent from titles, or preview answers.
4. `## Carried plan` followed by the prior week's plan (or "No plan from last week.").

Only after this whole block is visible should the six questions appear.

## Proofreading rule

Fix only **typos, spelling, punctuation, and grammar**. Do **not** change meaning,
rephrase for style, or add/remove ideas. Preserve the person's voice and word choices
(including casual ones). If a correction might change meaning, leave it. You are a
copy-editor, not a co-author.

## The questions the person answers

Present these verbatim, all together, with **nothing added** — no guidance, examples, or
drafts. (*"What's your plan?"* is not here — it is carried in from last week.)

1. Happiness
2. What did you do last week?
3. How did it go?
4. What do you plan to do this week?
5. What might stress you up?
6. Future-self: would I do anything differently?

Agent notes (do **not** show these):

- **Happiness** is a free list of what made them happy/proud — capture an optional 1–10
  only if they volunteer it; never ask for one.
- **"What's your plan?"** is carried from the previous reflection's *"What do you plan to
  do this week?"* — show it as context, never ask it fresh.
- The rewind is context, not a draft response. Never pre-fill an answer from calendar
  titles or turn the recap into coaching.
- **"What do you plan to do this week?"** carries forward to next week's *"What's your
  plan?"*.

## Output template

Write `Moon/weeks/<ISO-week>/reflection.md` in this shape (Obsidian-friendly frontmatter
+ headings). `happiness` is optional — include it only if they gave a number.

```markdown
---
week: <ISO-week>            # e.g. 2026-W24
date: <YYYY-MM-DD>          # date this reflection was written
type: reflection
happiness: <n/10>           # optional; omit if not given
---

# Reflection — <ISO-week>

## Happiness

<proofread list>

## What's your plan?

<carried from last week's "What do you plan to do this week?"; "No plan from last week." if none>

## What did you do last week?

<proofread answer>

## How did it go?

<proofread answer>

## What do you plan to do this week?

<proofread answer — carries to next week's "What's your plan?">

## What might stress you up?

<proofread answer>

## Future-self: would I do anything differently?

<proofread answer>
```

## Next step

After the reflection is saved, run the **coaching playbook**
([`coaching.md`](coaching.md)): it reads this reflection plus the week's
`time-report.md` and `events.json` and gives grounded advice for the week ahead.

## Degraded mode

- **No time report or events** — run Engine A for the target week first. Do not begin the
  six-question intake without showing the calculated allocation and calendar rewind.
- **No counted events** — still show the complete Summary table and say that no counted
  calendar events were recorded for the week.
- **No previous reflection** — *"What's your plan?"* is "No plan from last week."
- **Reflection already exists for the week** — show the rewind first, then confirm before
  starting intake or overwriting it.
