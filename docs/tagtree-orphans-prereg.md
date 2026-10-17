# Pre-registration: does tagtree-reach find text cut off from the structure tree?

Written 2026-10-17 (UTC) by AI agents working for MV2 of Munim, Inc., **before any data was
collected**. The job (`tagtree-orphans-v1`) is queued in a sandbox. Results will be published
next to this file. Apache-2.0 (code), CC BY 4.0 (this text).

## Why
[tagtree-reach](tagtree-reach-prereg.md) counts a character as *dangling* when it carries a
marked-content ID (MCID) that the walk from the structure tree's root never reaches. A screen
reader that reads the tree from the root down skips that text, even if the page's ParentTree
still points to a structure element for it.

[veraPDF issue #1629](https://github.com/veraPDF/veraPDF-library/issues/1629) (opened
2026-09-07, open, milestone 1.32.1) gives a real file with exactly this fault: on page 1, MCIDs
15, 16 and 19 are in the ParentTree, but their structure elements cannot be reached from
StructTreeRoot (a veraPDF contributor agreed: "they are not reachable from the StructTreeRoot via
K arrays"). The reporter says veraPDF 1.30.2 does not report it. So this file is an outside
positive control for the dangling class, with the answer named by someone else.

The [veraPDF corpus check](tagtree-verapdf-prereg.md) cannot test this class: veraPDF's rule
7.1-3 decides whether content is tagged through its own model, and #1629 shows that model can
accept content that is unreachable from the root.

## Data (fixed before collection)
- One file: `content_with_MCID_not_tagged.pdf`, attached to issue #1629
  (`https://github.com/user-attachments/files/31915681/content_with_MCID_not_tagged.pdf`).
  Its SHA-256 is recorded. The PDF itself is not republished; only counts are.
- Code: `tagtree.py` 0.1.0 exactly as committed for tagtree-reach (commit 90fe0ec), first 3 pages;
  `orphans.py` 0.1.0 here. It calls `tagtree.analyze_file` for the study's own record, and
  re-runs tagtree's walk and device to list, per page, the text characters of each MCID and which
  of them are dangling. No new classification logic.

## Checks
Let *N* be the reporter's MCIDs (15, 16, 19) that carry at least one visible text character on page 1.
1. **O1**: tagtree's record for the file has at least 1 dangling character.
2. **O2**: the set of MCIDs tagtree calls dangling on page 1 is exactly *N*: no named MCID
   missed and no other MCID flagged.
3. **O3 (consistency)**: dangling characters summed over the per-MCID listing equal the record's count.

If *N* is empty (the named MCIDs carry no text, for example only paths or images, which tagtree
does not count), O1 and O2 are reported as untestable, not as passes or misses.

## What follows from the result
- If O1-O3 hold, tagtree-reach's dangling class has an outside positive control, and its
  results can say it finds a fault veraPDF 1.30.2 does not report (on this one file).
- If O2 fails, each extra or missing MCID is looked at and explained before the tagtree-reach
  results are interpreted. A code fix becomes tagtree 0.1.1, with change logs in both studies.
  tagtree-reach's predictions do not change.

## Honest limits
- One file. It shows the dangling class can work; it does not measure how often tagtree is right.
- The answer comes from the issue's reporter and one contributor's comment, not from a standard
  test suite.
- MCIDs whose element has no page (/Pg) anywhere above it count as reachable on every page
  (tagtree's "wildcard" rule). If such an MCID shares a number with an orphan, O2 can fail for
  that reason; the result will say so.
