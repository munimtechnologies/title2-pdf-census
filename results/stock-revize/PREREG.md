# Pre-registration: how many US local governments serve Revize's stock accessibility statement unfinished? (stock-revize)

Status: plan, committed on 2026-11-06 before any address in this study was read by its crawl.
The crawl starts only once this file, `revize_stock.py` 0.1.0, `stock153.py` 0.1.0,
`template_check.py` 0.1.0 and `a11y_pages.py` are on main, and it runs main's copies.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Apache-2.0 (code),
CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the
ADA Title II rule does not require an accessibility statement, and nothing here is legal advice.

## Why

MV2's [template-pages](../template-pages/TEMPLATE-PAGES-RESULT.md) result (2026-11-06) counted 29
US local-government accessibility pages that are still an unedited vendor template, 28 of them on
CivicPlus sites. Its check (`template_check.py`) only recognises placeholders written in capitals,
such as "YOURMUNICIPALITY" or "[INSERT CITY NAME]". Its limits section says mixed-case placeholders
are not flagged. This plan measures what that limit missed.

Sites built by the vendor Revize carry a stock accessibility statement at
`/accessibility_statement/index.php`. It aims at WCAG 2.1 Level AA, has numbered sections ("1. Our
Commitment", ... "4. Limitations & Alternatives", "5. Feedback", "6. Enforcement") and six
placeholders written in mixed case:

| Placeholder | Where |
|---|---|
| `[Date]` | "Last updated: [Date]" |
| `[Your Agency/Website Name]` | the first sentence and the feedback section |
| `[Contact Email]` | feedback section |
| `[Contact Phone]` | feedback section |
| `[Agency Address]` | feedback section ("Mailing Address") |
| `[X business days]` | "We aim to respond to accessibility feedback within [X business days]." |

In MV2's two census samples, 39 of the accessibility pages found by following links from a home
page sit at an `/accessibility_statement` address (19 of 808 pages in the 50,000+ census, 20 of
1,042 in the 10,000-49,999 census), and the census's saved snippet shows the stock statement's
first section on at least 22 of them (9 and 13). The template-pages re-read read all 39 again and
flagged none.

**Seen before this plan (disclosed).** While writing it, AI agents working for MV2 read two of
those pages through a public reader service and found all six placeholders still unfilled:
Raymore, Missouri (Q955130, small cohort) and Penobscot County, Maine (Q1124743, large cohort).
Web searches also showed the unfilled or partly filled statement on sites outside the frame (a
village in Ohio, a small Michigan city, a Kansas county, a sheriff's office and a water utility).
Both governments in the frame are counted like any other host; the result note will name them as
seen before. The census also found one small-cohort page (Charleston, Illinois, Q577909) whose
statement starts "WEBSITE_NAME is partially conformant", a different template; such tokens are
described, not graded.

**Prior art, searched on 2026-11-06:** searches for the placeholders return individual live pages
and generic statement templates (for example the guidance at section508.gov and vendors' blog
templates), but no count, survey or study of how many governments serve this stock statement, or
how many left its placeholders in. The 2026 statement and scan studies listed in MV2's earlier
plans scan pages for errors; none reads statements for template text.

## Frame (fixed now)

The stock-153 frame, unchanged: every row of `results/a11y-pages/a11y-pages.csv` (1,657
governments of 50,000 or more; cohort **large**) and of `results/small-pages/eligible.csv` (3,588
governments of 10,000 to 49,999; cohort **small**), one row per website host (the `www.` dropped),
the large frame first, each in Wikidata ID order. A row whose website has no usable host is dropped
(this includes the one Connecticut town, Q1020609, whose name and links are withheld as
`[withheld]` in the published small-pages tables). For each host the census record is kept:
**home_ok**, **home_failed** or **not_sampled**, and whether the page the census found was an
`/accessibility_statement` page.

**Gate F1:** the frame has **4,800 to 5,245** hosts. Otherwise nothing is read.

## Reading (fixed now)

For each host, one request for `<scheme>://<host as listed>/accessibility_statement/index.php`,
with the census's requests unchanged (`a11y_pages.py`): robots.txt read first and honoured,
redirects followed, a pause after each request, at most 16 hosts at a time. The page is read only
if it answers 200 with HTML of 200 or more visible characters. Then, on the visible text:

- **stock statement**: the heading "Our Commitment" directly followed by "We aim to follow the Web
  Content Accessibility Guidelines" (case and spacing ignored). Whether the HTML mentions Revize is
  recorded but not required.
- **placeholder**: a stock statement that still carries any of the six placeholders above (case
  and spacing inside the brackets ignored).
- **unfilled**: a stock statement that still carries `[Your Agency/Website Name]`.
- **hidden**: a placeholder page whose government's home page the census read, but the page the
  census found (if any) was not an `/accessibility_statement` page.

**Gate G1:** at least **80%** of hosts answered (any HTTP status, or a robots.txt that forbids
the address). Otherwise nothing is graded.

## Predictions (graded by `revize_stock.grade`)

| | Prediction | Graded only if |
|---|---|---|
| **R1** | At least **30** hosts serve the stock statement at `/accessibility_statement/index.php` | F1 and G1 |
| **R2** | At least **4** of them are unfilled (still say `[Your Agency/Website Name]`) | F1 and G1 |
| **R3** | At least **15%** of stock statements keep at least one placeholder | **20** stock statements |

Reasons, written before reading: the census samples alone found at least 22 stock statements by
following links (and 39 pages at that address, some of them rewritten), the 1,088 unsampled small
governments should add several, and statements that no home page links to add some (R1); two unfilled statements in the frame are already known, and partly filled
ones were seen outside it (R2); 2 of the 22 statements the censuses found are known to be unfilled
before any partly filled ones are counted, and the response time "[X business days]" looks easy to
forget (R3).

**Described, not graded:** status and census record by cohort; stock statements by cohort, census
record and Revize markup; how many carry each placeholder and how many placeholders each carries;
how many of the placeholder pages `template_check.py` (unchanged) flags; placeholders on pages that
are not the stock statement; other mixed-case bracket placeholders and tokens such as WEBSITE_NAME
on any page read; `/accessibility_statement` pages the census found that are no longer a stock
statement; the list of placeholder pages.

## Honest limits

- One address per host. A stock statement elsewhere (another path, another host, a PDF) is not
  found, so the counts are floors; the study does not say whether visitors ever reach the page.
- A government may fix its page at any time; each address is read once.
- The stock-statement test needs the vendor's own first heading and sentence; a statement that was
  rewritten there but kept a placeholder elsewhere is described, not graded.
- The frame is the governments with a website in Wikidata that MV2's two censuses used, not every
  US local government; governments under 10,000 people are not in it.
- A government whose name contains a word that MV2's publishing tool blocks has its name and links
  withheld as `[withheld]` in the published tables; its Wikidata ID is kept.

## After grading

`hosts.csv` (one row per host: status, a hash of the text, the flags, the first other bracket
placeholder found; no page text), `result.json` and `result.txt` go to `results/stock-revize/` with
a result note and a test that re-grades every figure from the saved table. Results are published
whether the predictions hold or not. No government or vendor is contacted about a page by MV2
without a person checking it first.
