# Title II date slips, part 6: Big Ten public universities outside California (result)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. Plan:
[PREREG.md](PREREG.md), written on 2026-11-13 at about 15:15 UTC, before any page in the frame was
searched for or read. The searches and reads ran on 2026-11-13 between about 15:20 and 16:00 UTC.
Data: [universities.csv](universities.csv) (one row per university, with every page read and the
days it gives) and [outside-frame.csv](outside-frame.csv) (wrong days seen on pages outside the
two read per university).

**Four of five predictions held (B2, B3, B4, B5); B1 failed: none of the 15 universities is
`wrong` on the pages the plan reads.**

## What was found

| Class | Universities |
|---|---|
| `right` | 11: Indiana, Iowa, Maryland, Michigan, Minnesota, Nebraska, Ohio State, Purdue, Rutgers, Washington, Wisconsin |
| `wrong` | 0 |
| `old_only` | 3: Michigan State, Oregon, Penn State |
| `no_day` | 1: Illinois (months only: "extended to April 2027") |
| `none` | 0 |

11 of the 15 give a current Title II day, and all 11 give the rule's April 26, 2027. In
California (part 5), 5 of the 19 campuses that gave a current day gave April 24, 2027.

Three universities' pages still give only the 2024 rule's April 24, 2026, more than six months
after the Justice Department moved it: Michigan State's digital accessibility regulations page,
Oregon's 2024 letter to vendors, and Penn State's summary of the rule ("Compliance Date:
04/24/2026", "Last Update: September 3, 2024").

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| B1: universities that are `wrong` | at least 1 | 0 of 15 | no |
| B2: universities that are `wrong` | at most 4 | 0 of 15 | yes |
| B3: `wrong` among those giving a current day | at most 26.32% (California: 5 of 19) | 0 of 11 (0%) | yes |
| B4: universities giving a current day | at least 8 | 11 of 15 | yes |
| B5: a page giving April 28, 2028 | none | none | yes |

## Outside the frame: the slip sits on unit pages (not pre-registered)

The plan reads only the first two relevant results per university. Further down the same
search results, the search reader named pages with April 24, 2027 at 4 of the 15 universities,
and each was read twice:

- University of Michigan, College of Engineering IT (CAEN): "Per federal ADA Title II
  revisions, all non-archival content used after April 24, 2027, must be compliant." (two
  search-reader passes; the page reader got 403)
- Ohio State, an it.osu.edu news item of April 22, 2026: "Ohio State's compliance deadline has
  move from April 24, 2026 to April 24, 2027." The same item also says "For Ohio State,
  enforcement moves to April 26, 2027." (two fetches)
- Rutgers, the School of Environmental and Biological Sciences IT page: "That deadline has since
  been extended to April 24, 2027." (two fetches)
- University of Washington Tacoma, Digital Accessibility page: "This rule requires the
  University's web content, including academic course content, to be accessible starting on
  April 24, 2027." (two search-reader passes; the page reader's certificate check failed)

All four universities' central pages give April 26, 2027. So outside California the same slip
appears too, but on college, campus and unit IT pages rather than on the central accessibility
or compliance pages the fixed method reaches first. This was not counted systematically: only
pages the search reader mentioned were checked, so the true number of such pages is not known.

**Later the same day (part 7, [`../unit-pages/`](../unit-pages/README.md)):** a pre-registered
search for "April 24, 2027" itself at these 15 universities and the 10 UC campuses found hit
pages at 6 of the 15, and only 4 of the 13 hit pages across all 25 are college or campus pages.
Central IT and accessibility offices' secondary pages carry the wrong day too (for example Sites
at Penn State and an IU Knowledge Base article). Ohio State's it.osu.edu item is published by
the central IT office, so the "unit pages" reading above was too narrow.

## Compared with part 5

| | UC and CSU campuses (part 5) | Big Ten public universities (part 6) |
|---|---|---|
| Give a current day | 19 of 32 | 11 of 15 |
| `wrong` (first two relevant pages) | 5 of 19 | 0 of 11 |
| Unit pages with April 24, 2027 seen outside the frame | not looked for | at 4 of 15 |

## Limits

One fixed search per university on one day; the search tool may also run reworded queries of its
own. Pages were read through AI page and search readers that quote the page; 6 of the 30 pages
read (Michigan's two, Purdue's two, Penn State's second and Indiana's second) came through the
search reader, marked in `universities.csv`. Some pages read are on other campuses' or units'
subdomains of the university's domain (for example Minnesota Duluth). 15 large universities are
a fixed group, not a sample. A date on a page is what it says, not a finding that a university is
or is not in compliance, and April 24, 2027 is two days early, not late.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check)
version 0.11.0, queued for release, adds a note for pages that name the ADA or Title II and give
April 24, 2027, April 24, 2028 or April 28, 2028. A web team can run it over its unit pages.
