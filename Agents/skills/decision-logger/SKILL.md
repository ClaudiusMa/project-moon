---
name: decision-logger
description: Record a critical human decision in Human/decisions.md. Use when the user explicitly asks to log, save, capture, or document a resolved product, architecture, process, or project decision.
---

You are the **Decision Logger**. Your job is to record critical human decisions in `Human/decisions.md`.

## When To Use

- The user explicitly asks to log, save, capture, or document a decision
- A discussion ends with a clear, durable decision the user wants preserved for future chats
- The decision affects product direction, architecture, process, scope, or another durable project constraint

Do **not** use this skill for open questions, loose brainstorming, or routine status updates.

## Read Scope

Read only what you need:

1. `Human/decisions.md`
2. A clear version source only if one obviously exists, for example `VERSION`, `package.json`, `pyproject.toml`, `Cargo.toml`, or another file the user explicitly points you to
3. The current conversation for the decision details

Do **not** read other `Human/` files unless the user points you there.

## Output File

- `Human/decisions.md` only

## File Invariants

Keep the file in this shape:

```md
# Decisions
Version: {PROJECT_VERSION_OR_CURRENT}

Use this as the human decision log for the current project version or working phase.
Archive or reset this file before changing the version header convention.

## Format

- Date:
- Decision:
- Why:
- Tradeoffs:
- Follow-up:

## Decisions

- None recorded yet.
```

## Logging Rules

- Keep one version header at the top of the file. Do not repeat the version inside each decision entry.
- If a reliable project version source exists, use it for the file version.
- If no reliable version source exists, preserve the current version header instead of inventing one.
- If the file already contains a different version and real decisions are present, do **not** silently relabel old decisions under the new version. Tell the user the log appears to belong to an older version and should be archived or reset first.
- Remove `- None recorded yet.` when adding the first real entry.
- Append new decisions under `## Decisions`.
- Keep the exact field list for each decision:
  - `Date:` `YYYY-MM-DD`
  - `Decision:` one clear sentence naming the choice
  - `Why:` the main reason for the choice
  - `Tradeoffs:` the main cost, downside, or rejected alternative
  - `Follow-up:` the next concrete action, or `None`
- Keep entries concise and factual. Prefer one short paragraph or sentence per field.
- If the conversation does not supply enough detail to write a reliable entry, ask the user one short clarifying question instead of guessing.

## Completion

- Update `Human/decisions.md`.
- Confirm what decision was logged and which version header the file now carries.
