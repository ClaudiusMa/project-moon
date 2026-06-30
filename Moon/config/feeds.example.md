# Moon — calendar feeds (template)

Copy this to your private `Astronaut/rocket.md` and fill in your values:

    mkdir -p Astronaut && cp Moon/config/feeds.example.md Astronaut/rocket.md

`Astronaut/` is gitignored, so your secret URLs and data never leave your machine.

Each identity `id` below maps to ONE source: its Google Calendar **"Secret address in
iCal format"** URL (preferred — it auto-refreshes, so data never goes stale), or a local
`.ics` path. Keys must match the ids in [`categories.yaml`](categories.yaml). Only lines
that start with `-` are read; everything else is prose. Placeholder values (left as `<…>`)
are skipped.

- timezone: America/Los_Angeles

## Identities (one Google calendar each)

- support_self_family: <secret iCal URL or local .ics path>
- designer_taste: <secret iCal URL or local .ics path>
- builder: <secret iCal URL or local .ics path>
- reliable_man: <secret iCal URL or local .ics path>
- exceptional_people: <secret iCal URL or local .ics path>
- superman: <secret iCal URL or local .ics path>
- loyal_friend: <secret iCal URL or local .ics path>
- grateful_son: <secret iCal URL or local .ics path>

## Invisible (unallocated)

Calendars that are NOT an identity — your everyday/primary calendar, a "Trash" calendar,
etc. Their time appears as an **"Invisible (unallocated)"** slice in the weekly report, so
drift is visible without being dressed up as an identity. Optional; add one line per calendar.

- invisible: <secret iCal URL or local .ics path>
