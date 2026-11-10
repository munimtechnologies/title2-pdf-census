# govuk-stock: what the accessibility statements of UK government organisations with their own website say (pre-registration)

Registered 2026-11-10, before any organisation's own website was read for this study. Scripts:
`govuk_stock.py` 0.1.0 with its offline tests (`test_govuk_stock.py`), which builds its frame with
`govuk_frame.py` 0.1.0 (tests: `test_govuk_frame.py`) and reads each site with the unchanged
`council_stock.py` 0.1.0 and `statement_template_check.py` 0.3.0 already in this repository. Made
by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text and
the data CC BY 4.0. Organisation names, statuses and addresses come from GOV.UK (Open Government
Licence v3.0).

## Why

Public sector bodies in the UK must publish an accessibility statement for each website and keep
it under regular review (The Public Sector Bodies (Websites and Mobile Applications) (No. 2)
Accessibility Regulations 2018, SI 2018/952, regulation 8). GOV.UK's sample statement asks for a
review at least once a year, and the Government Digital Service has monitored against WCAG 2.2 AA
since October 2024.

Most central government organisations publish on GOV.UK, which has one statement for the whole
site. The ones GOV.UK marks as "exempt", "joining" or "transitioning" run a website of their own
(agencies, non-departmental public bodies, public corporations and others), and GOV.UK's content
item for each gives that website's address. MV2's census of the UK's principal councils
([COUNCIL-STOCK-RESULT.md](../uk-councils/COUNCIL-STOCK-RESULT.md)) found a statement on 284 of
379 council hosts; 191 of the 284 name WCAG 2.2, and 105 of 271 dated statements (38.75%) carry a
date more than a year old. Accessibility.build's September 2026 review covers councils and the
FTSE 100. Searches on 2026-11-10 found no published count of which WCAG version these central
bodies' statements name or how old their review dates are; GDS publishes monitoring summaries,
not a table per body. This study asks the council questions of them, with the same reader.

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job first runs `govuk_frame.py` 0.1.0, which reads only `www.gov.uk/api`: every page of the
organisations list (`/api/organisations`), then the content item
(`/api/content/government/organisations/<slug>`) of every organisation whose GOV.UK status is
exempt, joining or transitioning. The address is `details.organisation_govuk_status.url`; its host
(without `www.`) is the organisation's own host unless it is `gov.uk` or a
`.publishing.service.gov.uk` host. It writes `govuk-frame.csv` and `govuk-frame.json`, and the
result records the frame's size and SHA-256. The frame is the distinct own hosts of organisations
with one of those statuses whose content item was read; organisations on one host are counted on
it, and the host is named after the first of them by slug.

What was looked at before registering, all on GOV.UK and none on an organisation's own site: page 1
of the organisations list (1,273 organisations in 64 pages on 2026-11-10; three entries read in
full); GOV.UK's search API counts of organisations by state (exempt 302, joining 14, transitioning
1 on 2026-11-10); and one content item, Active Travel England (exempt, with its own website).

## Method

- Order: hosts sorted by SHA-256 of the seed `govuk-stock-2026-11` plus the host. 4 hosts at a
  time; for each host one request at a time with a 1-second pause after each. The crawl stops
  starting new hosts after 120 minutes; a host not started counts as not answered.
- Each host is read exactly as in the council census, with `council_stock.py` 0.1.0 unchanged:
  `robots.txt` is read first and a page it disallows is not requested; the home page
  `https://www.<host>/` (or `https://<host>/` if the first gets no answer at all); the best
  statement link on the organisation's own site; one more hop from a page that links to the
  statement; then two fixed addresses, `/accessibility-statement` and then `/accessibility`. At
  most 5 addresses per host. A 429 or 503 is asked once more after 30 seconds.
- A page counts as a statement when it answers 200 with HTML, is not a home page, has at least 200
  characters of visible text, says "accessibility statement" and names WCAG or the enforcement
  procedure.
- Rules: `statement_template_check.py 0.3.0`, byte-identical to release v0.3.0 of MV2's free
  a11y-statement-check (the job compares the two before any organisation's site is requested), and
  `council_stock.py`'s date reader: the statement's date is the later of the latest "last reviewed /
  updated" date and the latest "prepared / published on" date.
- Stored per host: its organisations' slug, title, type and status, the status of the read, how the
  statement was found, its address, text length and SHA-256, rule ids, WCAG version, dates and flags.
  No page text and no person's name is stored.

## Gates (nothing is graded unless all hold)

- P0: this file is on main, and the checker matches the release.
- F1 (checked on the frame before any website is read; if it fails, no website is requested): at
  least 1,000 organisations read from the list, at most 10 content items that could not be read,
  at most 2 rows dropped by the publishing tool's blocked word, and at least 100 distinct hosts.
- G1 (at least 90% of hosts answered): any HTTP status, including a robots.txt answer.

## Predictions (fixed before any website is read)

- O1 (at least 75% of own hosts) serve a statement found this way. The same reader found one on
  74.93% of council hosts; these bodies are monitored centrally, so this predicts at least as many.
- O2 (at most 3 hosts) serve a statement with a 0.3.0 placeholder (councils: 1).
- O3 (at least 70% of read statements name WCAG 2.2 as the highest version), that is, ahead of the
  councils' 67.25%.
- O4 (at least 25% of dated statements carry a statement date before 2025-11-01), that is, were
  last reviewed (or prepared) more than a year before this census (councils: 38.75%). O3 is graded
  only with at least 60 read statements, and O4 only with at least 60 dated statements.

The result is published whether the predictions hold or not.

## Described, not graded

Status of every host and its home page; how each statement was found; organisations behind the
found statements; highest WCAG version; statements with GOV.UK's compliance sentence; statements
without a date; date source and year; placeholder rule ids and hosts; statements on another host;
links to another site; addresses blocked by robots.txt; distinct texts; all of these by type of
organisation; and from the frame, organisations without an address, addresses on GOV.UK itself and
hosts shared by several organisations.

## Limits

GOV.UK's status and address are what GOV.UK says on the day; an organisation may run several sites,
and only the one GOV.UK names is read. Not every organisation in the frame is necessarily covered by
the regulations (public service broadcasters, for one, are excluded). A statement linked only from
another page, served on another site, published as a PDF, or behind a firewall that refuses this
reader is missed, so a statement not found here is not proof that an organisation has none. A date
is what the statement says, not when it was really reviewed, and an up-to-date date says nothing
about whether the statement is accurate. One page per host, read once, on one day. The placeholder
rules are 0.3.0's, unchanged. This counts what statements say; it does not test whether a website is
accessible, and nothing here calls an organisation in breach.
