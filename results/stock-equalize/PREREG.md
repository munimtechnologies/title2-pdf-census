# Pre-registration: how many US local governments publish the Accessibility Checker statement template unfinished? (stock-equalize)

Status: plan, committed on 2026-11-07 before any address in this study was read by its crawl.
The crawl starts only once this file, `equalize_stock.py` 0.1.0, `stock153.py` 0.1.0,
`template_check.py` 0.1.0 and `a11y_pages.py` are on main, and it runs main's copies.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Apache-2.0 (code),
CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the
ADA Title II rule does not require an accessibility statement, and nothing here is legal advice.

## Why

MV2's [stock-153](../stock-153/STOCK-153-RESULT.md) study asked 5,243 US local-government website
hosts for CivicPlus's stock accessibility address and found 222 unedited templates. Three of its
flagged pages were not CivicPlus pages: for South Euclid, Ohio (Q1909193), Colfax County, Nebraska
(Q484745) and Miami Lakes, Florida (Q995006) the address redirected to an `/accessibility-statement/`
page that still says "[YOUR COMPANY NAME]". That is a third template family, and this plan counts it.

The text is the accessibility statement template published by Equalize Digital, whose
Accessibility Checker plugin for WordPress creates an **unpublished draft** page pre-filled with it
for the site owner to complete. Publishing it unfinished is the site's step, not the plugin's. The
template begins
"[YOUR COMPANY NAME] is committed to providing a fully accessible website experience for all users of all abilities ..."
and carries these capitalised placeholders:

| Placeholder | Key |
|---|---|
| `[YOUR COMPANY NAME]` or `[COMPANY NAME]` | name |
| `[ SPECIFIC STANDARD, VERSION, LEVEL ]` | standard |
| `[LIST ACCESSIBILITY FEATURES HERE]` | features |
| `[LIST ITEMS YOU'RE WORKING TO FIX HERE]` | fix |
| `[IT MAY HELP TO REVIEW THE OPEN ISSUES TAB ...]` | issues |
| `[YOUR ACCESSIBILITY EMAIL ADDRESS]` | email |
| `[YOUR PHONE NUMBER]` | phone |

**Seen before this plan (disclosed).** Besides the three stock-153 pages above, AI agents working
for MV2 read South Euclid's page through a fetch tool on 2026-11-07 and found seven placeholders
unfilled, and a web search showed the same opening sentence with "[YOUR COMPANY NAME]" on Miami
Lakes' page and on several non-government sites. MV2's small-pages census snippets show the
template's second section ("We follow the Web Content Accessibility Guidelines (WCAG) version 2.1
as our guiding principle ...") at `/accessibility-statement/` for Dickinson County, Iowa (Q112069),
Nobles County, Minnesota (Q491196) and Gilmer County, Georgia (Q493054); the large-cohort census
snippets show none. All six are counted like any other host and will be named as seen before.

**Prior art, searched on 2026-11-07:** searches for the template's sentences return individual
live pages (governments, firms, charities) and the vendor's own guide, but no count, survey or
study of how many sites, government or not, publish this template, or how many left its
placeholders in. The 2026 statement and scan studies listed in MV2's earlier plans scan pages for
errors; none reads statements for template text.

## Frame (fixed now)

The stock-153 frame, unchanged: every row of `results/a11y-pages/a11y-pages.csv` (1,657
governments of 50,000 or more; cohort **large**) and of `results/small-pages/eligible.csv` (3,588
governments of 10,000 to 49,999; cohort **small**), one row per website host (the `www.` dropped),
the large frame first, each in Wikidata ID order. A row whose website has no usable host is dropped
(this includes the one Connecticut town, Q1020609, whose name and links are withheld as
`[withheld]` in the published small-pages tables). For each host the census record is kept:
**home_ok**, **home_failed** or **not_sampled**, and whether the page the census found was an
`/accessibility-statement` page.

**Gate F1:** the frame has **4,800 to 5,245** hosts. Otherwise nothing is read.

## Reading (fixed now)

For each host, one request for `<scheme>://<host as listed>/accessibility-statement/` (the address
WordPress gives a page titled "Accessibility Statement"), with the census's requests unchanged
(`a11y_pages.py`): robots.txt read first and honoured, redirects followed, a pause after each
request, at most 16 hosts at a time. The page is read only if it answers 200 with HTML of 200 or
more visible characters. Then, on the visible text:

- **template statement**: the sentence "is committed to providing a fully accessible website
  experience for all users of all abilities" (case and spacing ignored), whether or not the name
  before it was filled in. Whether the HTML mentions the plugin (a11ychecker, Equalize Digital) is
  recorded but not required.
- **placeholder**: a template statement that still carries any of the placeholders above (case
  and spacing inside the brackets ignored).
- **unfilled**: a template statement that still carries `[YOUR COMPANY NAME]` or `[COMPANY NAME]`.
- **hidden**: a placeholder page whose government's home page the census read, but the page the
  census found (if any) was not an `/accessibility-statement` page.

**Gate G1:** at least **80%** of hosts answered (any HTTP status, or a robots.txt that forbids
the address). Otherwise nothing is graded.

## Predictions (graded by `equalize_stock.grade`)

| | Prediction | Graded only if |
|---|---|---|
| **W1** | At least **10** hosts serve the template statement at `/accessibility-statement/` | F1 and G1 |
| **W2** | At least **5** of them keep at least one placeholder | F1 and G1 |
| **W3** | At least **30%** of template statements keep at least one placeholder | **10** template statements |

Reasons, written before reading: six template statements in the frame are already known (three
through stock-153's redirects, three in the small census's snippets), and the 1,088 unsampled small
governments, pages no home page links to and the large cohort should add at least four (W1). Three
known pages keep "[YOUR COMPANY NAME]", and a template that arrives as a ready-made draft is easy
to publish before it is finished (W2, W3). If fewer than 10 template statements are found, W3 is
not graded and the counts are reported as they are.

**Described, not graded:** status and census record by cohort; template statements by cohort,
census record and plugin markup; unfilled statements; how many carry each placeholder and how many
placeholders each carries; how many of the placeholder pages `template_check.py` (unchanged) flags;
pages that carry the template's second section without its first sentence; placeholders on pages
that are not the template statement; other bracket placeholders on any page read;
`/accessibility-statement` pages the census found that are no longer a template statement; the list
of placeholder pages.

## Honest limits

- One address per host. A template statement at another address (another slug, another host, a
  PDF) is not found, so the counts are floors; the study does not say whether visitors ever reach
  the page.
- A government may fix its page at any time; each address is read once.
- The template test needs the template's first sentence; a statement rewritten there but keeping a
  placeholder elsewhere is described, not graded.
- The frame is the governments with a website in Wikidata that MV2's two censuses used, not every
  US local government; governments under 10,000 people are not in it.
- A government whose name contains a word that MV2's publishing tool blocks has its name and links
  withheld as `[withheld]` in the published tables; its Wikidata ID is kept.

## After grading

`hosts.csv` (one row per host: status, a hash of the text, the flags, the first other bracket
placeholder found; no page text), `result.json` and `result.txt` go to `results/stock-equalize/`
with a result note and a test that re-grades every figure from the saved table. Results are
published whether the predictions hold or not. No government or vendor is contacted about a page
by MV2 without a person checking it first.
