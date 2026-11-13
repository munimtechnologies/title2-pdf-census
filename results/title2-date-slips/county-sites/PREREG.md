# Title II date slips, part 4: do the counties copy their association's wrong days? (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13 at about 08:50 UTC, before any county website in this frame was searched
for or read in this run. It is committed in the same commit as the result (the publish lane runs
after the run ends), so the only proof of order is this note and the times below. What was
already known: part 3 (`../counties/`, 2026-11-13 04:45-05:30 UTC) found that the Maryland
Association of Counties (MACo) gives "April 24, 2027" and "April 28, 2028" (the same pair as the
National Association of Counties page read in part 1), and the Michigan Association of Counties
gives "April 24, 2027" for counties of 50,000 or more. No county's own website was read in parts
1-3, and no row of MV2's earlier city-and-county census was looked at for this check.

## Why

A wrong day on an association page only matters if it reaches what counties tell residents.
Maryland and Michigan are the two states whose county associations gave wrong days, so their
counties are the most likely place to find the slip on a county's own site.

## Frame (`frame-prereg.csv`, 39 entries)

- Maryland: all 24 county-level jurisdictions (23 counties and Baltimore City).
- Michigan: the 15 most populous counties (2020 Census), all of them 50,000 or more, the group
  the Michigan association's wrong day is about.

Domains were written from memory before searching. Where the domain is unsure (marked `unsure`),
or a domain-limited search returns nothing from that domain, the real domain is found with one
web search for the county's name and noted.

## Method (as in parts 2 and 3)

1. For each county, one web search limited to its domain with the fixed query
   `ADA Title II website accessibility rule compliance deadline extension` (no date words).
2. Read, in result order, up to 2 results that are pages on the county's domain about the ADA
   Title II web rule or the county's own web accessibility (statement, policy, plan, news,
   meeting agenda or minutes). PDFs that cannot be read are recorded as such; the search
   reader's quotes are used and marked.
3. For each page, quote every sentence giving a Title II compliance day and compare with
   28 CFR 35.200(b): April 26, 2027 (50,000 or more) and April 26, 2028 (under 50,000).
4. Each county gets one class:
   - `wrong`: a read page gives a current day the rule does not have (for example April 24,
     2027, April 24, 2028, April 27, 2028 or April 28, 2028 as a current deadline);
   - `right`: a read page gives a current day, and every current day given matches;
   - `old_only`: only the 2024 rule's days (April 24, 2026 / April 26, 2027 as the deadline);
   - `no_day`: pages about the rule or the county's web accessibility, but no day;
   - `none`: no such page in the results.
5. Every wrong day is read twice, in two separate fetches.

## Predictions (fixed now)

- P1: at most 2 of the 39 counties are `wrong` (the slips rarely reach counties' own pages).
- P2: at least 20 of the 39 counties are `none`.
- P3: among counties that give any day (`right`, `wrong` or `old_only`), at least half are
  `old_only` (counties' own pages were mostly not updated after the April 20, 2026 rule).
- P4: no county page gives April 28, 2028.
- P5: at least 3 counties give a current day (`right` or `wrong`).

## Limits known in advance

One search per county on one day; search results vary, and many county pages (agendas, PDFs)
are not indexed or not readable. Pages are read through AI page and search readers that quote
the page. 39 counties in two states are not a sample of US counties. A county page not found
is not proof the county has none, and a date on a page is what it says, not a finding that a
county is or is not in compliance.
