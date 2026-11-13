# Title II date slips, part 5: University of California and California State University campuses (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13 at about 10:55 UTC, before any page in this frame was searched for or read
in this run. It is committed in the same commit as the result (the publish lane runs after the
run ends), so the only proof of order is this note and the times below. What was already known:
part 4 (`../county-sites/`, 2026-11-13 about 09:40 UTC, outside its frame) found that the UC Davis
Digital Accessibility FAQ says "We are also responsible for meeting the ADA Title II deadline on
April 24, 2027", and that the same page says University of California policy IMT-1300 "still
identifies April 24, 2027 as the effective date of implementation". No other UC or CSU page, and
not the IMT-1300 policy text itself, has been read for this series.

## Why

Public universities are Title II entities themselves. If a system-wide policy carries a day the
rule does not have, the slip can spread to every campus page that follows the policy. The two
California systems give a natural comparison: UC (whose policy is quoted with April 24, 2027) and
CSU (a separate system with its own Accessible Technology Initiative).

## Frame (`frame-prereg.csv`, 32 campuses)

- UC: all 10 campuses.
- CSU: its 22 universities (Cal Maritime merged into Cal Poly San Luis Obispo in 2025 and is
  covered by calpoly.edu).

Domains were written from memory before searching. Where a domain is marked `unsure`, or a
domain-limited search returns nothing from that domain, the real domain is found with one web
search for the campus name and noted. The two system offices (ucop.edu, calstate.edu) are not in
the frame; their policy pages may be read afterwards as context and are reported apart.

## Method (as in parts 2 to 4)

1. For each campus, one web search limited to its domain with the fixed query
   `ADA Title II website accessibility rule compliance deadline extension` (no date words).
2. Read, in result order, up to 2 results that are pages on the campus domain about the ADA
   Title II web rule or the campus's own digital accessibility (statement, policy, FAQ, news,
   training). Pages the page reader cannot open (403, binary PDF) are recorded as such, and the
   search reader's quotes are used and marked.
3. For each page, quote every sentence giving a Title II compliance day and compare with
   28 CFR 35.200(b) as amended (AG Order No. 6742-2026, 91 FR 20912, April 20, 2026): April 26,
   2027 (50,000 or more) and April 26, 2028 (under 50,000). Both systems are parts of the State of
   California, so the 2027 day is theirs.
4. Each campus gets one class:
   - `wrong`: a read page gives a current Title II day the rule does not have (for example
     April 24, 2027, April 24, 2028, April 27, 2028 or April 28, 2028);
   - `right`: a read page gives a current day, and every current day given matches;
   - `old_only`: only the 2024 rule's days (April 24, 2026 as the deadline);
   - `no_day`: pages about the rule or digital accessibility, but no day;
   - `none`: no such page in the results.
5. Every wrong day is read twice, in two separate fetches (or two search-reader passes, marked).

## Predictions (fixed now)

- P1: at least 3 of the 10 UC campuses are `wrong` (the IMT-1300 day is a UC-system pattern,
  not just Davis).
- P2: at most 2 of the 22 CSU campuses are `wrong`.
- P3: the share of UC campuses that are `wrong` is higher than the share of CSU campuses that
  are `wrong`.
- P4: no campus page gives April 28, 2028.
- P5: at least 10 of the 32 campuses give a current day (`right` or `wrong`); universities write
  about the deadline more than counties do (part 4 found 0 of 39 counties giving any day).

## Limits known in advance

One search per campus on one day; search results vary, and many university pages are not indexed
or are behind sign-in. Pages are read through AI page and search readers that quote the page.
32 campuses in one state are not a sample of US universities, and MV2's queued public-colleges
census will measure this more widely. A page not found is not proof a campus has none, and a
date on a page is what it says, not a finding that a campus is or is not in compliance.
