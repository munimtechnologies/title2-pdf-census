# Title II date slips, part 16: state education agencies' newsletters, memos and mailings about the Title II web rule (pre-registration)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data: CC BY 4.0.

Written on 2026-11-16 at about 16:35 UTC, after this run started (16:17 UTC) and before any search
for this part was run. It is committed in the same commit as the result (the publish lane runs
after the run ends), so the only proof of order is this note and the times below.

## Why this part

Part 15 (2026-11-16, 02:05-03:30 UTC) searched each of the 50 state education agencies (SEAs) for a
standing explainer page about the ADA Title II web rule and found a dated one for only 2 (North
Carolina current, South Carolina stale). Read outside its count, dated newsletters and mailings from
Wisconsin, Vermont and Oklahoma gave the dates. Part 15's frame excluded such items by its candidate
test. This part uses the frame part 15 missed: dated communications (newsletters, memos, mailings,
bulletins, news items) on each SEA's own domains. The question is whether an item's date predicts
whether its Title II dates are current: items written after the April 20, 2026 extension should
give the new dates, and stale dates should sit only in items written before it.

## Known before registering (may have shaped the predictions)

- The rule: 28 CFR 35.200(b) as amended by AG Order No. 6742-2026 (91 FR 20912, April 20, 2026):
  April 26, 2027 for public entities of 50,000 or more, April 26, 2028 for smaller ones and all
  special districts. The 2024 rule had April 24, 2026 and April 26, 2027.
- From part 15's outside count (`../sea-explainers/outside-count.csv`): Wisconsin DPI's WISE
  Insights newsletter of March 17, 2026 (2024 first date right, second date given wrongly as April
  24, 2027) and its administrators' biweekly mailing of April 21, 2026 (current); Vermont AOE's
  Weekly Field Memo of May 21, 2026 (current); an Oklahoma SDE page modified Nov 4, 2026 (current,
  month and year only); search summaries (not read) of PDFs from Idaho (May 2026, new dates),
  Louisiana (April 2026, 2024 dates), Minnesota, Nebraska and Tennessee. These count here only if
  this part's search returns them and they pass the candidate test.
- Part 11: of pages dated April 20-30, 2026 with an exact new first day, 1 of 9 gave the wrong
  April 24, 2027; parts 1-10 found the wrong day mainly in guides and associations.
- No search of any SEA domain with this part's query had been run before this note.

## Frame (50 SEAs, fixed)

The 50 SEAs and their domains in `seas.csv` (same list as part 15). For the 10 states whose SEA
shares a state portal domain (CT, IN, ME, MI, NJ, ND, OR, TN, OK, PA), only results whose URL path
is the SEA's count, and the query gets `department of education` added at the end.

## Method

1. For each state, in alphabetical order, one web search limited to the SEA's domains with the
   fixed query `ADA Title II web accessibility deadline school districts newsletter OR memo OR update`
   (plus `department of education` for the 10 shared-domain states). The search tool may reword
   the query itself; that is a limit, not corrected.
2. **Candidates**, in the order returned: non-PDF results on the SEA's domains (and path) whose
   title or URL presents a dated communication: a newsletter, memo, mailing, bulletin, update,
   digest, message, announcement, press or news release, news item, or "weekly"/"monthly" item,
   or a title made only of a date or issue number. Examples written before the first search:
   "WISE Insights March 2026", "Biweekly Mailing April 21, 2026", "Weekly Field Memo: Recent News
   and Items of Interest", "Superintendent's Weekly Message", "News Release: ...", "LEA Bulletin
   2026-14", "Updates for District Leaders - May 2026", a URL path containing newsletter, memo,
   mailing, bulletin, news, update, message, announce, digest or weekly. **Not candidates**:
   standing explainer, guidance, policy or accessibility-statement pages (part 15's frame), PDFs
   (listed separately, not read: the page reader cannot open many of them), board minutes,
   contracts, RFPs, single districts' or schools' pages, and items not about web or digital
   accessibility. When unclear, not a candidate. Search summaries are never used to class a page.
3. Read the **first 2 candidates** per SEA with the page reader, asking for the item's date (issue,
   memo, posting or "updated" date), every Title II compliance date with its quote, and whether the
   2026 extension is mentioned. Unreadable pages (403, 404, bot check, empty) are listed and
   replaced by the next candidate, up to 3 attempts per SEA. Every stale or wrong-day page is read
   twice.
4. Page classes (as in parts 14-15): **current** (April 26, 2027 for 50,000+ and/or April 26, 2028
   for smaller entities, or says the dates were extended to 2027/2028); **stale** (2024 dates as in
   force, no extension or 2028 date, in an item dated on or after 2026-04-20 or undated); **old
   news** (2024 dates in an item dated before 2026-04-20); **wrong day** (April 24, 2027, April 24,
   2028, April 27, 2028 or April 28, 2028 given as a new Title II day); **mixed**; **no date**.
   Separately, for items giving the 2024 rule's dates, whether each 2024 date is given right
   (April 24, 2026 / April 26, 2027) or wrong.
5. "Item date" = the date the page shows for the item; if none, "undated".

## Predictions (fixed now)

- N1 (gate): at least 8 SEAs have at least one read candidate that states a Title II compliance
  date (any class except no date). If not, N2, N3 and N5 are not graded.
- N2: of read candidates dated on or after 2026-04-20 that give dates as in force (current, stale,
  wrong day, mixed), at least 80% are current. Graded only if there are at least 5 such items.
- N3: no read candidate dated on or after 2026-05-01 is stale. Graded only if at least 3 read
  candidates dated on or after 2026-05-01 give a Title II date.
- N4: of read candidates dated before 2026-04-20 that give the 2024 dates, at most 20% give a 2024
  date wrong. Graded only if there are at least 5 such items.
- N5: fewer than 15% of read candidates dated on or after 2026-04-20 that give an exact new day
  give a wrong day. Graded only if there are at least 5 such items.
- N6: at least 15 of the 50 SEAs have at least one candidate (part 15's explainer frame: 10).

## Limits known in advance

One search per SEA on one day through one search engine; its ranking decides which items are read,
and an index miss is not a finding that an SEA sent no such item. Two items per SEA are a sample.
PDFs (memos are often PDFs) are not read. Newsletters hosted on outside mail services (GovDelivery,
Smore, Constant Contact) are outside the frame because the search is limited to SEA domains. Pages
are read through an AI page reader that quotes the page. A date on a page is what it says, not a
finding about any entity's compliance.
