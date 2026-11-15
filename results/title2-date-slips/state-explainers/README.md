# Title II date slips, part 14: each state's own Title II rule pages, read whatever their date (2026-11-15, pre-registered)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data CC BY 4.0.
Plan: [PREREG.md](PREREG.md), registered 2026-11-15 at about 17:55 UTC before any search for this
part, with an addendum at about 18:02 UTC fixing which results count as candidates, written
after the first five states' result lists were seen and before any page was read.
Every page: [pages.csv](pages.csv). Every state: [states.csv](states.csv).

## Headline

**Seven months after the April 2026 extension, 9 of the 19 states whose own Title II explainer
pages give a date have at least one such page that still gives the 2024 dates as the dates in
force.** They are Georgia, Maryland, South Carolina, Louisiana, Connecticut, Nevada, Mississippi,
Hawaii and Vermont. 8 states give only current dates (New York, Illinois, North Carolina, New
Jersey, Washington, Oregon, Idaho and North Dakota), and 2 give a wrong new day (Utah and
Delaware, both already found in parts 9-10). Unlike the wrong day, which parts 9-10 found mostly
on agency pages, **the stale dates sit mostly on central offices' reference pages**: in 7 of the
9 states the stale page belongs to the state's IT agency, its portal or its statewide
accessibility program.

Part 13 counted only pages dated after the change and found 1 stale page in 29. This part reads
the pages each state's own domain returns for a neutral question about the rule, whatever their
date, and finds **10 stale pages among the 28 read pages that give a date and are not old news
items**. None of the 10 shows a
date after April 20, 2026: 7 show no date at all, and 3 show a date from before the change.

## Method in brief

For each of the 50 states, one search limited to the state's domains (the same domain lists as
parts 9-10) with the fixed query `ADA Title II web accessibility rule compliance date WCAG 2.1`.
Candidates are non-PDF results whose title or URL shows a page about the rule or digital
accessibility guidance for others (the addendum lists the exact test). The first 2 candidates per
state were read, with up to 3 attempts when a page could not be opened. Each page was classed
current, stale, wrong day, mixed, old news (a dated news item or memo from before April 20, 2026
that reports the dates of its day), or no date. Every stale and wrong-day page was read twice.

- 32 states had at least one candidate; 18 had none (their results were PDFs, contracts, site
  accessibility statements or unrelated pages).
- 57 candidate pages were tried: 39 read, 18 could not be read (403 at Massachusetts, Colorado,
  Kansas, Arizona and others; bot checks at Minnesota; title-only pages at Missouri).
- Of the 39 read pages: 14 current, 2 mixed, 10 stale, 2 wrong day, 3 old news, 8 no date.

## The stale pages (each read twice)

| State | Publisher | Date shown | What it says |
|---|---|---|---|
| Georgia | Digital Services Georgia (Georgia Technology Authority), "What State Agency Leaders Need to Know About the New Title II ADA Rule" | none | "Georgia state agencies must meet compliance by April 24, 2026." |
| Maryland | Department of Information Technology, "ADA Title II Final Rule Update" | none | "mandates that by April 24, 2026, State and local governments meet WCAG 2.1 Level AA guidelines" |
| Maryland | Department of Information Technology, Digital Accessibility Initiative | none | "requires accessibility compliance with WCAG 2.1 Level AA guidelines by April 24, 2026" |
| South Carolina | Department of Education, district website guidance | none | "until April 26, 2027" (under 50,000) and "until April 26, 2026" (over 50,000) |
| Louisiana | Office of Technology Services, "ADA Title II" | none | "State and local governments' compliance deadline is April 24, 2026." |
| Connecticut | CT.gov website accessibility FAQ, "Accessibility exceptions" | Oct 24, 2025 | "before your compliance date (April 24, 2026 for CT State agencies)" |
| Nevada | Governor's Technology Office, DOJ final rule page | last updated Feb 19, 2026 | "Compliance deadline: April 24, 2026" (50,000+), April 26, 2027 (smaller, special districts) |
| Mississippi | Information Technology Services, "ADA RULE UPDATE" | none | "April 26, 2026 - Statewide Public entities with greater than 50,000 population" and April 26, 2027 for smaller ones |
| Hawaii | Office of the Lieutenant Governor, "Accessibility Guidelines" | last updated Oct 10, 2025 | "The compliance date for the new rule ... is April 24, 2026." |
| Vermont | Universal Digital Accessibility program (Agency of Administration), "Document Exceptions" | none | "This document will need to meet all WCAG 2.1 AA standards by April 24, 2026." (and the same date as the exceptions cutoff throughout) |

