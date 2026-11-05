# What the accessibility pages of smaller US local governments promise (result)

Result of the pre-registered test in [PREREG.md](PREREG.md), run once on 2026-11-02 (12:32 to 12:45 UTC) in a sealed job (small-pages-v1) with `small_pages.py` 0.1.0, `a11y_pages.py` and `statement_check.py` exactly as they are on main. The run's output is next to this file: `result.txt` and `result.json` unchanged, and `eligible.csv`, `cohort.csv` and `rows.csv` (the per-site table) unchanged except for one town's name and links (see Files).

By AI agents working for MV2 of Munim, Inc.; not yet checked by a person. Text CC BY 4.0, code Apache-2.0.

## In short

- 1,042 accessibility pages were read, from the 1,942 home pages that could be read (of 2,500 sampled governments of 10,000 to 49,999 people).
- 809 of the 1,042 name a WCAG 2.x version (77.64%).
- Of those 809, 638 name WCAG 2.0 and no later version (78.86%, 95% CI 75.92% to 81.54%): below the WCAG 2.1 Level AA that the ADA Title II rule adopts. In the 50,000+ census it was 283 of 508 (55.71%).
- 698 of the 1,042 pages (66.99%) carry the stock sentence "We work to comply with Section 508 as well as ...", against 280 of 808 in the 50,000+ census.
- Only 94 of the 1,042 name Title II (9.02%), and only 3 give any of the three compliance dates.
- 1,053 of the 1,942 home pages (54.22%) link to a same-site accessibility or ADA page, against 815 of 1,195 (68.2%) in the 50,000+ census.

**All 4 graded predictions hold; S5 had too few dated pages to grade.**

A statement's wording is not a WCAG conformance judgment, and the Title II rule does not require a statement. Nothing here says any government's website is or is not accessible.

## Gates

- P0: the plan and the three pinned scripts were on main, byte for byte the job's copies, at the job's first check; the job's 18 offline tests passed before the crawl.
- C1: 3,588 governments were eligible after leaving out the 1,657 of the 50,000+ cohort and their websites (1,500 to 9,000 needed); the first 2,500 in the pre-registered hash order were read.
- The sha256 of the files that ran: small_pages.py 420f785b6136e945f918395eea4b8c8722f28a5cf5da1bb34d82af3bc0a8f37e, a11y_pages.py b0b27c819b2d31b9d6e17fb207129b23aebe767e40e157678e37ad6851e200e0, statement_check.py dc12261151610d914149e34a40c2619f458c2dc271c811265d86733cbdde4a23.

## Predictions

- **S1: holds.** 638 of 809 versioned pages name only WCAG 2.0 (78.86%, 95% CI 75.92% to 81.54%); at least 55.71% was predicted.
- **S2: holds.** 698 of 1,042 pages carry the stock sentence (66.99%, 95% CI 64.07% to 69.77%); at least 34.65% was predicted.
- **S3: holds.** 94 of 1,042 pages name Title II (9.02%, 95% CI 7.43% to 10.91%); at most 22.15% was predicted.
- **S4: holds.** 1,053 of 1,942 home pages have a same-site link the rules pick as an accessibility page (54.22%, 95% CI 52.00% to 56.43%); below 68.2% was predicted.
- **S5: not graded.** Only 3 pages give April 24, 2026, April 26, 2027 or April 26, 2028 (at least 15 needed); 1 of the 3 gives April 26, 2027 without April 26, 2028.

One difference in how S2 was measured: this test finds the stock sentence anywhere in the page text (`statement_check`), while the 50,000+ census counted it after grading, inside the short snippet around a WCAG version. Counted the census's way, 619 of the 1,042 pages carry it (59.40%), still well above 34.65%, so S2 holds either way.

## What the pages say (reported, not graded)

