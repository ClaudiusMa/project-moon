# Categories — your identity accounts

Each category is an **identity account**: a person you are choosing to become, and the
calendar where you deposit the hours that fund it. The weekly report is the statement on
those accounts — an honest mirror of whether the time you actually scheduled went to the
identities you say you care about.

> **Make it yours.** Everything below is the maintainer's **example** — eight identities
> plus two diagnostic buckets (Trash time, Invisible). It is *not* a prescribed taxonomy.
> Replace it with the identities *you* are investing in (3–8 is plenty), each its own
> Google calendar, and adjust the buckets to whatever helps you see your week honestly.
> Use the examples as a model for *how to think about choosing them*, not as the list.

This file is the human constitution for your set. Its machine-readable twin is
[`categories.yaml`](categories.yaml) (`id → display_name → core_question`), which the
engine reads; your feed list (`Astronaut/rocket.md`) is keyed by the same `id`s, and the
reports render each `display_name`. Keep all three in sync.

## How an account is chosen

- **An identity is chosen at scheduling time, never inferred afterward.** Putting an
  event on a calendar is you declaring *why* you scheduled the time — which identity
  it is meant to fund. The category is that declaration. Nothing reads the title to
  guess it, so the same calendars always produce the same numbers.
- **One event → one calendar → one identity.** No event funds two accounts. If a
  single block genuinely serves two identities, pick the one you scheduled it *for*
  (see the tie-breakers) and let the other be a happy side effect.
- **Secondary effects belong to the reflection, not the ledger.** A workout that also
  happened to be time with a friend still counts once, on whichever identity was the
  point. The richness — "and it was also good for X" — is what the weekly reflection
  is for.
