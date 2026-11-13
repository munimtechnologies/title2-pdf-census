# Title II date slips, part 3: state associations of counties (result, 2026-11-13)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

The plan and the five predictions are in `PREREG.md`, written at about 04:45 UTC on 2026-11-13,
before any page in this frame was searched for or read. Pages were searched and read between
about 04:45 and 05:30 UTC the same day. `frame-prereg.csv` is the frame as written before
searching; `counties.csv` adds each association's class and the domains found by name search;
`pages.csv` lists every page read.

## The rule

28 CFR 35.200(b), as amended by the Justice Department's interim final rule (AG Order No.
6742-2026, 91 FR 20912, April 20, 2026): **April 26, 2027** for public entities of 50,000 or
more, **April 26, 2028** for smaller ones and all special district governments. The 2024 rule
had April 24, 2026 and April 26, 2027.

## Result

47 state associations of counties (every state with county government except Alaska, whose
borough association was read in part 2). One web search each, limited to the association's
domain, with the fixed query `ADA Title II website accessibility rule compliance deadline
extension`.

| Class | Associations |
|---|---|
| right: gives a current day, every current day matches the rule | 4 (CA, KY, OH, TX) |
| wrong: at least one page gives a current day the rule does not have | 2 (MD, MI) |
| old_only: only the 2024 rule's dates | 1 (IA) |
| no_day: Title II pages found, but no day | 5 (KS, ND, PA, SC, VA) |
| none: no page about the rule in the results | 35 |

The two `wrong` associations:

- **Maryland Association of Counties (MACo)**, Conduit Street post "Deep Dive: Beyond the ADA
  Digital Accessibility Deadline", June 10, 2026: "Counties with populations greater than 50,000
  residents: April 24, 2027" and "Counties with populations of 50,000 residents or fewer: April
  28, 2028". This is exactly the pair on the National Association of Counties (NACo) page that
  part 1 found wrong.
- **Michigan Association of Counties**, Legislative Update of April 24, 2026: "Counties with
  50,000+ in population: April 24, 2027" (its under-50,000 day, April 26, 2028, is right).

Each wrong day was read twice, in two separate fetches. Neither page has a correction note.

## Predictions

- **P1 held:** 2 associations are `wrong` (at least 1 predicted).
- **P2 failed:** 2 of the 6 associations that give a current day are wrong (33.3%). The
  prediction was fewer than 1 in 3.
- **P3 failed:** neither wrong association has a read page giving the rule's days. Maryland's
  other two pages give the 2024 dates (March 13) and years only (August 5); Michigan's give the
  2024 dates (March 27, 2026) and relative terms (April 26, 2024). This differs from part 2,
  where all three wrong leagues also had a right page.
- **P4 failed:** only 6 of 47 associations give a current day (at least 12 predicted). County
  associations post far less on the rule than municipal leagues (23 of 49 in part 2), at least
  in what a search of their own sites finds.
- **P5 held:** Maryland's page gives April 28, 2028, NACo's wrong day.

## NACo, re-read the same day (described, not predicted)

NACo's page "DOJ rule grants extension on ADA web-based accessibility requirements" (dated Jun
24, 2026, with update notes for June 22, April 20 and March 3, 2026 and September 22, 2025) still
says, under its April 20 update: "Counties with populations over 50,000: April 24, 2027" and
"Counties with populations at or below 50,000: April 28, 2028". Its September 22, 2025 update
also says smaller counties had "until April 24, 2027" under the 2024 rule, which had April 26,
2027.

## What the three parts show together

- Pages written for counties are wrong more often than other pages in this series. Counting
  NACo and Texas County Progress (part 1) with the six associations here, 4 of 8 county-facing
  pages or associations that give a current day give a wrong one. Among municipal leagues it was
  3 of 23, and among vendor, law-firm and news guides 0 of 14 (part 1). The numbers are small.
- The Maryland page repeats NACo's exact pair, including April 28, 2028, a day that no other page
  in this series gives (none of the 49 leagues, none of the other 26 guides in part 1). That suggests the slip travels from the national association to a state
  one. Copying cannot be proved from the text alone.
- The associations that give the rule's days (California, Kentucky, Ohio, Texas) wrote their
  stories in the week the rule came out, and Kentucky and Ohio also give the former days right.

## Limits

- One search per association on one day. 35 associations had no page about the rule in the
  results; that does not mean they have none (members-only pages, newsletters and PDFs are often
  not indexed). Search results vary by time and place.
- Pages were read through AI page and search readers that quote the page. Three sources could
  only be read through the search reader's quotes (Iowa's PDF magazine, and Kansas and New York,
  whose pages returned 403 and 404 to the page reader). Kentucky's article URL came from the
  headline the search reader quoted.
- Six domains were unsure in the prereg list. Hawaii, Illinois and South Dakota were found by
  name search; Delaware and Massachusetts have associations with no website found; no Vermont
  county association was found.
- A wrong day on an association page is not a wrong day on a county's own site. Whether counties
  copy these days into their own accessibility statements is still the open question; MV2's
  queued censuses of entities' own pages will count it.

## Use

A county that copied the Maryland or Michigan pages would tell residents a date its rule does
not have. MV2's free a11y-statement-check
(https://github.com/munimtechnologies/a11y-statement-check) flags April 24, 2027, April 24,
2028 and April 28, 2028 near ADA or Title II from version 0.11.0, which is released only once its
offline tests pass (still waiting for compute on 2026-11-13).
