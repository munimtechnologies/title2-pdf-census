# Title II date slips, part 14: each state's own Title II rule pages, read whatever their date (pre-registration)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data: CC BY 4.0.

Written on 2026-11-15 at about 17:55 UTC, after this run started (17:47 UTC) and before any search
for this part was run. It is committed in the same commit as the result (the publish lane runs
after the run ends), so the only proof of order is this note and the times below.

## Why this part

Part 13 (earlier today) counted only pages dated after the April 2026 extension and found almost no
stale ones (1 of 29). Its lesson: pages that get updated give the new dates, and the stale ones are
the pages nobody touched, so they carry an old date or none. A date-gated frame defines staleness
away. This part reads a fixed list of reference pages, the pages each state's own domain returns
for a neutral question about the rule, **whatever date they show**.

## Known before registering (may have shaped the predictions)

- The rule: 28 CFR 35.200(b) as amended by AG Order No. 6742-2026 (91 FR 20912, April 20, 2026):
  April 26, 2027 for public entities of 50,000 or more, April 26, 2028 for smaller ones and all
  special districts. The 2024 rule had April 24, 2026 and April 26, 2027.
- **Nevada** is already known to have a stale page: the Governor's Technology Office's Digital
  Accessibility page on the rule (ada.nv.gov, "Last updated 02/19/2026") gives "Compliance deadline:
  April 24, 2026" with no notice of a change (part 13, read twice). It counts here only if this
  part's search returns it.
- **Georgia**: the Georgia Technology Authority's post of 2026-02-18 counting down to April 24,
  2026 was seen in part 13 (a dated news item written before the change).
- Parts 9-10 found 12 states with a page giving the wrong day April 24, 2027 when searched for
  that exact date: New York, Illinois, Michigan, Washington, Tennessee, Maryland, Wisconsin,
  Oregon, Utah, Idaho, Delaware, North Dakota.
- MV2's crawl of state .gov accessibility pages (results/state-pages) found that accessibility
  pages rarely give any Title II day.
No search of any state domain with this part's query had been run before this note.

## Frame (50 states, fixed)

The 50 states with the domain lists used in parts 9-10 (`all-50-states.csv` there), subdomains
included.

## Method

1. For each state, in census-rank order, one web search limited to its domain list
   (`allowed_domains`) with the fixed query
   `ADA Title II web accessibility rule compliance date WCAG 2.1`.
   The search tool may reword the query itself; that is a limit, not corrected.
2. **Explainer candidates**: in the order returned, results on the state's domain list whose title
   or URL shows the page is about the Justice Department's Title II web accessibility rule (a rule
   summary, FAQ, guidance, policy, training or news page about the rule or the state's work to
   meet it). Generic accessibility statements, unrelated ADA pages, and PDFs are not candidates.
   Search summaries are never used to class a page.
3. Read the **first 2 candidates** per state with the page reader, asking for the date shown (and
   any "updated" date), every Title II compliance date with its quote, and whether the 2026
   extension is mentioned. Unreadable pages (403, 404, bot check) are listed and replaced by the
   next candidate, up to 3 attempts per state.
4. Each read page gets one class:
   - **current**: gives April 26, 2027 for 50,000+ and/or April 26, 2028 for smaller entities, or
     says the dates were extended to 2027/2028;
   - **stale**: gives April 24, 2026 as the 50,000+ date and/or April 26, 2027 as the
     smaller-entity date as the dates in force, with no mention of the extension or of any 2028
     date. Exception: a dated news item or announcement dated before 2026-04-20 that reports the
     dates of its day is **old news**, not stale;
   - **wrong day**: gives April 24, 2027, April 24, 2028, April 27, 2028 or April 28, 2028 as a
     Title II day;
   - **mixed**: gives a 2024 date as in force and a new date as in force;
   - **no date**: states no Title II compliance date.
5. Each state gets one class: `stale` if any read page is stale; else `wrong day` if any is wrong
   day; else `current` if any is current or mixed; else `old news only`; else `none` (no
   candidate, or no candidate states a date). A state can show both stale and wrong-day pages;
   both are recorded.
6. Each stale or wrong-day page is read twice (two fetches). The date each page shows is recorded
   as shown (none if none).

## Predictions (fixed now)

- E1 (gate): at least 20 states have at least one read page that states a Title II compliance date
  (classes current, stale, wrong day, mixed or old news). If not, E2 and E3 are not graded.
- E2: among states with a dated explainer (class current, stale or wrong day), between 10% and 30%
  are `stale` (inclusive).
- E3: at least one state other than Nevada is `stale`.
- E4: at least 80% of the stale pages show no date or a date before 2026-04-20. Graded only if
  there are at least 3 stale pages.
- E5: every state with a wrong-day page in this frame is one of the 12 found in parts 9-10.
  Graded only if at least one wrong-day page is found.

## Addendum (about 18:02 UTC, after the first 5 states' result lists were seen, before any page was read)

Step 2 needed an operational test, fixed now and applied to all 50 states including the first 5.
A non-PDF result on the state's domain list is a **candidate** if its title or URL either (a) names
Title II, the ADA, the DOJ, a "rule", a "deadline" or "compliance" in connection with web or digital
accessibility, or (b) presents itself as digital or web accessibility guidance for others (words
such as guide, guidance, getting started, leadership, FAQ, requirements, program, training,
resources, best practices). **Not candidates**: a page titled only "Accessibility", "Accessibility
Statement", "Accessibility Policy" or "ADA Disclaimer" that describes one site's own accessibility;
contracts, RFPs, bills, audits, transcripts; state-law certification pages (e.g. California's
website accessibility certification); and pages of counties, cities or schools served on a state
domain. When it is unclear, the result is not a candidate. Results the reader cannot open count
as attempts (step 3).

## Limits known in advance

One search per state on one day through one search engine; its ranking decides which pages are
read, and an index miss is not a finding that a state has no such page. Two pages per state are a
sample of a state's pages, not all of them. Agencies outside the domain lists are not searched.
Pages are read through an AI page reader that quotes the page. A date on a page is what it says,
not a finding about any entity's compliance.
