# Title II date slips, part 2: state municipal leagues (result, 2026-11-13)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

The plan and the four predictions are in `PREREG.md`, written at about 01:45 UTC on
2026-11-13, before any page in this frame was searched for or read. Pages were searched and read
between about 01:45 and 02:30 UTC the same day. `leagues.csv` is the frame (written before
searching) with each league's class added afterwards; `pages.csv` lists every page read.

## The rule

28 CFR 35.200(b), as amended by the Justice Department's interim final rule published on April 20, 2026
(AG Order No. 6742-2026, 91 FR 20912 per eCFR's source note; re-read on eCFR on 2026-11-13): **April 26, 2027** for public entities of
50,000 or more, **April 26, 2028** for smaller ones and all special district governments. The
2024 rule had April 24, 2026 and April 26, 2027.

## Result

49 state municipal leagues (Hawaii has none). One web search each, limited to the league's
domain, with the fixed query `ADA Title II website accessibility rule compliance deadline
extension`.

| Class | Leagues |
|---|---|
| right: gives a current day, every current day matches the rule | 20 |
| wrong: at least one page gives a current day the rule does not have | 3 |
| old_only: only the 2024 rule's dates | 4 |
| no_day: Title II pages found, but no day | 3 |
| none: no page about the rule in the results | 19 |

The three `wrong` leagues:

- **League of Minnesota Cities**, resource page "Website Accessibility Recommendations for
  Minnesota Cities": its deadline list says "Cities with a population of 50,000 or more persons
  Compliance deadline: April 24, 2027", while the update note at the top of the same page says
  April 26, 2027. The League's news story of 2026-04-20 gives both days right.
- **Vermont League of Cities and Towns**, resource page "New Federal Rule Requires Municipal
  Website and Mobile App Accessibility (Updated)": the table cells read "April 24, 2026 2027" and
  "April 24, 2027 2028". The year was changed and the day kept, so it shows April 24, 2027 and
  April 24, 2028. The under-50,000 row is wrong whichever year is read, because the 2024 rule's
  day was April 26 too. VLCT's news story of 2026-04-21 gives both days right.
- **Tennessee Municipal League**, Tennessee Town & City article of 2026-04-22: "and to April
  27, 2028 for municipalities with a population less than 50,000". Its later article of
  2026-06-10 gives April 26, 2028.

Each wrong day was read twice, in two separate fetches.

## Predictions

- **P1 held:** 3 leagues are `wrong` (at least 1 predicted).
- **P2 held:** 3 of the 23 leagues that give a current day are wrong (13.0%), fewer than 1 in 3.
  Leaving out the two leagues whose only current-day page was written by a vendor (Colorado,
  South Carolina): 3 of 21 (14.3%).
- **P3 failed:** Minnesota and Vermont use April 24, but Tennessee's wrong day is April 27,
  2028. Not every slip is the April 24 carry-forward.
- **P4 held:** 23 of 49 leagues give a current day (at least 15 predicted).

## What else the pages show

- In all three wrong leagues, another page on the same site gives the rule's days. The slips
  sit in pages that were updated after the fact (Minnesota, Vermont) or in the first news story
  (Tennessee), not in the leagues' main extension stories.
- The two April 24 slips look like a "plus one year" edit. Vermont's table visibly changed only
  the year. Minnesota's update note gives April 26, 2027 but the list below it says April 24,
  2027, which is the 2024 rule's April 24, 2026 plus one year. The rule did not add exactly one
  year to the first date: it moved April 24, 2026 to April 26, 2027.
- The 2024 rule's own days were already garbled on league pages before the extension: New
  Hampshire (2024) and Tennessee (2025-11-03) give "April 24, 2027" for smaller entities, Vermont's
  original table did the same, Delaware's league page still gives "April 26, 2026" for
  communities under 50,000, Pennsylvania gives "April 26, 2026" as the former first date, and
  Accelerate Indiana Municipalities' 2025 brochure speaks of July 2026 and July 2027.
- Part 1 found 3 of 9 government and association pages wrong. Here the rate among leagues is
  lower (3 of 23), so association pages are not wrong as often as part 1's small sample
  suggested. Wrong pages exist in about one league in eight that gives a current day.

## Limits

- One search per league on one day. 19 leagues had no page about the rule in the results;
  that does not mean they have none (members-only pages, PDFs and newsletters are often not
  indexed). Search results vary by time and place.
- Pages were read through AI page and search readers that quote the page. Four pages (Alabama,
  Maine and South Carolina PDFs, and two slide decks) could only be read through the search
  reader's quotes. The Vermont table's strikethrough could not be seen in the text.
- The prereg list gave Delaware's domain as dllg.org; it returned nothing and the league's real
  domain, dllg.us, was found by a name search, as the plan allowed. No real domain was found
  for the Nevada league.
- A wrong day on a league page is not a wrong day on a city's own site. Whether cities copy
  these days into their own accessibility statements is the open question; MV2's queued
  censuses of entities' own pages will count it.

## Use

A city that copied the Minnesota or Vermont table would tell residents a date its rule does not
have. MV2's free a11y-statement-check (https://github.com/munimtechnologies/a11y-statement-check)
flags April 24, 2027 and April 24, 2028 from version 0.11.0, which is released only once its
offline tests pass (still waiting for compute on 2026-11-13). April 27, 2028 is not flagged yet.