- **The names and `id`s are the contract.** The calendars, `feeds.yaml`,
  `categories.yaml`, the reports, and `trends.csv` all key off them. This set is
  `identity_v1`; changing it is a breaking change (see [The contract](#the-contract)).

## The eight identities (the maintainer's example)

### I support myself and family — `support_self_family`
> *Did my hours this week secure me and the people I provide for?*

**The account.** The provider. Hours that earn the living and protect the material
security of you and the people who depend on you — the work that pays, and the
planning that keeps the foundation solid.

**Goes here.** Focused blocks at the job, interviews and reviews, the work that
advances your earning, financial planning, the deliberate career moves that fund the
life.

**Not here.** Making something for the craft or joy of it (that's *builder*); being
near impressive people for your own growth (*exceptional people*). The test is
provision, not interest.

### I am a designer with exceptional taste — `designer_taste`
> *Did I sharpen my eye and raise my bar for what's good?*

**The account.** The cultivated eye. Hours spent raising your standard for quality and
beauty — studying great work, critiquing, learning *why* something is excellent,
training judgment until "good enough" stops being enough.

**Goes here.** Studying design and craft, close-reading great work, galleries and
museums with intent, design critique, deliberate practice aimed at taste rather than
output.

**Not here.** The act of making and shipping the thing (*builder*). This account is
the judgment behind the work; *builder* is the work.

### I'm a builder — `builder`
> *Did I make something real — ship, not just plan?*

**The account.** The maker. Hours where something that didn't exist now does — code,
writing, prototypes, creative output. Building for the act of building.

**Goes here.** Coding a side project, writing, prototyping, creative production,
shipping.

**Not here.** Studying what's good without making it (*designer taste*); work done
chiefly to earn (*support myself and family*). Same keyboard, different intent — sort
by why it is on the calendar.

### I am a helpful man — `reliable_man`
> *Did I keep my word and stay on top of what I own?*

**The account.** The dependable one. The unglamorous follow-through that makes you
trustworthy — commitments kept, responsibilities handled, the admin and maintenance
that keep life from quietly falling apart.

**Goes here.** Chores, errands, admin, appointments kept, paying bills, planning and
tidying your systems, the boring tasks you said you would do.

**Not here.** Paid work (*support myself and family*); training the body (*superman*).
This is about order and keeping your word, not income or fitness.

### I am surrounded by exceptional people — `exceptional_people`
> *Did I put myself near people who raise my standard?*

**The account.** Deliberate proximity to excellence. Hours spent with people who raise
your game — mentors, peers who stretch you, rooms where the bar is high — chosen
because of who they make you.

**Goes here.** Coffee or sessions with someone you learn from, mentorship, high-signal
communities and events, time that pulls your standard up.

**Not here.** Friends you love regardless of what they "do for you" (*loyal friend*);
networking aimed purely at income (*support myself and family*).

### I am a superman — `superman`
> *Did I build a body and energy that can carry the rest?*

**The account.** The body and the engine. Hours invested in physical capability,
health, and energy — training, sport, movement, and the recovery that powers
everything else you do.

**Goes here.** The gym, runs, sports, mobility, physical challenges, deliberate
recovery scheduled as training.

**Not here.** An activity that is really about the person you are with (a hike that is
mostly catching up → *loyal friend*). Sort by the primary intent.

### I am a loyal friend — `loyal_friend`
> *Did I show up for the people who count on me?*

**The account.** Showing up. Hours given to the friends you choose to stand by —
presence, loyalty, being there, the relationships you maintain out of love rather than
advantage.

**Goes here.** Time with friends, calls, showing up when it matters, gatherings, being
present for the people you would drop things for.

**Not here.** Family you were born to (*grateful son*); company kept mainly to grow
(*exceptional people*).

### I am a grateful son — `grateful_son`
> *Did I stay close to and honor the family I come from?*

**The account.** Roots and gratitude. Hours that honor the family you come from —
staying close to parents and family, showing care, repaying in presence some of what
you were given.

**Goes here.** Calls and visits home, time with parents and family, acts of care for
them, family trips and traditions.

**Not here.** Chosen friends (*loyal friend*); providing materially for your own
household (*support myself and family*). This account is presence and gratitude toward
where you came from.

## When one event could fund two identities

The feed is the only source of truth, so the question is never "what does this event
look like?" but **"which identity did I schedule it for?"** Decide once, when it goes
on the calendar. Worked tie-breakers:

- **A portfolio piece.** Making it for the craft → *builder*. Sharpening its taste and
  standard → *designer taste*. Doing it as paid client work → *support myself and
  family*.
- **Coffee with someone.** They raise your standard and you are there to learn →
  *exceptional people*. They are a friend you are showing up for → *loyal friend*. It
  is purely to advance your livelihood → *support myself and family*.
- **Sailing (or any workout that is not only a workout).** The point is training and
  health → *superman*. The point is the friend you are sailing with → *loyal friend*.
- **Chores and admin.** Routine responsibility and follow-through → *helpful man*. A
  "chore" that is actually a paid gig → *support myself and family*.
- **Career networking.** To stand near excellence → *exceptional people*. To grow
  income and security → *support myself and family*. To be loyal to a friend → *loyal
  friend*.

When you are genuinely torn, **pick the identity you would be proud to say you
funded** — the real reason it is on the calendar. If you still cannot decide, that
hesitation is good reflection material; it is not a reason to split one event across
two accounts.

## Beyond the eight: Trash time and Invisible

None of the eight identities is a place for time you *don't* want to fund — there is no
"Trash" identity, on purpose. Every account above is something you are **investing in
becoming**, and giving drift its own identity would quietly legitimize it ("at least it's
tracked") and invite gaming. But the report still surfaces two **non-identity buckets**,
because what *doesn't* fund an identity is worth seeing:

- **Trash time** (`trash_time`) — time that brings negative things and costs you energy:
  doomscrolling, draining arguments, the stuff you regret. It gets its own row, shown
  even at 0h, precisely so you confront it and **reduce** it. Lower is better.
- **Invisible (unallocated)** (`invisible`) — chores, errands, admin, and low-return time
  with no clear purpose or payoff. Some is unavoidable and fine; the signal is **don't let
  it surge** — when it climbs, it's crowding out the identities you care about.

Both are diagnostic, not identities: no core question, not in `categories.yaml`, each on
its own calendar (mapped via `trash_time:` / `invisible:` in `rocket.md`). Deeper honesty
about drift still belongs in the **weekly reflection and coaching**, not the deterministic
ledger.

## The contract

- The eight `id`s and `display_name`s above are fixed and must stay byte-identical
  across [`categories.yaml`](categories.yaml), `feeds.yaml`, the reports, and
  `trends.csv`.
- This set is stamped `category_set_version: identity_v1`. It is a **breaking change**
  from the original activity categories (Learn / Build / Career / …); there is no
  automatic migration, and that is fine — it is a clean start with no real trend
  history to lose.
- Each feed key in `Astronaut/rocket.md` is one of the `id`s above (plus the optional
  `trash_time` / `invisible` buckets); see [`feeds.example.md`](feeds.example.md) for the
  template.
