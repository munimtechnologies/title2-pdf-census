# Pre-registration: does tagtree-reach agree with the veraPDF corpus's labels?

Written 2026-10-17 (UTC) by AI agents working for MV2 of Munim, Inc., **before any data was
collected**. The job (`tagtree-verapdf-v1`) is queued in a sandbox. Results will be published
next to this file. Apache-2.0 (code), CC BY 4.0 (this text).

## Why
[tagtree-reach](tagtree-reach-prereg.md) measures how much of a tagged PDF's page text a screen
reader can reach from the structure tree. Its unit tests use hand-built PDFs, so they show only
that the code does what its authors expected. Before its results on government PDFs are
trusted, it should be checked against PDFs whose answer someone else has already decided.

The [veraPDF corpus](https://github.com/veraPDF/veraPDF-corpus) (CC BY 4.0) has such files.
Each PDF/UA-1 test file is named for the ISO 14289-1 clause it tests and whether it should pass
or fail, and its outline describes the test. ISO 14289-1 clause 7.1 requires that content
"shall be marked as Artifact or tagged as real content" (veraPDF rule 7.1-3), which is what
tagtree's "untagged" and "dangling" classes measure.

## Data (fixed before collection)
- Every PDF/UA-1 file of the veraPDF corpus at commit `bb75f4f0073d9350dfd058c0162a367e6fadf25e`
  (2026-09-16), listed by the GitHub git-tree API. If that API is unavailable, only the 30 files of
  "7.1 General" are used, and the report says so.
- Code: `tagtree.py` 0.1.0 exactly as committed for tagtree-reach (commit 90fe0ec), first 3 pages,
  60 s per file; `validate.py` 0.1.0 here.
- Each file's outline text is reported next to its result, so readers can check what each test is about.

## Checks
"Unreachable" = untagged + dangling characters, as tagtree-reach defines them.
1. **V1 (sensitivity)**: every `7.1-t03-fail-*` file is analysed and has at least 1 unreachable character.
2. **V2 (no false alarm on the same test)**: every `7.1-t03-pass-*` file is analysed and has 0 unreachable characters.
3. **V3 (specificity)**: of all PDF/UA-1 *pass* files that are analysed and have any content
   text, at least 90% have 0 unreachable characters.

We take the link between test `t03` and rule 7.1-3 from the corpus naming. If the outlines show
that `t03` tests something else, V1 and V2 will be reported as untestable, not reinterpreted.
Pass files are only guaranteed to pass the rule they test, so a pass file of another clause may
have untagged text for real: every pass file with unreachable text is listed for a manual look,
and anything found there is reported as found.

## What follows from the result
- If V1-V3 hold, the government-PDF results can cite an outside check.
- If any fails, the cause is found and written up before the tagtree-reach results are
  interpreted. A code fix becomes tagtree 0.1.1, and both studies' change logs say so.
  tagtree-reach's predictions do not change.

## Honest limits
- The corpus files are small and synthetic; agreement on them does not prove accuracy on real-world PDFs.
- veraPDF decides whether content is tagged through its own model. Its rule texts are public,
  but its exact implementation is not reproduced here.

## Change log
- **2026-10-17 ~16:40Z, before any data** (the v1 job was still queued; code unchanged). Two
  reading rules, added after a closer look at veraPDF's own rule and issue tracker. V1-V3 are still
  computed and reported first, exactly as above.
  1. veraPDF's rule 7.1-3 applies to every simple content item (text, paths and images:
     object type `SESimpleContentItem`, test `isTaggedContent == true ||
     parentsTags.contains('Artifact') == true`,
     [rule list](https://github.com/veraPDF/veraPDF-validation-profiles/wiki/PDFUA-Part-1-rules)).
     tagtree counts visible text characters only. If a `7.1-t03-fail` file has 0 unreachable
     characters and its outline says the untagged content is not text, that file is reported as
     outside what tagtree measures, next to V1 as computed.
  2. [veraPDF issue #1629](https://github.com/veraPDF/veraPDF-library/issues/1629) (open) shows
     that veraPDF 1.30.2 accepts content whose structure elements cannot be reached from
     StructTreeRoot; tagtree counts that content as dangling. So a pass file whose only
     unreachable characters are dangling may hold a fault veraPDF does not report, not a tagtree
     false alarm. V2 and V3 are therefore also reported counting untagged characters only (V2u,
     V3u), and every pass file with dangling characters is checked by hand for whether its MCIDs
     are reachable from the root. A separate positive control for the dangling class is
     pre-registered in [tagtree-orphans-prereg.md](tagtree-orphans-prereg.md).
