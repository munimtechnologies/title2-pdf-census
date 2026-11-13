# Title II date slips, part 8: searching the 22 CSU campuses for "April 24, 2027" (result)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0. Plan:
[PREREG.md](PREREG.md), written on 2026-11-13 after this run began (19:47 UTC) and before any
search in this part. The searches and reads ran later in the same run, on 2026-11-13. Data:
[campuses.csv](campuses.csv) (one row per campus), [hit-pages.csv](hit-pages.csv) (every page
counted, with its quote and how it was read) and [candidates.csv](candidates.csv) (pages that
looked like hits but were not counted, and why).

**Three of five predictions held (C2, C4, C5). C1 and C3 failed. Searching for the wrong day found
no CSU campus beyond the three that part 5 had already found, but it found three more pages at
those campuses, including a Provost's message at Cal Poly San Luis Obispo.**

## What was done

Part 7's method, unchanged: for each of the 22 California State University campuses of part 5, one
web search limited to the campus's domain with the fixed query `"April 24, 2027" ADA Title II
accessibility`. Every result that the search's title, snippet or summary tied to April 24, 2027 was
read. A page counts as a **hit** if a sentence on it gives April 24, 2027 as an ADA Title II (or
"federal") compliance day, deadline, effective day or content cutoff. The rule, 28 CFR 35.200(b) as
amended by AG Order No. 6742-2026 (91 FR 20912, April 20, 2026), has April 26, 2027 for public
entities of 50,000 or more, which includes every CSU campus.

## What was found

3 of the 22 campuses have at least one hit page (Cal State East Bay, Cal State Northridge and Cal
Poly San Luis Obispo); 6 pages in all. They are the same three campuses that part 5 classed as
`wrong` from the first two pages of a search with no date words.

| Group | Searched | With a hit | Share |
|---|---|---|---|
| CSU (this part) | 22 | 3 | 13.64% |
| UC (part 7) | 10 | 2 | 20% |
| Big Ten (part 7) | 15 | 6 | 40% |

Who publishes the 6 pages:

| Level | Pages | Pages |
|---|---|---|
| `central` | 5 | CSUN Today's "The ADA in 2026"; CSUN Universal Design Center's ADA Title II Update page and its June event page; Cal Poly's Provost's messages; the Cal Poly Report of May 6, 2026 |
| `division` | 1 | Cal State East Bay's Online Campus "Accessibility and Compliance" page |
| `unit` | 0 | |
| `other` | 0 | |

Pages new to this series:

- Cal Poly San Luis Obispo, Office of the Provost, message of 4/28/26 "Instructional Materials
  Accessibility: Title II Update": the compliance timeline for large public entities, including
  CSU campuses, "has been extended by one year to April 24, 2027." The campus newsletter of May 6,
  2026 (part 5) repeats the day. The Provost's later message of 8/24/26, on the same page, says
  "has been extended to April 26, 2027", so the office moved to the right day without changing
  the April message.
- Cal State Northridge, Universal Design Center event "June | Accessibility for Academic Support
  Staff": "The Americans with Disabilities Act (ADA) has been updated with new requirements for
  course materials. These changes take effect April 24, 2027." It names the ADA, not Title II;
  without it, Northridge still has two hit pages and every count by campus stays the same.
- Cal State Northridge's ADA Title II Update page gives April 26, 2027 as the deadline but April
  24, 2027 in all three dated exception cutoffs ("Documents created prior to April 24, 2027 ...",
  "Posts made before April 24, 2027 ...") and in its archiving note. Part 5 had noted the cutoffs.

Four of the 6 pages give April 24, 2027 and no April 26, 2027 anywhere; two give both days
(Northridge's update page and Cal Poly's Provost's messages).

## Predictions

| Prediction | Line | Result | Held |
|---|---|---|---|
| C1: campuses with a hit | at least 4 | 3 of 22 | no |
| C2: campuses with a hit | at most 11 | 3 of 22 | yes |
| C3: a hit at a campus that part 5 did not class `wrong` | at least 1 | 0 | no |
| C4: share of hit pages that are `unit` | at most half | 0 of 6 (1 of 6 with `division` counted as unit) | yes |
| C5: hit pages that also give April 26, 2027 | at least 2 | 2 | yes |

## What this changes

At the Big Ten (part 7), searching for the wrong day found it at 6 universities where the first
pages read had shown none. At the CSU it found no new campus: the three campuses whose first
pages showed the wrong day are the only ones where the wrong-day search found it, and none of the
other 19 campuses' results carried it. At all three CSU campuses the wrong day sits on central pages (a provost, a
campus newsletter, campus news, the accessibility office), not on college pages, which agrees with
part 7's revision of part 6: the slip is not mainly a unit-page problem.

## Not counted (see candidates.csv)

- The search reader said Cal State Long Beach's ADA Title II update page gives "by April 24,
  2027". The page reader found "By April 26, 2027" and no April 24, 2027. Part 5 had seen the
  same wrong summary, and part 7 saw the same kind of slip with UNL's Digital Commons page. A
  summary can be wrong, which is why every hit was read.
- Pages that matched only the date: a Sacramento State awards flyer, a San José State softball
  game, Sonoma State's registrar calendar and a concert, and three CSUN music event pages (one gave
  404 when read).

## Limits

One search per campus on one day. The search tool may run reworded queries of its own, and an
index does not hold every page, so 3 of 22 is a lower bound. Pages were read through AI page and
search readers that quote the page; one hit (East Bay) rests on search-reader passes because the
page reader got a certificate error. 22 campuses are a fixed group, not a sample, and they had
already been studied in part 5, which shaped the predictions. A date on a page is what it says, not
a finding that a campus is or is not in compliance, and April 24, 2027 is two days early, not
late.

## Use

MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check)
version 0.11.0, queued for release, adds a note for pages that name the ADA or Title II and give
April 24, 2027, April 24, 2028 or April 28, 2028.
