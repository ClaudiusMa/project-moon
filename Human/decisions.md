# Decisions
Version: current

<!--
## How To Use This File

- Record only durable human decisions here.
- Keep one version or phase header at the top if your team groups decisions that way.
- Do not use this file for open questions, routine status updates, or loose brainstorming.
-->

Use this as the human decision log for the current project version or working phase.
Archive or reset this file before changing the version header convention.

## Format

- Date:
- Decision:
- Why:
- Tradeoffs:
- Follow-up:

## Decisions

- Date: 2026-06-14
- Decision: Build Project Moon as a tool-agnostic, open-source system — plain-markdown playbooks plus portable scripts and data conventions anchored on AGENTS.md — that any agentic coding tool can run (Claude Code, Codex, etc.), not Claude-Code-only features.
- Why: It is an open-source project; users may run it under Claude Code, Codex, or other agents, so the core cannot depend on one tool's proprietary capabilities.
- Tradeoffs: Cannot lean on Claude-Code conveniences (MCP, skills, routines) as the core; deterministic logic must live in portable scripts; more upfront design for portability. Tool-specific adapters become optional layers on top.
- Follow-up: Decide the portable calendar-access and scheduling paths that work across tools.

- Date: 2026-06-14
- Decision: Run weekly as an interactive session (compute stats, then guided reflection) with an optional scheduled nudge that pre-pulls the calendar stats; scheduling is a per-tool adapter, not a hard dependency.
- Why: Reflection needs the human in the loop, the nudge preserves the weekly habit, and the system must still work on tools that lack scheduling (degrades to manual/on-demand).
- Tradeoffs: Not fully unattended; the scheduler is implemented separately per tool (system cron / Claude routine / Codex equivalent).
- Follow-up: None — revisit when selecting scheduler adapters.

- Date: 2026-06-14
- Decision: Store reflections and time reports as local markdown files in a `Moon/` data directory as the source of truth, authored to be Obsidian-vault compatible; no Notion or other external integration in v1.
- Why: Maximum flexibility, fully version-controlled, tool-agnostic, and directly usable inside Obsidian.
- Tradeoffs: No Notion-style database/UI; Obsidian features (wikilinks, frontmatter) become conventions the writers must follow.
- Follow-up: None.

- Date: 2026-06-14
- Decision: Time accounting reads the personal Google Calendar only (excludes the work calendar) for v1.
- Why: Fits the personal-development framing (Learn/Build/Workout/Social) and keeps work meetings out of the signal.
- Tradeoffs: Misses time spent in work meetings, so the weekly picture is partial.
- Follow-up: None.

- Date: 2026-06-14
- Decision: Compute cognitive hours by ceiling each event up to the next whole hour, counting every event (no minimum duration) and merging overlapping events so double-booked time is not double-counted.
- Why: Attention comes in blocks and the leftover minutes of a block are unusable, so a 45-minute block costs a full cognitive hour; counting all events also captures small context-switch costs.
- Tradeoffs: Tiny events (e.g. a 10-minute standup) cost a full cognitive hour, which can over-count. Flagged by the user as likely to change.
- Follow-up: Revisit the no-floor rule after reviewing real weekly data; tune if small events distort totals.

- Date: 2026-06-14
- Decision: Ingest one private `.ics` (iCal) feed per category. The user keeps a separate Google calendar per category (confirmed by a real export: `X-WR-CALNAME:Building`), so an event's category is the calendar it lives on (a configured feed→category map), never a title prefix. Event titles stay free-form descriptions of the actual work and are used only as reflection context ("what did you do this week"), not for categorization. No Google Cloud project, no OAuth, no color, no title prefixes, and no LLM categorization step.
- Why: The user already organizes time by category-named calendars and does not want to prefix every event. Category-by-calendar is fully deterministic and 100% precise, which removes the entire LLM-classification engine and makes the weekly time math reproducible across any tool. `.ics` carries exact start/end times plus the calendar name.
- Tradeoffs: Requires one secret `.ics` URL per category calendar (~8 feeds) and discipline to file each event on the correct calendar; an event on the wrong calendar is miscategorized with no automatic correction. Supersedes the earlier title-prefix-convention decision, which is withdrawn.
- Follow-up: Map each category to its calendar feed URL, store the secret URLs in gitignored config, and decide the cross-category overlap attribution rule during implementation planning.
