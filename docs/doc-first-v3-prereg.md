# Pre-registration: with 16 pages, does site_check 0.1.2 keep what 0.1.1 found and match random pages?

Written 2026-10-17, before the job ran, and committed with the second test's results. The job
fetches this file and hashes it with its code. Its code and results will be added next to this
file and scored against the predictions below, whatever they show.

## Why

The second test ([doc-first-v2-results.md](doc-first-v2-results.md)) found that 0.1.2's fallback
won back the sites where random pages already worked (175 of 193 sites reached a readable PDF,
against 177 for random pages and 170 for 0.1.1), but cost too much on the hard sites: on the zero
set it found a PDF link on 46 of 125 sites against 59 for 0.1.1. At all 14 sites it lost, it had
fallen back after 4 or fewer document-like pages, while 0.1.1 read 5 or more document-like pages
at 13 of them.

With 8 pages, "half the pages" means 4. With 16 pages it means 8: the fallback starts only after
as many document-like pages as 0.1.1 reads in all, and 8 more pages remain for the others. On
sites where it finds PDF links quickly, it stops early, so the extra pages cost little there. So
this test runs 0.1.2's code unchanged with 16 pages, against random pages with the same 16 pages,
and against 0.1.1 with 8 (the arm whose reach on hard sites it must keep). If it passes, site_check
0.1.3 makes 16 the default.

This idea came from looking at the second test's per-site rows (the arms' counts, not the
sites' pages), so the main test is again on **200 control sites neither earlier test used**. The
zero set has no fresh sites, so it is used a third time.

## Design

- **Sites,** all from `results/v0.2.1/sites.csv` (pinned to commit 279e85e):
  - *Zero set:* status `ok`, `pages_read` > 0 and `pdf_links` = 0 (129 sites), as before.
  - *Control 3:* 200 sites with status `ok`, `pages_read` > 0 and `pdf_links` > 0, leaving out
    the first test's 100 and the second test's 200 control sites, chosen by the census's seeded
    `sample()` (seed "doc-first-control-3").
  - *Smoke:* ada.gov and section508.gov, the Actor's examples. Reported, with no prediction.
- **Arms:** A = `census.crawl_site` 0.2.2, 16 random inner pages; B = `site_check.crawl` 0.1.1
  (commit 279e85e), 8 pages; D = `site_check.crawl` 0.1.2 (commit 5ef6cbb, the file the second
  test ran), 16 pages. Each checks at most 2 PDFs, with a 1-second pause between requests and
  robots.txt honoured. A runs first on each site, then B and D in an order set per site by a hash.
- **Analysed:** sites where all three arms read the home page. Outcomes: at least one PDF link;
  at least one readable PDF. Paired comparisons with exact two-sided McNemar tests.
- **Weighted share:** the zero set and control 3 together stand for every site the second full
  run read: 129 with no PDF link and 1,001 with one. Each arm's share of sites reaching a readable
  PDF is the two sets' shares weighted 129 : 1,001.
- **Published:** aggregate counts only, plus the two smoke sites. Per-site rows are not
  published, and no local government is named.

## Predictions

1. Control 3: D reaches at least one readable PDF at a share **no more than 2 percentage points
   below A**.
2. Control 3: D reaches at least one readable PDF at **no fewer sites than B**.
3. Zero set: D finds at least one PDF link at a share **no more than 5 percentage points below
   B** (the prediction 0.1.2 failed with 8 pages).
4. Zero set: D beats A on discordant pairs for "at least one PDF link", exact McNemar
   **p < 0.01**.
5. Control 3: D reads **fewer** inner pages in total than A.
6. Weighted share: D's share of sites reaching a readable PDF is **higher than A's**.

## What would count against it

If prediction 1 or 6 fails, the Actor's description will say that random sampling reaches PDFs
more often on some sites, and will suggest giving PDF links directly. If prediction 3 fails,
reading more pages does not recover what the fallback costs, and the rule needs another look.
The default stays 8 pages and the Actor is not published until this test is scored.

## Limits

Three arms on the same day are not simultaneous, and A always runs first. The zero set is used a
third time and B's result on it is known. D reads up to twice as many pages as B, so D beating B
is no credit to the rule by itself; the comparison that matters for the rule is D against A at
the same budget. The weighted share has no confidence interval here and rests on the second
full run's split of sites; small differences in it mean little. Sites keep documents behind
search forms or scripts that no arm reads. The word list and the half-the-pages rule were
written by AI agents working for MV2 of Munim, Inc. and not tuned on the new control sites.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (text).
