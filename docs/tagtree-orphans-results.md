# Results: does tagtree-reach find text cut off from the structure tree?

Scored 2026-10-18 (UTC) by AI agents working for MV2 of Munim, Inc., against
[tagtree-orphans-prereg.md](tagtree-orphans-prereg.md) and its change log, all written before any
data was collected. Job `tagtree-orphans-v1` ran in a sandbox on 2026-10-17 (22:49-22:57 UTC).
Files: [results/orphans-v1/](../results/orphans-v1/) (`summary.json`, `results.md`,
`code-sha256.txt`). `test_results_tagtree.py` recomputes every number here. Counts only: the PDF
attached to the issue is not republished. Apache-2.0 (code), CC BY 4.0 (this text).

## The case
[veraPDF issue #1629](https://github.com/veraPDF/veraPDF-library/issues/1629): on page 1 of the
attached file, marked-content IDs (MCIDs) 15, 16 and 19 are listed in the ParentTree, but their
structure elements "are not reachable from the StructTreeRoot via K arrays" (a veraPDF
contributor's words). The file's SHA-256 is recorded in `summary.json`.

## The three checks
| Check | Measured | Held? |
|---|---|---|
| O1: at least 1 dangling character | 383 | Yes |
| O2: the dangling MCIDs on page 1 are exactly the named ones that carry text | 15, 16, 19 (named: 15, 16, 19) | Yes |
| O3: per-MCID dangling counts add up to the record | 351 + 4 + 28 = 383 | Yes |

All three named MCIDs carry text, so none was untestable. Page 1 has 398 characters of text: 15
are reachable (MCID 0) and 383 are not, so 96.2% of the page is cut off from the tree.

## What this shows, in the words the pre-registration fixed
tagtree's dangling class has an outside positive control: on this file it found exactly the text
another person had identified as **not reachable from StructTreeRoot via K arrays**, and nothing
else. This is a statement about reachability from the root, the order a screen reader that walks
the tree follows. No PDF specification defines a direction for reading the structure tree, so this
does not say the file fails PDF/UA, and we do not call it non-conformant.

The reporter says veraPDF 1.30.2 does not report this fault. Re-checked on 2026-10-18: the issue
is still open (milestone 1.32.1, no linked fix), and the release notes of veraPDF 1.30.3
(2026-10-09, the latest release) do not mention it. We did not run veraPDF ourselves.

## Limits
- One file. It shows the dangling class can work; it does not measure how often tagtree is right.
- The answer comes from the issue's reporter and one contributor's comment, not from a standard
  test suite.
