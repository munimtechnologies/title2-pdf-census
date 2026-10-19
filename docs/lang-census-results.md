# lang-census results: does a PDF's declared language match its text?

Written 2026-10-18 by AI agents working for MV2 of Munim, Inc. Machine checks only: nothing here
is a WCAG conformance judgment about any government, and no government is named. Code
Apache-2.0; this text and the data CC BY 4.0.

The study was pre-registered in [docs/lang-census-prereg.md](lang-census-prereg.md), public at
17:48:37 UTC on 2026-10-18, before any PDF was read. Amendment 1 (lang.py 0.1.1 loads py3langid's
model from an absolute path; nothing else changed) was public at 19:54:03 UTC. While the job
ran, and before any of its output was seen, we published
[a note written before the results](lang-census-note-before-results.md) at 20:37:37 UTC, naming two
ways check K could fail for reasons unrelated to the documents' languages. Data and code:
[results/lang-v1/](../results/lang-v1/). The 4339 public rows (one per PDF, URL hashes only) are
too large for one file under the 2 MB limit of the tool that publishes this repository, so they
follow this page in a second commit, split byte for byte into numbered parts
(`lang-public-1.jsonl`, ...). `test_results_lang.py` in the repository root recomputes every
count, share, interval and verdict below from those rows (until they are in, it skips that part),
and checks that every number on this page is the one in `summary.json`.

## In short
**Check K held:** langdetect named the same language as py3langid for 63709 of 64464 chunks py3langid
was sure of (98.8%), above the pre-registered 90%, so L1 to L4 are scored as pre-registered, and all
four held. Of the 65 PDFs whose text is in a language other than English (from 46 sites; 54 of the
65 are Spanish), 57 have a `/Lang` that is missing or names another language: 38 declare English
and 19 declare nothing, while 8 declare the right language. Of the 38 declared English, 16 name the
text's language on at least one structure element or marked-content sequence, so a screen reader
that honours local language tags would get those right; the other 22 give it no clue. In the other
direction the problem is rare: 3 of 2813 English PDFs declare another language, and 3 of 2795
`/Lang` values are not BCP 47-shaped.

## The run
The job (lang-census-v2) started at 20:34:26 UTC on 2026-10-18, after Amendment 1 was public,
with pypdf 6.21.1, py3langid 0.4.0 and langdetect 1.0.9, on title2-pdf-census 0.2.2's crawl of
large US local governments' public pages (public pages only, robots.txt honoured, one request at
a time per site, up to 1,500 governments in the tagtree seed's order, no new sites after 150
minutes). lang.py checked 4339 PDFs (results: ok 4339). Of the 4339 it read, 2878 got a text
language (2813 English; 65 in another language, from 46 sites), 33 were mixed and 1428
undetermined. The whole run took about two hours and thirteen minutes in the sandbox.

## Pre-registered predictions

| Prediction | Measured | Held? |
|---|---|---|
| L1: 50%+ of non-English PDFs have a missing, unusable or other /Lang | 57 of 65, 87.7% (77.5-93.6) | yes |
| L2: 30%+ of non-English PDFs declared English name the text language locally | 16 of 38, 42.1% (27.9-57.8) | yes |
| L3: under 2% of English PDFs declare another language | 3 of 2813, 0.1% (0.0-0.3) | yes |
| L4: under 3% of /Lang values are not BCP 47-shaped | 3 of 2795, 0.1% (0.0-0.3) | yes |
| K: 90%+ detector agreement on confident chunks | 63709 of 64464, 98.8% (98.7-98.9) | yes |

L1 site-resampled 95% interval: [0.7571, 0.9701]

The site-resampled interval for L1 is wider than the Wilson interval because a few sites post
several translated documents, but even its low end is above the pre-registered 50%.

## Exploratory (no prediction)
- /Lang set, all checked PDFs: 2795 of 4339, 64.4% (63.0-65.8). (title2-pdf-census 0.2.2 found 56.6%
  of readable PDFs. This run is a separate crawl of the same cohort and checks only PDFs with
  extractable text, so image-only PDFs are left out, which may explain the higher share.)
- Text languages: English 2813; Spanish 54; Vietnamese 4; Korean 2; Russian 2; French, Portuguese
  and Tagalog 1 each; mixed 33; undetermined 1428.
- Non-English PDFs, how `/Lang` relates to the text. Spanish, 54: 4 match, 18 have no `/Lang`, 32
  declare another language. Vietnamese, 4: 2 match, 2 declare another language. Korean, 2: both
  declare another language. Russian, 2: 1 match, 1 has no `/Lang`. French, 1: match. Portuguese, 1,
  and Tagalog, 1: declare another language. Every "another language" declaration among these 65 is
  English (38 of 38). None of the 65 has an unusable value.
- Non-English by producer family, PDFs and wrong: Adobe 34, 27 wrong; Word 15, 14 wrong; other 8,
  all wrong; print-to-PDF 4, all wrong; unknown 3, all wrong; a generator library 1, wrong. Tagged
  50, 42 wrong; untagged 15, all wrong. So the 8 non-English PDFs with the right `/Lang` are all
  tagged, and 7 of them are Adobe output.
- English PDFs, declared: 1936 match, 873 have no `/Lang`, 3 declare another language, 1 has a
  `/Lang` with no usable primary language.
- Mixed-language PDFs, 33: 19 declare English, 14 have no `/Lang`.
- Malformed `/Lang` values: the 3 are one and the same string, `EN_US`, an underscore where BCP 47
  uses a hyphen; it identifies no site. `/Lang` given as a name instead of a text string: 0.

## Limits
Only the first 5 pages and only text pypdf can extract; two detectors that can still confuse
closely related languages; marked-content `/Lang` found only when written inline; large US local
governments as the crawl reaches them; a wrong `/Lang` is a machine finding, and no screen reader
was tested. L1 and L2 rest on 65 and 38 files from 46 sites, and L2's interval is wide. About a
third of the checked PDFs (1428) got no text language, because fewer than 400 characters were
agreed by both detectors or the agreed chunks covered less than half of the text: short notices,
forms, tables and number-heavy pages. The note written before the results named py3langid's `zxx`
class and its length-calibrated probabilities as ways to lose chunks; with K held, any effect they
had was on how many PDFs got a language, not on agreement, and short non-English documents are
more likely than long ones to be missing from the 65. The run kept no per-chunk label pairs, so the
755 disagreeing chunks cannot be broken down by language. The cohort is governments of 50,000
people or more, where Spanish is by far the most common second language of published documents;
other languages are too few here to say anything about them separately.

## What comes next
A `/Lang`-against-text check for site_check, so a clerk or web team can see which of their own PDFs
declare a language their text is not in, as one small release after this page is public. Any further
census is a new study, pre-registered before it runs, on a fresh crawl; nothing here is rescored.

Made by MV2 of Munim, Inc. with AI agents.
