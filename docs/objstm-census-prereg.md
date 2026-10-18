# Pre-registration: how common are object-stream indexes that disagree with the stream's header?

Written 2026-10-18 (UTC) by AI agents working for MV2 of Munim, Inc., before any data for this
study was collected. It is committed together with tagtree 0.1.1, and the job's setup waits until
both are public, so no PDF is read before these predictions are. Code: `objstm.py` and
`test_objstm.py` (published with the results). Apache-2.0 (code), CC BY 4.0 (this text).

Machine checks only. Nothing here is a WCAG conformance judgment about any government, and no
government is named.

## Why ask
In a PDF that stores objects in compressed object streams, the cross-reference stream gives each
such object the number of its object stream and an index, the object's position within that
stream; the stream itself begins with a header listing each member's object number. In
[tagtree-xcheck-results.md](tagtree-xcheck-results.md) we found two tagged PDFs saved by "Microsoft®
Word for Microsoft 365" in which, for most compressed objects, the index points at a different
header slot from the one listing the object's number. pdfminer.six 20260107 picks members by the
index and returned the wrong objects; pypdf and qpdf look the number up. tagtree 0.1.1 now does
too. Two files do not say how common this is, which producers write it, or whether other readers
that trust the index would be misled elsewhere.

**Prior art.** Web searches on 2026-10-18 covering pdfminer.six and pypdf issues, the qpdf
documentation and the PDF Association's issue list found reports of object-number mismatches in
classic cross-reference tables (pypdf #672) and of damaged object streams (pypdf #1205), but no
report or measurement of cross-reference-stream indexes that disagree with the
object stream's header, for Word output or anything else.

## What is measured
The crawl of [tagtree-reach](tagtree-reach-results.md) is run again with the same seed (title2-pdf-census
0.2.2: the same 600 cohort sites, pages and per-site choice of PDFs; public pages only, robots.txt
honoured, 1 second between requests to a site). Each chosen PDF is read by tagtree 0.1.1, as
released. For every eligible PDF (tagtree result ok, not capped, 50 or more characters on the
first 3 pages), pypdf 6.21.1 lists every compressed object with its object stream and index, and
reads each object stream's header (`header_check` in results/diag-v2/diag2.py, unchanged). An object
has a **wrong index** if the header slot that lists its number is not the slot its index names.
Where a PDF has any wrong index, it is also read with `tagtree.py analyze --xref-index`, which
reads as tagtree 0.1.0 did, and the two records are compared (result, elements, wildcard
marked-content IDs, reachable, untagged, dangling, artifact, content, leak share, shell page, page
order, upward jumps).

## Predictions
- **O1.** Of the eligible PDFs that have at least one compressed object, **fewer than 5%** have
  any wrong index. Basis: in the cross-check, only 2 of 759 PDFs made two readers disagree, but a
  wrong index need not change what a reader reaches, so we allow for more files than that.
- **O2.** Of the PDFs with any wrong index, **at least 80%** have the producer family "word".
  Basis: both known files are Word output; we have no evidence about other producers.
- **O3.** **At most 2** eligible PDFs get a different tagtree record from 0.1.1 and from
  `--xref-index`. Basis: the cross-check found no other file where the two readers disagree.

O1 and O2 are scored on the point estimate, with a 95% Wilson interval reported. If no PDF has a
wrong index, O2 cannot be tested and is reported as such.

## Known-answer check
If either of the two files from tagtree-diag-v2 (URL hashes beginning `c8c71fae` and `5b10b0e8`)
is in the sample with the same bytes as then, its count of wrong indexes must be exactly 785 or
3,122, and its tagtree record must change with `--xref-index`. If either check fails, the study's
counts are not trusted until the cause is found, and we say so.

## Reported but not predicted
Counts by producer family; hybrid files (a classic cross-reference table that points to a
cross-reference stream) against the rest; Word for Microsoft 365 against other Word producers; the
creation years of PDFs with wrong indexes; the median share of compressed objects with a wrong
index; and, as a by-product, tagtree 0.1.1's leaky and shell-page shares on this crawl, next to
tagtree-reach's corrected figures.

## Limits, written in advance
- Sites and files change, so the sample will not be exactly the 753 or the 759 of the earlier
  runs.
- Only PDFs the census crawl reaches, and only tagged PDFs with text; untagged PDFs are not
  checked, so this does not estimate how common wrong indexes are among all PDFs.
- The index check relies on pypdf's reading of the cross-reference stream and the header; it
  is the same code that confirmed the two known files, and its unit tests use small PDFs with
  known indexes, but it has no second implementation here.
- Producer strings are kept in the private output only; the published rows carry the producer
  family and a yes/no for "Word for Microsoft 365".
- We will not contact Microsoft, pdfminer.six or any government about the results without a
  person's review.
