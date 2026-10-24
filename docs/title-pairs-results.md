# Results: does the post-extension drop in PDF titles hold within the same governments?

MV2 of Munim, Inc. (made with AI agents). 2026-10-24. Text CC BY 4.0; code Apache-2.0.
Pre-registration: [title-pairs-prereg.md](title-pairs-prereg.md). Code: `title_pairs.py`, tested by
`test_title_pairs.py`. Earlier steps: [deadline-split-results.md](deadline-split-results.md) (the pooled
drop), [site-split-results.md](site-split-results.md) (the same question for tagging) and
[title-mix-results.md](title-mix-results.md) (titles within software groups).

**Summary.** PDFs that US cities and counties of 50,000+ created in the six months after DOJ postponed
the ADA Title II compliance date carried a document title less often than PDFs from the year before
(39.0% vs 45.1%, −6.1 points, pooled over files). Counting each government once, the drop shrinks to
−4.8 points (95% interval −10.0 to +0.5). Within the 329 governments with files on both sides, the
average change is −3.7 points (−9.5 to +2.1): 93 governments went up, 103 went down and 133 did not
change (sign test p = 0.52). In the three months either side of the extension, the 102 governments with
files on both sides show no drop at all (+0.8 points). Among the 31 governments with at least 3 files on
each side, titles rose on average (+3.9). **5 of 6** pre-registered predictions held. The one that
failed (U2) is the main paired test: −3.7 is past the −3 point line we set. So a modest within-government
drop over the longer windows cannot be ruled out, but it is not established either. Most of the pooled
drop, and all of it in the three-month windows, looks like a change in which governments posted. That is
the same pattern found for tagging.

## Background
On 2026-04-20, four days before the original date, the US Department of Justice issued an interim final
rule (91 Fed. Reg. 20902) moving the Title II web-accessibility compliance date for public entities
serving 50,000 or more from 2026-04-24 to 2027-04-26. A document title is a WCAG 2.4.2 / PDF/UA basic.
The title-mix study showed that the title drop is not a change in software mix (−5.3 of −6.1 points was
within the same software groups), but noted that "same software" is not "same government". This study
holds the government fixed.

## Data and method
- The same `title2-pdf-census` v0.2.2 row file (crawl started 2026-10-16T23:55:01Z): rows with `result`
  "ok" and a `created` date, repeated links kept as in the pooled analysis. `title` = non-blank /Title in
  the document information dictionary (`census.py` `analyze_pdf`). Site = `qid` (one Wikidata item per
  city, county or town government). The row file is not published because its rows name sites;
  `census.py` regenerates such a file.
- Windows by `created`, inclusive: PRE 2025-04-20..2026-04-19, POST 2026-04-20..2026-10-16; R3
  2026-01-20..04-19, A3 2026-04-20..07-19; placebo PRE0 2024-04-20..2025-04-19, POST0
  2025-04-20..2025-10-16.
- Site-weighted: each site's title share in a window, averaged over sites with at least one file there;
  after minus before, Welch normal-approximation 95% interval. Paired: sites with files in both windows,
  per-site change in title share, exact two-sided sign test (ties dropped), mean with a normal 95%
  interval; also for sites with at least 3 files in each window.
- Order of events: the pre-registration and `title_pairs.py` were committed at 2026-10-24 03:47:24Z
  (68a9822). A separate local job then ran that script on the row file and finished at 03:48:52Z; this
  write-up grades its saved output, which no one read before this session. The pre-registration's
  header says "Written ~02:00Z": that is when it was drafted. It was committed unchanged later, and the
  commit time is the reliable one. Treat it as an internal pre-registration.

**Totals reconcile to the published ones** (titled/files): PRE 488/1,081, POST 446/1,143, R3 185/390,
A3 157/396, PRE0 246/554, POST0 177/379. Sites with files: PRE 556, POST 525, R3 265, A3 252, PRE0 348,
POST0 270.

## Results (points; 95% intervals in brackets)

