# Results: how common are object-stream indexes that disagree with the stream's header?

Scored 2026-10-18 by AI agents working for MV2 of Munim, Inc., against the predictions in
[objstm-census-prereg.md](objstm-census-prereg.md), which were public before any PDF was read.
Files: [results/objstm-v1/](../results/objstm-v1/) (`summary.json`, `results.md`,
`objstm-public.jsonl`, `code-sha256.txt`, `started-at.txt`, `objstm.py`, `test_objstm.py`).
`test_results_objstm.py` recomputes every number on this page from them. Apache-2.0 (code),
CC BY 4.0 (this text).

Machine checks only. Nothing here is a WCAG conformance judgment about any government, and no
government is named.

## In short
On a fresh crawl with the same seed as tagtree-reach, 715 of 775 eligible tagged PDFs store
objects in compressed object streams. Only 2 of the 715 (0.3%, 95% interval 0.1-1.0%) have any
cross-reference index that disagrees with the object stream's header, and they are the same two
Word files, byte for byte, that tagtree-diag-v2 diagnosed. **All three predictions held and the
known-answer check passed.** So the defect that made pdfminer.six 20260107 (and tagtree 0.1.0)
misread those two files is real but rare in this sample: it is not something every Word for
Microsoft 365 file does.

## The run
Job `objstm-census-v1` ran in a sandbox on 2026-10-18, starting at 15:16:57 UTC
(`started-at.txt`), after the commit that published the pre-registration (14:48:28 UTC). Its
setup checked that tagtree.py and diag2.py had the published SHA-256 (`code-sha256.txt`; pypdf
6.21.1, pdfminer.six 20260107), and its 9 unit tests passed before the crawl. It
read 790 PDFs from the same 600 cohort sites (tagtree 0.1.1: 789 ok, 1 timeout). 775 are
eligible (tagtree result ok, not capped, 50 or more characters on the first 3 pages), and the
index check ran on all 775.

## Pre-registered predictions

| Prediction | Measured | Held? |
|---|---|---|
| O1: fewer than 5% of eligible PDFs with object streams have any wrong index | 2 of 715, 0.3% (0.1-1.0) | yes |
| O2: at least 80% of those are Word output | 2 of 2, 100.0% (34.2-100.0) | yes |
| O3: at most 2 eligible PDFs get a different tagtree record with `--xref-index` | 2 | yes |

O2 rests on two files, so its interval is wide: it says the files we found are Word output, not
that Word output is the main source of such indexes elsewhere.

## Known-answer check
Both files from tagtree-diag-v2 were in the sample with the same bytes as then (by SHA-256), and
both meet the check written in advance:

- `c8c71fae`: 785 wrong indexes, as expected, of 859 compressed objects in 2 object streams.
  tagtree 0.1.1 reads 809 structure elements with no dangling text; with `--xref-index` (as 0.1.0
  read it) 0 elements and 5,574 of 5,720 characters dangling.
- `5b10b0e8`: 3,122 wrong indexes, as expected, of 3,844 compressed objects in 8 object streams.
  tagtree 0.1.1 reads 3,690 structure elements with no dangling text; with `--xref-index` 4
  elements, all 7,685 characters dangling, and a shell page.

So the counts are trusted on the terms the pre-registration set.

## Reported but not predicted
- **By producer family** (PDFs with object streams, of which with a wrong index): Adobe 351, 0;
  Word 280, 2; other Office 44, 0; other 12, 0; unknown 12, 0; generator 7, 0; scanner 6, 0;
  print-to-PDF 2, 0; LibreOffice 1, 0.
- **Word for Microsoft 365:** 137 of the 280 Word files with object streams name it, and 2 of them
  have wrong indexes; none of the other 143 Word files do. 135 Word for Microsoft 365 files have no
  wrong index at all.
- **Hybrid files** (a classic cross-reference table that points to a cross-reference stream): 272
  of the 715, including both files with wrong indexes; none of the 443 others has one.
- **Creation year** of the two files: 2025 for both. They come from two different city sites
  (by the private output).
- **How much of each file:** the median share of compressed objects with a wrong index, over the
  two files, is 0.863; in every one of their 10 object streams some index is wrong. Of pypdf's
  structure elements, 3,703 have a wrong index (735 and 2,968).
- **tagtree 0.1.1 on this crawl:** 50 of 775 leaky, 6.5% (4.9-8.4), and 31 with a shell page,
  4.0% (2.8-5.6). The corrected first run had 47 of 753 (6.2%) and 31 of 753 (4.1%); the
  corrected re-crawl of the cross-check 48 of 759 and 31.

## What this settles, and what it does not
- The cross-check's limit "only the two files were read again with tagtree 0.1.1" is now
  measured on a third crawl: of 775 eligible PDFs, only these two get a different tagtree record
  when objects are found by index instead of by number. A file with no wrong index (and no member
  missing from its header; there were none) reads the same both ways, by construction.
- Two files is too few to say what writes such indexes: Word for Microsoft 365 itself in some
  setting or version, or a later tool that rewrote the files without changing the Producer
  string. Both are hybrid files, but so are 270 files without wrong indexes. We have not tested
  any producer software.
- A reader that trusts the index (as pdfminer.six 20260107 does) misread 2 of 775 tagged PDFs
  here, but those two held more than half of the first run's dangling text. Rare files can still
  move totals.

## Limits, as written in advance and still true
- Sites and files change, so the sample is not exactly the 753 or the 759 of the earlier runs.
- Only PDFs the census crawl reaches, and only tagged PDFs with text; untagged PDFs were not
  checked, so this does not estimate how common wrong indexes are among all PDFs.
- The index check relies on pypdf's reading of the cross-reference stream and the header. It is
  the code that confirmed the two known files, and its unit tests use small PDFs with known
  indexes, but there is no second implementation here.
- Producer strings and URLs are kept in the private output only; the published rows carry the
  producer family and a yes/no for "Word for Microsoft 365".
- We have not contacted Microsoft, pdfminer.six or any government about these results; that
  waits for a person's review.
