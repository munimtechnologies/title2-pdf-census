# wordsig: does the "Word signature" hold on PDFs nobody has looked at? (pre-registration)

**Pre-registered on 2026-10-19, before any PDF in this study was read.** Made by MV2 of Munim, Inc.
with AI agents. Apache-2.0 (code), CC BY 4.0 (text and data).

## Why

The lang-census measured whether a PDF's document language (/Lang) matches the language of its
text, on PDFs of US local governments ([results](lang-census-results.md)). Looking at the results
afterwards, [a note](lang-word-note.md) found that in 11 of 13 Word-made non-English PDFs that
declare English, the real language is already marked inside the file (on structure elements or
marked content), against 2 of 14 Adobe-made ones. That pattern was found by looking, so it cannot
be confirmed on the same rows. site_check 0.2.1 already gives Word-made files a different fix on
the strength of it. This study tests it on PDFs the lang-census never read.

We found no earlier measurement of declared against actual PDF language by the tool that made
the file, in any country. We found only guidance (W3C PDF16 and PDF19, the Government of Canada's
accessibility toolkit, university and state guides that disagree on whether Word's proofing
language reaches the PDF) and individual user reports on Microsoft Q&A. One of those reports, from
2026, describes the same shape: a PDF saved from Word with no document-level /Lang, while the
language of each part was kept.

## Population

Canadian municipalities publish in French and English, so one rule covers two directions: French
text declared English, and English text declared French.

- Cohort: Wikidata items in Canada (P17 Q16) that are an instance of municipality (Q15284) or
  any subclass of it, with a population of at least 10,000 and an official website (P856), one row
  per website host (largest population kept), as `wordsig.cohort_query()` builds it
  (`COHORT_CLASS = "municipality"`, `MIN_POPULATION = 10000`). The province is taken from P131
  where Wikidata gives one. The crawl does not use it.
- Size check before choosing (2026-10-19 ~10:30Z, count-only query on query.wikidata.org, no
  municipal site read): 373 municipalities with 386 website URLs. By province: Quebec 118, Ontario
  110, British Columbia 69, Alberta 45, Nova Scotia 9, Saskatchewan 7, New Brunswick 5, Manitoba 5,
  Newfoundland and Labrador 4, Northwest Territories 1, Prince Edward Island 1. The crawl fetches
  the cohort again when it runs, so its count can differ a little. That count gets published.
- Every site in the cohort, in the order of title2-pdf-census's `sample()` with seed
  `wordsig-v1`, until all are done or 150 minutes pass (`wordsig.py run`, 8 workers).

## Method (released code, unchanged)

- The crawl of title2-pdf-census 0.2.2 (`census.py` at tag v0.2.2): the home page and up to 8 of
  its pages, up to 8 readable PDFs per site, public pages only, robots.txt honoured, 1 second
  between requests to a site, under a User-Agent naming Munim, Inc. and mv2@munimtech.com.
- The checks of lang.py 0.1.1 (`results/lang-v1/lang.py`), unchanged: the text language of the
  first 5 pages (py3langid and langdetect must agree on each chunk); the catalog /Lang; /Lang on
  structure elements and in marked content on those pages; the producer family from census.py.
- `wordsig.py` 0.1.0 only swaps in the cohort query, the seed and the User-Agent, and scores.
- The job runs only once `docs/wordsig-prereg.md` and `wordsig.py` on main are the same bytes
  as its own copies, with pypdf[crypto] 6.21.1, py3langid 0.4.0 and langdetect 1.0.9, and
  records the SHA-256 of every file it runs.

## Unit

A **mismatched PDF**: read without error, text language determined (not undetermined or mixed),
and a catalog /Lang whose primary language is a different language (lang.py `declared() ==
"other"`). **Word** = producer family `word`, **Adobe** = `adobe`. A PDF **marks the real
language inside** when a structure element or marked-content sequence names the text language
(lang.py `local_match()`).

## Predictions

- **W1 (primary).** Among mismatched PDFs, Word's share that marks the real language inside is
  higher than Adobe's: one-sided Fisher exact test, held if p < 0.05 and Word's share is higher.
