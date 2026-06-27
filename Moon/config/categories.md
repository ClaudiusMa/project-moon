# Categories

Moon has **eight fixed categories**. Each maps to exactly one Google calendar, and
an event's category is simply the calendar it lives on — titles are free-form notes
for you and are never parsed to guess a category. Keep this set stable: it is the
key shared by the calendars, `feeds.yaml`, the cognitive-hour reports, and
`trends.csv`.

| Category | What goes here |
| --- | --- |
| **Learn** | Deliberate study and skill-building: courses, reading, tutorials, deep dives. |
| **Build** | Making things: coding, side projects, writing, creative production. |
| **Career** | Job and professional growth: focused work blocks, interviews, networking, planning. |
| **Habit** | Recurring personal-maintenance routines: meditation, journaling, chores, admin. |
| **Workout** | Physical training and movement: gym, runs, sports, mobility. |
| **Social** | Time with other people: friends, family, dates, calls, gatherings. |
| **Exploration** | Open-ended discovery and play: travel, wandering, new experiences, goalless hobbies. |
| **Trash** | Low-value time you'd rather reclaim: doomscrolling, aimless browsing, time sinks. |

## Notes

- These descriptions are starting definitions — tune the wording to match how you
  actually sort your calendars. The **names** are the contract; keep them exactly
  as above so the calendars, config, and reports line up.
- One event lives on one calendar, so it has one category. If something genuinely
  spans two (a workout with a friend), put it where it mattered most for that week.
- Each category name must match a calendar key in `feeds.yaml`
  (see [`feeds.example.yaml`](feeds.example.yaml) for the template).
