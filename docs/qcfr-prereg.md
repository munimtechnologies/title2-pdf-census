# qcfr: pre-registration

**Do Quebec municipalities' French PDFs declare French more often than those of other provinces?**

Pre-registered 2026-10-19 by MV2 of Munim, Inc. Made with AI agents. Apache-2.0 (code), CC BY 4.0
(this text). Code: `qcfr.py` 0.1.0 and `test_qcfr.py`, committed with this file; they reuse
`results/lang-v1/lang.py` 0.1.1 unchanged.

## Why

A screen reader picks its voice and pronunciation rules from a PDF's document language (the
catalog's `/Lang`). A French notice declared `en-US` is read aloud with English rules. The
wordsig crawl ([wordsig-results.md](wordsig-results.md)) read 1,616 PDFs from 367 Canadian
municipal websites and found, as an exploratory count with no prediction, that 193 of 440
French-text PDFs (43.9%) have a `/Lang` that is missing, unusable or names another language.

That 43.9% may hide two different situations. In Quebec, French is the language of municipal
administration, and office software there is usually installed in French, so a document written
in French is likely to be declared French by default. Outside Quebec, French documents are often
translations made on machines set up in English, which would declare English or nothing. We know
of no published measurement of document-language accuracy in PDFs by province or region, in
Canada or elsewhere: earlier censuses, including ours before lang-census, only asked whether
`/Lang` is set, not whether it names the language of the text.

## What is already known, and what is not

- The data exist: the wordsig crawl's rows (crawl run 2026-10-19, 13:04-13:42 UTC). No new crawl
  is made for this test.
- Public before this file: the cohort's size by province (367 sites, 112 in Quebec; the cohort
  was fetched from Wikidata when the crawl ran), and the all-Canada French count above.
- **Not computed by anyone working for MV2:** any count of French-text PDFs by province, group
  sizes included. The public wordsig rows (`results/wordsig-v1/wordsig-public-1.jsonl`) carry each
  PDF's province, so anyone could compute a PDF-level split; we have not, and this test is
  scored at site level, which needs the private rows' site ids.
- So this is a pre-registered analysis of data already collected, not a new sample. Its
  protection is that the prediction, the test and the minimums are fixed here before the split
  is looked at.

## Rows and groups

- Rows: the wordsig crawl's `docs-private.jsonl`, rows with `result` "ok" whose text language
  (`text_lang`, lang.py's two-detector rule) is `fr`.
- Wrong: lang.py's `wrong()`: the catalog `/Lang` is missing, unusable, or its primary subtag is
  not `fr` (so `fr-CA`, `fr-FR` and `fr` are all right).
- Groups: **quebec** = the site's province label is `Quebec`; **rest** = any other province or
  territory. Rows with no province are left out and counted. A site whose rows carry two groups is
  left out and counted.

## Prediction

**Q1.** The share of French-text PDFs with a wrong `/Lang` is higher for municipalities outside
Quebec than for Quebec's.

- Statistic: pooled share wrong in **rest** minus pooled share wrong in **quebec** (the gap).
- Test: one-sided permutation test at site level. The group labels of the sites that have at
  least one French-text PDF are shuffled, each site keeping all its PDFs; 20,000 permutations
  with Python's `random.Random("qcfr-v1")`; p = (1 + permutations whose gap is at least the
  observed gap) / 20,001. Site level because PDFs of one site share software and staff and are
  not independent.
- **Held** if the gap is above 0 and p < 0.05. **Not held** if the minimums are met and either
  fails.
- **Inconclusive: too few** if either group has fewer than 20 French-text PDFs or fewer than 4
  sites with a French-text PDF. Then nothing is claimed, whatever the shares.
- No power figure is given: the group sizes are part of the split and have not been counted. The
  minimums above are the guard.

## Reported without a prediction

- Each group's share with a site-resampled 95% interval (lang.py's `cluster_ci`).
- Each group's breakdown of declared `/Lang`: none, unusable, other, match; and which languages
  the "other" ones name.
- A PDF-level one-sided Fisher p, labelled as ignoring that PDFs of one site are alike.

## What would change the reading

- Held: French PDFs outside Quebec are where wrong document languages concentrate, and advice
  (and checkers such as site_check) should say so to bilingual municipalities outside Quebec.
- Not held: the wrong `/Lang` on French PDFs is not a minority-language effect; it is as common
  where French is the default.
- Either way the result is about municipalities of 10,000+ people listed on Wikidata with a
  website, about the PDFs the crawl reached, and about the first five pages' text. No screen
  reader is tested.

## Outputs

`qcfr.py --lang results/lang-v1/lang.py --docs <docs-private.jsonl> --out-dir <new folder>`
writes `summary.json`, `results.md` and `sites-public.json` (one `[group, French-text PDFs,
wrong]` triple per site, sorted, with no site name, URL or Wikidata id), from which anyone can
re-run the permutation test with `qcfr.score_sites`. Results are published whichever way they go.
Any change to this plan after the split is computed is published as a dated amendment and does
not change how Q1 is scored.
