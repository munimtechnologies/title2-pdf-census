# nhs-stock: what the accessibility statements of NHS trusts say (pre-registration)

Registered 2026-11-11, before any NHS trust's website was read for this study. Scripts:
`nhs_stock.py` 0.1.0 with its offline tests (`test_nhs_stock.py`), which builds its frame with
`nhs_frame.py` 0.1.0 and reads each site with the unchanged `council_stock.py` 0.1.0 and
`statement_template_check.py` 0.3.0 already in this repository. Made by MV2 of Munim, Inc. with AI
agents; not yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0. Trust codes,
names and website addresses come from NHS England's Organisation Data Service (Open Government
Licence v3.0).

## Why

Public sector bodies in the UK, NHS trusts among them, must publish an accessibility statement for
each website and keep it under regular review (The Public Sector Bodies (Websites and Mobile
Applications) (No. 2) Accessibility Regulations 2018, SI 2018/952, regulation 8). GOV.UK's sample
statement asks for a review at least once a year, and the Government Digital Service has monitored
against WCAG 2.2 AA since October 2024. Hospital, mental health, community and ambulance trusts run
some of the most used public websites in England.

MV2's two earlier censuses used the same reader. UK principal councils
([COUNCIL-STOCK-RESULT.md](../uk-councils/COUNCIL-STOCK-RESULT.md)): a statement on 284 of 379
hosts (74.93%), 191 of 284 naming WCAG 2.2 (67.25%), 105 of 271 dated statements (38.75%) more than
a year old. UK government organisations with their own website
([GOVUK-STOCK-RESULT.md](../govuk-orgs/GOVUK-STOCK-RESULT.md)): 202 of 283 hosts (71.38%), 139 of
202 naming WCAG 2.2 (68.81%), 81 of 191 dated statements (42.41%) more than a year old. Searches on
2026-11-11 found no published count, trust by trust, of which WCAG version NHS trusts' statements
name or how old their review dates are: one web agency's guide says many trust statements still
name WCAG 2.1 but gives no figures, and the Healthcare Financial Management Association's 2025
check of trust websites was about finding annual reports, not accessibility statements. This study
asks the council questions of NHS trusts, with the same reader.

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job first runs `nhs_frame.py` 0.1.0, which reads only NHS England's ODS Organisation Reference
Data API (`directory.spineservices.nhs.uk/ORD/2-0-0`): the list of active organisations whose
primary role is `RO197` ("NHS TRUST", which covers NHS trusts and NHS foundation trusts), then each
listed trust's own record. A trust's website is the first contact of type `http` in its record; its
host is that address's host without `www.`. It writes `nhs-frame.csv` and `nhs-frame.json`, and the
result records the frame's size and SHA-256. The frame is the distinct hosts of listed trusts whose
record was read and gives a website; trusts on one host are counted on it, and the host is named
after the first of them by ODS code. A trust whose record gives no website is counted in the frame
file but not read.

What was looked at before registering, all on the ODS API and none on a trust's own site: the list
above on 2026-11-11 (247 entries, all active RO197 trusts; three entries read by name), and three
trust records: Guy's and St Thomas' NHS Foundation Trust (RJ1) and Manchester University NHS
Foundation Trust (R0A), each with a website contact, and The Online NHS Trust (K0N6A, primary role
from 2026-04-07), with no contacts. The searches above returned short summaries of six trusts'
statements (Airedale, Leeds Community Healthcare, Nottinghamshire Healthcare, King's College
Hospital, University Hospitals of Morecambe Bay, Dartford and Gravesham); none of those pages was
fetched by us, and none of what they say set a threshold below.

## Method

- Order: hosts sorted by SHA-256 of the seed `nhs-stock-2026-11` plus the host. 4 hosts at a time;
  for each host one request at a time with a 1-second pause after each. The crawl stops starting new
  hosts after 120 minutes; a host not started counts as not answered.
- Each host is read exactly as in the council census, with `council_stock.py` 0.1.0 unchanged:
  `robots.txt` is read first and a page it disallows is not requested; the home page
  `https://www.<host>/` (or `https://<host>/` if the first gets no answer at all); the best
  statement link on the trust's own site; one more hop from a page that links to the statement; then
  two fixed addresses, `/accessibility-statement` and then `/accessibility`. At most 5 addresses per
  host. A 429 or 503 is asked once more after 30 seconds.
- A page counts as a statement when it answers 200 with HTML, is not a home page, has at least 200
  characters of visible text, says "accessibility statement" and names WCAG or the enforcement
  procedure.
- Rules: `statement_template_check.py 0.3.0`, byte-identical to release v0.3.0 of MV2's free
  a11y-statement-check (the job compares the two before any request to ODS or to a trust), and
  `council_stock.py`'s date reader: the statement's date is the later of the latest "last reviewed /
  updated" date and the latest "prepared / published on" date.
- Stored per host: its trusts' ODS code, name and kind, the status of the read, how the statement was
  found, its address, text length and SHA-256, rule ids, WCAG version, dates and flags. No page text
  and no person's name is stored.

## Gates (nothing is graded unless all hold)

- P0: this file is on main, and the checker matches the release.
- F1 (checked on the frame before any website is read; if it fails, no website is requested): at
  least 200 trusts read from the list, at most 10 trust records that could not be read, at most 2
  rows dropped by the publishing tool's blocked word, and at least 150 distinct hosts.
- G1 (at least 90% of hosts answered): any HTTP status, including a robots.txt answer.

## Predictions (fixed before any website is read)

- T1 (at least 75% of hosts) serve a statement found this way. Councils: 74.93%; central bodies:
  71.38%. This predicts that trusts, whose websites are a main way patients reach them, do at least
  as well as councils.
- T2 (at most 3 hosts) serve a statement with a 0.3.0 placeholder (councils: 1; central bodies: 1).
- T3 (at least 65% of read statements name WCAG 2.2 as the highest version). NHS England's own
  service manual says its services are built to WCAG 2.2 AA, but trusts publish their own statements; councils were at
  67.25% and central bodies at 68.81%.
- T4 (at least 30% of dated statements carry a statement date before 2025-11-01), that is, were last
  reviewed (or prepared) more than a year before this census (councils: 38.75%; central bodies:
  42.41%). T3 is graded only with at least 60 read statements, and T4 only with at least 60 dated
  statements.

The result is published whether the predictions hold or not.

## Described, not graded

Status of every host and its home page; how each statement was found; trusts behind the found
statements; highest WCAG version; statements with GOV.UK's compliance sentence; statements without
a date; date source and year; placeholder rule ids and hosts; statements on another host; links to
another site; addresses blocked by robots.txt; distinct texts; all of these by kind (trust or
foundation trust); and from the frame, trusts without a website in ODS, records that could not be
read and hosts shared by several trusts.

## Limits

The website is what ODS records on the day; a trust may run several sites (hospital, charity,
recruitment), and only the one ODS names is read. A statement linked only from another page, served
on another site, published as a PDF, or behind a firewall that refuses this reader is missed, so a
statement not found here is not proof that a trust has none. A date is what the statement says, not
when it was really reviewed, and an up-to-date date says nothing about whether the statement is
accurate. The pinned date reader also reads a planned review ("It will be reviewed in March 2027")
as a review date, a flaw found in the central-bodies census and being fixed in
a11y-statement-check 0.7.0; it is kept here unchanged so the three censuses stay comparable, and it can only make
statements look newer, so it works against T4. One page per host, read once, on one day. The
placeholder rules are 0.3.0's, unchanged. This counts what statements say; it does not test whether
a website is accessible, and nothing here calls a trust in breach.
