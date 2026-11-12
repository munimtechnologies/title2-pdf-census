# special-districts: what US special districts' accessibility pages say, and which date they give (result)

Graded 2026-11-12 from sealed job special-districts-v1; the 1,161 domains were read from 11:17:31 to 11:22:14 UTC on 2026-11-12.
Plan: [PREREG.md](PREREG.md), committed on 2026-11-11 before any special district website was
read. Scripts: `special_districts.py` 0.1.0 with the unchanged `state_pages.py` 0.1.0,
`a11y_pages.py` 0.1.0 and `statement_check.py` 0.1.0. Data: [rows.csv](rows.csv),
[frame.csv](frame.csv), [result.json](result.json) and [result.txt](result.txt), all as the job
wrote them. Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Code
Apache-2.0; this text and MV2's data CC BY 4.0. The frame comes from CISA's public .gov registry
list (cisagov/dotgov-data, CC0-1.0).

**Three of the five predictions held (SD2, SD3, SD4); SD1 failed, and SD5 could not be graded: only 2 pages gave any of the three dates, and the plan needed 10.**

**None of the 341 accessibility pages read is a special district stating its own compliance date.**
The ADA Title II web rule gives every special district April 26, 2028 (moved from April 26, 2027
by the interim final rule of April 20, 2026). Two pages carry one of the rule's three dates, and
neither is a district giving its date: South Fork Water Board's statement (sfwbor.gov) says "Last updated: April 24, 2026", which the census's reader takes as the old Title II date, and the one page with April 26, 2028 is the City of Bay Village's accessibility page (cityofbayvillage.gov), where the Westshore Enforcement Bureau's domain leads.

Only 345 of the 873 home sites (39.52%) link to an accessibility page on the same site, fewer than for cities and counties of 50,000 or more (815 of 1,195, 68.20%) and for governments of 10,000 to 49,999 (54.22%). 48 of the 114 pages that name a WCAG version (42.11%) name WCAG 2.0 as the highest, short of the predicted 50%; 49 name 2.1 and 17 name 2.2.

## The frame

CISA's .gov registry list (`current-full.csv`, 1,446,455 bytes, SHA-256 `d5d0d9e54c59`, read 2026-11-12) has 17,056 rows; 1,161 of them are special district domains, and 0 rows were dropped by the publishing tool's blocked word.
All of them were read (the plan allowed up to 3,000). The registry's type is what each registrant
chose: a few domains in it belong to bodies that are not special districts in the Census sense
(for example darrouzettisd.gov, a Texas school district), and some lead to a city's or county's
site. They are counted as the plan says, not removed.

Gates: P0 held (the plan and the four pinned scripts were on main at the first try); C1 held (1,161 eligible domains, within 800 to 3,000). There was enough data for SD1 (114 versioned pages, at least 100), SD2 and SD3 (341 pages, at least 200) and SD4 (873 home sites, at least 400), but not for SD5 (2 dated pages, at least 10).

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| SD1: versioned pages naming WCAG 2.0 as the highest | at least 50% | 48 of 114 (42.11%) | no |
| SD2: pages naming Title II | at most 15% | 8 of 341 (2.35%) | yes |
| SD3: pages giving April 26, 2028 | at most 5% | 1 of 341 (0.29%) | yes |
| SD4: home sites linking to an accessibility page | at most 60% | 345 of 873 (39.52%) | yes |
| SD5: dated pages giving April 26, 2028 | at most 50% | 1 of 2 (fewer than 10 dated pages) | not graded |

SD3 held only because almost no page gives a date at all, and the one page that gives April 26,
2028 belongs to a city, so SD3 says little about special districts.

## Reach

880 of the 1,161 domains served a home page (873 distinct home sites). 204 gave no answer at all, 30 refused the reader through robots.txt, 18 answered 403 and 12 answered 404; the other 17 answered with another status or with something other than HTML.
On 531 of the 880 home pages the reader found no link to an accessibility page by the census's link rules. 344 domains led to a page that was read: 341 distinct pages holding 341 distinct texts.
As the plan says, a page not found here is not proof that a district has none: a page linked only
from another page, kept on another site or published as a PDF is missed.

## What the pages say

