# Title II date slips: a hand check of 27 public guides (2026-11-12)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. This is a small hand
check, not a pre-registered census: no prediction was fixed before the pages were read.

**Part 2 (2026-11-13, pre-registered):** all 49 state municipal leagues, in
[`leagues/`](leagues/README.md). 3 of the 23 leagues that give a current day give a wrong one
(Minnesota, Vermont, Tennessee); one of the three slips is April 27, 2028, not April 24.

**Part 3 (2026-11-13, pre-registered):** 47 state associations of counties, in
[`counties/`](counties/README.md). Only 6 give a current day, and 2 of them give a wrong one:
Maryland repeats NACo's exact pair (April 24, 2027 and April 28, 2028) and Michigan gives April
24, 2027. Two of five predictions held. NACo's page still gave both wrong days on 2026-11-13.

**Part 4 (2026-11-13, pre-registered):** the websites of all 24 Maryland jurisdictions and
Michigan's 15 most populous counties, in [`county-sites/`](county-sites/README.md). None of the 39
gives any Title II compliance day, right or wrong: county pages name WCAG 2.1 and give a month or
year at most. Three of five predictions held, one failed and one could not be graded. Outside the
frame, ICMA (the International City/County Management Association) gives NACo's exact pair, and
UC Davis's accessibility FAQ gives "the ADA Title II deadline on April 24, 2027", the first
entity page in this series with a wrong day.

**Part 5 (2026-11-13, pre-registered):** all 10 University of California campuses and the 22
California State University campuses, in [`uc-csu/`](uc-csu/README.md). 19 of 32 give a current
day, and 5 of those 19 give April 24, 2027 instead of April 26, 2027: UC Davis, UC Irvine, Cal
State East Bay, Cal State Northridge and Cal Poly San Luis Obispo. Both systems' own pages give
the right day, so the slip arose campus by campus. Three of five predictions held; the two about
a UC-system pattern failed.

