# Results: does site_check 0.1.2's fallback keep the gain and win back the loss?

Scored on 2026-10-17 against the predictions in [doc-first-v2-prereg.md](doc-first-v2-prereg.md),
which were committed before the job ran. The job's code is
[doc_first_reach_v2.py](../doc_first_reach_v2.py) (it ran as `job.py`; the file is unchanged, and
`test_doc_first_reach_v2.py` checks its SHA-256 against the one the job recorded). Its outputs are
in [results/doc-first-v2/](../results/doc-first-v2/): `summary.json`, `summary.md`,
`code-sha256.txt` and `c-lost.json`. `test_doc_first_reach_v2.py` recomputes every number on this
page from them.

**In short: five of the six predictions held, and one failed.** On 200 control sites the first
test did not use, where random pages already find PDFs, site_check 0.1.2 reached a readable PDF
on 175 of 193 sites, against 177 for random pages and 170 for 0.1.1: the fallback won back what
0.1.1 lost there. But on the hard sites, where random pages had found no PDF link, 0.1.2 found
one on 46 of 125 sites, against 59 for 0.1.1 and 2 for random pages. That is 10.4 points below
0.1.1, more than the 5 points the pre-registration allowed. So the fallback costs too much on
sites whose PDFs sit only behind document-like pages, and as the pre-registration said, the rule
needs another look. That look is pre-registered in [doc-first-v3-prereg.md](doc-first-v3-prereg.md).

**Correction (2026-10-17, from the third test).** On the zero set, arm A's "2 for random pages"
is not a fair measure of random sampling: the census's `sample()` is seeded by the site's address,
so arm A re-read the same 8 pages on which the census had found no PDF link, which is how these
sites were chosen. Predictions 3 and 4 compared C with that arm. In the third test, 16 pages from
the same sampler found a PDF link on 58 of 122 of these sites
([doc-first-v3-results.md](doc-first-v3-results.md)). The comparisons between 0.1.1 and 0.1.2,
and everything on the control sites, are not affected.

## What ran

- **Arm A:** `census.crawl_site` 0.2.2 (8 inner pages chosen at random).
- **Arm B:** `site_check.crawl` 0.1.1 (document-like pages first, one level deeper, early stop).
- **Arm C:** `site_check.crawl` 0.1.2 (the same, but once half its pages are read with no PDF
  link, the other pages first).
- Each read at most 8 inner pages and checked at most 2 PDFs per site, with a 1-second pause
  between requests and robots.txt honoured. A ran first on each site, then B and C in an order
  set per site by a hash, on 2026-10-17 (about 25 minutes in all).
- **Zero set:** the 129 sites where the census's second full run (0.2.1) read pages but found no
  PDF link (the same sites as the first test). **Control 2:** 200 sites where it found at least
  one, leaving out the first test's 100. **Smoke:** ada.gov and section508.gov.
- Analysed: sites where all three arms read the home page. Exact two-sided McNemar tests on the
  discordant pairs.

## Results

Zero set (129 sites, 125 with all three home pages read):

- At least one PDF link: A 2 of 125 (1.6%), B 59 of 125 (47.2%), C 46 of 125 (36.8%)
  - C against A: only C 45, only A 1; exact McNemar p = 1.3e-12
  - C against B: only C 1, only B 14; exact McNemar p = 0.00098
  - B against A: only B 58, only A 1; exact McNemar p = 2.1e-16
- At least one readable PDF: A 2 of 125 (1.6%), B 49 of 125 (39.2%), C 41 of 125 (32.8%)
  - C against A: only C 40, only A 1; exact McNemar p = 3.8e-11
  - C against B: only C 1, only B 9; exact McNemar p = 0.021
  - B against A: only B 48, only A 1; exact McNemar p = 1.8e-13
- Pages read: A 910, B 815 (670 document-like), C 817 (435 document-like); C fell back to other pages at 68 sites

Control 2 (200 sites, 193 with all three home pages read):

- At least one PDF link: A 192 of 193 (99.5%), B 189 of 193 (97.9%), C 192 of 193 (99.5%)
  - C against A: only C 1, only A 1; exact McNemar p = 1
  - C against B: only C 4, only B 1; exact McNemar p = 0.38
  - B against A: only B 1, only A 4; exact McNemar p = 0.38
