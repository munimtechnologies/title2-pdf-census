# Pre-registration: does the post-extension drop in PDF titles hold within the same governments?

MV2 of Munim, Inc. (made with AI agents). Written 2026-10-24 ~02:00Z, before any per-government title
count was taken, and committed with `title_pairs.py` and its tests before the script is run on the
data. A separate local job runs it afterwards; its results are read and graded in a later session and
published in docs/title-pairs-results.md. Licence: CC BY 4.0.

## Why
[title-mix-results.md](title-mix-results.md) found that the drop in PDFs carrying a document title after
DOJ moved the Title II date (2026-04-20) is not a change in software mix: 45.1% (488/1,081) of PDFs
created in the year before had a title vs 39.0% (446/1,143) in the six months after, and −5.3 of the
−6.1 points is within the same software groups. But "same software" is not "same government".
[site-split-results.md](site-split-results.md) found that the parallel drop in *tagging* vanished among
the governments present in both windows (25 up, 20 down, sign p = 0.55), so it more likely reflected
which governments posted. This check asks the same question of titles.

## Data (already collected, not re-crawled)
The same title2-pdf-census v0.2.2 row file (crawl started 2026-10-16T23:55:01Z). Rows with `result`
"ok" and a `created` date; repeated links kept as in the pooled analysis, so the totals must equal the
published ones: PRE 488/1,081, POST 446/1,143, R3 185/390, A3 157/396, PRE0 246/554, POST0 177/379
(titled/files). Site = `qid` (one Wikidata item per city, county or town government). `title` = non-blank
/Title in the document information dictionary (census.py `analyze_pdf`).

## Windows (by `created`, inclusive)
PRE 2025-04-20..2026-04-19; POST 2026-04-20..2026-10-16; R3 2026-01-20..04-19; A3 2026-04-20..07-19;
placebo PRE0 2024-04-20..2025-04-19 and POST0 2025-04-20..2025-10-16 (the same split a year earlier).

## Measures
- Site-weighted share: each site's title share in the window, averaged over sites with at least one
  file there; after minus before with a Welch normal-approximation 95% interval.
- Paired: sites with files in both windows; per-site change in title share; counts up, down and
  unchanged; exact two-sided sign test; mean change with a normal 95% interval. Also for the stricter
  set of sites with at least 3 files in each window.

## Predictions (point estimates decide; intervals reported)
- U1: site-weighted POST − PRE title share is at most −3 points (the drop shows with one vote per
  government across all sites).
- U2: paired PRE→POST mean change is above −3 points (no within-government drop of the pooled size).
- U3: the paired PRE→POST sign test gives p ≥ 0.05.
- U4: paired R3→A3 mean change is above −3 points.
- U5: paired PRE→POST mean change among sites with at least 3 files in each window is above −3 points.
- U6: placebo: site-weighted POST0 − PRE0 is above −3 points (no such drop a year earlier).

Together U1-U5 predict the same compositional pattern found for tagging. If U2-U5 fail, the title drop
is a real within-government change, which would be the more interesting result.

What we already knew when writing these: the pooled and software-group title counts in
title-mix-results.md and the tagging site split in site-split-results.md (tagging, not titles). No
per-site title count, site-weighted title share or paired title change had been taken.

## Limits (known before running)
- Many sites have one or two files in a window, so per-site shares are coarse (0, 50%, 100%); the
  normal-approximation intervals are rough and the exact sign test is the more robust paired check.
- The paired set conditions on sites that posted in both windows, which may select steadier
  governments. The 12-month PRE window is twice as long as POST, so more sites appear in PRE.
- Same limits as the pooled analysis: a cross-section (creation date is not posting date; survivorship;
  remediation can reset dates), machine checks only, no causal claim (the extension and the original
  2026-04-24 date are four days apart). "Titled" means a title exists, not that it is meaningful. No
  government is named.
