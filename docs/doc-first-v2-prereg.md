# Pre-registration: does site_check 0.1.2's fallback keep the gain and win back the loss?

Written 2026-10-17, before the job ran, and committed with site_check 0.1.2. The job fetches this
file and hashes it with its code. Its code and results will be added next to this file and
scored against the predictions below, whatever they show.

## Why

The first test ([doc-first-results.md](doc-first-results.md)) found that reading document-like
pages first (site_check 0.1.1) finds PDF links on many sites where random pages find none, but
reaches a readable PDF less often on sites where random pages already work: 88 of 97 against
92 of 97, which failed its pre-registered 2-point margin. At most of the sites it missed, all 8
pages it read were document-like and none had a PDF link. 0.1.2 adds one rule: once half its
pages are read with no PDF link, it reads the site's other pages first.

0.1.2 was designed after seeing the first test's results and the list of the sites it missed
(not their pages). So the main test below is on **200 control sites the first test did not
use**. The zero set has no fresh sites, so it is reused, and 0.1.1 runs again on the same day.

## Design

- **Sites,** all from `results/v0.2.1/sites.csv` (pinned to commit 279e85e):
  - *Zero set:* the same rule as the first test: status `ok`, `pages_read` > 0 and
    `pdf_links` = 0 (129 sites).
  - *Control 2:* 200 sites with status `ok`, `pages_read` > 0 and `pdf_links` > 0, leaving
    out the first test's 100 control sites, chosen by the census's seeded `sample()` (seed
    "doc-first-control-2").
  - *Smoke:* ada.gov and section508.gov, the Actor's examples. Reported, with no prediction.
- **Arms:** A = `census.crawl_site` 0.2.2 (random pages); B = `site_check.crawl` 0.1.1 (fetched
  from commit 279e85e); C = `site_check.crawl` 0.1.2 (from main). Each reads at most 8 inner
  pages and checks at most 2 PDFs, with a 1-second pause between requests and robots.txt
  honoured. A runs first on each site, then B and C in an order set per site by a hash, so
  neither of them always goes last.
- **Analysed:** sites where all three arms read the home page. Outcomes: at least one PDF link;
  at least one readable PDF. Paired comparisons with exact two-sided McNemar tests.
- **Published:** aggregate counts only, plus the two smoke sites. Per-site rows are not
  published, and no local government is named.

## Predictions

1. Control 2: C reaches at least one readable PDF at a share **no more than 2 percentage points
   below A** (the prediction 0.1.1 failed).
2. Control 2: C reaches at least one readable PDF at **no fewer sites than B**.
3. Zero set: C finds at least one PDF link at **30% or more** of the analysed sites.
4. Zero set: C beats A on discordant pairs for "at least one PDF link", exact McNemar
   **p < 0.01**.
5. Zero set: C finds at least one PDF link at a share **no more than 5 percentage points below
   B** (what the fallback may cost on hard sites).
6. Control 2: C reads **fewer** inner pages in total than A.

## What would count against site_check 0.1.2

If prediction 1 fails, the Actor's description will say that on sites where random pages
already find PDFs, random sampling reaches them more often, and will suggest giving PDF links
directly or raising Pages to read. If prediction 5 fails, the fallback costs too much on sites
whose PDFs sit only behind document-like pages, and the rule needs another look. Either way, the
Actor is not published until this test is scored.

## Limits

Three arms on the same day are not simultaneous: a site can change or slow down between them,
and A always runs first. The zero set was used in the first test, and B's result on it is known.
Some sites keep documents behind search forms or scripts that no arm reads. The word list and the
half-the-pages rule were written by AI agents working for MV2 of Munim, Inc. and not tuned on
the new control sites.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (text).
