# Results: does reading document pages first find the PDFs random sampling misses?

Scored on 2026-10-17 against the predictions in [doc-first-prereg.md](doc-first-prereg.md), which
were committed before the job ran. The job's code is [doc_first_reach.py](../doc_first_reach.py)
(it ran as `job.py`; the file is unchanged, and `test_doc_first_reach.py` checks its SHA-256
against the one the job recorded). Its outputs are in [results/doc-first/](../results/doc-first/):
`summary.json`, `summary.md`, `code-sha256.txt` and `b-missed.json`. `test_doc_first_reach.py`
recomputes every number on this page from them.

**In short: four of the five predictions held, and one failed.** On the local-government sites
where random page sampling had found no PDF link, reading document-like pages first found one
on 60 of 127 sites, against 2 for random pages. But on sites where random pages already worked,
it reached a readable PDF less often (88 of 97 against 92 of 97). That is 4.1 points worse, more
than the 2 points the pre-registration allowed. So site_check 0.1.1 traded away some sites that
random sampling handled, and as the pre-registration said, it needed another look before the
Apify Actor is published. site_check 0.1.2 is that look. Its own test is pre-registered in
[doc-first-v2-prereg.md](doc-first-v2-prereg.md), on 200 sites this test did not use.

## What ran

- **Arm A:** `census.crawl_site` 0.2.2 (8 inner pages chosen at random).
- **Arm B:** `site_check.crawl` 0.1.1 (document-like pages first, one level deeper, early stop).
- Both read at most 8 inner pages and checked at most 2 PDFs per site, with a 1-second pause
  between requests and robots.txt honoured. A ran first on each site, then B, on 2026-10-17
  (about 11 minutes in all).
- **Zero set:** the 129 sites where the census's second full run (0.2.1) read pages but found no
  PDF link. **Control set:** 100 sites where it found at least one, chosen by a seeded sample.
- Analysed: sites where both arms read the home page. Exact two-sided McNemar tests on the
  discordant pairs.

## Results

Zero set (129 sites, 127 with both home pages read):

- At least one PDF link: A 2 of 127 (1.6%), B 60 of 127 (47.2%); only A 1, only B 59; exact McNemar p = 1.1e-16
- At least one readable PDF: A 2 of 127 (1.6%), B 50 of 127 (39.4%); only A 1, only B 49; exact McNemar p = 9.1e-14
- Pages read: A 926, B 829 (684 of B's document-like)

Control set (100 sites, 97 with both home pages read):

- At least one PDF link: A 97 of 97 (100.0%), B 90 of 97 (92.8%); only A 7, only B 0; exact McNemar p = 0.016
- At least one readable PDF: A 92 of 97 (94.8%), B 88 of 97 (90.7%); only A 6, only B 2; exact McNemar p = 0.29
- Pages read: A 764, B 317 (301 of B's document-like)

## The predictions, scored

1. **Held.** Zero set: B found at least one PDF link at 47.2% of the analysed sites (60 of 127);
   the prediction was 30% or more.
2. **Held.** Zero set: A found one at 1.6% (2 of 127); the prediction was 15% or fewer.
3. **Held.** Zero set: B beat A on the discordant pairs, 59 to 1, exact McNemar p = 1.1e-16; the
   prediction was p < 0.01.
4. **Failed.** Control set: B reached at least one readable PDF at 90.7% of sites against 94.8%
   for A, 4.1 points lower; the prediction allowed at most 2 points. The paired difference is not
   significant on its own (6 against 2, p = 0.29), but the pre-registered test was the 2-point
   margin, and it failed.
5. **Held.** Control set: B read 317 inner pages against 764 for A.

## Why B missed sites that random pages handled

On the control set, B found no PDF link at 7 sites where A found some. At all 7, B used its full
8 pages, and at 6 of them all 8 were document-like. We did not look at those pages; a likely
reason is that pages whose link text or address says Meetings, Plans, Notices, Resources and the
like are often calendars, search forms or pages with no files at all. 0.1.1 read every document-like page it had queued before any other page, so on
those sites it never reached the ordinary pages where A, by chance, found PDF links. These counts
come from the per-site rows, which are not published (they name governments); `b-missed.json`
holds them.

## What changed: site_check 0.1.2

Once half its pages are read and no PDF link has turned up, 0.1.2 reads the site's other pages
first, then any document-like pages left. Nothing else changed. With the default 8 pages it
reads up to 4 document-like pages, and then the others if those 4 found nothing. This was
designed after seeing the results above and the list of the 7 sites (not their pages), so it
is tested on 200 control sites this test did not use. The zero set has no fresh sites, so it is
reused there, and B is run again alongside C on the same day.

## Limits

- Two arms one after the other are not simultaneous: a site can change or slow down between them.
- 66 of the 127 zero-set sites gave no PDF link to either arm. Their documents may sit behind
  search forms or scripts, deeper than two clicks, or not exist.
- "Document-like" is a word list written by AI agents working for MV2 of Munim, Inc., not tuned
  on these sites.
- The census reads at most 8 random pages per site on purpose, so that its shares are not
  skewed toward one kind of page. This test is about site_check, the one-website self-check, not
  about the census's shares.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (text).
