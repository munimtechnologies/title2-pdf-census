# council-stock: what the UK's principal councils' accessibility statements say (pre-registration)

Registered 2026-11-09, before any council website was read for this study. Script:
`council_stock.py` 0.1.0 with its offline tests (`test_council_stock.py`). Made by MV2 of Munim, Inc.
with AI agents; not yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0.

## Why

Every UK council must publish an accessibility statement in the form of the model statement and
keep it under regular review (The Public Sector Bodies (Websites and Mobile Applications) (No. 2)
Accessibility Regulations 2018, SI 2018/952, regulation 8). GOV.UK's sample statement says a
statement must be reviewed at least once a year and must give the date of its last review, and its
compliance wording now names WCAG 2.2 AA.

The closest published count is accessibility.build's "State of accessibility statements, 2026"
(data of 2 September 2026): its checker found a statement for 206 of 303 UK local authorities
(68%) and scored which required sections each one has; 34 of the 206 gave no preparation or review
date. It does not report which WCAG version statements name, how old their review dates are, or
whether they keep template placeholders. MV2's school census in this repository
([SCHOOL-STOCK-RESULT.md](../uk-schools/SCHOOL-STOCK-RESULT.md)) found 327 English school
statements still carrying GOV.UK's sample fields "[email address]", "[phone number]" and "[number]".
This study asks the same questions of every principal council, where the statement is required.

## Frame (fixed before any page is read)

`council-frame.csv` (in this folder, 33,269 bytes, SHA-256 468dcfaa474411c1...; with
`council-frame.json`), built by `council_frame.py` 0.1.0 (sealed job council-frame-v1) from GOV.UK's
Local Links Manager export of 2026-11-09 (`links_to_services_provided_by_local_authorities.csv`,
SHA-256 541dfe3484a3...; Open Government Licence v3.0): for each of the 385 principal councils
(165 English districts, 62 English unitaries, 36 metropolitan boroughs, 33 London boroughs, 24
English counties, 32 Scottish councils, 22 Welsh unitaries and 11 Northern Irish districts) the
host on which most of its service links sit. No council website was requested to build it. Five
hosts are shared by councils that run one website (11 councils), so there are 379 distinct hosts;
each is read once and the councils on it are counted.

## Method

- Order: hosts sorted by SHA-256 of the seed `council-stock-2026-11` plus the host. 4 hosts at a
  time; for each host one request at a time with a 1-second pause after each.
- Home page: `https://www.<host>/`, or `https://<host>/` if the first gets no answer at all.
  `robots.txt` is read first for every host name asked; a page it disallows is not requested.
- The statement link: among the home page's links on the council's own site (its host, the host
  the home page ends on, or their subdomains), the first link whose text says "accessibility
  statement"; else the first whose address does; else the first whose text and address both
  mention accessibility and which is not an accessibility toolbar. Links to other sites are counted,
  not followed.
- If that page is not a statement but links to one (its text says "accessibility statement"), that
  one link is followed. If no statement is found this way, two fixed addresses are tried, decided
  now: `/accessibility-statement`, then `/accessibility`. At most 5 addresses per host. A 429 or 503
  is asked once more after 30 seconds.
- A page counts as a statement when it answers 200 with HTML, is not a home page, has at least
  200 characters of visible text, says "accessibility statement" and names WCAG or the enforcement
  procedure (the Equality and Human Rights Commission, the Equality Advisory and Support Service or
  the Equality Commission for Northern Ireland).
- Rules: the text is read with `statement_template_check.py 0.3.0`, byte-identical to release v0.3.0
  of MV2's free a11y-statement-check (the job compares the two before reading anything): its
  placeholder verdict, the highest WCAG version named and GOV.UK's compliance sentence.
- Dates: the latest date following "last reviewed / updated / revised" (or "reviewed / updated on")
  and the latest following "prepared / published / created / written / produced on"; the
  statement's date is the later of the two. Day-month-year, month-day-year, month-year (read as the
  month's last day), dd/mm/yyyy and yyyy-mm-dd are read; years outside 2018-2027 and impossible
  dates are not.
- Stored per host: status, how the statement was found, its address, text length and SHA-256,
  rule ids, version, dates and flags. No page text and no person's name is stored.

## Gates (nothing is graded unless all hold)

- P0: this file is on main and the checker matches the release.
- F1: `council-frame.csv` matches the bytes above: 385 councils, 379 hosts.
- G1 (at least 90% of hosts answered): any HTTP status, including a robots.txt answer.

## Predictions (fixed before any page is read)

- N1 (at least 85% of the 379 hosts) serve a statement found this way. accessibility.build found
  68%; this predicts most of the gap is how statements were looked for.
- N2 (at most 5 hosts) serve a statement with a 0.3.0 placeholder.
- N3 (at least 60% of read statements name WCAG 2.2 as the highest version).
- N4 (at least 25% of dated statements carry a statement date before 2025-11-01), that is, were
  last reviewed (or prepared) more than a year before this census. Graded only with at least 100
  dated statements; N3 only with at least 100 read statements.

The result is published whether the predictions hold or not.

## Described, not graded

Status of every host and its home page; how each statement was found; councils behind the found
statements; highest WCAG version; statements with GOV.UK's compliance sentence; statements without
a date; date source and year; placeholder rule ids and hosts; statements on another host; links to
another site; addresses blocked by robots.txt; distinct texts; all of these by kind of council.

## Limits

A statement that is linked only from another page, served on another site, published as a PDF, or
behind a firewall that refuses this reader is missed, so a statement not found here is not proof
that a council has none. A date is what the statement says, not when it was really reviewed, and an
up-to-date date says nothing about whether the statement is accurate. One page per council, read
once, on one day. The placeholder rules are 0.3.0's, unchanged.
