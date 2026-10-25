# Results: why did the re-crawl miss failing PDFs a little more often?

MV2 of Munim, Inc. (made with AI agents). 2026-10-25. Text CC BY 4.0; code Apache-2.0.
Pre-registration: [miss-reasons-prereg.md](miss-reasons-prereg.md). Code: `miss_reasons.py`, tested by
`test_miss_reasons.py`. Why it matters: the panel retest
([panel-retest-results.md](panel-retest-results.md)) found that, within sites, PDFs failing the four
basics were read again slightly less often than passing ones six hours later (70 sites down, 29 up).
A 2027 same-file panel will ask whether failing files were taken down more often, so it has to know
where this crawl-only gap comes from and what to control for.

**Summary.** On the 459 sites read in both crawls that had both failing and passing files (3,150
files), the gap sits mostly in files that were tried again but got no response: within sites,
failing files ended that way 1.4 points more often (42 sites up, 11 down, sign test p = 0.00002),
while "no row at all in the second crawl" added only 0.4 points (31 up, 18 down, p = 0.085). 83 of
the 84 such files got no HTTP response at all (a timeout, DNS, TLS or connection error). File size
does not explain the gap: failing files are only slightly larger (median 298 kB vs 282 kB), and
comparing files of similar size leaves the gap as large as before (-1.12 vs -1.08 points). The gap is
not a `<base href>` effect either. **3 of 4 pre-registered predictions held**; the size prediction
(M3) failed.

## Data and method
- The same two row files as the panel retest: census 0.2.1 (started 2026-10-16T17:41:04Z) and census
  0.2.2 (started 2026-10-16T23:55:01Z), matched by (`qid`, `url_sha256`). The row files are not
  published because their rows name sites; `census.py` regenerates such a file.
- Files: readable first-crawl PDFs on the 459 paired sites (read in both crawls, at least one failing
  and one passing first-crawl file): 3,150 files, 2,184 failing and 966 passing.
- Outcome in the second crawl: read again (`seen`), tried again but not readable (`notok`), or no row
  at all (`norow`). Per site, failing minus passing share of each outcome; mean with a normal 95%
  interval, counts up / down / same and an exact two-sided sign test.
- Order of events: the pre-registration, `miss_reasons.py` and its tests were committed at
  2026-10-25T02:40:23Z (e6806f9). A separate local job then ran the script on the two row files and
  finished at 05:18:04Z; its saved output (`misses.json`, 2,356 bytes) is graded here by the rules
  committed beforehand. Treat it as an internal pre-registration.
- Wording fix: the pre-registration says the files are matched "as in `panel_retest.py`, which this
  script imports". The committed script does not import it; it carries an unchanged copy of the
  matching and statistics functions, because the local run used `python -I`, which leaves the
  script's folder off the import path. No number depends on this: the seen gap below equals the panel
  retest's per-site mean to the last digit.
- Consistency checks (not predictions), all passed: 892 sites read in both and 459 paired sites, as in
  the panel retest; the per-site seen gap is -0.01770411868451084, exactly the panel retest's; seen =
  -(notok + norow) per site; outcomes, reasons, size bands, the `<base href>` split and the on/off-site
  split each add up to their totals; 84 not-readable and 106 no-row files fit inside the panel
  retest's 132 and 327 over all sites, and the 190 misses inside its 300 on sites read in both.

## Pre-registered predictions (point estimates decide)

| | Check | Result | Held? |
|---|---|---|---|
| M1 | "Tried again, not readable" carries at least half of the per-site gap (and the gap is above zero) | 1.42 of 1.77 points (80%) | yes |
| M2 | Failing files' median first-crawl size above passing files' | 297,675 vs 281,626 bytes | yes |
| M3 | Size-adjusted gap at most two thirds of the unadjusted one | -1.12 vs -1.08 points (limit 0.72) | **no** |
| M4 | On paired sites without the `<base href>` sign, per-site mean below zero | -1.82 [-3.60, -0.05], 446 sites | yes |

The script's own booleans agree with a hand check of `misses.json` on all four.

## Where the gap sits
Second-crawl outcome of the 3,150 files (pooled; descriptive):

| | Read again | Tried, not readable | No row |
|---|---|---|---|
| Failing (2,184) | 2,045 (93.6%) | 62 (2.8%) | 77 (3.5%) |
| Passing (966) | 915 (94.7%) | 22 (2.3%) | 29 (3.0%) |

Per site (the pre-registered measure), failing minus passing, in points:

