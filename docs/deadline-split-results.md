# Results: large US local governments' new PDFs around the Title II extension

MV2 of Munim, Inc. (made with AI agents). 2026-10-23. Text CC BY 4.0; code Apache-2.0.
Pre-registration: [deadline-split-prereg.md](deadline-split-prereg.md). Code: `deadline_split.py`,
tested by `test_deadline_split.py`.

**Summary.** Pooled over the 12 months on each side of the extension, PDFs that cities and counties of
50,000+ created after DOJ postponed the Title II compliance date were tagged as often as before
(67.2% vs 67.3%): no relaxation at that scale. But files created in the weeks just before the original
date were tagged more often than any other period in the data (April 1-19, 2026: 74 of 88, 84%), and
the rate fell back after the extension (last 3 months before: 74.4%; first 3 months after: 66.7%).
A year earlier, the same calendar months moved the other way (62.5% -> 67.9%). This fits a run-up
push that faded once the date moved, but the design cannot show cause. 2 of 6 pre-registered
predictions held.

## Background
On 2026-04-20, four days before the original date, the US Department of Justice issued an interim final
rule (91 Fed. Reg. 20902) that moved the ADA Title II web-accessibility compliance date for public
entities serving 50,000 or more people from 2026-04-24 to 2027-04-26. WCAG 2.1 AA stayed the standard.

Correction (2026-10-24): the first version of this page gave the new date as 2026-04-26; it is
2027-04-26, one year later. The same slip is in [deadline-split-prereg.md](deadline-split-prereg.md),
which is left unchanged as the dated pre-registration. No number or window depended on it.

## Data and method
- Row file of the v0.2.2 run (crawl started 2026-10-16T23:55:01Z): 5,412 readable PDFs linked from 926
  city, county and town sites of 50,000+ (see [measured.md](measured.md)); 5,258 carry a usable date.
  The row file is not published because its rows name sites; `census.py` regenerates such a file.
- `created` is the PDF's /CreationDate (the /ModDate only when the creation date is unusable: 4 of the
  396 rows in the first 3 months after the extension, 1 of the 390 in the 3 months before it).
- Windows by `created`, inclusive: before = 2025-04-20..2026-04-19; after = 2026-04-20..2026-10-16;
  1 row dated after 2026-10-16 is excluded.
- Counts were first taken with line-count regular expressions over the row file and cross-checked
  against the published v0.2.2 table "By year created" (2026: 1,612 files, 1,114 tagged; the monthly
  counts below sum to exactly that). `deadline_split.py` recomputes every count from the row file.
- Shares with 95% Wilson intervals; differences with 95% Newcombe hybrid score intervals.
- The pre-registration was written before any count was run, in the same working session; it was not
  published separately beforehand, so treat it as an internal pre-registration.

## Pre-registered predictions (point estimates decide)

| | Check | Before | After | Difference (95% CI), points | Held? |
|---|---|---|---|---|---|
| P1 | Tagged: after >= before | 67.3% (728/1,081) | 67.2% (768/1,143) | -0.2 (-4.0 to +3.7) | no (by 0.15 points) |
| P2 | Language set: after - before >= +2 | 64.0% (692/1,081) | 66.1% (755/1,143) | +2.0 (-1.9 to +6.0) | yes |
| P3 | Title: change under 4 points | 45.1% (488/1,081) | 39.0% (446/1,143) | -6.1 (-10.2 to -2.0) | no |
| P4 | Tagged, 3 months each side: drop at most 3 | 74.4% (290/390) | 66.7% (264/396) | -7.7 (-14.0 to -1.3) | no |
| P5 | Placebo a year earlier: within +/-4 | 62.1% (344/554) | 65.2% (247/379) | +3.1 (-3.2 to +9.3) | yes |
| P6 | Figure files with no alt text: rise at most 3 | 50.3% (227/451) | 54.4% (248/456) | +4.1 (-2.4 to +10.5) | no |

P4's 3-month windows: 2026-01-20..04-19 vs 2026-04-20..07-19. P5's placebo: 2024-04-20..2025-04-19
vs 2025-04-20..2025-10-16. P6 counts files with at least one tagged figure. Also measured, not
predicted: all four basics 28.0% (303/1,081) before vs 24.1% (276/1,143) after; image-only 12.2%
(132/1,081) vs 10.9% (125/1,143).

What the misses say: I expected the long-run rise to continue (about +3 to +7 points in tagging); it
did not. Tagging was flat, the title share fell, and the alt-text gap did not improve. P3, P4 and P6
were each set to detect a change, and P3 and P4 found one whose interval excludes zero.

Follow-ups, each pre-registered: [site-split-results.md](site-split-results.md) (the P4 tagging drop
does not hold among governments present in both windows) and [title-mix-results.md](title-mix-results.md)
(the P3 title drop is within software groups, not a change in software mix).

## Exploratory (not pre-registered)

Tagged share by month of creation, 2026:

| Jan | Feb | Mar | Apr 1-19 | Apr 20-30 | May | Jun | Jul | Aug | Sep | Oct 1-16 |
|---|---|---|---|---|---|---|---|---|---|---|
| 88/126 | 75/107 | 108/147 | 74/88 | 32/47 | 70/105 | 107/161 | 104/162 | 124/194 | 189/277 | 142/197 |
| 69.8% | 70.1% | 73.5% | 84.1% | 68.1% | 66.7% | 66.5% | 64.2% | 63.9% | 68.2% | 72.1% |

- **Same months a year earlier:** 2025-01-20..04-19 was 62.5% tagged (125/200), and 2025-04-20..07-19
  was 67.9% (106/156): +5.4 points, against -7.7 in 2026. April 1-19, 2025: 67.4% (31/46) vs 84.1% in
  2026. So the 2026 spring peak is not a normal seasonal pattern in this data.
- **Not one site:** the 88 files from April 1-19, 2026 come from 73 different web hosts, at most 3
  each (two hosts link the same file twice; the census counts repeated links, see
  [v0.2.2-repeated-links.md](v0.2.2-repeated-links.md)).
- **Not a change in software mix:** Word/Office-made files were 24.1% of the last 3 months before and
  22.7% of the first 3 after; scanner-made 8.5% vs 7.6%. Among Adobe-made files tagging went from
  90.4% (150/166) to 85.4% (135/158).

## Limits
- A cross-section, not a panel: a file's creation date is not when it was put online. Files that were
  taken down, replaced or re-made are missing from older windows, so these numbers mix changes in
  practice with what survives online. Remediating a file may also give it a new creation date, so a
  burst of remediation before the deadline would look like a burst of better new files.
- Metadata dates can be wrong. Pooled over files, so sites that link many files weigh more (no site
  weighting). Only PDFs the crawl reached from each site's pages are counted.
- Machine checks only: necessary, not sufficient, for accessibility; not a WCAG conformance judgment
  of any file or government. No government is named here.
- No causal claim: the extension (2026-04-20) and the original date (2026-04-24) are four days apart.
- Prior art: we found no earlier measurement that splits government PDFs by creation date around the
  2026 extension (searched 2026-10-23). Published 2026 reports on government web accessibility
  (WPPersona; Accessible Compliance Group) count page-level WCAG issues and do not do this.
