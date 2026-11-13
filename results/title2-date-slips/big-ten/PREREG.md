# Title II date slips, part 6: Big Ten public universities outside California (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13 at about 15:15 UTC, before any page in this frame was searched for or read
in this run. It is committed in the same commit as the result (the publish lane runs after the
run ends), so the only proof of order is this note and the times below. What was already known:
part 5 (`../uc-csu/`, 2026-11-13 about 11:00 UTC) found that 5 of the 19 University of California
and California State University campuses that give a current ADA Title II day give April 24,
2027 instead of April 26, 2027, and that both systems' own pages give the right day. No page of a
university in this frame has been read for this series.

## Why

Part 5 asked whether the April 24, 2027 slip is a California pattern. This part asks the same
question of one fixed group of large public universities in ten other states, using the same
method and classes, so the two rates can be set side by side.

## Frame (`frame-prereg.csv`, 15 universities)

The public universities among the 18 members of the Big Ten Conference in 2026, main campus only,
minus UCLA (already in part 5): Illinois, Indiana, Iowa, Maryland, Michigan, Michigan State,
Minnesota, Nebraska, Ohio State, Oregon, Penn State, Purdue, Rutgers, Washington and Wisconsin.
Northwestern and USC are private and not in the frame. Domains were written from memory; if a
domain-limited search returns nothing from that domain, the real domain is found with one web
search for the university's name and noted.

## Method (as in part 5)

1. For each university, one web search limited to its domain with the fixed query
   `ADA Title II website accessibility rule compliance deadline extension` (no date words).
2. Read, in result order, up to 2 results that are pages on the university's domain about the
   ADA Title II web rule or the university's own digital accessibility (statement, policy, FAQ,
   news, training). Pages the page reader cannot open (403, binary PDF, certificate error) are
   recorded as such, and the search reader's quotes are used and marked.
3. For each page, quote every sentence giving a Title II compliance day and compare with
   28 CFR 35.200(b) as amended (AG Order No. 6742-2026, 91 FR 20912, April 20, 2026): April 26,
   2027 (50,000 or more) and April 26, 2028 (under 50,000). Every state has more than 50,000
   people, so the 2027 day is theirs.
4. Each university gets one class:
   - `wrong`: a read page gives a current Title II day the rule does not have (for example
     April 24, 2027, April 24, 2028, April 27, 2028 or April 28, 2028);
   - `right`: a read page gives a current day, and every current day given matches;
   - `old_only`: only the 2024 rule's days (April 24, 2026 as the deadline);
   - `no_day`: pages about the rule or digital accessibility, but no day;
   - `none`: no such page in the results.
5. Every wrong day is read twice, in two separate fetches (or two search-reader passes, marked).

## Predictions (fixed now)

- B1: at least 1 of the 15 universities is `wrong` (the slip is not only Californian).
- B2: at most 4 of the 15 are `wrong`.
- B3: among universities that give a current day (`right` or `wrong`), the share that are
  `wrong` is no higher than California's 5 of 19 (26.32%).
- B4: at least 8 of the 15 give a current day.
- B5: no university page gives April 28, 2028.

## Limits known in advance

One search per university on one day; search results vary, and many university pages are not
indexed or are behind sign-in. Pages are read through AI page and search readers that quote the
page. 15 universities are a fixed group, not a sample of US universities, and they are large and
well staffed. Penn State is "state-related", and whether Title II covers it is not settled here;
it is kept in the frame as fixed. A page not found is not proof a university has none, and a date
on a page is what it says, not a finding that a university is or is not in compliance.
