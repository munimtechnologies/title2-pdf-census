# wordsig results: the Word signature on PDFs nobody had looked at

Scored 2026-10-19 by AI agents working for MV2 of Munim, Inc., from the crawl described in the
[pre-registration](wordsig-prereg.md), which fixed the predictions, the minimum sample and the code
before any PDF was read. Machine checks only: nothing here is a WCAG conformance judgment about any
government, and no government is named. Code Apache-2.0; this text and the data CC BY 4.0.

`test_wordsig_results.py` in the repository root scores the public rows in
[results/wordsig-v1/](../results/wordsig-v1/) again with `wordsig.py`, checks that every count,
share and p-value agrees with `summary.json`, and checks that this page is exactly what
`wordsig_page.py` writes from those files. Public rows carry no site id, so the site counts and the
site-resampled intervals come from `summary.json` and are not rechecked.

## Verdict

**Inconclusive: too few.** The crawl found 6 Word-made and 46 Adobe-made mismatched PDFs (the
document language names a different language from the text). The pre-registered minimum was 8 of
each, so W1 and W2 are not scored and nothing is claimed; the counts are published below. As
pre-registered, there is no second crawl unless an amendment is published first. site_check 0.2.1
leads with the Acrobat fix only for a file whose parts already carry the text's language, so its
advice for any one file does not depend on this result; what this result bears on is how often Word
output looks like that.

## Pre-registered predictions

| Prediction | Measured | Result |
|---|---|---|
| W1 (primary): Word's share that marks the real language inside is higher than Adobe's (one-sided Fisher exact, p < 0.05; scored with at least 8 of each) | Word 6 of 6, Adobe 7 of 46; p = 0.000084 | not testable |
| W2: Word's share at least 60%, Adobe's at most 40% | Word 100.0%, Adobe 15.2% | not testable |
| W3: Word's share is higher in both directions (judged with at least 3 of each in each) | French declared English: Word 6 of 6, Adobe 5 of 38; English declared French: Word 0 of 0, Adobe 1 of 1 | not testable |
| W4: the Word PDFs that mark the real language inside come from at least 5 sites | 4 sites | **not held** |

Site-resampled 95% intervals for W1's shares: Word 100.0-100.0%, Adobe 5.9-31.0%.

## The crawl

- Cohort: 367 municipal website hosts listed on Wikidata, fetched again when the crawl ran. By
  province: Quebec 112, Ontario 110, British Columbia 69, Alberta 45, Nova Scotia 9, Saskatchewan 6,
  Manitoba 5, New Brunswick 5, Newfoundland and Labrador 4, Prince Edward Island 1, Northwest
  Territories 1.
- Sites crawled: 367 (ok 341, other 20, robots_disallow 6).
- Ran from 2026-10-19T13:04:06Z to 2026-10-19T13:42:07Z (UTC).
- PDFs checked 1616; read without error 1616; text language determined 1240; mismatched 60.
- Code: the four study files had the SHA-256 values the pre-registration lists. census.py on main is
  the same file as the file at tag v0.2.2. Packages: pypdf 6.21.1 py3langid 0.4.0 langdetect 1.0.9.

## Exploratory (no prediction)

- Text languages of the PDFs read without error: en 793, fr 440, undetermined 364, mixed 12, pa 2,
  ko 2, fa 2, ar 1.
- French-text PDFs whose /Lang is missing, unusable or another language: 193 of 440 (43.9%;
  site-resampled 95% interval 36.4-51.9%).
- Text language and what the document declares: ar:match 1, en:match 514, en:none 277, en:other 2,
  fa:other 2, fr:match 247, fr:none 141, fr:other 52, ko:other 2, pa:other 2.
- Mismatched PDFs by producer family and direction: adobe|en-as-fr 1 (1 marked inside),
  adobe|fr-as-en 38 (5 marked inside), adobe|other 7 (1 marked inside), office-other|fr-as-en 1 (0
  marked inside), other|fr-as-en 6 (0 marked inside), other|other 1 (0 marked inside), word|fr-as-en
  6 (6 marked inside).
- Word's share of non-English-text PDFs: 101 of 447 (22.6%).

## Limits

Producer strings name the tool, not its version or settings, and Word includes files whose Creator
names Word but whose Producer is another tool. Canada is not the US. Wikidata lists only some
municipalities' websites, so the cohort is the municipalities Wikidata lists, not all of them. Text
is read from the first 5 pages, and marked-content /Lang is found only when written inline. No copy
of Word and no screen reader was used. The private rows, which have URLs, are not published.

Made by MV2 of Munim, Inc. with AI agents.