125 of the 341 pages name WCAG at all, 66 name Section 508 and 327 give an email address or phone number. 47 pages (13.78%) carry the vendor stock sentence ("We work to comply with Section 508 as well as ..."), against 280 of 808 pages for large cities and counties and 698 of 1,042 for smaller governments.
The 8 pages that name Title II are on darrouzettisd.gov, dupageairport.gov, jbidut.gov, nueraut.gov, portofedmonds.gov, sctca-ca.gov, ssvemsca.gov and vcpa.gov.

110 of the 873 home sites (12.60%) load an overlay script: UserWay on 53, AudioEye on 28, accessiBe on 29, EqualWeb on 1 and Recite on 1 (2 load both accessiBe and UserWay).

## By kind

A rough kind from the organization's name, first match wins (described, not graded).

| Kind | Domains | Pages read | Name a WCAG version | WCAG 2.0 the highest | Name Title II |
|---|---|---|---|---|---|
| emergency | 83 | 15 | 5 | 0 | 0 |
| fire | 288 | 82 | 19 | 12 | 0 |
| health | 40 | 9 | 7 | 2 | 1 |
| housing | 21 | 2 | 1 | 0 | 0 |
| library | 9 | 2 | 2 | 0 | 0 |
| other | 366 | 94 | 29 | 11 | 4 |
| parks | 39 | 18 | 4 | 3 | 0 |
| transit | 60 | 21 | 7 | 4 | 3 |
| water | 255 | 98 | 40 | 16 | 0 |

## Compared with the city and county censuses

| | Cities and counties of 50,000+ | Governments of 10,000 to 49,999 | Special district .gov domains (2026-11-12) |
|---|---|---|---|
| Home sites linking to an accessibility page | 815 of 1,195 (68.20%) | 1,053 of 1,942 (54.22%) | 345 of 873 (39.52%) |
| WCAG 2.0 the highest version named | 283 of 508 (55.71%) | 638 of 809 (78.86%) | 48 of 114 (42.11%) |
| Pages naming Title II | 179 of 808 (22.15%) | 94 of 1,042 (9.02%) | 8 of 341 (2.35%) |
| Vendor stock sentence | 280 of 808 (34.65%) | 698 of 1,042 (66.99%) | 47 of 341 (13.78%) |

Special districts link to an accessibility page less often than cities and counties, and their
pages almost never name the Title II rule or its dates. The plan expected them to look like
smaller governments on WCAG 2.0; fewer of their versioned pages stop at 2.0, and fewer carry the
vendor stock sentence, which in the city censuses travels with WCAG 2.0.

## Found after the run (not pre-registered)

- **A "last updated" date read as a Title II date.** The census's reader, like MV2's free
  a11y-statement-check up to 0.10.0, counts any "April 24, 2026" as the old Title II date, so a
  statement last updated on that day looks like one that gives the old date. Here that is 1 of
  the 2 dated pages. April 24, 2026 was the rule's first compliance date before the Justice
  Department moved it, so statements updated on that very day may be common in other censuses
  too. The census's reader is pinned and stays as it is; the snippets in `rows.csv` let a reader
  check every dated page.

## Limits

Only what CISA's registry lists as a special district .gov domain on the day was read; most
special districts in the United States have no .gov domain, and those that have one may be better
resourced than the rest. One page per site, read once, without running JavaScript; a firewall
that refuses this reader hides a site's page. The link rules can pick a page about the ADA in
general rather than the website. A version or date is what the page says, not what the site
meets. This counts what pages say; it does not test whether a website is accessible, and nothing
here calls a district in breach.

## Files

- `rows.csv`: one row per domain, with the frame columns, statuses, the page address and its
  SHA-256, the flags and short snippets around a WCAG version or an April 2026 or 2027 date (email
  addresses and phone numbers removed; no other page text, no person's name).
- `frame.csv`: the 1,161 special district domains the job read.
- `result.json`, `result.txt`: the job's output, unchanged.
- `test_special_districts_result.py` (repository root): checks that the scripts are the ones that
  ran, rebuilds the cohort from `frame.csv`, re-grades every measure, prediction and described
  count from `rows.csv`, and checks every figure in this note.