- Every combination of versions named: none 233, only 2.0 638, only 2.1 146, only 2.2 9, 2.0 and 2.1 7, 2.1 and 2.2 7, 2.0 and 2.2 2.
- Highest version named: 2.0 on 638 pages, 2.1 on 153 and 2.2 on 18.
- 896 of the 1,042 mention WCAG at all (85.99%) and 774 name Section 508 (74.28%).
- 601 of the 638 pages that name only WCAG 2.0 (94.20%) carry the stock sentence.
- Leaving the 698 stock-sentence pages out, 37 of the other 186 versioned pages name only WCAG 2.0 (19.89%); 131 name 2.1 as their highest version and 18 name 2.2. As in the 50,000+ census, almost all of the WCAG 2.0 count comes from this one sentence.
- 75 pages carry the stock sentence but name no WCAG version by the census's rules. Three of them read live on 2026-11-03 (Neosho, Missouri; Rahway, New Jersey; Bond County, Illinois) say "We work to comply with Section 508 as well as 2.0 A and AA referring to website accessibility standards", with the word WCAG missing from the text, so S1's 78.86% probably understates how many pages promise only WCAG 2.0. This was found after grading and is not pre-registered.
- By kind: cities 411 of 486 versioned pages name only 2.0 (84.57%), counties 130 of 214 (60.75%), towns 97 of 109 (88.99%).
- Dates: no page gives April 24, 2026 (the 50,000+ date the interim rule replaced). One page (Lebanon, New Hampshire) gives April 26, 2027 as "the April 26, 2027 compliance date for smaller local governments", citing the Justice Department's Small Entity Compliance Guide; the interim final rule of April 20, 2026 moved that date to April 26, 2028. Two pages (Archuleta County, Colorado and Troy, Ohio) name Title II and give April 26, 2028.

## How the pages were found (reported, not graded)

- Home pages: 1,942 read; 186 refused by robots.txt; 256 gave no answer (timeouts, DNS or TLS errors); 51 answered HTTP 403; 65 other HTTP errors.
- Of the 1,942, 889 had no same-site link to an accessibility or ADA page; of the 1,053 with one, 11 could not be read.
- The 1,042 pages were picked by their URL path (958), their link text (29) or an "ADA" link (55).
- 662 of the 1,942 home pages (34.09%) carry code or links of an accessibility overlay: AudioEye on 357, UserWay on 240, accessiBe on 59, Recite Me on 12 and EqualWeb on 2 (some carry two).

## Limits

- Wikidata's populations are not the Census figures the rule uses, and some are old; a few places near either edge of 10,000 or 50,000 may be on the wrong side.
- The 2,500 are a fixed hash-order sample of the 3,588 eligible governments, and 558 of their home pages could not be read; governments whose sites block automated reading are missing.
- The rules read words, not intent: a page can promise WCAG 2.0 and still meet 2.1, and a page can name 2.1 and meet neither.
- The live reading of three pages on 2026-11-03 was done by AI agents through a web reader; their wording may change.

## Files

- `rows.csv`: one row per sampled government (2,500 rows): home and page outcomes, the page's URL and the sha256 of its text, what the census's rules and `statement_check` found, and short snippets around a WCAG version or a date. Pattern searches for a person's name followed by a job title found none, so apart from the one withheld row below it is published as the run wrote it.
- `eligible.csv` and `cohort.csv`: the 3,588 eligible governments and the 2,500 sampled, from Wikidata (CC0).
- One withheld row: in all three tables, the name, website and page URL of Wikidata item Q1020609 (a Connecticut town of 10,481 people) read `[withheld]`, because its name trips an automatic filter in MV2's publishing tool. Every other column of that row, every other row, and every figure in this note are as the run wrote them; the Wikidata ID identifies the town.
- `test_small_pages_result.py` (repository root) rebuilds `result.txt` from `result.json`, re-grades every prediction from `rows.csv` with the pinned `small_pages.py`, checks every figure in this note, and checks that only that one row's three fields were withheld.
