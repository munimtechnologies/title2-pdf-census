# Title II date slips, part 15: state education agencies' Title II rule pages, read whatever their date (2026-11-16, pre-registered)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data CC BY 4.0.
Plan: [PREREG.md](PREREG.md), registered 2026-11-16 at about 02:20 UTC before any search for this
part. No addendum was needed. Every candidate page: [pages.csv](pages.csv). Every agency:
[seas.csv](seas.csv). Pages seen outside the count: [outside-count.csv](outside-count.csv).

## Headline

**The method that found dated Title II explainers for 19 of 50 states in part 14 finds them for
only 2 of the 50 state education agencies (SEAs).** North Carolina's Department of Public
Instruction gives the current dates (April 26, 2027 / April 26, 2028) and notes the April 2026
extension. South Carolina's Department of Education still gives the 2024 pair with the first day
wrong ("until April 26, 2026" for districts of more than 50,000, "until April 26, 2027" for
smaller ones), unchanged since part 14 read it the day before. No SEA page read here gives a
wrong new day.

The gate prediction failed, so the main test (what share of SEAs are stale) could not be graded.
The useful negative result is **where SEAs put the dates**: in district newsletters, biweekly
mailings, field memos and slide decks, which a test that reads pages by their title or URL does
not pick up. Read outside the count, three of those items dated after the change give the new
dates (Wisconsin DPI on April 21, 2026, Vermont's Agency of Education on May 21, 2026, and
Oklahoma's State Department of Education, last modified November 4, 2026).

## Method in brief

For each of the 50 SEAs, one search limited to its domains (shared state portals were limited to
the SEA's path, with `department of education` added to the query) using the fixed query
`ADA Title II web accessibility rule compliance date WCAG 2.1 school districts`. Candidates are
non-PDF results whose title or URL shows a page about the rule or digital accessibility guidance.
Site accessibility statements, special-education and assessment pages, RFPs and single-district
pages are not candidates. The first 2 candidates were read, with up to 3 attempts when a page
could not be opened. Each page was classed current, stale, wrong day, mixed, old news or no date.
The stale page was read twice.

- 10 of 50 SEAs had at least one candidate. The other 40 returned PDFs (manuals, slide decks,
  RFPs, board packets), the agency's own accessibility statement, or unrelated pages.
- 16 candidate pages were tried. 8 were read and 8 could not be read: 403 at Maryland (after a
  redirect to its new domain msde.maryland.gov), New Mexico and Virginia; certificate errors at
  New York; a bot check at California; a 404 at South Carolina.
- Of the 8 read pages, 1 is current (North Carolina), 1 is stale (South Carolina) and 6 give no
  date. The 6 come from California, Colorado, Nebraska, New Jersey, North Carolina and South
  Carolina: web standards pages, a training course page and topic hubs that name WCAG 2.1 or the
  2024 rule but give no compliance date.
- 9 of the 16 candidates were candidates by judgment rather than by the literal test (marked in
  pages.csv). Both dated pages came from candidates that meet the literal test, so no count below
  changes without the judgment calls.

## Predictions and results

| Prediction | Result | Held? |
|---|---|---|
| F1 (gate): at least 10 SEAs have a read page that states a Title II date | 2 (North Carolina, South Carolina) | **no** |
| F2: at least 30% of SEAs with a dated explainer are stale | 1 of 2; not graded (gate failed) | not graded |
| F3: at least one SEA other than South Carolina is stale | none | **no** |
| F4: at least 80% of stale pages show no date or a pre-change date | 1 stale page (no date shown); not graded (needs 3) | not graded |
| F5: fewer SEAs are wrong day than stale | 0 wrong day, 1 stale; not graded (gate failed) | not graded |
| F6: at most half of the 50 SEAs have any candidate | 10 of 50 | yes |

One held, two failed and three could not be graded. The predictions assumed that SEAs, like state
IT offices, keep standing reference pages about the rule. Most do not, at least none that one
search on their own domain surfaces as an HTML page.

## Outside the count (seen in search results, not candidates)

These were seen in this part's search results but fail the candidate test (titled only by a date
or an issue, or a PDF). The four HTML pages were read; the PDFs were not, and their dates are as
the search tool summarised them, so they are not findings.

| SEA | Item | Date shown | What it says |
|---|---|---|---|
| Wisconsin | WISE Insights newsletter (read twice) | March 17, 2026 | "April 24, 2026, is the deadline ... 50,000 or more persons"; smaller LEAs and special districts "have until April 24, 2027." |
| Wisconsin | Administrators' biweekly mailing | April 21, 2026 | "Update: Federal Accessibility Deadline Extended One Year"; "now have until April 26, 2027" (50,000+) and "April 26, 2028" (smaller districts and special-purpose entities) |
| Vermont | Weekly Field Memo | May 21, 2026 | "By April 26, 2028, Vermont public schools will be required to make their websites and digital content accessible" |
| Oklahoma | Standards & Learning page | last modified Nov 4, 2026 | "Starting in April 2027 ... 50,000 or more"; "In April 2028, schools of any size must comply" |
| Idaho, Louisiana, Minnesota, Nebraska, Tennessee | PDFs (slides, guides, legal summary) | various | per summaries only: Idaho's May 2026 slides give the new dates; the others give the 2024 dates (Louisiana's slides from an April 9, 2026 call) |

**A government counterexample to part 11's pattern.** Part 11 found that the three pages giving the
wrong new day April 24, 2027 had also given the 2024 rule's second date as April 24, 2027 (it was
April 26, 2027), and part 12 found no government publisher to test this on. Wisconsin DPI is one:
its March 17, 2026 newsletter gives the old second date as April 24, 2027, yet its April 21, 2026
mailing gives the rule's new days, April 26, 2027 and April 26, 2028. So having the old day wrong
did not lead this publisher to the wrong new day. One case, outside the count.

## What this means

- For school districts, the state agency's standing web pages are mostly silent on the dates. A
  district looking on its SEA's site for "the deadline" is more likely to meet a newsletter or
  slide deck whose date tells it whether it is current. Dated items tend to be current or plainly
  old; the undated standing page in South Carolina is the risk, because it looks current.
- South Carolina's page is the SEA counterpart of part 14's finding for state IT offices: an
  undated reference page with the 2024 dates, seven months after the change, and with a first day
  (April 26, 2026) the 2024 rule never had.
- MV2's a11y-statement-check would not flag South Carolina's page: its `old_title2_date` note
  needs April 24, 2026. The planned `old_title2_pair` note, with April 26, 2026 accepted as the
  old first day, would (see part 14). This was worked out from the checker's condition, not by
  running it.

## Limits

One search per SEA on one day through one search engine, so an index miss is not evidence that an
SEA has no such page. PDFs were not read, and much SEA guidance is in PDFs. Half the candidates
could not be opened by the page reader (403s, certificate errors, a bot check), so New York,
Maryland, New Mexico and Virginia have candidates but no read page. The candidate test, fixed in
advance, excludes newsletters titled only by date; that choice decided most of the result.
Pages were read through an AI page reader that quotes the page. A date on a page is what it says,
not a finding about any entity's compliance.
