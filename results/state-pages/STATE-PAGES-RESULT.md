# state-pages: what US state and territory governments' accessibility pages say (graded result)

Graded 2026-11-14 from the output of sealed job `state-pages-v1`, unchanged. The plan is
[PREREG.md](PREREG.md), registered 2026-11-11 before any state or territory website was read; the job
waited in the shared compute queue until 2026-11-14, and the 1,489 domains were read from 11:22:56 to
11:35:39 UTC on 2026-11-14. Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
Code Apache-2.0; this text and the data CC BY 4.0. Frame: CISA's .gov registry list (cisagov/dotgov-data,
CC0-1.0). `test_state_pages_result.py` re-grades every figure below from the saved tables.

## Headline

**One of the five predictions could be graded, and it failed: ST5. ST1 to ST4 could not be graded,
because the crawl read too few pages for the thresholds fixed in the plan.**

- Only 165 of the 644 home sites (25.62%) link to an accessibility page on the same site, far below
  the predicted 70% and below cities and counties of 50,000 or more (815 of 1,195, 68.20%).
- 140 of the 551 home pages with no same-site link do link to an accessibility page on another
  site (for example a statewide policy; the links were counted, not read). Counting those as well, 406 of the 817 domains that served a
  home page (49.69%) link to an accessibility page somewhere. (This is counted per domain, not per
  home site, and was not in the plan.)
- **None of the 170 accessibility pages read gives April 24, 2026, April 26, 2027 or April 26, 2028.**
  34 of them name Title II, but none states a compliance date. The misdated Title II deadlines that
  MV2's hand searches found on state domains ([results/title2-date-slips](../title2-date-slips/),
  parts 9 and 10) sit on other pages: newsletters, agency notices, minutes and plans.
- New Jersey's statewide accessibility page (`nj.gov/nj/accessibility.shtml`) names WCAG 2.0 as its
  only version, and 15 of the registry's New Jersey domains lead to it. The Florida Senate's page
  (`flsenate.gov/About/Accessibility`) also names only WCAG 2.0. Both were read again by hand on
  2026-11-14 and still say so.

## Frame and gates

CISA's .gov registry list (`current-full.csv`, 1,447,631 bytes, SHA-256 `e4a015251b45`, read
2026-11-14) has 17,071 rows; 1,489 of them are state or territory domains, and 0 rows were dropped by
the publishing tool's blocked word. All 1,489 were read (the plan allowed up to 2,000).

P0 held (the plan and the three pinned scripts were on main at the first try); C1 held (1,489 eligible
domains, within 1,000 to 4,000).

There was enough data for ST5 (644 home sites, at least 500), but not for ST1 and ST2 (67 versioned
pages, at least 100) or ST3 and ST4 (170 pages, at least 200).

## Predictions

| Prediction | Measure | Result | Held? |
|---|---|---|---|
| ST1: at most 40% of versioned pages name WCAG 2.0 as the highest | WCAG 2.0 highest | 10 of 67 (14.93%) | not graded |
| ST2: WCAG 2.1 highest more often than 2.0 and than 2.2 | highest version | 2.0: 10, 2.1: 52, 2.2: 5 | not graded |
| ST3: at most 22.15% of pages name Title II | Title II | 34 of 170 (20.00%) | not graded |
| ST4: at most 5% of pages carry the stock sentence | stock sentence | 3 of 170 (1.76%) | not graded |
| ST5: at least 70% of home sites link to an accessibility page on the same site | linked | 165 of 644 (25.62%) | no |

The ungraded figures are shown because the plan said they would be reported; they are not results of
the test. With fewer pages than planned, they can only be read as descriptions of these 170 pages.

## Reach

817 of the 1,489 domains served a home page (644 distinct home sites). 390 gave no answer at all, 164
refused the reader through robots.txt, 28 answered 403 and 60 answered 404; the other 30 answered with
another status or with something other than HTML, or crashed the reader (one site, on a link address
it could not parse).

On 551 of the 817 home pages the reader found no link to an accessibility page by the census's link
rules. 264 domains led to a page that was read: 170 distinct pages holding 169 distinct texts.

## What the pages say

77 of the 170 pages name WCAG at all, 43 name Section 508 and 133 give an email address or phone
number. 3 pages (1.76%) carry the vendor stock sentence ("We work to comply with Section 508 as well as
WCAG 2.x A and AA"), against 34.65% for large cities.

61 of the 644 home sites (9.47%) load an overlay script: accessiBe on 42, UserWay on 13, Recite on 3,
AudioEye on 2 and EqualWeb on 1.

| Kind | Domains | Pages read | Versioned | WCAG 2.0 highest | Title II |
|---|---|---|---|---|---|
| court | 122 | 20 | 5 | 1 | 5 |
| executive_other | 1288 | 136 | 55 | 7 | 26 |
| legislature | 79 | 14 | 7 | 2 | 3 |

## Compared with earlier censuses in this repository

| Measure | State and territory domains (this census) | Cities and counties of 50,000+ |
|---|---|---|
| Home sites linking to an accessibility page on the same site | 165 of 644 (25.62%) | 815 of 1,195 (68.20%) |
| Versioned pages naming WCAG 2.0 as the highest | 10 of 67 (14.93%) | 283 of 508 (55.71%) |
| Pages naming Title II | 34 of 170 (20.00%) | 179 of 808 (22.15%) |
| Pages with the stock sentence | 3 of 170 (1.76%) | 280 of 808 (34.65%) |

## Why ST5 failed (an explanation, not a test)

The prediction assumed state sites would behave like large city sites. The registry's state and
territory list is not a list of state portals: it holds courts, district attorneys, boards, councils
of governments and program sites (for example a state job board), many of them small single-purpose
sites. 140 domains whose home page has no same-site link point to an accessibility page on another
domain, which the plan's same-site rule
does not count, and many registered domains served no page at all. The plan's unit (a registered
domain, not an agency) is the main reason the numbers are not comparable with cities, and the low
page count is why ST1 to ST4 went ungraded.

## Prior work

Searches on 2026-11-11 and again on 2026-11-14 found automated scans of government websites for WCAG
failures, including a 2026 peer-reviewed baseline of U.S. state government homepages (Universal
Access in the Information Society, 2026, doi 10.1007/s10209-026-01328-5) and reports by Accessible
Compliance Group, WPPersona and AccessLumens. None was found that counts, page by page, which WCAG
version, rule or date state government accessibility pages name.

## Limits

Only what the registry lists as a state or territory domain on 2026-11-14 was read, one page per site,
once, without running JavaScript. A page linked only from another page, kept on another site, published
as a PDF, or behind a firewall that refuses this reader is missed, so a page not found is not proof
that a site has none. The link rules can pick an ADA page that is not about the website. A version or
date is what a page says, not what a site meets. This counts what pages say; it does not test whether
any website is accessible, and nothing here calls a government in breach.