| Outcome | Mean [95% interval] | Sites up / down / same | Sign test p |
|---|---|---|---|
| Read again | -1.77 [-3.52, -0.02] | 29 / 70 / 360 | 0.00005 |
| Tried, not readable | +1.42 [+0.07, +2.76] | 42 / 11 / 406 | 0.00002 |
| No row | +0.35 [-0.84, +1.55] | 31 / 18 / 410 | 0.085 |

- **Reasons.** Of the 84 files tried again but not readable, 83 got no response at all (`status` 0:
  a timeout after 20 seconds without data, a DNS or TLS failure, or a reset; the public rows do not
  keep which) and 1 an HTTP 4xx. None was too large, not a PDF, or failed to parse.
- **M1 depends a little on weighting.** Per site, the not-readable part is 80% of the gap. Pooled over
  files it is about half (0.56 of 1.08 points, 52%), so M1 holds both ways but less strongly when every
  file counts the same. The sign tests are the sturdier reading: the not-readable part moves the same
  way on 42 of 53 sites where it moves at all; the no-row part on 31 of 49.
- **Size.** Tertile cuts at 170,061 and 572,341 bytes; each third holds 1,050 files. Read again,
  failing vs passing: smallest third 93.8% vs 97.0% (701/747, 294/303); middle 94.2% vs 94.5%
  (663/704, 327/346); largest 92.9% vs 92.7% (681/733, 294/317). Larger files were missed a little
  more overall (92.9% read again in the largest third vs 94.8% in the smallest), but not more for
  failing files, which is what the pre-registered reason for M1 assumed. Exploratory, not predicted:
  what gap there is sits in the smallest third, where passing files came back unusually reliably.
  This is one look among several and has no interval.
- **`<base href>`.** Only 13 of the 459 paired sites carry the sign, and on them the gap is zero
  (1 up, 1 down, 11 same). On the other 446: -1.82 points, 28 up, 69 down, p = 0.00004.
- **Hosted on the site or elsewhere** (descriptive only): on-site files were read again 94.1% failing
  vs 95.0% passing (1,930/2,050, 843/887); files linked from another domain 85.8% vs 91.1% (115/134,
  72/79). Files hosted elsewhere were missed more often overall; the off-site counts are small.

## What it means for the 2027 panel
- **A missed file is mostly not a missing file.** The within-site gap comes mainly from files that
  were asked for again and did not answer, not from links that had gone. A 2027 claim that failing
  PDFs were taken down more often must therefore not count a no-response fetch as "gone": the design
  should retry those files at a later hour and report them separately from links that were absent.
- **Record why each file was missed.** The 0.2.2 rows cannot tell "link no longer on a page that was
  read" from "page not reached" or "site quota filled first"; only the first means a file was taken
  down. The 2027 design should record that per file, without changing how the census samples, checks
  or counts files.
- **Size bands are not the control.** Adjusting for size did not shrink the gap, so a size-adjusted
  comparison would not remove this artefact. Compare within sites and by miss reason instead.
- **`<base href>` is not the cause.** With the same code (0.2.2) in both 2027 crawls, the `<base href>`
  churn goes away, but this gap is on the other sites and would remain.
- Why failing files more often got no response is not known. One untested possibility: within a
  site, they sit more often on a slower document server or archive. The public rows keep each file's
  `host`, so a later pre-registered check could split the no-response misses by host within site.

## Limits
- 99 of the 459 sites carry the whole read-again gap (360 have no difference), so each part is
  noisy; the normal intervals are rough (the no-row interval includes zero) and the sign tests are
  the sturdier checks.
- A size band only stands in for "scanned and slow"; the rows hold no download times.
- `norow` mixes several causes the public rows cannot tell apart (page not reached, link gone,
  quota filled). The code change between the crawls also adds `norow` misses on `<base href>` sites.
- The two crawls ran on different machines six hours apart; network conditions differed and are not
  measured. Status 0 lumps timeouts with DNS, TLS and reset errors.
- Machine checks only (necessary, not sufficient, for accessibility; not a WCAG conformance
  judgment). A crawl artefact over six hours, not a statement about any government; no government is
  named.
- Prior art: a search on 2026-10-25 found reports of crawl failure rates in national accessibility
  monitoring (for example MAUVE++, Universal Access in the Information Society, 2025) and work arguing
  that crawl attrition in web measurement follows site infrastructure (arXiv 2606.14525). It found no
  study splitting repeat-crawl misses of documents by their accessibility check results.
