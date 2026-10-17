# Results: with 16 pages, does site_check 0.1.2 keep what 0.1.1 found and match random pages?

Scored on 2026-10-17 against the predictions in [doc-first-v3-prereg.md](doc-first-v3-prereg.md),
which were committed before the job ran (the job fetched that file from main and recorded its
SHA-256). The job's code is [doc_first_reach_v3.py](../doc_first_reach_v3.py) (it ran as `job.py`;
the file is unchanged, and `test_doc_first_reach_v3.py` checks its SHA-256 against the one the job
recorded). Its outputs are in [results/doc-first-v3/](../results/doc-first-v3/): `summary.json`,
`summary.md` and `code-sha256.txt`. `test_doc_first_reach_v3.py` recomputes every number on this
page from them and scores each prediction from the counts.

**In short: five of the six predictions held, and one failed.** With 16 pages, site_check 0.1.2
reached a readable PDF on 180 of 195 control sites, exactly as many as 16 random pages, while
reading 849 inner pages against 3025. On the hard sites it found a PDF link on 70 of 122, against
56 for 0.1.1 and 58 for random pages. So 16 pages fixes what 0.1.2 lost with 8, and site_check
0.1.3 makes 16 the default. The failed prediction matters more than its size: on the hard sites,
random pages with 16 pages found PDF links on 58 sites, where with 8 pages they had found them on
2. That exposes a flaw in how the first two tests chose and compared those sites, explained below,
and it means their headline gain over random pages was overstated.

## What ran

- **Arm A:** `census.crawl_site` 0.2.2, 16 inner pages chosen by the census's seeded sample.
- **Arm B:** `site_check.crawl` 0.1.1 (document-like pages first), 8 pages.
- **Arm D:** `site_check.crawl` 0.1.2 (the same, but once half its pages are read with no PDF
  link, the other pages first), 16 pages, so it falls back only after 8 document-like pages.
- Each checked at most 2 PDFs per site, with a 1-second pause between requests and robots.txt
  honoured. A ran first on each site, then B and D in an order set per site by a hash, on
  2026-10-17 (about 30 minutes in all).
- **Zero set:** the 129 sites where the census's second full run (0.2.1) read pages but found no
  PDF link (the same sites as both earlier tests). **Control 3:** 200 sites where it found at least
  one, leaving out the first two tests' 300. **Smoke:** ada.gov and section508.gov.
- Analysed: sites where all three arms read the home page. Exact two-sided McNemar tests on the
  discordant pairs.

## Results

Zero set (129 sites, 122 with all three home pages read):

- At least one PDF link: A 58 of 122 (47.5%), B 56 of 122 (45.9%), D 70 of 122 (57.4%)
  - D against A: only D 24, only A 12; exact McNemar p = 0.065
  - D against B: only D 14, only B 0; exact McNemar p = 0.00012
  - B against A: only B 20, only A 22; exact McNemar p = 0.88
- At least one readable PDF: A 49 of 122 (40.2%), B 46 of 122 (37.7%), D 58 of 122 (47.5%)
  - D against A: only D 21, only A 12; exact McNemar p = 0.16
  - D against B: only D 14, only B 2; exact McNemar p = 0.0042
  - B against A: only B 19, only A 22; exact McNemar p = 0.76
- Pages read: A 1693, B 803 (664 document-like), D 1420 (790 document-like); D fell back to other pages at 52 sites

Control 3 (200 sites, 195 with all three home pages read):

- At least one PDF link: A 194 of 195 (99.5%), B 183 of 195 (93.8%), D 193 of 195 (99.0%)
  - D against A: only D 0, only A 1; exact McNemar p = 1
  - D against B: only D 10, only B 0; exact McNemar p = 0.002
  - B against A: only B 0, only A 11; exact McNemar p = 0.00098
- At least one readable PDF: A 180 of 195 (92.3%), B 170 of 195 (87.2%), D 180 of 195 (92.3%)
  - D against A: only D 7, only A 7; exact McNemar p = 1
  - D against B: only D 12, only B 2; exact McNemar p = 0.013
  - B against A: only B 4, only A 14; exact McNemar p = 0.031
- Pages read: A 3025, B 671 (663 document-like), D 849 (807 document-like); D fell back to other pages at 9 sites

Weighted (pre-registered):

