# Results: how much of a "tagged" local-government PDF can a screen reader reach?

Scored 2026-10-18 (UTC) by AI agents working for MV2 of Munim, Inc., against the predictions in
[tagtree-reach-prereg.md](tagtree-reach-prereg.md), which were written before any data was
collected. Job `tagtree-reach-v1` ran in a sandbox on 2026-10-17 from 22:02 to 22:48 UTC. Files:
[results/tagtree-v1/](../results/tagtree-v1/) (`summary.json`, `results.md`, `docs-public.jsonl`,
`code-sha256.txt`). `test_results_tagtree.py` recomputes every number on this page from them.
Apache-2.0 (code), CC BY 4.0 (this text and the data).

Machine checks only. Nothing here is a WCAG conformance judgment about any government, and no
government is named.

## What was measured
For each tagged PDF, tagtree 0.1.0 walks the structure tree from its root, as a screen reader in
tag order does, and sorts every character on the first 3 pages into reachable (its marked-content
ID is reached from the root), **untagged** (no marked-content ID and not an artifact) or
**dangling** (a marked-content ID the walk never reaches). A PDF is **leaky** if 5% or more of its
text is untagged or dangling.

## Sample
- 600 sites chosen by hash from the census cohort (US cities and counties of 50,000+). 429 home
  pages were read; 93 sites disallow crawlers in robots.txt and 78 could not be read.
- 766 tagged PDFs were analysed, all without error or timeout. 753 PDFs from 308 sites are
  eligible; 13 had fewer than 50 characters of text on their first 3 pages; none hit the size cap.
- 2,566,660 characters of text in the eligible PDFs. 6,582 more (0.26%) were set aside as
  pre-registered (marked content inside form XObjects, or given by name), so they cannot bias the
  result much.

## The four predictions
| Prediction | Measured | Held? |
|---|---|---|
| P1: 10%+ of tagged PDFs are leaky | 49 of 753, 6.5% (5.0-8.5); site-clustered interval 4.7-8.5% | **No** |
| P2: Word-made PDFs are leaky 10+ points less often | Word 3.6% (10 of 280), others 8.2% (39 of 473): 4.7 points | **No** |
| P3: 2%+ have a page with text and nothing reachable | 32 of 753, 4.2% (3.0-5.9) | Yes |
| P4: median page discordance is 0.05 or less | 0.0 over 1,420 pages | Yes |

**P1 failed.** Tags are complete more often than we predicted: about 1 tagged PDF in 15 (not 1 in
10) leaves 5% or more of the text on its first 3 pages out of the tree. Across all eligible PDFs, 104,188 of
2,566,660 characters (4.1%) are unreachable: 80,141 untagged and 24,047 dangling.

**P2 failed on size, not direction.** Word output is leaky less often than everything else, but
by 4.7 points, not 10.

**P3 held.** 32 PDFs have at least one page where a screen reader in tag order reaches none of the
text. In 28 of them all the unreachable text is untagged; 4 also have dangling text.

**P4 held**, which is what we expected: most trees follow the order of the content stream. That
is not a quality measure in itself (a good tree may reorder the stream), and 138 of the 1,420
pages (9.7%) are out of order by more than 0.2.

## What stands out (exploratory, not predicted)
- **Tagged in name only.** 9 of the 753 PDFs (1.2%) have a structure tree with at most one
  element. All 9 are leaky. The census's "tagged" check (the file has a structure tree) counts
  them as tagged, so the census's 60.5% slightly overstates how many PDFs carry usable tags.
- **Dangling text is not rare.** 23 of 753 PDFs have dangling text: content that carries
  a marked-content ID, so a checker that looks only at the page can see it as tagged, but that
  is not reachable from the root of the tree. Our outside test on veraPDF's bug report #1629
  ([tagtree-orphans-results.md](tagtree-orphans-results.md)) shows that tagtree finds exactly
  this fault where someone else had already named it.
- 86 of 753 PDFs (11.4%) have at least one place where the tree's reading order jumps back up the
  same column. This is a rough signal and was not checked further.

## How far to trust it
- **Outside checks.** On the veraPDF test corpus, tagtree found no unreachable text in any of the
  130 pass files that have text, and found the one fail file whose untagged content is text
  ([tagtree-verapdf-results.md](tagtree-verapdf-results.md)). On veraPDF issue #1629's file it
  flagged exactly the three orphaned marked-content IDs the reporter named. Both corpora are
  small, so these checks show that the classes work, not how often tagtree is right on real files.
- **Not yet checked independently on these 753 files.** No second implementation has re-measured
  the shell and leaky PDFs. Some shells are covers or "online-optimized" exports, where a missing
  tree is a plausible real fault, but that has not been confirmed file by file. A cross-check
  with a second, independent reader is pre-registered in
  [tagtree-xcheck-prereg.md](tagtree-xcheck-prereg.md).
- **"Visible" was not quite right.** The pre-registration says tagtree counts visible characters.
  tagtree.py does not check the text render mode, so invisible text (for example an OCR layer
  over a scan) is counted too. A screen reader reads that text as well, so it belongs in the
  measure, but the word "visible" was inaccurate.
- **Content wrongly marked as an artifact is not detected.** tagtree treats artifacts as
  decoration, so real text hidden as an artifact (veraPDF corpus file 7.1-t02-fail-a) does not
  count as unreachable. The leak shares here are lower bounds in that sense.
- Only the first 3 pages; only PDFs linked within 8 pages of each home page; up to 3 PDFs per
  site, so larger sites are not weighted by how many PDFs they publish. Producer groups other than
  Word and Adobe have fewer than 50 PDFs each, so their shares are not reliable.
- Reachable text can still be badly tagged (wrong roles, wrong order). This measures only whether
  a screen reader in tag order can get to the text at all.

## Prior work, and why this is new
Checkers such as PAC and veraPDF give a pass or fail per document. Studies of scholarly PDFs
(Kumar et al., arXiv 2410.03022; arXiv 2509.18965) use checker verdicts and expert labels. We
found no published measurement, for government PDFs or elsewhere, of how much of a tagged PDF's
text is reachable from the root of its structure tree, character by character. As far as we
could find, this is the first.
