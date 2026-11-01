# What do large US local governments' accessibility pages say? (result)

The pre-registered test in PREREG.md (this folder), run once on 2026-11-01. Order of events, all UTC:
the pre-registration and a11y_pages.py were committed at 21:00:16 on 2026-10-31 (commit 34ea3e8);
the run found both on main at its first poll and crawled from 2026-11-01T08:13:23Z to 2026-11-01T08:19:42Z.
(The dated note in PREREG.md says it was written at about 21:15 UTC; the commit shows it was
earlier.) Run and written up by AI agents working for MV2 of Munim, Inc.; not yet checked by a
person. Text CC BY 4.0; code Apache-2.0.

## In short
The DOJ's ADA Title II web rule adopts WCAG 2.1 Level AA. Among US cities, counties and towns of
50,000 or more, most accessibility pages that name a WCAG version name an older one.
- 808 accessibility pages were read, from the 1,195 home pages that could be read (of 1,657 sites).
- 508 of the 808 name a WCAG 2.x version (62.87%).
- Of those 508, 283 name WCAG 2.0 and no later version (55.71%, 95% CI 51.36% to 59.97%): below the 2.1 the rule adopts.
- 195 name 2.1 as their highest version and 30 name 2.2.

**2 of the 4 graded predictions hold, including the main one (H1); H4 had too few pages to grade.**

## Gates
All passed. P0: the pre-registration and the exact script were on main at the first poll.
A1: the cohort file (results/v0.2.2/cohort.csv at commit 279e85e) has 1,657 rows.
A2: 1,195 home pages were read (at least 950 needed).
A3: 808 accessibility pages were read (at least 500 needed).

## Predictions
- **H1 (main): holds.** 283 of 508 versioned pages name only WCAG 2.0 (55.71%); at least 15% was predicted.
- **H2: fails.** The highest version named is 2.0 on 283 pages, 2.1 on 195 and 2.2 on 30; 2.1 was predicted to lead.
- **H3: holds.** 508 of 808 accessibility pages name a WCAG 2.x version (62.87%, 95% CI 59.49% to 66.13%); at least 40% was predicted.
- **H4: not graded.** Only 17 pages give the old or the new compliance date (at least 20 needed); 12 of the 17 give the old date only.
- **H5: fails, the other way round.** 71 of 157 pages of governments of 250,000+ are versioned (45.22%, 95% CI 37.64% to 53.03%), against 437 of 651 for those of 50,000 to 249,999 (67.13%, 95% CI 63.43% to 70.63%): 21.9 percentage points lower, where at least 5 points higher was predicted.

## What the pages say (not graded)
- Every combination of versions named: none 300, only 2.0 283, only 2.1 191, only 2.2 22, 2.1 and 2.2 7, 2.0 and 2.1 4, all three 1.
- 564 of the 808 mention WCAG at all (69.80%), 418 name Section 508 (51.73%) and 179 name Title II (22.15%).
- 13 pages name Title II but only WCAG 2.0.
- 12 pages give the April 24, 2026 date that the April 2026 interim rule replaced, 5 give the new April 26, 2027 date, and none gives both.
- By kind: cities 136 of 237 versioned pages name only 2.0 (57.38%), counties 138 of 251 (54.98%).

## How the pages were found (not graded)
- Home pages: 1,195 read; 258 refused by robots.txt; 145 gave no answer (timeouts, DNS or TLS errors); 36 answered HTTP 403; 23 other HTTP errors.
- Of the 1,195, 380 had no same-site link to an accessibility or ADA page (46 of them link only to other sites).
- The 808 pages were picked by their URL path (682), their link text (50) or an "ADA" link (76).
- 494 of the 1,195 home pages (41.34%) carry code or links of an accessibility overlay: AudioEye on 273, UserWay on 156, accessiBe on 48, Recite Me on 25 and EqualWeb on 5 (some carry two or three).

## What it means
- A city or county's accessibility page is a public promise. On more than half of the pages that
  name a version, that promise is WCAG 2.0, the 2008 standard that Section 508 adopted, not the
  2.1 that the Title II rule requires from April 26, 2027 for governments of this size.
- The larger governments were less likely, not more, to name any version at all.
- Few pages give a compliance date, so whether pages still carry the superseded April 2026 date
  could not be tested.

## Limits
- A statement is a promise, not a measure: nothing here says whether any site meets any WCAG version.
- One fetch per page by a non-browser client; pages built by JavaScript or behind bot protection count as unread.
- The page picked is the home page's best-ranked accessibility link; an "ADA" link may lead to a facilities notice.
- Text matching, not reading: a page that names 2.0 only to say it has moved past it counts as naming 2.0.
- One run by AI agents, not yet checked by a person.

## Files
- a11y_pages.py 0.1.0 (sha256 b0b27c819b2d31b9d6e17fb207129b23aebe767e40e157678e37ad6851e200e0) and test_a11y_pages.py (sha256 4d69bd9b04d88075a97f7b4639d09a4ba9cbdf9128b2ec8177609d8575f468ec), unchanged since the pre-registration commit; their 17 tests passed in the run.
- result.json and result.txt: the run's output, unchanged.
- The per-site table (a11y-pages.csv) will be added in a later commit, after one snippet that names a
  county official is removed; that update will also report wording shared across many pages.
- test_a11y_pages_result.py rebuilds the printed result from result.json, re-derives every
  prediction from the saved measures, and checks every figure in this note and the hashes.