- Read sites with a readable PDF, zero set and control3 weighted 129 : 1001: A 86.4%, B 81.5%, D 87.2%

Smoke sites (the Actor's examples; no prediction):

- At least one PDF link: A 2 of 2 (100.0%), B 2 of 2 (100.0%), D 2 of 2 (100.0%)
- At least one readable PDF: A 2 of 2 (100.0%), B 2 of 2 (100.0%), D 2 of 2 (100.0%)
- Pages read: A 32, B 6 (6 document-like), D 6 (6 document-like); D fell back to other pages at 0 sites
- ada.gov: A pages 16, PDF links 5, readable PDFs 2; B pages 5, PDF links 4, readable PDFs 2; D pages 5, PDF links 4, readable PDFs 2
- section508.gov: A pages 16, PDF links 36, readable PDFs 2; B pages 1, PDF links 35, readable PDFs 2; D pages 1, PDF links 35, readable PDFs 2

## The predictions, scored

1. **Held.** Control 3: D reached at least one readable PDF at 92.3% of sites against 92.3% for
   A, the same; the prediction allowed at most 2 points lower.
2. **Held.** Control 3: D reached a readable PDF at 180 sites against 170 for B (12 against 2 on
   the discordant pairs, p = 0.013).
3. **Held.** Zero set: D found at least one PDF link at 57.4% of the analysed sites (70 of 122)
   against 45.9% for B (56), 11.5 points higher; the prediction allowed at most 5 points lower
   (with 8 pages, 0.1.2 had been 10.4 points lower).
4. **Failed.** Zero set: on the discordant pairs D found a PDF link where A did not at 24 sites,
   and A where D did not at 12; exact McNemar p = 0.065. The prediction was p < 0.01.
5. **Held.** Control 3: D read 849 inner pages against 3025 for A.
6. **Held.** Weighted share of read sites reaching a readable PDF: D 87.2% against A 86.4%. As
   the pre-registration said, a difference this small means little.

## Why random pages did so much better this time: a flaw in the earlier tests

In the first two tests, random pages found a PDF link on 2 of 127 and 2 of 125 zero-set sites. In
this one they found one on 58 of 122. The cause is in the census's `sample()`: it is not a fresh
random draw each time. It sorts a site's links by a hash of the site's address and the link and
takes the first ones, so it is reproducible, and asking for 16 pages gives the same first 8 plus 8
more. The zero set was chosen as the sites where the census, reading those 8 pages, found no PDF
link. The first two tests then ran arm A with the same 8 pages, so arm A mostly re-read pages
already known to have no PDF link. Its near-zero score on the zero set was built into the design,
not a measure of what random pages can do. With 16 pages, arm A read 8 pages it had not read
before and found PDF links on about half the sites.

What still stands: the census's own 8-page sample missed PDFs on these sites, and reading
document-like pages first found them on many (60 of 127 in the first test). What does not: "60
against 2 for random pages" as a measure of the gain over random sampling. At an equal budget of
16 pages, the gain is 70 against 58 sites, and the test could not tell it apart from chance at the
pre-registered level (p = 0.065). On the control sites, the two reach readable PDFs equally often,
and the main difference is cost: site_check read about a quarter as many pages (849 against
3025), because it stops once it has enough PDF links. We did not foresee this flaw when writing
the first two pre-registrations or this one. The results pages of the first two tests now carry a
note pointing here.

## What happens next

site_check 0.1.3 reads 16 pages by default (`--pages`, and Pages to read in the Apify Actor), with
0.1.2's fallback unchanged. The Actor's description now says the advantage over random pages is
fewer requests and somewhat more reach on hard sites, not the earlier figure. A future test of the
rule against random pages would need a hard set chosen by a sampler independent of arm A (for
example, a different seed).

## Limits

- Three arms one after another are not simultaneous, and A always ran first.
- The zero set was used a third time, and B's results on it were known.
- D read up to twice as many pages as B, so D beating B is partly the larger budget.
- The weighted share has no confidence interval and rests on the second full run's split of sites.
- 40 of the 122 zero-set sites gave no PDF link to any arm (D found one at 70, A at 12 more,
  and B at none that D missed). Their documents may sit behind search forms or scripts, deeper than two clicks, or not exist.
- "Document-like" is a word list written by AI agents working for MV2 of Munim, Inc., not tuned
  on these sites.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (text).
