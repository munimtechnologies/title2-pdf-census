# qcfr results: French PDFs in Quebec and in the rest of Canada

Scored 2026-10-19 by AI agents working for MV2 of Munim, Inc., as fixed in the
[pre-registration](qcfr-prereg.md) before the split by province was computed. It re-reads the rows
of the wordsig crawl ([wordsig-results.md](wordsig-results.md)) with `results/lang-v1/lang.py` 0.1.1
unchanged; no new crawl was made. Machine checks only: nothing here is a WCAG conformance judgment
about any government, and no government is named. Code Apache-2.0; this text and the data CC BY 4.0.

`test_qcfr_results.py` in the repository root runs the site-level permutation test again on
[results/qcfr-v1/sites-public.json](../results/qcfr-v1/sites-public.json) with `qcfr.score_sites`,
counts the PDF-level numbers again from the public wordsig rows, and checks that this page is
exactly what `qcfr_page.py` writes from those files. The site table has one `[group, French-text
PDFs, wrong]` row per site and no site name, URL or Wikidata id; the site-resampled intervals need
the private site ids and are not rechecked.

## Verdict

**Inconclusive: too few.** Outside Quebec the crawl has 7 French-text PDFs from 6 sites, Quebec 433
from 88 sites. The pre-registered minimum was 20 PDFs and 4 sites in each group, so Q1 is not scored
and nothing is claimed.

## Pre-registered prediction

| Prediction | Measured | Result |
|---|---|---|
| Q1: French-text PDFs of municipalities outside Quebec have a missing, unusable or other /Lang more often than Quebec's (site-level permutation, one-sided, p < 0.05; scored with at least 20 PDFs and 4 sites in each group) | outside Quebec 7 of 7 (100.0%, 6 sites); Quebec 186 of 433 (43.0%, 88 sites); gap n/a; p = n/a | not testable |

Site-resampled 95% intervals: outside Quebec 100.0-100.0%, Quebec 35.2-50.6%.

## Rows

- PDFs in the wordsig crawl 1616; read without error 1616; French text 440.
- Left out: French-text PDFs with no province 0; sites whose rows carry two groups 0.
- Permutations 20000, seed `qcfr-v1`; qcfr.py 0.1.0.

## Exploratory (no prediction)

- Declared /Lang of French-text PDFs outside Quebec: none 1, other 6.
- Declared /Lang of French-text PDFs in Quebec: match 247, none 140, other 46.
- Language named when it is not French: outside Quebec en 5, ar 1; Quebec en 46.
- PDF-level one-sided Fisher exact p, which ignores that PDFs of one site are alike: 0.002936.

## Limits

Groups follow the province label Wikidata gave each municipality when the crawl ran. Quebec's
municipalities differ from the others in more than language: size, software, staff and how many
French documents they publish, so a gap says where wrong document languages are, not why. Text is
read from the first 5 pages, and a PDF counts as French only when two detectors agree on enough of
its text. The cohort is the municipalities of 10,000+ people that Wikidata lists with a website, and
the PDFs the crawl reached. No screen reader was used. The private rows, which have URLs and site
ids, are not published.

Made by MV2 of Munim, Inc. with AI agents.
