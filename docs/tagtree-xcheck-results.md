# Results: does a second, independent reader agree with tagtree-reach?

Scored 2026-10-18 (UTC) by AI agents working for MV2 of Munim, Inc., against the checks in
[tagtree-xcheck-prereg.md](tagtree-xcheck-prereg.md), which were written before any data was
collected. Job `tagtree-xcheck-v1` ran in a sandbox on 2026-10-18 from 05:19 to 06:35 UTC; the
crawl finished well inside its 150-minute limit. Files: [results/xcheck-v1/](../results/xcheck-v1/)
(`summary.json`, `results.md`, `pairs-public.jsonl`, `code-sha256.txt`). `test_results_xcheck.py`
recomputes every number on this page from them and from [results/tagtree-v1/](../results/tagtree-v1/).
Apache-2.0 (code), CC BY 4.0 (this text and the data).

Machine checks only. Nothing here is a WCAG conformance judgment about any government, and no
government is named.

## What was done
The crawl of [tagtree-reach](tagtree-reach-results.md) was run again with the same seed: the same
600 sites, pages and per-site choice of PDFs. Each chosen PDF was read twice from the same bytes:
by tagtree 0.1.0 (pdfminer.six) and by a reader written for this test on pypdf, which walks the
structure tree and reads the content streams without any pdfminer code. tagtree's own walk was
also run on pdfminer's parse and compared, page by page, with the pypdf reader's walk.

## Sample
- 771 tagged PDFs were analysed by tagtree, all without error; 759 are eligible (50 or more
  characters on the first 3 pages, under the size cap), and the pypdf reader read all 759 without
  error. Neither walk failed on any of them.
- Sites and files change, so this is not exactly the first run's set of 753. Both PDFs on which
  the readers disagree (below) are in both runs, with identical tagtree records.

## The five checks
| Check | Agreement | Bar | Held? |
|---|---|---|---|
| X1: same number of structure elements reached from the root | 757 of 759 (99.7%) | 95% | Yes |
| X2: both walks reach exactly the same marked-content IDs | 757 of 759 (99.7%) | 95% | Yes |
| X3: "has dangling text" agrees | 757 of 759 (99.7%) | 95% | Yes |
| X4: "has a shell page" agrees | 758 of 759 (99.9%) | 90% | Yes |
| X5: "leaky" (5% or more unreachable) agrees | 757 of 759 (99.7%) | 90% | Yes |

**All five held.** As the pre-registration set out, this confirms tagtree's tree walk, its
dangling class and its shell and leaky flags on real files, with a second parser and a second walk.
It checks the parsing and the walk, not the definitions: both readers were written by the same
team from the same class definitions.

## The two disagreements
Both are PDFs saved from Word (URL hashes beginning `c8c71fae` and `5b10b0e8`; both records are
in `summary.json`). On them, tagtree reaches 0 and 4 structure elements from the root; the pypdf
reader reaches 809 and 3,690. tagtree counts 5,574 and 7,685 characters of dangling text, almost
all of the text on their first 3 pages, and gives the second a shell page; the pypdf reader finds
no dangling or untagged text in either.

X2 shows where the difference lies. tagtree's walk on pdfminer's parse and the pypdf reader's walk
follow the same rules, and on the other 757 PDFs they reach exactly the same marked-content IDs.
On these two they do not, so the two libraries read these files differently; tagtree's walk and
its classes are not what differs.

**Which reading is right is not settled yet.** In the first run only 10 of 280 Word PDFs were
leaky, so a full tree with nothing unreachable is the more plausible reading, but we do not treat
that as proof. One candidate cause, not confirmed: pdfminer.six takes an object out of a
compressed object stream by its position in the stream's token sequence (`objs[2n + index]` in
`pdfdocument.py`) and does not use the byte offset the stream lists for each object, so one
unexpected token would shift every later object in that stream. A diagnostic job
(`tagtree-diag-v1`) is queued. It reads both files again with a third parser (qpdf, through
pikepdf), compares object by object what pdfminer and pypdf return for every structure element,
and runs tagtree again with pdfminer reading object streams by offset.

## What it would change in the first run
Both files are among tagtree-reach's 753, and they weigh more than their number: they hold 13,259
of the first run's 24,047 dangling characters (55.1%). If pdfminer misreads them and the pypdf
reader is right, the first run's figures become:

- leaky: 47 of 753 (6.2%), not 49 (6.5%). P1 (10% or more) still fails.
- Word against the rest: Word 2.9% (8 of 280) against 8.2% (39 of 473): 5.4 points. P2 (10
  points) still fails.
- shell page: 31 of 753 (4.1%), not 32 (4.2%). P3 (2% or more) still holds.
- dangling text in 21 PDFs, not 23; 10,788 dangling characters, not 24,047; 90,929 of 2,566,660
  characters (3.5%) unreachable, not 104,188 (4.1%).
- structure tree with at most one element: 8 PDFs, not 9.

[tagtree-reach-results.md](tagtree-reach-results.md) keeps its numbers until the diagnosis is in,
with a note pointing here. If the diagnosis confirms a pdfminer misreading, tagtree 0.1.1 gets the
fix, both results pages say so, and the first run's numbers stay published next to the corrected
ones.

## The re-crawl itself (exploratory, no prediction)
tagtree finds 50 of 759 PDFs leaky, 6.6% (5.0-8.6), and 32 with a shell page, 4.2% (3.0-5.9),
against 49 and 32 of 753 in the first run. The leaky count includes both files above and the shell
count includes the second.

## Honest limits
- **Agreement per PDF does not bound error in the totals.** 757 of 759 is 99.7%, yet the two
  exceptions hold most of the first run's dangling characters. A misread file can look like a
  broken tree, which is exactly what this measure counts, so totals of unreachable text are the
  figures most exposed to parser errors.
- The pypdf reader counts bytes of shown strings, not characters, so its leak shares differ a
  little from tagtree's; the checks compare flags, decided by the point estimate.
- The same team wrote both readers from the same definitions, so a shared misunderstanding of
  the PDF format would not show up here.
- As in the first run: first 3 pages only; invisible text (such as an OCR layer) is counted; real
  text wrongly marked as an artifact is not detected.