**Part 6 (2026-11-13, pre-registered):** the 15 public Big Ten universities outside California,
in [`big-ten/`](big-ten/README.md). 11 give a current day on the pages the method reads first,
and all 11 give the rule's April 26, 2027; 3 still give only April 24, 2026. Four of five
predictions held; the one expecting at least one wrong university failed. Further down the same
search results, unit pages at 4 of the 15 (Michigan's College of Engineering IT, an Ohio State IT
news item, Rutgers' SEBS IT and UW Tacoma) give April 24, 2027, so the slip is there too, on
college and campus pages rather than central ones.

**Part 7 (2026-11-13, pre-registered):** the same 25 universities (15 Big Ten, 10 UC), each
searched for the wrong day itself, in [`unit-pages/`](unit-pages/README.md). 8 of the 25 have at
least one page giving April 24, 2027 as a Title II day (6 of 15 Big Ten, 2 of 10 UC), 13 pages in
all. Only 4 of the 13 are college or campus pages; 6 are central accessibility, compliance or IT
pages (for example Sites at Penn State's "April 24, 2027 Deadline") and 3 are campus-wide
divisions. So part 6's "unit pages, not central" was too narrow: the wrong day sits on the
central offices' secondary pages too. Three of five predictions held. Two search-reader claims of
the wrong day did not hold when the page was read, and UCSF's news item had been corrected.

**Part 8 (2026-11-13, pre-registered):** the 22 CSU campuses, searched for the wrong day the same
way, in [`csu-wrong-day/`](csu-wrong-day/README.md). 3 of 22 have a page giving April 24, 2027 (6
pages), and they are the same three campuses part 5 found (East Bay, Northridge, San Luis Obispo):
no new campus, unlike the Big Ten. 5 of the 6 pages are central, among them a Provost's message at
Cal Poly San Luis Obispo that the campus newsletter repeated. None is a college page. Three of five
predictions held; the two expecting a new campus failed.

**Part 9 (2026-11-13, pre-registered):** the state government domains of the 25 most populous
states, searched for the wrong day the same way, in [`state-wrong-day/`](state-wrong-day/README.md).
7 of 25 have a page giving April 24, 2027 as the Title II day (18 pages): New York, Illinois,
Michigan, Washington, Tennessee, Maryland and Wisconsin. Unlike at universities, 16 of the 18 are
agency pages, not central ones; the one central page is New York's statewide accessibility policy
NYS-P08-005 (modified 2026-10-07): "The current compliance deadline is now April 24, 2027." Most
of the 18 read the April 2026 extension as one year after April 24, 2026. Three of four
predictions held; the one expecting a page that also gives April 26, 2027 failed.

## The rule

The Justice Department's interim final rule (AG Order No. 6742-2026, 91 FR 20912, April 20,
2026) moved the ADA Title II web and mobile app dates. 28 CFR 35.200(b), read on eCFR on
2026-11-12, now says:

- (b)(1) "Beginning April 26, 2027": public entities with a total population of 50,000 or
  more, other than special district governments.
- (b)(2) "Beginning April 26, 2028": public entities with a total population of less than
  50,000, and all special district governments.

The 2024 rule had April 24, 2026 and April 26, 2027. So the first date moved from the 24th to
the 26th, while the second kept its day.

## What was done

On 2026-11-12, between about 22:30 and 23:00 UTC, three web searches were run with these
fixed queries, and the first ten results of each were read:

- Q1: `ada.gov web rule extension April 26, 2027 interim final rule fact sheet`
- Q2: `league of cities ADA Title II web accessibility rule compliance date extended 2027 2028 members`
- Q3: `association of counties ADA Title II website accessibility deadline extension April 2027 counties`

That gives 27 different pages (three results came up twice and are listed once, under the
first query). For each page, every sentence giving a Title II compliance day was quoted, and
the current days were compared with the rule. `pages.csv` lists every page, its publisher, the
date it shows, the two days it gives and anything else noticed.

## What was found

- 3 pages could not be read (the Federal Register page sent the reader to a bot check, and two
  ADA.gov PDFs could not be opened with the tools used). 24 were read.
- 23 of the 24 give both current days. Level Access gives only months and years for Title II.
- **20 of 23 give the rule's days. 3 do not, and all 3 are written for local or state
  government officials:**
  - National Association of Counties, page dated Jun 24, 2026: "Counties with populations over
    50,000: April 24, 2027" and "Counties with populations at or below 50,000: April 28, 2028".
  - Delaware Government Information Center, accessibility newsletter issue 10, posted June 9,
    2026: "April 24, 2027 for sites serving populations greater than 50,000" and "April 24, 2028
    for smaller government sites", with a countdown "until Revised Accessibility Deadline
    (4/24/27)".
  - Texas County Progress (County Judges and Commissioners Association of Texas): "until April
    24, 2027" for counties of 50,000 and over, and April 26, 2028 for smaller counties.
- By publisher type: 3 of the 9 government and local-government association pages that give
  both days are wrong, and 0 of the 14 vendor, guide, law-firm and news pages are.
- Two older pages (MRSC and Jackson Lewis) give the current days right but name the former
  first date in two different ways (April 24, 2026 and April 26, 2026; April 24, 2026 and April
  22, 2026).

Every wrong day uses April 24, the day of the 2024 rule's first date, carried a year or two
forward. The rule kept April 26 for both new dates instead.

Two pages outside this sample, read on the same day, do the same: Community College Daily's
report of 2026-04-19, written the day before the rule was published, gives April 24, 2027 and
April 24, 2028, and know-the-ada.com gives April 24, 2028 for special districts.

## Limits

- Three queries on one day. Search results change and may differ by place and person. Q1 and Q3
  contain date words ("April 26, 2027", "April 2027"), which may favour pages using those words.
- Pages were read through an AI web reader that quotes the page. The wrong days on the three
  pages were each read twice (two separate fetches), but a slip by the reader cannot be ruled out.
- 9 and 14 pages are small groups. The difference between them is a pattern to test, not a
  measured rate. Part 2 tested it on all 49 state municipal leagues and found a lower rate
  (3 of 23); part 3 found 2 of 6 among state associations of counties.
- Wrong days here are two days early, so a reader who plans to them is not late. The risk is
  in what gets copied: an entity's own accessibility statement that repeats "April 24, 2027"
  states a date its rule does not have.

## Use

Version 0.11.0 of MV2's free a11y-statement-check
(https://github.com/munimtechnologies/a11y-statement-check) adds the note `title2_wrong_date`
for pages that name the ADA or Title II and give April 24, 2027, April 24, 2028 or April 28,
2028 (also as "4/24/27"). It is released only if all of its offline tests pass.
