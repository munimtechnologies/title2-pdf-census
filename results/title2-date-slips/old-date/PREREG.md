# title2-date-slips part 12: does an old wrong date predict the new wrong date? (pre-registration)

Registered 2026-11-15 at about 07:40 UTC, before any search for this part was run. Made by MV2 of
Munim, Inc. with AI agents; not yet checked by a person. Text CC BY 4.0.

## Known before registering

- The 2024 ADA Title II web rule (89 FR 31320, April 24, 2024) set April 24, 2026 (public entities of
  50,000 or more) and April 26, 2027 (smaller entities and special districts). The Justice
  Department's interim final rule (91 FR 20912, April 20, 2026) moved them to April 26, 2027 and
  April 26, 2028 (28 CFR 35.200(b)).
- Part 11 found, without having predicted it, that all 3 pages dated April 17-20, 2026 that give the
  wrong new first day "April 24, 2027" (Delaware GIC, Community College Daily, NACo) also give the
  2024 rule's second date as April 24, 2027, while all 9 right pages that mention that date give
  April 26, 2027. The National Association of Counties (NACo) already gave the old small-county date
  as April 24, 2027 in an update of September 22, 2025, and later gave April 24, 2027 as the new
  first day. Its page is known, so NACo is reported but left out of grading.
- Parts 1-10 listed pages giving the wrong new day at universities, state agencies, leagues and
  county associations (ICMA and the Maryland Association of Counties repeat NACo's pair). Whether
  those publishers had the old second date wrong before April 2026 was not checked.

## The idea being tested

If a publisher believed the 2024 rule's two dates were April 24, 2026 and April 24, 2027, then "one
year later" gives April 24, 2027 for the new first date. So publishers that wrote the old second date
as April 24, 2027 before the extension should later give the wrong new day more often than
publishers that wrote it as April 26, 2027.

## Method

Stage 1, the two groups. Fixed queries, web-wide, run once each in this order:

1. `"April 24, 2027" ADA Title II web accessibility rule smaller entities 50,000`
2. `"April 24, 2027" "Title II" web accessibility "fewer than 50,000" 2025`
3. `"April 24, 2027" special district ADA website accessibility deadline 2024`
4. `"April 24, 2026" "April 24, 2027" ADA Title II`
5. `"April 26, 2027" ADA Title II web accessibility rule smaller entities 50,000 2025`
6. `"April 24, 2026" "April 26, 2027" ADA Title II`

A candidate is any result that could be a page dated April 24, 2024 to April 16, 2026 stating the
2024 rule's dates. Every candidate is read with WebFetch (quotes asked for the date shown and every
Title II date). A page joins:

- group E (old wrong) if, as the rule then in force, it gives April 24, 2027 as the second (smaller
  entity or special district) date;
- group C (old right) if it gives April 26, 2027 for that date.

The page must show a date before 2026-04-17 for that text (publication date, or a dated section). A
page now carrying only the new dates is not counted in stage 1. One publisher (organisation or
domain) counts once. Group C is capped at the first 15 publishers in query order; group E is not
capped. Unreadable pages (403, 404, PDF the reader cannot open) are listed and not counted. Search
summaries are never used for a count.

Stage 2, follow-up. For each publisher in E and C, one search restricted to its domain:
`Title II web accessibility compliance date extended 2027`, then, if nothing usable is found, a
second one: `ADA Title II April 2027 deadline`. Up to 3 candidates per publisher are read. The
follow-up result is the new first (50,000+) day given on a page, or a dated section of a page, dated
2026-04-17 or later: April 24, 2027 / April 26, 2027 / another day / none found. If one publisher has
pages with different days, all are listed and it counts as "April 24, 2027" if any page gives it.
For stage 2 only, a page's current text counts when it is the same page as in stage 1 and now states
the new dates.

## Predictions (fixed now)

- R1: group E has at least 5 publishers (the old wrong date was not rare).
- R2: of group E publishers with a follow-up day, at least 40% give April 24, 2027. Graded only if at
  least 4 have a follow-up day.
- R3: of group C publishers with a follow-up day, at most 15% give April 24, 2027. Graded only if at
  least 5 have a follow-up day.
- R4: R2's share is at least 25 points higher than R3's share. Graded only if R2 and R3 are graded.
- R5: government bodies and government associations make up a larger share of group E than of
  group C.

## Limits

A web search reaches only what its index holds and ranks; four of the six stage-1 queries contain
"April 24, 2027" or the April 24 pair, and the groups are found by different queries. Pages edited
since 2024 may show new text under an old date. This is a small hand check, not a census, read
through an AI web reader that quotes the page; wrong days are read twice.
