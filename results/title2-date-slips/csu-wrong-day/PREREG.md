# Title II date slips, part 8: the wrong-day search at the 22 CSU campuses (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13, after this run started (19:47 UTC) and before any search in this part was
run. It is committed in the same commit as the result (the publish lane runs after the run ends),
so the only proof of order is this note and the times below.

What was already known (and so may have shaped these predictions): part 5 (`../uc-csu/`) read the
first two relevant results of a search with no date words at each CSU campus and found April 24,
2027 at Cal State East Bay, Cal State Northridge and Cal Poly San Luis Obispo (CSUN's update page
also has exception cutoffs "prior to April 24, 2027"). Part 7 (`../unit-pages/`) ran the search
below at 15 Big Ten universities and 10 UC campuses: 6 of 15 Big Ten and 2 of 10 UC had at least
one page giving April 24, 2027, 13 pages in all, of which 6 were central, 4 unit and 3 campus-wide
divisions. Nothing else was looked at for this part.

## Question

Searched for the wrong day itself, how many CSU campuses have a page giving April 24, 2027 as an
ADA Title II day, and on what kind of page? Is the CSU rate like the UC rate or the Big Ten rate?

## Frame (22 campuses, fixed)

The 22 CSU campuses of part 5, with the same domains: csub.edu, csuci.edu, csuchico.edu,
csudh.edu, csueastbay.edu, fresnostate.edu, fullerton.edu, humboldt.edu, csulb.edu,
calstatela.edu, csumb.edu, csun.edu, cpp.edu, csus.edu, csusb.edu, sdsu.edu, sfsu.edu, sjsu.edu,
calpoly.edu, csusm.edu, sonoma.edu, csustan.edu.

## Method (part 7's, unchanged)

1. For each campus, one web search limited to its domain (`allowed_domains`) with the fixed query
   `"April 24, 2027" ADA Title II accessibility`. The search tool may also run reworded queries of
   its own; that is recorded as a limit, not corrected.
2. Candidate pages: every result on the domain whose title, snippet or the search reader's summary
   shows "April 24, 2027" (or "4/24/2027", "4/24/27").
3. Each candidate is read with the page reader. It is a **hit** if a sentence on the page gives
   April 24, 2027 as an ADA Title II (or "federal" digital accessibility) compliance day,
   deadline, effective day or content cutoff. A page that names April 24, 2027 only as something
   else (for example an event, or a campus or CSU policy deadline that the page does not tie to
   Title II) is not a hit. Every hit is read twice (two fetches; if the page reader fails, two
   search-reader passes, marked). A page already read twice in part 5 needs one read here.
4. Each hit page gets exactly one level (the list is exhaustive):
   - `central`: the campus's accessibility or ATI office, ADA/504 or compliance office, central
     IT, or campus-wide news, newsletter, president, provost or academic senate pages;
   - `division`: another campus-wide service unit (for example a teaching-and-learning or faculty
     development center, an online-education office, or a finance and administration division);
   - `unit`: a college, school, department, library, a unit's own IT group, news or blog;
   - `other`: anything that fits none of the three (for example a hosted journal article, a
     student page or a system-wide page served on the campus domain).
   For U3-style grading, only `unit` counts as unit; the result also reports the counts with
   `division` counted as unit. Each hit page also records whether it gives April 26, 2027 too.
5. Each campus gets `hit` (at least one hit page) or `no_hit`.

## Predictions (fixed now)

- C1: at least 4 of the 22 campuses are `hit`.
- C2: at most 11 of the 22 are `hit`.
- C3: at least one campus that part 5 did not class `wrong` is `hit`.
- C4: at most half of all hit pages are `unit`.
- C5: at least 2 hit pages also give April 26, 2027.

## Limits known in advance

One search per campus on one day, and the search index does not hold every page, so counts are
lower bounds. Several CSU sites refused the page reader in part 5 (certificate errors), so more
pages will rest on search-reader passes. Pages are read through AI page and search readers that
quote the page. 22 campuses are a fixed group, not a sample. A date on a page is what it says, not
a finding that a campus is or is not in compliance, and April 24, 2027 is two days earlier than the
rule's April 26, 2027, not later.
