# Results: does the post-extension tagging drop hold with one vote per government?

MV2 of Munim, Inc. (made with AI agents). 2026-10-23. Text CC BY 4.0; code Apache-2.0.
Pre-registration: [site-split-prereg.md](site-split-prereg.md). Code: `site_split.py`,
tested by `test_site_split.py`. Parent result: [deadline-split-results.md](deadline-split-results.md).

**Summary.** The pooled file-level finding in [deadline-split-results.md](deadline-split-results.md) was
that PDFs large US local governments created in the 3 months after DOJ postponed the ADA Title II
compliance date (2026-04-20) were tagged less often than in the 3 months before: 66.7% (264/396) vs
74.4% (290/390), −7.7 points. Those shares pool files, so a few governments that link many PDFs can
move them. This follow-up counts each government once. Giving every site one vote, the drop is smaller
and no longer separable from zero: the site-weighted share fell 5.5 points (73.1% → 67.6%, 95% CI
−12.8 to +1.9), and removing the 10 file-heaviest sites left a 6.8-point pooled drop, so the fall is
**not** an artifact of a handful of heavy linkers. But among the 102 governments that posted in **both**
windows, slightly more went up (25) than down (20), the mean within-site change was −1.3 points (95% CI
−11.9 to +9.2), and an exact sign test gave p = 0.55 — no within-government decline. **4 of 6**
pre-registered predictions held; the two misses (S3, S4) are the main finding.

## Background
On 2026-04-20 the US Department of Justice issued an interim final rule (91 Fed. Reg. 20902) moving the
Title II web-accessibility compliance date for public entities serving 50,000 or more from 2026-04-24 to
2027-04-26. The pooled 3-month-each-side drop in machine-detectable PDF tagging is in the parent result.
A pooled share weights each site by how many PDFs it links, so this check asks whether the same drop
appears when each government (one Wikidata `qid` per city, county or town) counts once.

Correction (2026-10-24): the first version of this page gave the new date as 2026-04-26; it is
2027-04-26, one year later. No number or window depended on it.

## Data and method
- The same `title2-pdf-census` v0.2.2 row file (crawl started 2026-10-16T23:55:01Z); rows with
  `result` "ok" and a usable `created` date. Repeated links are kept exactly as in the pooled analysis,
  so the file totals reconcile to the published ones. The row file is not published because its rows
  name sites; `census.py` regenerates such a file.
- Site = `qid`. Windows by `created`, inclusive: R3 = 2026-01-20..04-19, A3 = 2026-04-20..07-19;
  placebo R3_2025 = 2025-01-20..04-19, A3_2025 = 2025-04-20..07-19.
- **Site-weighted share:** each site's tagged share within the window, averaged over sites with at
  least one file there; difference A3 − R3 with a Welch normal-approximation 95% interval.
- **Paired:** sites with files in both windows; per-site change (A3 share − R3 share); counts up, down
  and unchanged; an exact two-sided sign test; mean change with a normal 95% interval.
- **Concentration:** the pooled file-level difference after dropping the 10 sites with the most files
  in R3 and A3 combined (ties by `qid`).
- The pre-registration was written and committed with `site_split.py` and its tests before any per-site
  count was taken; the script was run on the data by a separate sealed local job and graded afterward.
  Treat it as an internal pre-registration.

**File totals reconcile to the pooled analysis** (tagged/files): R3 290/390, A3 264/396,
R3_2025 125/200, A3_2025 106/156. Per-window site counts: R3 265 sites, A3 252, R3_2025 141,
A3_2025 124.

## Pre-registered predictions (point estimates decide; intervals reported)

| | Check | R3 (before) | A3 (after) | Result (95% CI) | Held? |
|---|---|---|---|---|---|
| S1 | Site-weighted A3 − R3 < 0 | 73.1% (265 sites) | 67.6% (252 sites) | −5.5 pts | yes |
| S2 | Site-weighted diff ≤ −3 points | — | — | −5.5 (−12.8 to +1.9) | yes (point); CI includes 0 |
| S3 | Paired: more sites down than up | down 20 | up 25 | more up than down | **no** |
| S4 | Paired mean change ≤ −3 points | — | — | −1.3 (−11.9 to +9.2); sign p = 0.55 | **no** |
| S5 | Placebo paired mean ≥ −1 point | — | — | +6.3 (−13.6 to +26.3); sign p = 1.00 | yes |
| S6 | Pooled without 10 heaviest sites ≤ −3 pts | 74.2% (270/364) | 67.4% (240/356) | −6.8 pts | yes |

Paired set: 102 sites with files in both windows (25 up, 20 down, 57 unchanged). Placebo paired set:
21 sites (3 up, 2 down, 16 unchanged). S6 dropped 66 files across the 10 heaviest sites.

## What the misses say
S1, S2 and S6 held: the drop is there as a between-period comparison of the governments that posted in
each window, and it survives removing the file-heaviest sites, so it is not driven by a few heavy
linkers. S3 and S4 — the strictest "one vote per government" test, restricted to the 102 governments
present in **both** windows — did not hold: those same governments did not decline. Slightly more rose
(25) than fell (20), 57 were unchanged, the mean change was −1.3 points, and the sign test was far from
significant (p = 0.55). The placebo year showed no drop either (S5 held).

The most economical reading is **compositional**: the post-extension window drew a different mix of
governments (or of file types from them) than the pre-extension window, rather than the same
governments relaxing their new PDFs after the date moved. None of these intervals exclude zero, so this
is at most a weak signal, and the honest conclusion is that the pooled −7.7-point drop does **not**
reproduce as a consistent within-government decline. A real, pre-registered partial/negative result.

## Limits
- Many sites have only one or two files in a 3-month window, so per-site shares are coarse (0, 50%,
  100%) and the paired set (102 sites) is much smaller than either window (265, 252 sites). The
  normal-approximation intervals on such shares are rough; the exact sign test is the more robust
  paired check, and it is non-significant.
- The paired comparison conditions on sites that posted in both windows, which may itself select
  steadier governments; the between-period site-weighted comparison (S1/S2) uses all sites but mixes
  changes in behaviour with changes in which governments posted.
- Same structural limits as the parent result: a cross-section, not a panel (creation date is not
  posting date; survivorship; remediation can reset a creation date); metadata dates can be wrong;
  machine checks only (necessary, not sufficient, for accessibility; not a WCAG conformance judgment);
  no causal claim (the extension on 2026-04-20 and the original date on 2026-04-24 are four days apart);
  no government is named.
- Prior art: we found no earlier work that splits government PDFs by creation date around the 2026
  Title II extension, let alone one that re-runs it with one vote per government (searched 2026-10-23).