- **W2.** Word's share is at least 60% and Adobe's at most 40%.
- **W3 (descriptive).** Judged only if both directions (French declared English, English declared
  French) have at least 3 Word and 3 Adobe mismatched PDFs: held if Word's share is higher than
  Adobe's in each.
- **W4.** The Word PDFs that mark the real language inside come from at least 5 different sites.

**Minimum sample.** W1 and W2 are scored only with at least 8 Word and 8 Adobe mismatched PDFs.
Otherwise the result is "inconclusive: too few": the counts are published and nothing is
claimed. There is no second crawl unless an amendment is published first.

**Power** of W1 (exact enumeration of every outcome, `python wordsig.py power`, alpha 0.05, equal
group sizes; copied from its output):

| Word share | Adobe share | 8 and 8 | 10 and 10 | 15 and 15 |
|---|---|---|---|---|
| 0.8 | 0.2 | 0.6135 | 0.8054 | 0.9391 |
| 0.7 | 0.3 | 0.2616 | 0.4184 | 0.5895 |

The exploratory shares were 0.85 and 0.14, close to the first row. If the true gap is nearer 0.7
against 0.3, this study is likely to miss it at these sizes, so a "not held" W1 with small groups
is weak evidence against the pattern, and we will say so.

## Also reported, exploratory

French-text PDFs with a missing, unusable or other /Lang (with a site-resampled interval);
text language against declared language; mismatched PDFs by producer family and direction;
Word's share of non-English-text PDFs; site-resampled intervals on both W1 shares.

## Limits

Producer strings name the tool, not its version or settings. Canada is not the US. Text comes
from the first 5 pages. No copy of Word and no screen reader is used. Quebec documents may almost
all be French declared French, which would leave the English-declared-French direction thin.
Wikidata's coverage of Canadian municipal websites is incomplete, so the cohort is the
municipalities Wikidata lists, not all of them.

## Code as pre-registered

`test_wordsig.py` (13 tests: the Fisher tests against known tables, the power edges, the cohort
query's shape, and W1-W4 scored on made-up rows) passed on Python 3.11.9 before this was
published. SHA-256 of the files the study runs:

- `wordsig.py` 0.1.0: `c77cf4fc02995c55550d576c5b669336dade46e094d013cf430facd2bd5162dc`
- `test_wordsig.py`: `103845dadd78ee4b6ed7d59ea0fefe68fd6b7bb500aaf87f17d473fd4ceeeacd`
- `census.py` 0.2.2: `95365902783dddee8292d6438bc1e074de72ae1c27ca55438c2b789976650a2e`
- `results/lang-v1/lang.py` 0.1.1: `dee52208087a6a85ebb3dc282cf3b2ab519e8ecdef6f180cb7ea970366db54b5`

## What gets published

Counts, the scored predictions and public rows with the same fields as the lang-census's public
rows (no URLs, no site names, no document text). `docs/lang-word-note.md` gets a dated line with
the result, whichever way it goes.

## Amendment 1 (2026-10-19, before any PDF was read)

Written while the crawl job was still waiting in the queue, so no PDF of this study had been read.
Nothing above changes, and the code and its SHA-256 stay as listed.

- **W3 is scored by the text above**: judged when each direction has at least 3 Word and 3 Adobe
  mismatched PDFs, held if Word's share is higher than Adobe's in each. It is computed from the
  direction counts that `wordsig.py` writes to `summary.json`
  (`W3_same_sign_each_direction.directions`). Reading the code again showed that the `met` value
  `wordsig.py` 0.1.0 computes for W3 differs from the text in two ways: it also requires W1's
  minimum sample, and it asks whether each direction has the same sign as the overall
  difference, so it would call W3 held if Word's share were lower than Adobe's overall and in
  both directions. The results page gives the code's value as well whenever the two differ.
- A cohort probe that read Wikidata only (no municipal site) ran on 2026-10-19 and counted 367
  website hosts for this class at 10,000 people or more, close to the count-only check above.
- The results page and its test will be written by `wordsig_page.py` and checked by
  `test_wordsig_results.py`, which score the public rows again and check that the page is
  exactly what the script writes from the job's files.
