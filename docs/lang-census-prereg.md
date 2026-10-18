# Pre-registration: does a PDF's declared language match the language of its text?

Written 2026-10-18 (UTC) by AI agents working for MV2 of Munim, Inc., before any data for this
study was collected. The job's setup waits until this file and the study's code
(`results/lang-v1/lang.py`, byte for byte the code that runs) are public on main, so no PDF is
read before these predictions are. Tests: `results/lang-v1/test_lang.py`. Apache-2.0 (code),
CC BY 4.0 (this text).

Machine checks only. Nothing here is a WCAG conformance judgment about any government, and no
government is named.

## Why ask
Screen readers pick a voice and pronunciation rules from a PDF's document language, the
catalog's `/Lang` entry, unless a structure element or a marked-content sequence gives another
language for part of the text. A Spanish notice whose `/Lang` says `en-US` is read aloud with
English rules, which can make it hard to follow. WCAG 2.1 success criterion 3.1.1 (Language of
Page) and PDF/UA both ask for the right language, not just any language. Our census
(title2-pdf-census 0.2.2) found `/Lang` set on 56.6% of readable PDFs from large US local
governments, but, like the checkers we know of, it only asked whether the entry exists.

**Prior art.** Web searches on 2026-10-18 found measurements of *missing* language declarations
(the WebAIM Million: 13.5% of home pages in 2026 declare no language; our own census for PDFs),
one large study of *mismatched* declarations on web pages (LangCrUX, arXiv 2508.18328: 120,000
websites in 12 mostly non-Latin-script languages, with the finding that automated testing tools
only check that a declaration is present), and studies that compare declared and detected
language in other metadata (Crossref records, arXiv 2503.11853; HTTP Content-Language, arXiv
1409.5443). We found no measurement of whether PDF `/Lang` values match the text, for
government documents or any other set.

## What is measured
The crawl is title2-pdf-census 0.2.2's (public pages only, robots.txt honoured, 1 second between
requests to a site, up to 8 pages and 8 PDFs per site), on up to 1,500 governments of its cohort
in the order set by tagtree-reach's seed, so the first 600 are the sites of the earlier tagtree
studies. It stops starting new sites after 150 minutes. Every PDF the census reads (pypdf opens
it and it is not image only) is checked, tagged or not:

- **Declared language:** the catalog `/Lang` value; whether it is BCP 47-shaped (a 2-3 letter
  primary subtag and optional subtags, or private use `x-...`); its primary language.
  Deprecated codes are mapped (for example `iw` to `he`, `nb` to `no`).
- **Local languages:** `/Lang` on structure elements (up to 20,000 nodes), and `/Lang` written
  inline in marked content on the first 5 pages.
- **Text language:** the text pypdf extracts from the first 5 pages (up to 20,000 characters),
  split into chunks of about 200 characters. Each chunk is read by two independent detectors,
  py3langid 0.4.0 and langdetect 1.0.9 (seeded). A chunk is **agreed** if both name the same
  language with probability 0.9 or more. A PDF's text language is the language of 80% or more
  of its agreed characters, if it has at least 400 agreed characters and they are at least half
  of all chunk characters; "mixed" if no language reaches 80%; otherwise "undetermined".
- A PDF's `/Lang` is **wrong** for its text if it is missing, has no usable primary language
  (for example `English` or `x-none`), or names a different primary language.

## Predictions
- **L1.** Of the PDFs whose text language is not English, **at least 50%** have a wrong `/Lang`.
  Basis: 43% of readable PDFs have no `/Lang` at all, and we expect many translated documents
  to keep the English default of the template or tool they were made with.
- **L2.** Of the PDFs whose text language is not English but whose `/Lang` names English, **at
  least 30%** name the text language on at least one structure element or marked-content
  sequence. Basis: Word can record a paragraph's language when it differs from the document's,
  and Word is the largest producer in the earlier samples; we have no direct evidence.
- **L3.** Of the PDFs whose text language is English, **fewer than 2%** have a `/Lang` naming
  another language.
- **L4.** Of the PDFs with any `/Lang`, **fewer than 3%** have a value that is not BCP 47-shaped.

L1 to L4 are scored on the point estimate, with a 95% Wilson interval reported; for L1 we also
report an interval that resamples sites, because one site can post many translated documents.
If no PDF qualifies for a prediction, it is reported as not testable.

## Checks on the method
- **Known answers (unit tests, run first in the job):** one-page PDFs built in the tests with
  Spanish or English text and a chosen catalog, element and marked-content `/Lang` must come out
  exactly as built (text language, declared language, local languages, wrong or not), and a page
  with too little text must be "undetermined".
- **K.** Across all checked PDFs, of the chunks py3langid gives probability 0.9 or more,
  **at least 90%** must get the same language from langdetect. If K fails, the detectors
  disagree too often for the text languages to be trusted, and we say so instead of scoring
  L1 to L3 as findings.

## Reported but not predicted
Counts of text languages; for non-English PDFs, how `/Lang` relates to the text, by language,
by producer family, and tagged or not; the declared language of mixed-language PDFs; how
English PDFs declare; the most common malformed values; `/Lang` written as a name instead of a
text string; and the share of checked PDFs with any `/Lang`.

## Limits, written in advance
- Only the first 5 pages, and only text pypdf can extract; fonts without a usable Unicode map
  give garbled text, which the detectors should leave undetermined rather than mislabel.
- Language detection is weaker on short or mixed text, which is why two detectors must agree
  and a PDF needs 400 agreed characters. Closely related languages can still be confused.
- `/Lang` in marked content is found only when written inline in the page's content stream,
  not through named property lists or in form XObjects; the structure tree is read up to 20,000
  nodes. So L2 may undercount local language markings.
- A wrong `/Lang` is a machine finding. Whether a particular screen reader then mispronounces a
  document depends on the reader and its settings; we did not test readers.
- The sample is large US local governments' sites as the census crawl reaches them. Sites change
  between runs, and we expect few non-English PDFs, so L1 and L2 may rest on a small number of
  files and sites; the counts will be stated plainly.
- Published rows carry a URL hash, language codes and counts; URLs and raw `/Lang` strings stay
  in the private output (the summary lists the 20 most common malformed values).
- We will not contact any government, tool maker or standards body about the results without a
  person's review.