| Comparison | Pooled over files | Site-weighted | Paired sites | Up / down / same | Sign p | Paired mean |
|---|---|---|---|---|---|---|
| PRE → POST | −6.1 | −4.8 [−10.0, +0.5] | 329 | 93 / 103 / 133 | 0.52 | −3.7 [−9.5, +2.1] |
| R3 → A3 | −7.8 | −7.7 [−15.8, +0.4] | 102 | 26 / 24 / 52 | 0.89 | +0.8 [−10.2, +11.9] |
| Placebo PRE0 → POST0 | +2.3 | −1.3 [−8.8, +6.1] | 110 | 27 / 27 / 56 | 1.00 | −0.9 [−12.0, +10.2] |
| PRE → POST, ≥ 3 files each side | | | 31 | 14 / 10 / 7 | 0.54 | +3.9 [−8.2, +16.1] |

Pooled changes are from the published counts (488/1,081 → 446/1,143; 185/390 → 157/396; 246/554 →
177/379).

## Pre-registered predictions (point estimates decide; intervals reported)

| | Check | Result | Held? |
|---|---|---|---|
| U1 | Site-weighted PRE→POST at most −3 points | −4.8 | yes |
| U2 | Paired PRE→POST mean above −3 points | −3.7 | **no** |
| U3 | Paired PRE→POST sign test p ≥ 0.05 | 0.52 | yes |
| U4 | Paired R3→A3 mean above −3 points | +0.8 | yes |
| U5 | Paired PRE→POST mean (≥ 3 files each side) above −3 points | +3.9 | yes |
| U6 | Placebo site-weighted PRE0→POST0 above −3 points | −1.3 | yes |

## Plain reading
- **With one vote per government, the drop is smaller and no longer clear.** Site-weighted, the PRE→POST
  drop is −4.8 points and its interval just reaches zero. The three-month comparison keeps its size
  (−7.7) but its interval also reaches zero.
- **Within the same governments, the picture splits by window.** Over the year-before vs six-months-after
  windows, the average government's title share fell 3.7 points. That is past our −3 line, so U2 failed,
  and it is about 60% of the pooled drop. But slightly more governments went down than up (103 vs 93), the
  sign test is far from significant, and the interval includes zero. In the three months either side, the
  102 governments with files on both sides show no drop (+0.8; 26 up, 24 down). The 31 governments with
  at least 3 files on each side, whose per-site shares are least noisy, went up (+3.9).
- **Same pattern as tagging.** [site-split-results.md](site-split-results.md) found that the 3-month
  tagging drop (−7.7 pooled, −5.5 site-weighted) became −1.3 within the 102 governments with files on both
  sides (25 up, 20 down). Titles behave the same way in the same windows: a drop when each government
  counts once (titles −7.7, tagging −5.5), and roughly nothing within governments (titles +0.8, tagging
  −1.3). One reading fits both this and the title-mix result. The governments whose files make up more
  of the later window use the same common software (Word, Acrobat) but leave titles off more often.
  Individual governments did not clearly change their own practice. This reading is untested, not a
  finding.
- **No such drop a year earlier.** The placebo split is near zero both site-weighted (−1.3) and paired
  (−0.9; 27 up, 27 down).

## Limits
- Many governments have only one or two files in a window, so per-site shares are coarse (0%, 50%,
  100%), and 133 of the 329 paired governments did not change at all. The normal intervals are rough;
  the sign test is the more robust paired check. Nothing here is significant either way, so "no clear
  within-government drop" is a weak claim, not proof of no change.
- Pairing keeps only governments that posted in both windows, which may select steadier ones. The
  12-month PRE window is twice as long as POST, so more governments appear in PRE (556 vs 525 overall).
- The −3 point line was a pre-registered convention, not a significance threshold. U2 failed by 0.7
  points; we report it as failed.
- Same limits as the parent result: a cross-section, not a panel (creation date is not posting date;
  survivorship; remediation can reset a creation date); metadata dates can be wrong; machine checks only
  (necessary, not sufficient, for accessibility; not a WCAG conformance judgment). "Titled" means a title
  exists, not that it is meaningful. No causal claim (the extension on 2026-04-20 and the original date on
  2026-04-24 are four days apart). No government is named.
- Prior art: a search on 2026-10-24 found no earlier measurement of government PDF titles paired by
  government around the 2026 Title II extension. Published 2026 reports count page-level WCAG issues;
  an August 2026 vendor page says document gaps "didn't move with the deadline" but gives no data.
