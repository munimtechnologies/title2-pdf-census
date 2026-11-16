# Title II date slips, part 16: state education agencies' newsletters, memos and mailings (result)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data: CC BY 4.0.
Pre-registration: [`PREREG.md`](PREREG.md), written 2026-11-16 at about 16:35 UTC, before the first
search. Searches and reads ran from about 16:35 to 17:40 UTC on 2026-11-16.

## Question

Part 15 found that the 50 state education agencies (SEAs) rarely keep a standing web page with the
ADA Title II web rule's compliance dates, and that the dates appeared in newsletters and mailings
instead. This part searched each SEA's own domains for those dated communications, to test whether
an item's date predicts whether its Title II dates are current.

## Answer: the frame failed again; one search per SEA almost never surfaces a readable dated item

| | count |
|---|---|
| SEAs searched (one fixed query each) | 50 |
| SEAs with at least one candidate (dated communication on its own domain, not a PDF) | 8 (CO, GA, MO, NC, SC, VT, VA, WI) |
| candidates in all | 22 (10 of them Georgia's weekly digests) |
| candidates tried / read | 12 / 6 |
| unreadable | 6: two South Carolina memo links that serve compressed PDFs, two North Carolina "update" downloads that redirect to the home page, Virginia (403), Vermont (403 on two fetches) |
| read items that give a Title II compliance date | 2, both Wisconsin DPI |
| SEAs with a read item giving a date | 1 |

The two dated items:

- Wisconsin DPI administrators' biweekly mailing, **Tuesday, April 21, 2026**: "Districts and public
  entities serving populations of 50,000 or more now have until April 26, 2027, to comply" /
  "smaller districts and special-purpose entities now have until April 26, 2028." **Current**, one
  day after the rule appeared in the Federal Register.
- Wisconsin DPI administrators' biweekly mailing, **Tuesday, September 16, 2025**: "Some districts may
  fall under an April 2026 deadline." / "Most others may fall under an April 2027 deadline." **Old
  news** (before the change; months and years only).

The other four read items (Colorado's news bureau plan update, two Georgia weekly digests from August
and October 2025, Missouri's special-education listserv archive) give no Title II date.

## Predictions

| | prediction | result |
|---|---|---|
| N1 (gate) | at least 8 SEAs have a read candidate stating a Title II date | **failed** (1) |
| N2 | at least 80% of read items dated on or after 2026-04-20 that give dates as in force are current | not graded (gate failed; 1 such item, current) |
| N3 | no read item dated on or after 2026-05-01 is stale | not graded (gate failed; 0 such items) |
| N4 | at most 20% of read pre-2026-04-20 items giving the 2024 dates give one wrong | not graded (1 such item, months only) |
| N5 | under 15% of read post-change items with an exact new day give a wrong day | not graded (gate failed; 1 such item, right) |
| N6 | at least 15 SEAs have any candidate | **failed** (8) |

None held; two failed; four could not be graded.

## What the search results show instead (not counted)

Where an SEA's search results did carry the rule's dates, they sat almost entirely in **PDFs**,
which this frame excluded because the page reader cannot open many of them (two South Carolina
"memo" links that look like web pages turned out to be such PDFs). Per the search summaries only,
not read: Louisiana's DOE ran an "ADA compliance" item in seven monthly EdTech calls from September
2025 to April 2026, and its April 9, 2026 deck gives the 2024 dates; Nebraska's January 2026 district
plan guide and a Minnesota GovDelivery attachment give the 2024 dates; an undated Tennessee
Department of Education legal summary gives the 2024 dates; Idaho's May 2026 grants slides give the
new dates. See [`outside-count.csv`](outside-count.csv) and [`search-log.csv`](search-log.csv).

Two pages outside the frame were read:

- The Michigan Office of the Auditor General's 2024 archive page still says its documents were
  "published before the April 24, 2027 compliance date" (read twice; no page date). Part 9
  recorded the same disclaimer on three other Auditor General pages on 2026-11-13.
- A search summary said New Jersey's Office of Information Technology lists "Final Rule Compliance
  Deadline: April 24, 2027". Read, its page gives "April 26, 2027" as the State of New Jersey's
  deadline: the summary was wrong, which is why this series never counts search summaries.

## What this means

Across parts 15 and 16, two frames and 100 searches on SEA domains surfaced a readable, dated Title
II page or item for only 3 of 50 SEAs (North Carolina and Wisconsin current, South Carolina stale).
That is a finding about **where SEAs publish**, not about what they say: their guidance to districts
on this rule is mostly in slide decks, memos and attachments (PDF), and in mail sent through outside
services. Measuring whether SEA guidance is current needs a PDF-reading crawl of those files, not
more web-page searches. That is the planned next step (a small compute job that downloads a fixed
list of SEA PDFs and extracts every sentence with a Title II date).

## Limits

One search per SEA on one day through one search engine (which rewrote the query, dropping the OR
terms); an index miss is not a finding that an SEA sent nothing. Two items per SEA at most were
read; Georgia's eight 2026 digests were not read under the method. Reads ran from a different
machine than part 15, and two sites (Vermont, Virginia) refused it with 403. Pages were read through
an AI page reader that quotes the page. Dates on a page are what it says, not a finding about any
entity's compliance.

## Files

- `PREREG.md`: the plan and predictions, fixed before the first search.
- `search-log.csv`: per SEA, the results, candidates and on-topic PDFs.
- `pages.csv`: every candidate tried, with read status, item date, class and quotes.
- `outside-count.csv`: pages seen or read outside the count.
