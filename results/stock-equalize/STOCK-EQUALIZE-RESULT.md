# Result: 6 US local-government websites serve the Accessibility Checker statement template, 3 of them unfinished (stock-equalize)

Status: graded. Pre-registered in [PREREG.md](PREREG.md) (committed 2026-11-07 before its crawl read any address) and run once, by sealed job `stock-equalize-v1` on 2026-11-07 (21:17 to 21:38 UTC), after the plan, `equalize_stock.py` 0.1.0 and the pinned `stock153.py`, `template_check.py` and `a11y_pages.py` were on main. **Predictions W1 and W2 failed, and W3 was not graded.**

Made by MV2 of Munim, Inc. with AI agents working for him; not yet checked by a person. Apache-2.0 (code), CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the ADA Title II rule does not require an accessibility statement, and nothing here is legal advice. No government or vendor has been contacted about a page.

## Headline

Equalize Digital's Accessibility Checker plugin for WordPress creates an unpublished draft page titled "Accessibility Statement", pre-filled with a template that begins "[YOUR COMPANY NAME] is committed to providing a fully accessible website experience for all users of all abilities" and has seven placeholders for the site owner to replace. Publishing the draft unfinished is the site's step, not the plugin's.

**6 of the 5,243 website hosts serve the Accessibility Checker statement template at `/accessibility-statement/`**, and **3 of the 6 still carry its placeholders**, starting with "[YOUR COMPANY NAME]" where the government's name belongs. All 6 are the six named in the plan as seen before it: the crawl found no template statement that MV2's earlier studies had not already met. The template is much rarer on these sites than the plan expected.

The 3 unfinished statements do not add to MV2's count of unfinished vendor templates: they are 3 of stock-153's 222 flagged hosts, because each of those governments' CivicPlus stock address `/153/Accessibility` redirects to the same page (the page text has the same hash in both studies). The count of hosts serving an unfinished vendor template at one of the stock addresses read so far stays at **235 of 5,243 (4.48%)** (222 hosts from [stock-153](../stock-153/STOCK-153-RESULT.md) and 13 from [stock-revize](../stock-revize/STOCK-REVIZE-RESULT.md)).

## Predictions

| | Prediction | Result | Held |
|---|---|---|---|
| W1 | At least 10 hosts serve the template statement | 6 | no |
| W2 | At least 5 of them keep at least one placeholder | 3 | no |
| W3 | At least 30% of template statements keep a placeholder | 3 of 6 (50%, 95% CI 18.76-81.24%) | not graded (fewer than 10 template statements) |

Gates: the frame is stock-153's, 5,243 website hosts (2 rows without a usable host were dropped), inside F1's 4,800 to 5,245, and 4,750 of 5,243 hosts (90.60%) answered, above G1's 80%.

**Why W1 and W2 failed** (written after reading): the plan expected the 1,088 small governments outside the census sample, pages that no home page links to, and the large cohort to add at least four template statements to the six already known. They added none: 3,638 hosts answered 404 (no page at the address), and no large-cohort host serves the template.

## What else the run shows (described, not graded)

- 347 pages could be read at the address (118 large-cohort, 229 small-cohort). All 6 template statements are on small-cohort hosts (governments of 10,000 to 49,999 people).
- By census record: 3 at the address the census had found, 2 hidden and 1 of a government outside the census sample ("hidden": the census read the home page but the accessibility page it found was a different one). The three the census had found have their placeholders filled in.
- 5 of the 6 template statements carry the plugin's markup in their HTML; no other page read does.
- The 3 unfinished statements each keep the same 6 of the template's 7 placeholders: name, features, fix, issues, email and phone. None keeps `[ SPECIFIC STANDARD, VERSION, LEVEL ]`. `template_check.py` (unchanged) flags all 3.
- 1 page carries the template's second section ("We follow the Web Content Accessibility Guidelines (WCAG) version ...") without its first sentence and keeps no placeholder: Hutchinson, Minnesota (Q1986612).
- No page that is not the template statement carries one of its placeholders. 17 pages read carry a bracketed text of the kinds the study records: 14 are an email address hidden by a web host's email protection (`[email protected]`) and 3 are the "[YOUR COMPANY NAME]" pages above.
- 55 `/accessibility-statement` pages that the census had found are not the template statement this time (the census did not test for this template, so how many ever were is not known).
- Seen before the plan (disclosed in PREREG.md), all six: South Euclid, Ohio (Q1909193), Colfax County, Nebraska (Q484745) and Miami Lakes, Florida (Q995006) through stock-153's redirects; Dickinson County, Iowa (Q112069), Nobles County, Minnesota (Q491196) and Gilmer County, Georgia (Q493054) through the small census's snippets.

## What this adds

A negative result for this template: among 5,243 US city, county and town websites, the Accessibility Checker draft is published at its WordPress address by 6, and left unfinished by 3, all already known. The unfinished-template counts in this repository come from other vendors' stock pages: CivicPlus (222 hosts) and Revize (13) for cities, counties and towns, and Finalsite's 2017 template for school districts ([district-pages](../district-pages/DISTRICT-PAGES-RESULT.md), 129 of 933 pages read). A plugin that ships the template as an unpublished draft may be one reason so few are published unfinished; this study cannot test that.

## Honest limits

- One address per host, read once: a template statement under another slug, on another host or in a PDF is not found, so 6 and 3 are floors, and a government may have fixed its page since.
- The template test needs the template's first sentence; a statement rewritten there but keeping a placeholder elsewhere would be missed, though no other page read carries one of the template's placeholders.
- 6 template statements is too small a base for a share: W3's interval runs from 18.76% to 81.24%, and W3 was not graded.
- The frame is the governments with a website in Wikidata that MV2's two censuses used, not every US local government; governments under 10,000 people are not in it.

## Files

`hosts.csv` (one row per host: status, a hash of the page text, the flags, the first other bracketed text found; no page text), `result.json` and `result.txt` are the run's output, unchanged. `test_stock_equalize_result.py` (repository root) re-grades every measure and prediction from `hosts.csv` with the pinned `equalize_stock.py`, checks every figure in this note, and checks the three unfinished pages against stock-153's table.

## Every statement that keeps a placeholder

| Cohort | Wikidata ID | Name | State | Kind | Placeholders left | Census record |
|---|---|---|---|---|---|---|
| small | Q995006 | Miami Lakes | Florida | town | name+features+fix+issues+email+phone | hidden |
| small | Q484745 | Colfax County | Nebraska | county | name+features+fix+issues+email+phone | not_sampled |
| small | Q1909193 | South Euclid | Ohio | city | name+features+fix+issues+email+phone | hidden |
