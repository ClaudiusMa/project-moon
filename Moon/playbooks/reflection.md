# Reflection Playbook

Engine B's weekly ritual. An agentic tool (or a human) follows this playbook to run
a short guided reflection and save it as the week's `reflection.md`. It is
**tool-agnostic** — nothing here depends on a specific assistant.

## Cadence

The review is done the **following week**, looking back at the week that just closed —
so the framing is "last week." The review also sets the plan for the week ahead, which
carries forward: this reflection's *"What do you plan to do next week?"* becomes the next
reflection's *"What's your plan?"*, so each week you see plan versus reality.

## Purpose

Bare questions — no prompts, no hints, no auto-fill — answered in one pass. The absence
of scaffolding is the point: what the person recalls unaided, and what they mention
first, reveals how intentionally they lived and what actually weighs on them. Happiness
is a free list. *"What's your plan?"* is **carried in** from last week (not asked).

## Inputs (read-only)

- **Target week** — the just-completed ISO week to review (default: most recent
  completed week). Confirm it.
- **Previous reflection** — read only to carry its *"What do you plan to do next week?"*
  forward into this reflection's *"What's your plan?"*. If there's none, that section is
  "No plan from last week."

This playbook does **not** read `events.json` and writes nothing except the reflection
file. Keeping recall unaided is deliberate — the calendar/data view belongs to the coach.

## Output

- **`Moon/weeks/<ISO-week>/reflection.md`** — written from the template at the bottom.
  Gitignored (personal) and dated: do **not** overwrite an existing reflection without
  explicit confirmation.

## Procedure

1. **Pick the week** (the completed week to review) and confirm it.
2. **Carry the plan.** Read the previous reflection's *"What do you plan to do this
   week?"* and place it in this reflection's *"What's your plan?"* (verbatim). If there's
   no prior reflection, use "No plan from last week."
3. **Present the bare questions all at once** — exactly as written below, nothing added.
   Show the carried plan as context. Let the person answer in one pass.
4. **Proofread each answer** under the rule below.
5. **Write the file** from the template and read it back.

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
4. What do you plan to do next week?
5. What might stress you up?
6. Future-self: would I do anything differently?

Agent notes (do **not** show these):

- **Happiness** is a free list of what made them happy/proud — capture an optional 1–10
  only if they volunteer it; never ask for one.
- **"What's your plan?"** is carried from the previous reflection's *"What do you plan to
  do this week?"* — show it as context, never ask it fresh.
- Keep every question **unaided** — no calendar drafts, no event lists, no hints. The
  unprompted recall is the signal; the coach contrasts it with the schedule afterward.
- **"What do you plan to do next week?"** carries forward to next week's *"What's your
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

<carried from last week's "What do you plan to do next week?"; "No plan from last week." if none>

## What did you do last week?

<proofread answer>

## How did it go?

<proofread answer>

## What do you plan to do next week?

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

- **No previous reflection** — *"What's your plan?"* is "No plan from last week."
- **Reflection already exists for the week** — confirm before overwriting.
