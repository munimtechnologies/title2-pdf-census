# Pre-registration: why did the re-crawl miss failing PDFs a little more often?

MV2 of Munim, Inc. (made with AI agents). Written 2026-10-24 ~23:45Z, before any of the splits below
was counted, and committed with `miss_reasons.py` and its tests before the script is run on the data.
A separate local job runs it afterwards; its results are graded in a later session and published in
docs/miss-reasons-results.md. Licence: CC BY 4.0.

## Why
The panel retest ([panel-retest-results.md](panel-retest-results.md)) held all six predictions, but
its placebo was not clean. Within the 459 sites read in both crawls that had both failing and passing
files, failing files (not all four basics) were read again less often: mean -1.8 points (95% interval
-3.5 to -0.02), 70 sites down, 29 up, sign test p = 0.00005. Six hours apart no government removes
files for their accessibility, so some part of how the crawler misses files is tied to what the files
are. A 2027 same-file panel will ask whether failing files were taken down more often, so it needs to
know which part of the miss carries this gap, and what to control for.

## Data (already collected, not re-crawled)
The same two row files as the panel retest: census 0.2.1 (started 2026-10-16T17:41:04Z) and census
0.2.2 (started 2026-10-16T23:55:01Z), one row per PDF tried, URL replaced by `url_sha256`. Files are
matched by (`qid`, `url_sha256`), as in `panel_retest.py`, which this script imports.

## Measures
On readable first-crawl files on the paired sites (read in both crawls, at least one failing and one
passing first-crawl file):
- Outcome in the second crawl: read again (`seen`); tried again but not readable (`notok`: a row with
  another `result`); no row at all (`norow`: the page or link was not reached again, the link was gone,
  or the site's quota of files filled first).
- Per site, failing minus passing share of each outcome; mean with a normal 95% interval, counts up /
  down / same and an exact two-sided sign test. The three means satisfy seen = -(notok + norow), and
  the seen mean must equal the panel retest's -0.0177 on 459 sites (a consistency check: if it does not,
  stop and find out why before grading).
- For `notok` files: the second-crawl reason (`no_response` = status 0, i.e. timeout, DNS, TLS or
  reset; `http_4xx`, `http_5xx`; `too_large`; `not_pdf`; `parse_error`), failing vs passing.
- File size: first-crawl `bytes`, median for failing and passing files; tertiles of `bytes` over these
  files; read-again gap (failing minus passing) pooled, and averaged over tertiles weighted by their
  file counts (size-adjusted).
- Per-site gap on paired sites with and without the `<base href>` sign (a first-crawl 404 on a link
  with a space), as in the panel retest.
- Descriptive only: read again for failing and passing files hosted on the site vs off it
  (`same_site`).

## Predictions (point estimates decide)
- M1: the "tried again but not readable" part carries at least half of the gap: the notok mean is at
  least half of (notok mean + norow mean), and that sum is above zero. Reason: failing files are more
  often scanned and large, so slower to fetch and more likely to time out.
- M2: failing files are larger: their median first-crawl size is above that of passing files.
- M3: size explains at least a third of the pooled gap: the size-adjusted gap is at most two thirds
  of the unadjusted one in absolute value.
- M4: the gap is not only a `<base href>` effect: on paired sites without that sign, the per-site mean
  is still below zero.

What we already knew when writing these: the panel retest's printed totals (459 of the 5,285 readable
first-crawl files not read again, 327 with no second row and 132 tried again but not readable, over
all sites; 145 of 174 files read again on the 43 `<base href>` sites and 4,681 of 4,952 elsewhere) and
its per-site placebo above. None of these was split by basic4, outcome, size or site kind on the
paired sites; no row was opened for this study.

## Limits (known before running)
- 99 of the 459 sites carry the whole gap (360 have no difference), so the split parts will be noisy;
  the normal intervals are rough and the sign tests are the sturdier checks.
- A size band only stands in for "scanned and slow"; the rows hold no download times.
- `norow` mixes several causes the public rows cannot tell apart (page not reached, link gone,
  quota). The code change between the crawls also adds `norow` misses on `<base href>` sites.
- Machine checks only; a crawl artefact, not a statement about any government. No government is named.