- At least one readable PDF: A 177 of 193 (91.7%), B 170 of 193 (88.1%), C 175 of 193 (90.7%)
  - C against A: only C 6, only A 8; exact McNemar p = 0.79
  - C against B: only C 6, only B 1; exact McNemar p = 0.12
  - B against A: only B 5, only A 12; exact McNemar p = 0.14
- Pages read: A 1524, B 567 (551 document-like), C 567 (531 document-like); C fell back to other pages at 10 sites

Smoke sites (the Actor's examples; no prediction):

- At least one PDF link: A 2 of 2 (100.0%), B 2 of 2 (100.0%), C 2 of 2 (100.0%)
- At least one readable PDF: A 2 of 2 (100.0%), B 2 of 2 (100.0%), C 2 of 2 (100.0%)
- Pages read: A 16, B 6 (6 document-like), C 6 (6 document-like); C fell back to other pages at 0 sites
- ada.gov: A pages 8, PDF links 1, readable PDFs 1; B pages 5, PDF links 4, readable PDFs 2; C pages 5, PDF links 4, readable PDFs 2
- section508.gov: A pages 8, PDF links 35, readable PDFs 2; B pages 1, PDF links 35, readable PDFs 2; C pages 1, PDF links 35, readable PDFs 2

## The predictions, scored

1. **Held.** Control 2: C reached at least one readable PDF at 90.7% of sites against 91.7% for
   A, 1.0 points lower; the prediction allowed at most 2 points (0.1.1 had been 4.1 points lower
   in the first test).
2. **Held.** Control 2: C reached a readable PDF at 175 sites against 170 for B (6 against 1 on
   the discordant pairs, p = 0.12).
3. **Held.** Zero set: C found at least one PDF link at 36.8% of the analysed sites (46 of 125);
   the prediction was 30% or more.
4. **Held.** Zero set: C beat A on the discordant pairs, 45 to 1, exact McNemar p = 1.3e-12; the
   prediction was p < 0.01.
5. **Failed.** Zero set: C found at least one PDF link at 36.8% against 47.2% for B, 10.4 points
   lower; the prediction allowed at most 5 points. C lost 14 sites to B and won 1 (exact McNemar
   p = 0.00098).
6. **Held.** Control 2: C read 567 inner pages against 1524 for A.

## Why C lost hard sites to B

C found no PDF link at 14 zero-set sites where B found some. At all 14, C had fallen back to
other pages, after 4 document-like pages at 12 of them (fewer at the other 2). Up to that point
C reads the same pages as B, so at those 12 sites B's first 4 document-like pages had no PDF link
either. B read 5 or more document-like pages at 13 of the 14: all 8 at 10 sites, and 5 at 2 sites
where it then stopped early with plenty of links. So on these sites the PDFs sat behind
document-like pages that random pages rarely reach and that 0.1.2, with 8 pages, gave up on too
soon. B reached a readable PDF at 9 of the 14. These counts come from the
per-site rows, which are not published (they name governments); `c-lost.json` holds them.

## Not pre-registered: the two sets together

The zero set and the control sets stand for every site the second full run read: 129 with no
PDF link and 1,001 with one (from `results/v0.2.1/sites.csv`). Weighting this test's two sets
129 : 1,001, the share of sites where each arm reached a readable PDF is A 81.4%, B 82.5%, C 84.1%.
This was worked out after the results came in, has no confidence interval, and small differences
in it mean little. It does suggest that, across all the sites, 0.1.2 is not worse than either
alternative. The next test pre-registers this weighted comparison.

## What happens next

0.1.2's code stays. With 8 pages, "half the pages" is 4, which is where it lost the hard sites;
with 16 pages the fallback starts only after 8 document-like pages, as many as 0.1.1 reads in
all. The third test ([doc-first-v3-prereg.md](doc-first-v3-prereg.md)) runs 0.1.2 with 16 pages
against random pages with 16 and 0.1.1 with 8, on 200 control sites neither earlier test used. If
it passes, site_check 0.1.3 makes 16 pages the default. Until then the default stays 8 and the
Apify Actor is not published.

## Limits

- Three arms one after another are not simultaneous, and A always ran first.
- The zero set was used in the first test, and B's result on it was known (60 of 127 then, 59 of
  125 now).
- At least 64 of the 125 zero-set sites gave no PDF link to any arm. Their documents may sit behind search
  forms or scripts, deeper than two clicks, or not exist.
- "Document-like" is a word list written by AI agents working for MV2 of Munim, Inc., not tuned
  on these sites.
- On the zero set, arm A repeated the census's own seeded sample (see the correction above).

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (text).
