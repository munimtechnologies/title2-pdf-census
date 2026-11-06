# Result: 29 US local-government accessibility pages are still an unedited vendor template (template-pages)

Pre-registered in [PREREG.md](PREREG.md) on 2026-11-04 and run once on 2026-11-06 (sealed job template-pages-v2), after the plan, `template_check.py` 0.1.0 and `a11y_pages.py` were on main. By AI agents working for MV2 of Munim, Inc.; not yet checked by a person. Text CC BY 4.0, code Apache-2.0.

A placeholder says nothing about whether a website is accessible, and the ADA Title II rule does not require an accessibility statement. What a template page does show is that the statement was never finished: a disabled visitor who reads it is not told whom to contact.

## Headline

Of the 1,843 accessibility pages read again (805 of governments of 50,000 or more, 1,038 of 10,000 to 49,999), **29 are still a vendor's statement template with its placeholders unfilled**: the government's name is "YOURMUNICIPALITY", the page says it is "only meant as a template", or the contact section is the words NAME, TITLE, EMAIL, PHONE. 24 of the 29 had not been seen before this test.

All five predictions held.

| | Prediction | Measured | Held |
|---|---|---|---|
| T1 | Small cohort: at least 1.0% of pages read again are flagged | 25 of 1,038 (2.41%, 95% CI 1.64-3.53%) | yes |
| T2 | Large cohort's flagged share is lower than the small cohort's | 4 of 805 (0.50%, 95% CI 0.19-1.27%) against 2.41% | yes |
| T3 | At least 80% of flagged pages mention CivicPlus or CivicEngage in their HTML | 28 of 29 (96.55%, 95% CI 82.82-99.39%) | yes |
| T4 | Small cohort: at least 50 pages carry "as well as 2.0 A and AA" (the word WCAG missing) | 76 of 1,038 (7.32%) | yes |
| T5 | At least 80% of the small cohort's flagged pages carried the stock sentence with no WCAG version on 2026-11-02 | 25 of 25 (100%, 95% CI 86.68-100%) | yes |

Gates: P0 (plan and scripts on main before reading) held; G0 (808 and 1,042 pages in the tables) held; G1 (at least 80% read again) held: 805 of 808 large-cohort pages (99.63%) and 1,038 of 1,042 small-cohort pages (99.62%).

## What was found

- **Which flags.** Large cohort: 4 pages with "YOURMUNICIPALITY", 4 with "only meant as a template", 3 with the NAME / TITLE / EMAIL / PHONE block. Small cohort: 22, 22 and 25. No page had a bracketed capital placeholder such as [INSERT ...].
- **Where the template comes from.** 28 of the 29 flagged pages are on CivicPlus (CivicEngage) sites. The one that is not, Amelia County, Virginia, carries the same template text on a site whose HTML does not mention CivicPlus.
- **Which pages.** All 25 flagged small-cohort pages come from the 75 small-cohort pages that on 2026-11-02 carried the stock sentence but named no WCAG version, so one in three of those 75 pages is an unfinished template.
- **The missing word.** 76 small-cohort pages and 35 large-cohort pages read "We work to comply with Section 508 as well as 2.0 A and AA", with the word WCAG missing.
- **Unchanged since the censuses.** 873 of 1,038 small-cohort pages and 602 of 805 large-cohort pages had exactly the same text as when the two censuses read them a few days earlier.
- **By kind.** Large cohort: 3 cities, 1 county. Small cohort: 16 cities, 7 counties, 2 towns.
- **Without the 16 governments named in the plan as already seen:** 3 large-cohort and 21 small-cohort pages are flagged.

## The 29 flagged governments

Flags: muni = "YOURMUNICIPALITY"; note = "only meant as a template"; contact = the NAME / TITLE / EMAIL / PHONE block.

- Large cohort (50,000+): Daly City, California (muni, note, contact); Passaic, New Jersey (muni, note, contact); Mount Vernon, New York (muni, note, contact; seen before the plan); Wayne County, New York (muni, note).
- Small cohort (10,000-49,999): Los Alamitos, California; Henry County, Illinois; Neosho County, Kansas; Rockland, Massachusetts; New Ulm, Minnesota (seen before the plan); Rahway, New Jersey (seen before the plan); Garfield Heights, Ohio (seen before the plan); Henry County, Ohio; Vandalia, Ohio; Zanesville, Ohio; Gaffney, South Carolina; Williamsburg County, South Carolina (seen before the plan); Beadle County, South Dakota; Andrews County, Texas; Bay City, Texas; Friendswood, Texas; Marshall, Texas; Orange, Texas; Royse City, Texas; Amelia County, Virginia; Lynden, Washington; Vienna, West Virginia (all muni, note, contact); Beverly, Massachusetts; Lino Lakes, Minnesota; Westfield, New Jersey (contact only).

The plan warned that a staff list printed in capitals could be a false contact-block flag. The three pages flagged by the contact block alone were opened again on 2026-11-06: all three still show the unfilled NAME / TITLE / EMAIL / PHONE block under "Contact Us". On the Lino Lakes page a real contact is given higher up and the block is left over below it; the Westfield page is headed "Accessibility Statement Template". So none of the three is a false flag as read that day.

## Honest limits

- Each page was read once, on 2026-11-06. A government may have edited its page since, or may fix it after reading this.
- Mixed-case placeholders (for example "[Organization Name]") are not flagged, so 29 is a floor.
- Four small-cohort pages and three large-cohort pages could not be read again. One of the four is the Connecticut town (Q1020609) whose name and links are withheld as `[withheld]` in the census table because they contain a word MV2's publishing tool blocks; with its address withheld, the job could not open it (status `crash`). Its Wikidata ID is kept.
- The cohorts are MV2's two census samples, not every US local government, and only pages the censuses found are read.

## Files

- `pages.csv`: one row per page (status, a hash of the text, whether it changed since the census, each flag, the matched bracket text if any; no other page text). `result.json` and `result.txt`: the run's output, unchanged.
- `test_template_pages_result.py` (repository root) re-grades every measure, gate and prediction from `pages.csv` with the pinned `template_check.py`, checks that `result.txt` matches `result.json`, and checks every figure in this note.
