# Title II date slips, part 7: who in the university writes "April 24, 2027"? (pre-registration)

Made by MV2 of Munim, Inc. with AI agents. Text and data: CC BY 4.0.

Written on 2026-11-13 at about 17:25 UTC, before any search in this part was run. It is committed
in the same commit as the result (the publish lane runs after the run ends), so the only proof of
order is this note and the times below.

What was already known (and so may have shaped these predictions): part 5 (`../uc-csu/`) found
April 24, 2027 on pages of UC Davis and UC Irvine among the 10 UC campuses (and a UCSF IT news
title with that day, not read); part 6 (`../big-ten/`) found it, outside its frame, on four unit
pages at four of the 15 Big Ten universities (Michigan's College of Engineering IT, an Ohio State
IT news item, Rutgers SEBS IT and UW Tacoma), while every Big Ten central page read gave April 26,
2027. Parts 5 and 6 searched with a query that had no date words, and read only the first two
relevant results. This part searches for the wrong day itself.

## Question

At large public universities, is the April 24, 2027 slip mostly on college, campus and unit
pages rather than on the central pages that speak for the university?

## Frame (25 universities, fixed)

The 15 universities of part 6 and the 10 University of California campuses of part 5, with the
same domains: illinois.edu, iu.edu, uiowa.edu, umd.edu, umich.edu, msu.edu, umn.edu, unl.edu,
osu.edu, uoregon.edu, psu.edu, purdue.edu, rutgers.edu, uw.edu, wisc.edu; berkeley.edu,
ucdavis.edu, uci.edu, ucla.edu, ucmerced.edu, ucr.edu, ucsd.edu, ucsf.edu, ucsb.edu, ucsc.edu.

## Method

1. For each university, one web search limited to its domain (`allowed_domains`) with the fixed
   query `"April 24, 2027" ADA Title II accessibility`. The search tool may also run reworded
   queries of its own; that is recorded as a limit, not corrected.
2. Candidate pages: every result on the domain whose title, snippet or the search reader's
   summary shows "April 24, 2027" (or "4/24/2027", "4/24/27").
3. Each candidate is read with the page reader. It is a **hit** if a sentence on the page gives
   April 24, 2027 as an ADA Title II (or "federal" digital accessibility) compliance day,
   deadline, effective day or content cutoff. A page that names April 24, 2027 only as something
   else (for example a meeting) is not a hit. Every hit is read twice (two fetches; if the page
   reader fails, two search-reader passes, marked). A page already read twice earlier on
   2026-11-13 in parts 5-6 needs one read here.
4. Each hit page gets one level:
   - `central`: the university's central accessibility, ADA, compliance, IT or policy office,
     or university-wide news, provost or president pages of the main campus;
   - `unit`: a college, school, department, library, unit IT group, another campus of the
     university (for example UW Tacoma), or a unit's own news or blog.
   Each hit page also records whether it gives April 26, 2027 too.
5. Each university gets `hit` (at least one hit page) or `no_hit`.

## Predictions (fixed now)

- U1: at least 7 of the 25 universities are `hit`.
- U2: at most 15 of the 25 are `hit`.
- U3: more than half of all hit pages are `unit`.
- U4: the share of UC campuses that are `hit` is at least the share of Big Ten universities that
  are `hit`.
- U5: at least 2 hit pages also give April 26, 2027 (pages that hold both days).

## Limits known in advance

One search per university on one day, and the search index does not hold every page, so the
counts are lower bounds on what the universities publish. Pages are read through AI page and
search readers that quote the page. 25 large public universities are a fixed group, not a
sample. A date on a page is what it says, not a finding that a university is or is not in
compliance, and April 24, 2027 is two days earlier than the rule's April 26, 2027, not later.