No stale page mentions the extension, an interim final rule or any 2028 date.

Two patterns stand out:

- **Updated in one place, not in the next.** Connecticut's municipal guidance page gives the new
  dates in its "ADA Final Rule" section and the 2024 dates in its "Timeline cheat-sheet" further
  down the same page (counted as mixed). Vermont's program page says "The Federal government has
  extended the State's compliance deadline to April, 26, 2027", while its own Document Exceptions
  page still gives April 24, 2026 throughout. In Georgia and South Carolina, another state
  office's page read here gives the new dates (Georgia's ADA Coordinator's Office, the South
  Carolina State Library).
- **A second wrong old day.** South Carolina's Department of Education and Mississippi ITS give
  the 2024 rule's first date as April 26, 2026; the rule said April 24, 2026. North Carolina's
  Digital Commons event page has the new day in its text and "4/24/26" in its image alt text.

## Predictions and results

| Prediction | Result | Held? |
|---|---|---|
| E1 (gate): at least 20 states have a read page that states a Title II date | 22 (19 current, stale or wrong day, plus 3 old news only) | yes |
| E2: 10-30% of states with a dated explainer are stale | 9 of 19 (47%) | **no** (higher) |
| E3: at least one state other than Nevada is stale | 8 others | yes |
| E4: at least 80% of stale pages show no date or a date before 2026-04-20 | 10 of 10 | yes |
| E5: every wrong-day state is one of the 12 from parts 9-10 | Utah, Delaware (both in the 12) | yes |

Four of five held. E2 failed because staleness is far more common than guessed.

Four pages were candidates by judgment rather than by the literal words of the addendum (New
Jersey's and North Dakota's hubs, Arkansas's memo, Vermont's Document Exceptions page; marked in
pages.csv). Without them, 8 of 17 states are stale (47%), so E2 fails either way.

## What this means

The 2024 dates have mostly disappeared from pages that were updated after April 2026 (part 13),
but they remain on many reference pages that state governments wrote for their own agencies and
for local governments before the change. Those are the pages officials are told to follow, and
most of them carry no date, so a reader cannot tell they are out of date. Measured this way, the
stale dates are a bigger problem than the wrong day April 24, 2027 that parts 1-11 tracked: that
showed up in 2 states here, against 9 with stale pages.

The dates are wrong in the safe direction for someone planning work (April 24, 2026 is earlier
than the rule's April 26, 2027), but a state that tells its agencies the deadline was April 24,
2026 and gives no new date is giving a date that has already passed and that the rule no longer
uses, as well as the wrong cutoff for its archived-content and preexisting-document exceptions.

## Use: what MV2's checker catches

MV2's free a11y-statement-check (0.10.2, as read in part 13) adds `old_title2_date` when a page
gives April 24, 2026 and neither April 26, 2027 nor April 26, 2028. By that condition it would
flag 7 of the 10 stale pages (Georgia, both Maryland pages, Louisiana, Connecticut, Hawaii,
Vermont) and miss 3: Nevada's (the full 2024 pair, the gap found in part 13) and South
Carolina's and Mississippi's (April 26, 2026 instead of April 24, 2026). This was worked out from
the checker's condition, not by running it. The planned `old_title2_pair` note should also treat
"April 26, 2026" as the old first date.

## Limits

One search per state on one day through one search engine, and only 2 pages per state, so this is
a sample of each state's pages; a state classed current or none may still have stale pages
elsewhere (search summaries pointed to some, for example in Montana, Michigan and Wisconsin, which
were never read or counted), and a state classed stale may have current pages too. 18 states had
no candidate, and 18 of 57 candidate pages could not be read; Massachusetts, Colorado, Kansas,
Arizona and Missouri have no read page at all. The candidate test needed an addendum after the
first five result lists were seen and four judgment calls. Pages were read through an AI page
reader that quotes the page; stale and wrong-day pages were read twice. Nevada's page was known
before registering. A date on a page is what it says, not a finding about any entity's
compliance.
