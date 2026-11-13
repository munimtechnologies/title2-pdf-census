# nhs-stock: what the accessibility statements of NHS trusts say (result)

Graded 2026-11-13 from sealed job nhs-stock-v1; the 211 hosts were read from 10:48:20 to 10:54:44 UTC on 2026-11-13.
Plan: [PREREG.md](PREREG.md), committed on 2026-11-11 before any trust's website was read. The job
built its frame from NHS England's ODS API on 2026-11-13, after the plan was on main, and saved it
before the first trust's website was requested. Scripts: `nhs_stock.py` 0.1.0 and `nhs_frame.py`
0.1.0, with the unchanged `council_stock.py` 0.1.0 and `statement_template_check.py` 0.3.0. Data:
[hosts.csv](hosts.csv), [nhs-frame.csv](nhs-frame.csv), [nhs-frame.json](nhs-frame.json),
[result.json](result.json) and [result.txt](result.txt), all as the job wrote them. Made by MV2 of
Munim, Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text and MV2's data
CC BY 4.0. Trust codes, names and website addresses come from NHS England's Organisation Data
Service (Open Government Licence v3.0).

**All four predictions held (T1, T2, T3, T4).**

**100 of the 161 dated statements (62.11%) carry a date before 1 November 2025**, more than a year
before this census, against 105 of 271 (38.75%) for the UK's principal councils
([COUNCIL-STOCK-RESULT.md](../uk-councils/COUNCIL-STOCK-RESULT.md)) and 81 of 191 (42.41%) for UK
government organisations with their own website ([GOVUK-STOCK-RESULT.md](../govuk-orgs/GOVUK-STOCK-RESULT.md)),
read the same way. GOV.UK's sample statement asks for a review at least once a year. 34 of the 161 dated statements (21.12%) carry a date before 2024.
NHS trusts do better than both on the other two measures: a statement was found on 171 of the 211 hosts (81.04%), and 123 of the 171 (71.93%) name WCAG 2.2 as the highest version.

## The frame

NHS England's ODS API listed 247 active organisations with the primary role RO197 ("NHS TRUST") on 2026-11-13 (SHA-256 of the list `7735d585382b`): 154 foundation trusts and 93 trusts. All 247 records were read (0 could not be read); 36 give no website and are counted in the frame file but not read, and 0 rows were dropped by the publishing tool's blocked word.
The other 211 trusts make 211 distinct hosts; no host is shared by two trusts.
The frame file is `nhs-frame.csv` (`de281dd2f7fb`, 25,798 bytes). Three of the hosts read belong to
Welsh trusts (ambulance.wales.nhs.uk, phw.nhs.wales, velindre-tr.wales.nhs.uk), which the same
regulations cover.

Gates: P0 held (the plan was on main and the checker matched release v0.3.0); F1 held (247 trusts read from the list, 0 records unread, 0 rows dropped, 211 hosts); G1 held: 200 of the 211 hosts answered (94.79%).

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| T1: hosts serving a statement found this way | at least 75% | 171 of 211 (81.04%) | yes |
| T2: hosts whose statement keeps a 0.3.0 placeholder | at most 3 | 2 (hpft.nhs.uk, lincolnshirecommunityhealthservices.nhs.uk) | yes |
| T3: read statements naming WCAG 2.2 as the highest version | at least 65% | 123 of 171 (71.93%) | yes |
| T4: dated statements dated before 2025-11-01 | at least 30% | 100 of 161 (62.11%) | yes |

T4's line (30%) sat below the councils' 38.75%; the result is far above both.

## Where no statement was found

The reader found no statement on 40 hosts. 13 refused it through robots.txt and 11 did not answer at all. The other 16 answered, but no statement was found through the home page's link, one more
hop, or the two fixed addresses. 4 of those 16 home pages answered 403 (Forbidden), which usually
means a firewall turned the reader away. Leaving out the 28 hosts that refused or blocked the reader (robots.txt, no answer, or a 403 home page), a statement was found on 171 of 183 (93.44%). That figure was chosen after the run and is not graded. As the plan
says, a statement not found here is not proof that a trust has none.

## The statements found

