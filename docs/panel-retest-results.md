# Results: do two crawls six hours apart see the same government PDFs, and agree on them?

MV2 of Munim, Inc. (made with AI agents). 2026-10-24. Text CC BY 4.0; code Apache-2.0.
Pre-registration: [panel-retest-prereg.md](panel-retest-prereg.md). Code: `panel_retest.py`, tested by
`test_panel_retest.py`. Why it matters: the four 2026 follow-ups (latest:
[title-pairs-results.md](title-pairs-results.md)) found that pooled before/after shares move mostly
because different governments posted, so the next step is a same-file panel, and a panel needs these
two baselines first.

**Summary.** The second full run (0.2.1) and the third (0.2.2) of the census crawled the same US
city and county websites about six hours apart on 2026-10-16. Matching files by government and
address hash, the later crawl read again 91.3% of the 5,285 PDFs the earlier one read (94.1% on the
892 sites read in both). On the 4,826 files read twice, the five machine checks agreed on all but 3
(99.94%), and the byte count on all but 7 (99.85%). Files that fail the four basics were read again
about as often as files that pass (91.1% vs 92.1%). **All 6 pre-registered predictions held.** One
thing the thresholds hide: within sites, failing files were read again slightly less often than
passing ones, and the direction is consistent (70 sites down, 29 up, sign test p = 0.00005; mean
-1.8 points, 95% interval -3.5 to -0.02). Six hours apart no government removed files for their
accessibility, so this is a small crawl artefact that a later panel has to beat.

## Data and method
- First crawl: census 0.2.1 (the second full run, started 2026-10-16T17:41:04Z), 5,285 readable PDFs
  from 922 sites. Second crawl: census 0.2.2 (the third full run, started 2026-10-16T23:55:01Z, a
  different machine), 5,412 readable PDFs from 926 sites. Both totals match the published ones
  (all four basics in the first crawl: 1,136 of 5,285 = 21.5%, as in the README). The row files are
  not published because their rows name sites; `census.py` regenerates such a file.
- Match key: (`qid`, `url_sha256`). "Read again" = readable (`result` "ok") in both crawls. Agreement
  on files read twice: `tagged`, `lang`, `title`, `image_only`, `basic4`; `bytes`; `created`.
- Per-site placebo: sites read in both crawls with at least one failing and one passing first-crawl
  file; per site, read-again share of failing minus passing files; exact two-sided sign test (ties
  dropped) and a normal 95% interval for the mean.
- Order of events: the pre-registration, `panel_retest.py` and its tests were committed at
  2026-10-24T19:29:16Z (de3b11b; tests passed). A separate local job then ran the script on the two
  row files and finished at 22:09:30Z. This write-up grades its saved output (`retest.json`, 1,262
  bytes), which no one read before this session. Treat it as an internal pre-registration.
- Consistency checks (not predictions), all passed: files tried again with any result (4,958) are at
  least the files read again (4,826); the `<base href>` split adds up (145 + 4,681 = 4,826 read again;
  174 + 4,952 = 5,126 files); 3 files differ on some check, between the largest single-check count
  (3) and the sum (7).

## Pre-registered predictions (point estimates decide)

| | Check | Result | Held? |
|---|---|---|---|
| R1 | At least 80% of readable first-crawl files read again | 91.3% (4,826 / 5,285) | yes |
| R2 | On sites read in both crawls, at least 90% read again | 94.1% (4,826 / 5,126) | yes |
| R3 | On files read twice, all five checks agree for at least 99% | 99.94% (4,823 / 4,826) | yes |
| R4 | On files read twice, byte count identical for at least 98% | 99.85% (4,819 / 4,826) | yes |
| R5 | Pooled, failing minus passing read-again share within 5 points | -1.0 (91.1% vs 92.1%) | yes |
| R6 | Per site, mean failing minus passing within 5 points of zero | -1.8 [-3.5, -0.02] | yes |

