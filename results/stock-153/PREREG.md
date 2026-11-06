# Pre-registration: how many US local governments still serve CivicPlus's stock accessibility page? (stock-153)

Status: plan, committed on 2026-11-06 before any address in this study was read. The crawl
starts only once this file, `stock153.py` 0.1.0, `template_check.py` 0.1.0 and `a11y_pages.py`
are on main, and it runs main's copies.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Apache-2.0 (code),
CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the
ADA Title II rule does not require an accessibility statement, and nothing here is legal advice.

## Why

MV2's [template-pages](../template-pages/TEMPLATE-PAGES-RESULT.md) result (2026-11-06) found 29
US local-government accessibility pages that are still an unedited vendor template: the page says
"YOURMUNICIPALITY is committed to ...", calls itself "only meant as a template", or leaves the
contact section as NAME / TITLE / EMAIL / PHONE. 28 of the 29 are on CivicPlus (CivicEngage) sites,
and all 28 sit at the same address: `/153/Accessibility`. In the two census samples, 101 of the
accessibility pages found were at a `/153/` address (32 of 808 in the 50,000+ census, 69 of 1,042
in the 10,000-49,999 census), and 28 of those 101 were flagged.

That re-read only saw pages the censuses had found by following links from a home page, and the
smaller census read a sample of 2,500 of its 3,588 governments. A template page that no home page
links to, or that sits on an unsampled government's site, was never seen. Asking every site for
the one stock address can find them.

Prior art, searched on 2026-11-06: web searches for "YOURMUNICIPALITY" and for the stock address
return individual live template pages, and CivicPlus's help pages describe its accessibility
page, but no count, survey or study of how many governments still serve the unedited template
was found. Those searches, made before this plan, showed live templates for two governments in
the frame, both on a host other than the one the frame lists: Alhambra, California (Q752681; the
census read its home page and found no accessibility link) and Lincoln, Rhode Island (Q1816735;
not in the census sample). They are counted like any other host if the listed host leads to the
template, and the result note will say they were seen before. Searches also showed a public
library's and a county subsite's template pages, which are not in the frame. The 2026
statement and scan studies listed in MV2's earlier plans (AccessLumens, Accessible Compliance
Group and others) scan pages for errors; none reads statements for template text.

## Frame (fixed now)

- Every row of `results/a11y-pages/a11y-pages.csv` (1,657 governments of 50,000 or more; cohort
  **large**) and of `results/small-pages/eligible.csv` (3,588 governments of 10,000 to 49,999;
  cohort **small**), as published on main.
- One row per website host (the `www.` dropped), the large frame first, then the small one, each
  in Wikidata ID order; later rows with the same host are counted as duplicates. A row whose
  website has no usable host is dropped; this includes the one Connecticut town (Q1020609) whose
  name and links are withheld as `[withheld]` in the published small-pages tables.
- For each host the census record is kept: **home_ok** (the census read the home page),
  **home_failed** (it could not), or **not_sampled** (a small-frame government outside the
  census's 2,500), and whether the accessibility page the census found was a `/153/` page.
- **Gate F1:** the frame has **4,800 to 5,245** hosts. Otherwise nothing is read.

## Reading (fixed now)

For each host, one request for `<scheme>://<host as listed>/153/Accessibility`, with the census's
requests unchanged (`a11y_pages.py`): robots.txt read first and honoured, redirects followed, a
pause after each request, at most 16 hosts at a time. The page is read only if it answers 200 with
HTML of 200 or more visible characters. Then:

- **flagged**: any of `template_check.py`'s four placeholder flags, unchanged (YOURMUNICIPALITY,
  "only meant as a template", the NAME / TITLE / EMAIL / PHONE block, a bracketed capital
  placeholder).
- **stock page**: the HTML mentions CivicPlus or CivicEngage, the text mentions accessibility, and
  the final address (after redirects) is still a `/153/` page.
- **hidden**: flagged, and the census read this government's home page but the accessibility
  page it found (if any) was not a `/153/` page.

**Gate G1:** at least **80%** of hosts answered (any HTTP status, or a robots.txt that forbids
the address). Otherwise nothing is graded.

## Predictions (graded by `stock153.grade`)

| | Prediction | Graded only if |
|---|---|---|
| **S1** | At least **40** hosts serve a flagged page at `/153/Accessibility` | F1 and G1 |
| **S2** | At least **5** flagged hosts are hidden | F1 and G1 |
| **S3** | At least **20%** of stock pages are flagged | **50** stock pages |
| **S4** | The flagged share of probed hosts (robots.txt did not stop the request) is higher in the small cohort than in the large one | **800** probed hosts in each cohort |

Reasons, written before reading: the census samples alone found 28 flagged `/153/` pages, the
1,088 unsampled small governments should add about ten more, and unlinked templates add some
(S1); a template that no page links to is easy to forget (S2); 28 of the 101 `/153/` pages the
censuses found were flagged, 27.7% (S3); the template re-read found 2.41% of small-cohort pages
flagged against 0.50% of large-cohort pages (S4).

**Described, not graded:** status and census record by cohort; flagged hosts by cohort, census
record (found at `/153/`, hidden, home not read, not sampled), kind and state; flags; flagged
pages without CivicPlus markup or not at a `/153/` address; the stock sentence and the sentence
with the word WCAG missing on stock pages; `/153/` pages the census found that are no longer a
stock page; the list of flagged governments.

## Honest limits

- One address per host. A template elsewhere on a site (another page number, another host, a PDF)
  is not found, so the count is a floor; a `/153/` page can be a stock page without being linked
  anywhere, and the study does not say whether visitors ever reach it.
- A government may fix its page at any time; each address is read once.
- Mixed-case placeholders (for example "[Organization Name]") are not flagged.
- The frame is the governments with a website in Wikidata that MV2's two censuses used, not every
  US local government; governments under 10,000 people are not in it.
- A government whose name contains a word that MV2's publishing tool blocks has its name and
  links withheld as `[withheld]` in the published tables; its Wikidata ID is kept.

## After grading

`hosts.csv` (one row per host: status, a hash of the text, the flags; no page text),
`result.json` and `result.txt` go to `results/stock-153/` with a result note and a test that
re-grades every figure from the saved table. Results are published whether the predictions hold
or not. No government is contacted about its page by MV2 without a person checking it first.