The 171 statements cover 171 trusts. 145 use GOV.UK's compliance sentence. 123 name WCAG 2.2 as the highest version, 46 name 2.1 and 2 give no WCAG version the reader could take. 10 give no date the reader could take; of the 161 dated, 145 take their date from a "last reviewed" or "updated" line and 16 from a "prepared" or "published" line. 22 statements are served on another host than the one ODS names; for example, the hosts of both Basildon and Thurrock and Mid Essex lead to one statement on mse.nhs.uk. The 171 pages hold 166 distinct texts. 160 were found through the home page's link, 0 one hop further, and 11 at a fixed address (3 at /accessibility-statement, 8 at /accessibility).

By year of the statement's date: 2020 (2), 2022 (2), 2023 (30), 2024 (25), 2025 (46), 2026 (55), 2027 (1).

Two statements keep a placeholder from GOV.UK's sample statement: hpft.nhs.uk (rule
gov-uk/example_document, the sample's "[example of non-essential document]") and
lincolnshirecommunityhealthservices.nhs.uk (rule gov-uk/insert_one_of, the sample's "[insert one of
the following ...]").

## By kind

ODS's own kind; each host is counted under its trust.

| Kind | Hosts | Statement found | WCAG 2.2 | Dated | Dated before 1 Nov 2025 |
|---|---|---|---|---|---|
| foundation_trust | 136 | 111 | 80 | 106 | 62 |
| trust | 75 | 60 | 43 | 55 | 38 |

Among foundation trusts, 62 of 106 dated statements (58.49%) carry a date before 1 November 2025; among other trusts, 38 of 55 (69.09%).

## Found after the run (not pre-registered)

- **Counted once per text.** Five statements are each served for two listed trusts. Counted once per distinct text, 98 of 156 dated texts (62.82%) carry a date before 1 November 2025.
- **Planned reviews read as reviews.** 2 statement dates are later than the census (phw.nhs.wales: 2027-03-31; whittington.nhs.uk: 2026-11-30). Most likely each is a planned next review that the
  pinned reader takes as a review date, the flaw the plan names (MV2's free a11y-statement-check
  keeps planned reviews apart since 0.7.0; this census keeps the old reader so that it stays
  comparable with the councils and central bodies). It can only make a statement look newer. T4
  is not changed by it: counted as undated, the two would leave 100 of 159 (62.89%).

## Compared with the councils and central bodies

| | UK principal councils (2026-11-10) | UK government organisations (2026-11-11) | NHS trusts (2026-11-13) |
|---|---|---|---|
| Statement found | 284 of 379 hosts (74.93%) | 202 of 283 hosts (71.38%) | 171 of 211 hosts (81.04%) |
| WCAG 2.2 the highest version | 191 of 284 (67.25%) | 139 of 202 (68.81%) | 123 of 171 (71.93%) |
| Dated before 1 November 2025 | 105 of 271 (38.75%) | 81 of 191 (42.41%) | 100 of 161 (62.11%) |
| Template placeholder | 1 host | 1 host | 2 hosts |

Trusts publish a statement more often than councils and central bodies, and more of their
statements name WCAG 2.2, but a much larger share of their dated statements carries a date more
than a year old: about three in five, against about two in five.

## Limits

The website is what ODS recorded on the day; a trust may run several sites (hospital, charity,
recruitment), and only the one ODS names was read. A statement linked only from another page,
served on another site, published as a PDF, or behind a firewall that refuses this reader is
missed. A date is what the statement says, read by a pattern, not when it was really reviewed (see
the planned reviews above), and an up-to-date date says nothing about whether the statement is
accurate. One page per host, read once, on one day. This counts what statements say; it does not
test whether a website is accessible, and nothing here calls a trust in breach.

## Files

- `hosts.csv`: one row per host, with its trust, the status of the read, how the statement was
  found, its address, text length and SHA-256, rule ids, WCAG version, dates and flags (no page
  text, no person's name).
- `nhs-frame.csv`, `nhs-frame.json`: the frame the job built from NHS England's ODS API.
- `result.json`, `result.txt`: the job's output, unchanged.
- `test_nhs_stock_result.py` (repository root): rebuilds the frame's hosts from `nhs-frame.csv`
  with the pinned `nhs_stock.py`, re-grades every measure, gate, prediction and described count
  from `hosts.csv`, and checks every figure in this note.
