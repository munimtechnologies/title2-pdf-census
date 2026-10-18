# Results: does tagtree-reach agree with the veraPDF corpus's labels?

Scored 2026-10-18 (UTC) by AI agents working for MV2 of Munim, Inc., against
[tagtree-verapdf-prereg.md](tagtree-verapdf-prereg.md) and its change log, all written before any
data was collected. Job `tagtree-verapdf-v1` ran in a sandbox on 2026-10-17 (21:20-21:28 UTC).
Files: [results/verapdf-v1/](../results/verapdf-v1/) (`summary.json`, `results.md`,
`results.jsonl`, `code-sha256.txt`). `test_results_tagtree.py` recomputes every number here.
The corpus is [veraPDF/veraPDF-corpus](https://github.com/veraPDF/veraPDF-corpus) at commit
`bb75f4f` (CC BY 4.0, by the veraPDF consortium); its file names and outline text are quoted in
the results files, and no PDF is republished. Apache-2.0 (code), CC BY 4.0 (this text).

## Data
296 PDF/UA-1 files, listed by the git tree API (so the 30-file fallback was not needed). 295 were
analysed; 1 has no structure tree (7.1-t11-fail-a, whose test is exactly that).

## The three checks, as computed
| Check | Measured | Held? |
|---|---|---|
| V1: every 7.1-t03 fail file has unreachable text | 1 of 2 | **No** |
| V2: no 7.1-t03 pass file has unreachable text | 0 of 2 | Yes |
| V3: 90%+ of pass files with text have none unreachable | 130 of 130 | Yes |

## V1, read by the rule written before the data
The miss is **7.1-t03-fail-a**. Its outline says "Image is not marked as Artifact or real
content": the untagged content is an image, and tagtree counts only text. Its text counts are
identical to its pass twin, 7.1-t03-pass-a (20 reachable, 13 artifact), so the only difference
between the two files is content tagtree does not measure. The change log of 2026-10-17 ~16:40Z
said such a file would be "reported as outside what tagtree measures, next to V1 as computed",
and that is how it is reported: V1 as computed did not hold; the one fail file whose untagged
content is text (7.1-t03-fail-b, "Content stream doesn't contain an Artifact tag") was found, with
12 untagged characters. Two fail files are a very small test.

## V2u and V3u (untagged characters only)
No file in the corpus has any dangling characters, pass or fail, so V2u and V3u are the same as V2
and V3, and no pass file needed a manual look. It also means **this corpus never exercises the
dangling class.** The separate known-answer test on veraPDF issue #1629
([tagtree-orphans-results.md](tagtree-orphans-results.md)) covers it.

## What else the corpus shows
- Of the 295 analysed files, only one has any unreachable text: 7.1-t03-fail-b. No file testing
  another clause set off a false alarm, though those files were not required to be clean.
- **A blind spot, stated plainly:** 7.1-t02-fail-a ("Note is present in Artifact") hides real text
  as an artifact (196 artifact characters). tagtree treats artifacts as decoration, so it reports
  nothing wrong there. Text wrongly marked as an artifact is outside what tagtree measures.

## What follows
The pre-registration said that if all checks hold, the government-PDF results can cite an outside
check. V2 and V3 held, and V1 failed only for content outside tagtree's scope, as the reading rule
foresaw. The government-PDF results ([tagtree-reach-results.md](tagtree-reach-results.md)) cite
this check with that caveat. No code change was needed, so tagtree stays at 0.1.0.

## Limits
- The corpus files are small and synthetic; agreement on them does not prove accuracy on
  real-world PDFs.
- The labels come from the corpus files' names and outlines. No veraPDF version was run here.
