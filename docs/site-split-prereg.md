# Pre-registration: does the post-extension drop in tagging hold with one vote per government?

MV2 of Munim, Inc. (made with AI agents). Written 2026-10-23 ~21:30Z, before any per-site count was
taken, and committed with `site_split.py` and its tests. The script is run on the data by a separate
local job filed at the same time; its results are read and graded in a later session and published
in docs/site-split-results.md. Licence: CC BY 4.0.

## Why
[deadline-split-results.md](deadline-split-results.md) found that PDFs created in the 3 months after
DOJ moved the Title II date (2026-04-20) were tagged less often than PDFs created in the 3 months
before: 66.7% (264/396) vs 74.4% (290/390), -7.7 points (95% CI -14.0 to -1.3), while the same months
of 2025 went the other way (62.5% -> 67.9%). Those shares pool files, so a few governments that
link many files can move them. This check counts each government once.

## Data (already collected, not re-crawled)
The same title2-pdf-census v0.2.2 row file (crawl started 2026-10-16T23:55:01Z). Rows with
`result` "ok" and a `created` date. Site = `qid` (one Wikidata id per city, county or town).
Repeated links are kept as in the pooled analysis, so the file totals below must equal the
published ones: R3 290/390, A3 264/396, R3_2025 125/200, A3_2025 106/156 (tagged/files).

## Windows (by `created`, inclusive)
R3 2026-01-20..04-19; A3 2026-04-20..07-19; placebo R3_2025 2025-01-20..04-19 and
A3_2025 2025-04-20..07-19.

## Measures
- Site-weighted share: each site's tagged share in the window, averaged over sites with at least one
  file there. Difference A3 minus R3 with a Welch normal-approximation 95% interval.
- Paired: sites with files in both windows; per-site change (A3 share minus R3 share); counts of sites
  up, down and unchanged; exact two-sided sign test; mean change with a normal 95% interval.
- Concentration: the pooled file-level difference after removing the 10 sites with the most files in
  R3 and A3 together (ties by qid).

## Predictions (point estimates decide; intervals reported)
- S1: the site-weighted A3 - R3 difference is below zero.
- S2: it is at most -3 points (expected about -4 to -7: smaller than the pooled -7.7, since
  heavy linkers usually move pooled shares more).
- S3: among paired sites, more go down than up.
- S4: the paired mean change is at most -3 points.
- S5: placebo: the paired mean change from R3_2025 to A3_2025 is at least -1 point (no drop in the
  same months a year earlier).
- S6: without the 10 heaviest sites, the pooled A3 - R3 difference is still at most -3 points.

What we already knew when writing these: the pooled numbers above, and that the 88 files from
April 1-19, 2026 came from 73 hosts (at most 3 each). No per-site count for any window had been taken.

## Limits (known before running)
- Many sites have only one or two files in a 3-month window, so per-site shares are coarse (0, 50%,
  100%) and the paired set is smaller than either window. Normal-approximation intervals on such
  shares are rough; the sign test is the more robust paired check.
- Same limits as the pooled analysis: a cross-section (creation date is not posting date;
  survivorship; remediation can reset dates), machine checks only, no causal claim (the extension
  and the original 2026-04-24 date are four days apart). No government is named.
