# Title II date slips, part 10: searching the other 25 state government domains for "April 24, 2027" (result)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. Plan:
[PREREG.md](PREREG.md), written on 2026-11-14 after this run began (00:47 UTC) and before any
search in this part. The searches and reads ran later in the same run, between about 00:55 and
01:35 UTC on 2026-11-14. Data: [states.csv](states.csv) (one row per state),
[hit-pages.csv](hit-pages.csv) (every page counted, with its quote and how it was read),
[candidates.csv](candidates.csv) (pages that looked like hits but were not counted, and why) and
[all-50-states.csv](all-50-states.csv) (this part and part 9 together).

**All five predictions held. 5 of the 25 states ranked 26-50 by population have at least one page
on their state domain giving April 24, 2027 as the ADA Title II day, 9 pages in all: Oregon, Utah,
Idaho, Delaware and North Dakota. With part 9, 12 of the 50 states (24%) have such a page, 27
pages in all. 8 of this part's 9 pages were written after the extension was announced, and 5 of
them record what was said between April 17 and April 24, 2026, the week around the rule's
publication.**

## What was done

Part 9's method, unchanged: for each of the states ranked 26-50 in the 2020 Census, one web search
limited to the state's government domain (two zone names for Oklahoma, Arkansas, Kansas, New
Mexico, Nebraska, Delaware and Wyoming) with the fixed query `"April 24, 2027" ADA Title II
accessibility`. Every result that the search's title, snippet or summary tied to April 24, 2027
was read. A page counts as a **hit** if a sentence on it gives April 24, 2027 as an ADA Title II
(or "federal") compliance day, deadline, effective day or content cutoff. The rule, 28 CFR
35.200(b) as amended by AG Order No. 6742-2026 (91 FR 20912, April 20, 2026), has April 26, 2027
for public entities of 50,000 or more, which includes every state, and April 26, 2028 for smaller
entities; before the amendment it had April 24, 2026 and April 26, 2027.

## What was found

| Group | Searched | With a hit | Share |
|---|---|---|---|
| States 26-50 (this part) | 25 | 5 | 20% |
| States 1-25 (part 9) | 25 | 7 | 28% |
| **All 50 states** | **50** | **12** | **24%** |
| CSU campuses (part 8) | 22 | 3 | 13.64% |
| UC campuses (part 7) | 10 | 2 | 20% |
| Big Ten universities (part 7) | 15 | 6 | 40% |

Who publishes the 9 pages:

| Level | Pages | Publishers | Who |
|---|---|---|---|
| `central` | 2 | 1 | Delaware Government Information Center (newsletter issue 10; "DOJ to Extend ADA Deadline") |
| `agency` | 6 | 5 | Oregon State Marine Board (2), Oregon Board of Dentistry, Utah Department of Transportation, Idaho Department of Water Resources, North Dakota Ethics Commission |
| `other` | 1 | 1 | Town of Bluff, Utah (council minutes on the state Public Notice Website) |

Across all 50 states: 27 pages, 3 `central` (New York ITS's policy and Delaware GIC's two posts),
22 `agency` and 2 `other`. None of this part's 9 pages was seen giving April 26, 2027 as well
(for the five PDFs the search reader quoted only parts of the text).

### When the wrong day was written (sorted after reading; not pre-registered)

- **The week around the rule, April 17-24, 2026 (5 pages).** Delaware's GIC posted on April 17,
  three days before the rule was published, that the Justice Department would extend "the
  current ADA compliance deadline of April 24, 2026 by a full year to April 24, 2027". Oregon's
  Marine Board's July board book says the state was notified on April 17 that the deadline would
  be moved to April 24, 2027. Utah's Department of Transportation told staff on April 22, two days
  after publication, "to April 24, 2027". On April 24, Oregon's Board of Dentistry heard that the
  deadline "has been extended until April 24, 2027" (minutes printed in June), and North Dakota's
  Ethics Commission minuted an email from the state IT agency (NDIT) saying "the deadline ... has
  been moved back 1 year", followed by "Websites now need to comply by April 24, 2027". NDIT's own
  hub now gives April 26, 2027.
- **Later, still unchanged (3 pages).** The Marine Board's forms library (no date), Delaware's
  newsletter of June 9 (with a countdown "until Revised Accessibility Deadline (4/24/27)"), and
  Idaho Water Resources' strategic plan of July 1, whose previous plan had "by April 24, 2026".
- **Before the extension (1 page).** Bluff's council minutes of November 4, 2025: "Bluff's deadline
  for ADA Rule is April 24, 2027." Bluff is a small town, whose day under the 2024 rule was April
  26, 2027.

In each of the four states whose central IT or accessibility office the search results showed
(Oregon EIS, Utah Design System, Idaho ITS, North Dakota NDIT), that office gives April 26, 2027.
Delaware is the exception: there the wrong day is the central office's own. Part 1 found
Community College Daily's report of April 19, 2026, also written before the rule was published,
giving April 24, 2027 and April 24, 2028. Read together, these pages suggest the wrong day was in
circulation before the rule's text was public (the text set April 26; April 24, 2027 is a
Saturday) and stayed on pages written in that first week. That is a reading of nine dated pages,
not a traced chain of copying.

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| T1: states with a hit | at least 2 | 5 of 25 | yes |
| T2: states with a hit | fewer than 7 | 5 of 25 | yes |
| T3: `agency` hit publishers more than `central` | more | 5 against 1 | yes |
| T4: Delaware is `hit` | hit | hit (2 GIC pages) | yes |
| T5: states with a hit, all 50 | at most 13 | 12 | yes |

T4 was weak by design: Delaware's newsletter was known before the plan was written.

## Close calls (see hit-pages.csv and candidates.csv)

- **Idaho rests on one borderline page.** Water Resources' plan sets its own task deadline, "for
  compliance with Federal ADA requirements ... by April 24, 2027". It is counted because the
  method counts a compliance day tied to the federal ADA. Without it, 4 of 25 states hit (11 of 50),
  and every prediction still holds.
- **Utah has an `other` page too** (Bluff), but Utah is a hit on the UDOT page alone.
- **Not counted:** an Oklahoma Works conference book of October 2024 ("by either April 24, 2026,
  or April 24, 2027, depending upon the size of the population") now returns HTTP 404, though the
  search index still quotes it; Idaho Purchasing's "These requirements take full effect on April
  24, 2027" names no ADA or federal rule; New Mexico's Secretary of State gives "effective April
  2027" with no day; the rest matched only the date (contract expiries, a scallop season, a STEM
  festival, a commission term).
- Delaware GIC's archive listings repeat the two posts' excerpts and were not counted as more
  pages (decided after reading; no prediction depends on page counts).

## Limits

One search per state on one day. The search tool may run reworded queries of its own, and an
index does not hold every page, so 5 of 25 and 12 of 50 are lower bounds. Agencies on other
domains were not searched. Pages were read through AI page and search readers that quote the
page; five hits (the Marine Board's board book, the Dentistry packet, Bluff's minutes, Idaho Water
Resources' plan and North Dakota's minutes, all PDFs) rest on two search-reader passes each
because the page reader could not read the file. The "when written" sorting was done after
reading. 50 states are the whole group, not a sample. A date on a page is what it says, not a
finding that a state is or is not in compliance, and April 24, 2027 is two days earlier than the
rule's April 26, 2027, not later.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check)
version 0.11.0, queued for release, adds a note for pages that name the ADA or Title II and give
April 24, 2027, April 24, 2028 or April 28, 2028.
