# Reflection Playbook

Engine B's weekly ritual. An agentic tool (or a human) follows this playbook to run
a short guided reflection and save it as the week's `reflection.md`. It is
**tool-agnostic** — nothing here depends on a specific assistant.

## Purpose

Six questions, asked **one at a time**, lightly proofread, and saved as a clean
dated record for one ISO week. The "what did you do this week?" answer is
auto-drafted from that week's events so the person starts from a recap, not a blank
page.

## Inputs

- **Target week** — an ISO week key, `YYYY-Www` (e.g. `2026-W24`). Default to the
  **most recent completed week** (last Monday–Sunday in local time). Confirm the
  week with the person before starting.
- **`Moon/weeks/<ISO-week>/events.json`** *(optional, read-only)* — used only to
  auto-draft question 4. This playbook **never writes** `events.json`. If the file
  is missing, skip the auto-draft and ask question 4 cold (see Degraded mode).

## Output

- **`Moon/weeks/<ISO-week>/reflection.md`** — written from the template at the
  bottom. This file is gitignored (it is personal) and is a dated record: do **not**
  overwrite an existing reflection for the week without explicit confirmation.

## Procedure

1. **Pick the week.** Resolve the target ISO week and confirm it with the person.
2. **Prep the recap (for Q4).** If `events.json` exists for the week, read it
   (read-only) and build the draft described under question 4. If not, note that
   you'll ask question 4 directly.
3. **Ask the six questions one at a time.** Ask a question, wait for the answer,
   then move on. Do not batch them or show the next question before the current one
   is answered. Keep the person's own voice.
4. **Proofread each answer** as you receive it, under the rule below.
5. **Write the file** from the template once all six are answered. Read it back to
   the person.

## Proofreading rule

After each answer, fix only **typos, spelling, punctuation, and grammar**. Do
**not** change meaning, do not rephrase for style, do not add or remove ideas, and
do not "improve" the content. Preserve the person's voice and word choices. If a
correction might change the meaning, leave the original untouched. The reflection
is *their* record; you are a copy-editor, not a co-author.

## The six questions

Ask these in order, one at a time. The wording in **bold** is the question to ask;
the note under it is guidance for you, not something to read aloud.

1. **Happiness — how are you feeling about this week?**
   Let them answer freely. If they give a number, capture it (a 1–10 read is handy
   for trends); a number is optional, never required.

2. **What's your plan?**
   What they intend for the coming week — the shape they want it to take.

3. **How did it go?**
   How the week that just ended actually went, against what they'd hoped for it.

4. **What did you do this week?**
   **Auto-draft this from `events.json`.** Read the week's events, group their
   `title`s by `category`, drop exact duplicates, and present a short first-person
   recap as a *draft*, e.g.:

   > Here's what your calendar says you did this week — edit or add anything:
   > - **Build:** Moon ingestion script, refactor parser
   > - **Workout:** Morning run, climbing
   > - **Social:** Dinner with A, call with family

   Use only the event titles — don't invent activities or infer beyond what's
   there. The person edits, trims, or adds to the draft; their final version is the
   answer. (Degraded mode: if there's no `events.json`, just ask the question
   directly and let them recall it themselves.)

5. **What might stress you up?**
   What's coming that could weigh on them — deadlines, obligations, unknowns.

6. **Future-self: would I do anything differently?**
   Looking back from a little further out, what they'd change.

## Output template

Write `Moon/weeks/<ISO-week>/reflection.md` exactly in this shape (Obsidian-friendly
frontmatter + headings). Fill `week` with the ISO key and `date` with the date the
reflection was completed. `happiness` is optional — include it only if they gave a
number; otherwise omit that line.

```markdown
---
week: <ISO-week>            # e.g. 2026-W24
date: <YYYY-MM-DD>          # date this reflection was written
type: reflection
happiness: <n/10>           # optional; omit if not given
---

# Reflection — <ISO-week>

## Happiness — how are you feeling about this week?

<proofread answer>

## What's your plan?

<proofread answer>

## How did it go?

<proofread answer>

## What did you do this week?

<proofread, person-edited recap>

## What might stress you up?

<proofread answer>

## Future-self: would I do anything differently?

<proofread answer>
```

## Degraded mode

- **No `events.json` for the week** — skip the auto-draft; ask question 4 directly.
  Everything else runs unchanged.
- **Reflection already exists for the week** — do not overwrite it silently. Show
  the person the existing reflection and confirm before replacing it.
- **Reading `events.json` must stay side-effect free** — never modify or delete it
  from this playbook.
