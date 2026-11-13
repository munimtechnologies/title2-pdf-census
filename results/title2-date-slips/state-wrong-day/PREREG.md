# Title II date slips, part 9: the wrong-day search on 25 state government domains (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13, after this run started (22:30 UTC) and before any search in this part was
run. It is committed in the same commit as the result (the publish lane runs after the run ends),
so the only proof of order is this note and the times below.

What was already known (and so may have shaped these predictions): parts 1-8 of this series. Part
1 found no wrong day in 14 vendor, law and news guides; parts 2-3 found wrong days on 3 of 23
municipal-league and 2 of 6 county-association pages that give a day; part 4 found no day at all,
right or wrong, on 39 Maryland and Michigan county sites; parts 7-8 ran the search below at
universities and found April 24, 2027 at 6 of 15 Big Ten universities, 2 of 10 UC campuses and 3 of
22 CSU campuses, mostly on central pages. Outside the series, a held correction note (not yet sent)
concerns Delaware's Government Information Center newsletter, a state body (Delaware is not in this
frame). No search on any state domain below was run for this part before this note was written.

## Question

Searched for the wrong day itself, how many of the 25 most populous states have a page on their
state government domain giving April 24, 2027 as an ADA Title II day, and who publishes it: the
state's central IT or accessibility office, or another state agency? States are public entities
of 50,000 or more, so the rule's day for them is April 26, 2027 (28 CFR 35.200(b) as amended by
AG Order No. 6742-2026, 91 FR 20912).

## Frame (25 states, fixed)

The 25 most populous states in the 2020 Census, each with the domain list fixed here (subdomains
included). Where a state's agencies sit under two zone names, both are listed.

California ca.gov; Texas texas.gov; Florida myflorida.com, fl.gov; New York ny.gov;
Pennsylvania pa.gov; Illinois illinois.gov; Ohio ohio.gov; Georgia georgia.gov, ga.gov;
North Carolina nc.gov; Michigan michigan.gov; New Jersey nj.gov; Virginia virginia.gov;
Washington wa.gov; Arizona az.gov; Massachusetts mass.gov; Tennessee tn.gov; Indiana in.gov;
Maryland maryland.gov; Missouri mo.gov; Wisconsin wi.gov, wisconsin.gov; Colorado colorado.gov;
Minnesota mn.gov; South Carolina sc.gov; Alabama alabama.gov; Louisiana la.gov.

## Method (parts 7-8, unchanged except the levels)

1. For each state, one web search limited to its domain list (`allowed_domains`) with the fixed
   query `"April 24, 2027" ADA Title II accessibility`. The search tool may also run reworded
   queries of its own; that is recorded as a limit, not corrected.
2. Candidate pages: every result on the domain list whose title, snippet or the search reader's
   summary shows "April 24, 2027" (or "4/24/2027", "4/24/27").
3. Each candidate is read with the page reader. It is a **hit** if a sentence on the page gives
   April 24, 2027 as an ADA Title II (or "federal" digital accessibility) compliance day,
   deadline, effective day or content cutoff. A page that names April 24, 2027 only as something
   else (an event, a meeting, a state-law or grant deadline the page does not tie to Title II) is
   not a hit. Every hit is read twice (two fetches; if the page reader fails, two search-reader
   passes, marked).
4. Each hit page gets exactly one level (the list is exhaustive):
   - `central`: the state's IT agency or CIO office, its statewide accessibility or ADA
     coordinator office, the governor's office or the state portal;
   - `agency`: any other state agency, department, board, commission or state-run program;
   - `other`: anything that fits none of the two (for example a local government, school, college
     or vendor page served on the state domain).
   Each hit page also records whether it gives April 26, 2027 too.
5. Each state gets `hit` (at least one hit page) or `no_hit`.

## Predictions (fixed now)

- S1: at least 3 of the 25 states are `hit`.
- S2: at most 9 of the 25 are `hit` (below the Big Ten's 40%).
- S3: more hit pages are `agency` than `central`.
- S4: at least 1 hit page also gives April 26, 2027.

## Limits known in advance

One search per state on one day, and the search index does not hold every page, so counts are
lower bounds. Many state agencies use their own domains outside these lists (for example a
state university, a transit authority or an agency with a .com or .org address); those are not
searched. Pages are read through AI page and search readers that quote the page. 25 states are a
fixed group, not a sample. A date on a page is what it says, not a finding that a state is or is
not in compliance, and April 24, 2027 is two days earlier than the rule's April 26, 2027, not
later.
