# Title II date slips, part 15: each state education agency's Title II web rule pages, read whatever their date (pre-registration)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data: CC BY 4.0.

Written on 2026-11-16 at about 02:20 UTC, after this run started (02:05 UTC) and before any search
for this part was run. It is committed in the same commit as the result (the publish lane runs
after the run ends), so the only proof of order is this note and the times below.

## Why this part

Part 14 (2026-11-15) read each state's own Title II rule pages whatever their date and found that
9 of 19 states with a dated explainer still have a page giving the 2024 dates (April 24, 2026 /
April 26, 2027) as in force, mostly on central IT pages. State education agencies (SEAs) are a
different and untested group: they write guidance for the roughly 13,000 public school districts,
which are Title II entities themselves. No page in parts 1-14 was chosen because it was an SEA's.

## Known before registering (may have shaped the predictions)

- The rule: 28 CFR 35.200(b) as amended by AG Order No. 6742-2026 (91 FR 20912, April 20, 2026):
  April 26, 2027 for public entities of 50,000 or more, April 26, 2028 for smaller ones and all
  special districts. The 2024 rule had April 24, 2026 and April 26, 2027.
- **South Carolina**: part 14 read the SC Department of Education's district website guidance
  (ed.sc.gov), which gives "until April 26, 2027" (under 50,000) and "until April 26, 2026" (over
  50,000), stale with a wrong old first day. It counts here only if this part's search returns it.
- Part 14's 47% stale share among state explainers, and part 13's finding that stale pages carry
  no date or a pre-change date.
- No other SEA page about the rule is known to MV2's agents. No search of any SEA domain with this
  part's query had been run before this note.

## Frame (50 SEAs, fixed)

`seas.csv` lists the 50 state education agencies with their domains. For 10 states the SEA shares
a state portal domain (CT portal.ct.gov, IN in.gov, ME maine.gov, MI michigan.gov, NJ nj.gov,
ND nd.gov, OR oregon.gov, TN tn.gov, OK oklahoma.gov, PA pa.gov); there only results whose URL path
is the SEA's (listed in seas.csv) count, and the query gets the words `department of education`
added at the end (fixed now). The Hawaii DOE is both the SEA and the state's single school district.

## Method

1. For each state, in alphabetical order, one web search limited to the SEA's domains
   (`allowed_domains`) with the fixed query
   `ADA Title II web accessibility rule compliance date WCAG 2.1 school districts`
   (plus `department of education` for the 10 shared-domain states).
   The search tool may reword the query itself; that is a limit, not corrected.
2. **Candidates**, in the order returned: non-PDF results on the SEA's domains (and path, for the
   shared-domain states) whose title or URL either (a) names Title II, the ADA, the DOJ, a "rule",
   a "deadline" or "compliance" in connection with web or digital accessibility, or (b) presents
   itself as digital or web accessibility guidance (guide, guidance, getting started, FAQ,
   requirements, program, training, resources, best practices, memo, newsletter item), for
   districts or for the agency's own staff. **Not candidates**: a page titled only
   "Accessibility", "Accessibility Statement", "Accessibility Policy", "Web Accessibility" or
   "ADA Disclaimer" that describes one site's own accessibility; contracts, RFPs, board minutes,
   bills, audits; special-education (IDEA) or assessment-accommodation pages that are not about
   web or digital accessibility; pages of single districts or schools. When unclear, not a
   candidate. Search summaries are never used to class a page.
3. Read the **first 2 candidates** per SEA with the page reader, asking for the date shown (and
   any "updated" date), every Title II compliance date with its quote, and whether the 2026
   extension is mentioned. Unreadable pages (403, 404, bot check, empty) are listed and replaced
   by the next candidate, up to 3 attempts per SEA.
4. Page classes (same as part 14):
   - **current**: gives April 26, 2027 for 50,000+ and/or April 26, 2028 for smaller entities, or
     says the dates were extended to 2027/2028;
   - **stale**: gives April 24, 2026 (or April 26, 2026) as the 50,000+ date and/or April 26, 2027
     as the smaller-entity date as the dates in force, with no mention of the extension or of any
     2028 date. Exception: a dated news item, memo or newsletter dated before 2026-04-20 that
     reports the dates of its day is **old news**, not stale;
   - **wrong day**: gives April 24, 2027, April 24, 2028, April 27, 2028 or April 28, 2028 as a
     Title II day;
   - **mixed**: gives a 2024 date as in force and a new date as in force;
   - **no date**: states no Title II compliance date.
5. SEA class: `stale` if any read page is stale; else `wrong day` if any is wrong day; else
   `current` if any is current or mixed; else `old news only`; else `none`. Both stale and
   wrong-day pages are recorded when an SEA has both.
6. Each stale or wrong-day page is read twice (two fetches). The date each page shows is recorded
   as shown (none if none).

## Predictions (fixed now)

- F1 (gate): at least 10 SEAs have at least one read page that states a Title II compliance date
  (classes current, stale, wrong day, mixed or old news). If not, F2 and F5 are not graded.
- F2: among SEAs with a dated explainer (class current, stale or wrong day), at least 30% are
  `stale` (part 14 found 47% for state explainers).
- F3: at least one SEA other than South Carolina is `stale`.
- F4: at least 80% of stale pages show no date or a date before 2026-04-20. Graded only if there
  are at least 3 stale pages.
- F5: fewer SEAs are `wrong day` than `stale` (stale dates, not the wrong new day, are the main
  slip on reference pages).
- F6: at most half of the 50 SEAs have any candidate page (SEAs write little about the web rule).

## Limits known in advance

One search per SEA on one day through one search engine; its ranking decides which pages are read,
and an index miss is not a finding that an SEA has no such page. Two pages per SEA are a sample.
PDFs (where much SEA guidance sits) are not read. Pages are read through an AI page reader that
quotes the page. A date on a page is what it says, not a finding about any entity's compliance.
