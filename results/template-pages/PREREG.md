# Pre-registration: how many US local governments' accessibility pages are still an unedited template?

Written on 2026-11-04, before any page is read for this test. By AI agents working for MV2 of Munim, Inc.; not yet checked by a person. Text CC BY 4.0, code Apache-2.0.

## Why

MV2's two censuses of what US cities', counties' and towns' accessibility pages promise (`results/a11y-pages/`, governments of 50,000 or more; `results/small-pages/`, 10,000 to 49,999) found that most pages naming a WCAG version carry one stock sentence naming only WCAG 2.0. While writing up the second census, a few of the pages it read were opened live, and two of them turned out to be a vendor's template published without editing: the page says it is "only meant as a template local government accessibility statement", the government's name is the placeholder "YOURMUNICIPALITY", and the contact section is the words NAME, TITLE, EMAIL and PHONE. A web search then found more. Such a page tells a disabled visitor neither whom to contact nor what the government commits to.

Searches on 2026-11-03 and 2026-11-04 found template guides and lists of example statements, and a CivicPlus/CivicPulse survey of officials' priorities, but no count of how many government accessibility pages are unedited templates. This test makes that count for the 1,850 pages the two censuses read, and adds a check for it that anyone can rerun.

## What is read

- Every page with `page_status` ok in `results/a11y-pages/a11y-pages.csv` (808 pages, the large cohort) and in `results/small-pages/rows.csv` (1,042 pages, the small cohort), as those files are on main when the job starts.
- Each page is read once more by `template_check.py` 0.1.0 with the census's own requests (`a11y_pages.py`): robots.txt is honoured, one page per site, a one-second pause after each request, a public user agent naming MV2 and his email. Nothing is submitted and no other page is opened.

## What counts as a placeholder

A page re-read with at least 200 characters of visible text is **flagged** if its text has any of:

1. "YOURMUNICIPALITY" or "YOUR MUNICIPALITY" in capitals;
2. "only meant as a template" (any case);
3. the words NAME, TITLE, EMAIL and PHONE in capitals, in that order, with only spaces or punctuation between them;
4. a bracketed placeholder in capitals: [INSERT ...], [NAME OF ...], [URL OF ...], [CITY NAME] (or COUNTY, TOWN, VILLAGE, AGENCY, ORGANIZATION, ENTITY), [PHONE NUMBER], [EMAIL ADDRESS] or [YOUR ...].

Also counted: "as well as 2.0 A and AA", the stock sentence with the word WCAG missing, and whether the page's HTML mentions CivicPlus or CivicEngage.

## Gates

- **P0:** this plan, `template_check.py` and `a11y_pages.py` are on main, byte for byte the job's copies, before any page is read.
- **G0:** the two tables on main list exactly 808 and 1,042 pages read. If P0 or G0 fails, no page is read and the test can be run later.
- **G1:** in each cohort, at least 80% of the pages are read again with text (at least 0.80 of 808 and of 1,042). If G1 fails, the counts are reported and no prediction is graded.

## Predictions

- **T1.** In the small cohort, at least 1.0% of the pages read again are flagged.
- **T2.** The large cohort's flagged share is lower than the small cohort's.
- **T3.** Of all flagged pages (both cohorts), at least 80% mention CivicPlus or CivicEngage in their HTML. Graded only with at least 10 flagged pages.
- **T4.** In the small cohort, at least 50 pages read again carry "as well as 2.0 A and AA" (WCAG missing).
- **T5.** Of the small cohort's flagged pages, at least 80% were pages that on 2026-11-02 carried the stock sentence but named no WCAG version (`stock` True and `highest` empty in rows.csv). Graded only with at least 10 flagged pages.

## Already seen before this plan (named so the result can be read without them)

- Small cohort, read live on 2026-11-03: Neosho, Missouri (Q1000065); Rahway, New Jersey (Q1003082, a template); Bond County, Illinois (Q109526); Garfield Heights, Ohio (Q1007032, a template); Stow, Ohio (Q1007079); Middletown, Rhode Island (Q1013038); South Portland, Maine (Q1000166); Summit, New Jersey (Q1000642).
- Small cohort, found as templates by web searches on 2026-11-03 and 2026-11-04: Williamsburg County, South Carolina (Q502210); New Ulm, Minnesota (Q545119).
- Large cohort, found as a template by a web search on 2026-11-04: Mount Vernon, New York (Q835831).
- Large cohort, stock-sentence pages read live on 2026-11-01 and 2026-11-02 (not templates as read then): Burlington, North Carolina (Q1016633); Midwest City, Oklahoma (Q985298); Billings, Montana (Q166304); Apex, North Carolina (Q1876560); Grapevine, Texas (Q185216).
- The thresholds were set knowing these, and knowing from the tables that 69 small-cohort and 32 large-cohort rows contain "/153/" (a CivicPlus-style page path) and that 75 small-cohort pages carried the stock sentence without a version. No other page text was read for this plan. The result reports the flagged count without these 16 governments too.

## Output

`pages.csv` (one row per page: status, sha256 of the text, whether it changed since the census, each flag, the matched bracket text if any; no other page text), `result.json` and `result.txt`, including the list of flagged governments. `test_template_check.py` tests the rules offline.

## Limits

- A page is read once; a government may have edited it since, or may fix it after reading this.
- Mixed-case placeholders (for example "[Organization Name]") are not flagged, so the count is a floor.
- A staff list printed in capitals as NAME TITLE EMAIL PHONE would be a false flag; flagged pages are listed so anyone can check them.
- A placeholder says nothing about whether a website is accessible, and the ADA Title II rule does not require an accessibility statement.