## Where the missed files went
- 459 of the 5,285 first-crawl files were not read again. 159 of them are on the 30 sites the second
  crawl read no PDF from at all (it read 34 sites the first did not). The other 300 are on sites read
  in both.
- 327 of the 459 have no row at all in the second crawl (the site or the page with the link was not
  reached again, the link was gone, or the site's quota of files was filled before the crawler got to
  it). 132 were tried again but did not come back readable.
- On the 43 sites where the first crawl got a 404 on a link with a space (the sign of the
  `<base href>` gap that 0.2.2 fixed), 83.3% were read again (145 / 174). On the other 849 sites,
  94.5% (4,681 / 4,952). Descriptive only, as pre-registered: the code change explains part of the
  churn, which is why R1 and R2 are upper bounds on churn for two crawls with the same code.

## The floors a later panel has to beat
- **Churn floor (not seen again although nothing real changed):** 8.7% of all files; 5.9% on sites
  read in both crawls; 5.5% on those sites without the `<base href>` sign. A 2027 re-crawl with the
  same code (0.2.2) should miss fewer, and "files gone since" is only a finding above these levels.
- **Noise floor (same file, different result):** 3 of 4,826 files (0.06%) changed on some check:
  title 2, tagged 1, lang 1, image only 0, and so the four basics 3. 7 changed byte count (0.15%) and
  6 changed creation date (0.12%). Whether these are the same files replaced in the six hours was not
  measured. A later "this file was fixed" share is only a finding well above 0.06%.
- **Placebo gap:** within sites, failing files were missed about 1 to 2 points more often than passing
  ones even six hours apart. A 2027 claim that failing PDFs were taken down more often must be larger
  than this, compared within sites, and should report why each file was missed (no row vs tried and
  not readable).

## Plain reading
- **The census sees mostly the same files on a re-crawl, and its checks are stable.** Over nine in ten
  files come back, and on those the checks almost never flip. That makes a same-file panel workable:
  the URL hashes already in the published rows are enough to match files without storing addresses.
- **The placebo held, but not cleanly.** R6 held by its rule (-1.8 is inside 5 points), and the pooled
  gap is only -1.0. Yet among the 99 sites where the two shares differed, 70 read again fewer of their
  failing files. Nothing about accessibility should change in six hours, so the crawler's misses are
  not independent of a file's result. Possible causes, untested: failing files are more often scanned
  and large, so closer to the size limit or slower to fetch; or the `<base href>` change re-resolved
  links that more often lead to failing files. The sampler orders links by a hash of the address, so a
  file pushed out of a site's quota by a newly found link should be random with respect to its result;
  that cause is less likely. A follow-up that splits the misses by reason and file size can tell these
  apart.

## Limits
- The code change between the crawls inflates churn on `<base href>` sites, so R1 and R2 measure an
  upper bound for two crawls with identical code. Different machines may meet different blocking,
  which also shows up as churn.
- Six hours is short: this says nothing about how fast governments replace files over months.
- `bytes` can differ for a file generated on request even when nothing in it changed; R3 is the
  agreement that matters for a panel.
- Machine checks only (necessary, not sufficient, for accessibility; not a WCAG conformance
  judgment). Files cluster by site, so the pooled shares carry no interval here. The per-site interval
  is a normal approximation and only just excludes zero; the sign test is the sturdier check. Only R6
  was looked at this way, so this is one test, not a search across many. No government is named.
- Prior art: a search on 2026-10-24 found general studies of web-crawl reproducibility (Demir et al.,
  "Reproducibility and Replicability of Web Measurement Studies", WWW 2022; Zeber et al., "The
  Representativeness of Automated Web Crawls as a Surrogate for Human Browsing", WWW 2020; Jueckstock
  et al., "Towards Realistic and Reproducible Web Crawl Measurements", WWW 2021), and an open PDF
  crawler that skips files whose hash has not changed since its last run. It found no measurement of
  repeat-crawl churn or check agreement for accessibility checks on government PDFs, or of a URL-hash
  file panel for them.
