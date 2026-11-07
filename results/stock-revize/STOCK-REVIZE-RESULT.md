# Result: 13 of 32 Revize stock accessibility statements still carry template placeholders (stock-revize)

Status: graded. Pre-registered in [PREREG.md](PREREG.md) (committed 2026-11-06 before its crawl read any address) and run once, by sealed job `stock-revize-v1` on 2026-11-06 (23:25 to 23:47 UTC), after the plan, `revize_stock.py` 0.1.0 and the pinned `stock153.py`, `template_check.py` and `a11y_pages.py` were on main. All three predictions held.

Made by MV2 of Munim, Inc. with AI agents working for him; not yet checked by a person. Apache-2.0 (code), CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, the ADA Title II rule does not require an accessibility statement, and nothing here is legal advice. No government or vendor has been contacted about a page.

## Headline

Sites built by the vendor Revize carry a stock accessibility statement at `/accessibility_statement/index.php` with six placeholders written in mixed case, such as `[Your Agency/Website Name]` and `[X business days]`. MV2's earlier template check only looks for placeholders in capitals, so it could not see them.

**32 of the 5,243 website hosts serve Revize's stock accessibility statement**, and **13 of those 32 still carry at least one placeholder, 9 with all six**. 11 still carry `[Your Agency/Website Name]` where the agency's name belongs. `template_check.py` flags none of the 13, so the earlier count of unfinished templates missed every one of them.

**Both vendors together:** with the [stock-153](../stock-153/STOCK-153-RESULT.md) study, which read the CivicPlus address on the same 5,243 hosts, **235 of the 5,243 hosts (4.48%) serve an unfinished vendor template at one of the two stock addresses** (222 at the CivicPlus address, 13 at the Revize address); no host is in both. That is 43 of 1,656 large-cohort hosts (2.60%) and 192 of 3,587 small-cohort hosts (5.35%): governments of 50,000 or more people, and of 10,000 to 49,999. The link-following [template-pages](../template-pages/TEMPLATE-PAGES-RESULT.md) re-read had counted 29.

## Predictions

| | Prediction | Result | Held |
|---|---|---|---|
| R1 | At least 30 hosts serve the stock statement | 32 | yes |
| R2 | At least 4 are unfilled (still say `[Your Agency/Website Name]`) | 11 | yes |
| R3 | At least 15% of stock statements keep a placeholder | 13 of 32 (40.62%, 95% CI 25.52-57.74%) | yes |

Gates: the frame is stock-153's (5,243 website hosts, inside F1's 4,800 to 5,245), and 4,753 of 5,243 hosts (90.65%) answered, above G1's 80%. R1 held narrowly.

## What else the run shows (described, not graded)

- The 32 stock statements: 12 in the large cohort and 20 in the small cohort; all 32 carry Revize markup. By census record: 23 at the address the census had found, 4 hidden and 5 of governments outside the census sample.
- Placeholders left, by kind: `[Your Agency/Website Name]` 11, `[Date]` 10, `[Contact Email]` 9, `[Contact Phone]` 9, `[Agency Address]` 9, `[X business days]` 12. Of the 13 pages, 9 pages keep all six, 1 keep three and 3 keep one (the response time, `[X business days]`, is the one most often left).
- 7 of the 13 sit at the address the census had found, so MV2's template re-read read them and did not flag them; 3 are hidden and 3 belong to governments outside the census sample.
- 15 `/accessibility_statement` pages that the census had found are no longer the stock statement, or could not be read this time.
- 23 pages read carry another bracketed placeholder-like text (most are `[Date]` or an email address hidden by a web host's email protection); no page read carries a token such as WEBSITE_NAME.
- Seen before the plan (disclosed in PREREG.md): Raymore, Missouri (Q955130) and Penobscot County, Maine (Q1124743). Both keep all six placeholders and are counted like any other host.

## Honest limits

- One address per host, read once; a statement elsewhere is not found, so 32 and 13 are floors, and a government may have fixed its page since.
- 32 stock statements is a small base: R3's interval runs from 25.52% to 57.74%.
- Being served at an address is not being linked: the study does not say whether visitors reach these pages.
- The frame is the governments with a website in Wikidata that MV2's two censuses used, not every US local government; governments under 10,000 people are not in it. One government in the table below has no state in Wikidata.
- Other vendors' templates (for example the "[YOUR COMPANY NAME]" pages that stock-153 met behind three redirects) are not counted here.

## Files

`hosts.csv` (one row per host: status, a hash of the page text, the flags, the first other bracketed text found; no page text), `result.json` and `result.txt` are the run's output, unchanged. `test_stock_revize_result.py` (repository root) re-grades every measure and prediction from `hosts.csv` with the pinned `revize_stock.py`, checks every figure in this note, and recomputes the two-vendor count from both studies' tables.

## Every statement that keeps a placeholder

| Cohort | Wikidata ID | Name | State | Kind | Placeholders left | Census record |
|---|---|---|---|---|---|---|
| large | Q488885 | Highlands County | Florida | county | name+date+email+phone+address+days | found_rv |
| large | Q1124743 | Penobscot County | Maine | county | name+date+email+phone+address+days | found_rv |
| large | Q485588 | Athens County | Ohio | county | name+date+email+phone+address+days | found_rv |
| large | Q156216 | Benton County | Washington | county | days | hidden |
| small | Q990940 | Oxford |  | city | name+date+days | not_sampled |
| small | Q80018 | San Luis | Arizona | city | days | not_sampled |
| small | Q1207502 | Watertown | Connecticut | town | name+date+email+phone+address+days | found_rv |
| small | Q2443384 | Winder | Georgia | city | name+date+email+phone+address+days | found_rv |
| small | Q1018273 | Schererville | Indiana | town | name | hidden |
| small | Q3180809 | Berea | Kentucky | city | name+date+email+phone+address+days | found_rv |
| small | Q955130 | Raymore | Missouri | city | name+date+email+phone+address+days | found_rv |
| small | Q1012255 | Manchester | Tennessee | city | name+date+email+phone+address+days | not_sampled |
| small | Q501939 | Trousdale County | Tennessee | county | name+date+email+phone+address+days | hidden |
