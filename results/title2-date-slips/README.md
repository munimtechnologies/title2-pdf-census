# Title II date slips: a hand check of 27 public guides (2026-11-12)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. This is a small hand
check, not a pre-registered census: no prediction was fixed before the pages were read.

**Part 2 (2026-11-13, pre-registered):** all 49 state municipal leagues, in
[`leagues/`](leagues/README.md). 3 of the 23 leagues that give a current day give a wrong one
(Minnesota, Vermont, Tennessee); one of the three slips is April 27, 2028, not April 24.

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
  (3 of 23).
- Wrong days here are two days early, so a reader who plans to them is not late. The risk is
  in what gets copied: an entity's own accessibility statement that repeats "April 24, 2027"
  states a date its rule does not have.

## Use

Version 0.11.0 of MV2's free a11y-statement-check
(https://github.com/munimtechnologies/a11y-statement-check) adds the note `title2_wrong_date`
for pages that name the ADA or Title II and give April 24, 2027, April 24, 2028 or April 28,
2028 (also as "4/24/27"). It is released only if all of its offline tests pass.
