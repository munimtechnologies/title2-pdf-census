# Title II date slips, part 7: searching 25 universities for "April 24, 2027" (result)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. Plan:
[PREREG.md](PREREG.md), written on 2026-11-13 at about 17:25 UTC, before any search in this part.
The searches and reads ran on 2026-11-13 between about 17:25 and 18:10 UTC. Data:
[universities.csv](universities.csv) (one row per university), [hit-pages.csv](hit-pages.csv) (every
page counted, with its quote and how it was read) and [candidates.csv](candidates.csv) (pages that
looked like hits but were not counted, and why).

**Three of five predictions held (U1, U2, U5). U3 and U4 failed. The wrong day is not mostly on
college and campus pages, and the UC campuses did not show it more often than the Big Ten.**

## What was done

For each of the 25 universities of parts 5 and 6 (the 15 public Big Ten universities outside
California and the 10 University of California campuses), one web search limited to the
university's domain with the fixed query `"April 24, 2027" ADA Title II accessibility`. Every
result that the search's title, snippet or summary tied to April 24, 2027 was read. A page counts
as a **hit** if a sentence on it gives April 24, 2027 as an ADA Title II (or "federal") compliance
day, deadline, effective day or content cutoff. The rule, 28 CFR 35.200(b) as amended by AG Order
No. 6742-2026 (91 FR 20912, April 20, 2026), has April 26, 2027 for public entities of 50,000 or
more, which includes all 25.

## What was found

8 of the 25 universities have at least one hit page; 13 pages in all.

| Group | Universities with a hit | Hit pages |
|---|---|---|
| Big Ten (15) | 6: Indiana, Michigan, Ohio State, Penn State, Rutgers, Washington | 8 |
| UC (10) | 2: Davis, Irvine | 5 |
| All (25) | 8 (32%) | 13 |

Who publishes the 13 pages:

| Level | Pages | Examples |
|---|---|---|
| `central` (central accessibility, ADA, compliance or IT office) | 6 | IU's IT Knowledge Base, Ohio State's IT news, Sites at Penn State, UC Davis Accessibility (2), UC Irvine's Equal Opportunity & Compliance |
| `unit` (college, other campus, unit IT) | 4 | Michigan's College of Engineering IT, Rutgers SEBS IT, UW Tacoma, UW College of the Environment |
| campus-wide division (fits neither list in the plan) | 3 | Ohio State's Office of Administration and Planning, UC Davis Finance, Operations and Administration, UC Irvine's Division of Teaching Excellence and Innovation |

At 5 of the 8 universities, a central page or a campus-wide division's page carries the wrong
day. Examples:

- Sites at Penn State, the university's web service, under the heading "April 24, 2027
  Deadline": "... by the compliance deadline of April 24, 2027." (two fetches; the page gives no
  other 2027 day)
- UC Irvine's ADA Title II page: "The original DOJ deadline was April 24, 2026; the DOJ extended
  the deadline to April 24, 2027." (part 5; re-read here)
- Indiana's IT Knowledge Base article on archiving: content "publicly available on an IU website
  before April 24, 2027" may be archived without remediation, under a heading that says "before
  April 26, 2027" (two search-reader passes).

Ten of the 13 pages give April 24, 2027 and no April 26, 2027 anywhere. Three give both days
(Indiana's article, Ohio State's IT news item, UW's College of the Environment).

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| U1: universities with a hit | at least 7 | 8 of 25 | yes |
| U2: universities with a hit | at most 15 | 8 of 25 | yes |
| U3: share of hit pages that are `unit` | more than half | 4 of 13 (30.77%) | no |
| U4: UC share with a hit at least the Big Ten share | UC >= Big Ten | UC 2 of 10 (20%), Big Ten 6 of 15 (40%) | no |
| U5: hit pages that also give April 26, 2027 | at least 2 | 3 | yes |

U3 needs a word. The plan defined only `central` and `unit`, and three pages come from campus-wide
administrative or teaching divisions that are on neither list. They are graded as not `unit`,
because the plan's `unit` list (college, school, department, library, unit IT group, another
campus, a unit's own news) does not name them. Counting them as `unit` instead would give 7 of
13 (53.85%), and U3 would hold narrowly. Either way, central offices' own pages carry the wrong
day at 5 of the 8 universities.

## What this changes

Part 6 saw April 24, 2027 only on unit pages outside its frame and suggested the slip sits on
college and campus pages, not central ones. Searching for the wrong day itself shows that was too
narrow: central IT and accessibility offices' secondary pages (a knowledge-base article, a web
service's guidance page, an IT news item) carry it as well. The central pages that parts 5 and 6
read first mostly give April 26, 2027; the wrong day sits on the pages beside them.

## Not counted (see candidates.csv)

- The search reader said UNL's Digital Commons page gives "April 24, 2027". The page reader found
  "By April 24, 2026" and no 2027 date. A summary can be wrong, which is why every hit was read.
- UCSF IT's news item still has "april-24-2027" in its address and in the indexed title, but its
  headline and text now say April 26, 2027 (posted June 1, 2026). It was corrected.
- Three UC Irvine IT pages (Faculty Websites and UCI Sites, updated July to October 2026) say
  "April 24, 2027 is the deadline to comply with the UC IT Accessibility Policy". That is a UC
  policy deadline, not a Title II day, so the plan does not count it. UC's policy itself now uses
  April 26, 2027 (part 5).
- Pages that matched only the date, not the topic: Maryland Day, music and theatre events at
  Michigan and Penn State, UW Tacoma events, a UC San Diego job posting, a Minnesota study-abroad
  page and a Wisconsin summit.

## Limits

One search per university on one day. The search tool may run reworded queries of its own, and an
index does not hold every page, so 8 of 25 is a lower bound. Pages were read through AI page and
search readers that quote the page. Six of the 13 hits rest on search-reader passes (the page
reader got 403, a certificate error or a script placeholder), marked in hit-pages.csv. 25 large
public universities are a fixed group, not a sample, and they had already been studied in parts 5
and 6, which shaped the predictions. A date on a page is what it says, not a finding that a
university is or is not in compliance, and April 24, 2027 is two days early, not late.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check)
version 0.11.0, queued for release, adds a note for pages that name the ADA or Title II and give
April 24, 2027, April 24, 2028 or April 28, 2028. A web team can run it over its knowledge base,
service guides and news archive as well as its accessibility pages.
