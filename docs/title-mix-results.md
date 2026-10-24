# Results: is the post-extension drop in PDF titles a change in software or in practice?

MV2 of Munim, Inc. (made with AI agents). 2026-10-24. Text CC BY 4.0; code Apache-2.0.
Pre-registration: [title-mix-prereg.md](title-mix-prereg.md). Code: `title_mix.py`, tested by
`test_title_mix.py`. Parent result: [deadline-split-results.md](deadline-split-results.md).

**Summary.** PDFs that US cities and counties of 50,000+ created in the six months after DOJ postponed
the ADA Title II compliance date carried a document title less often than PDFs from the year before:
39.0% (446/1,143) vs 45.1% (488/1,081), −6.1 points. Splitting that change by the software that made
each file, almost none of it is a change in software mix (−0.8 points). It is a change **within** the
same software groups (−5.3 points; site-bootstrap 95% interval −10.3 to −0.4). It is concentrated in
the two largest groups: Office-made files fell from 39.1% to 29.4% titled, Adobe-made files from 43.3%
to 36.0%. The same split one year earlier shows no such within-group drop (+0.3 points). **6 of 6**
pre-registered predictions held. "Within the same software" does not mean "the same governments": see
Limits.

## Background
On 2026-04-20, four days before the original date, the US Department of Justice issued an interim final
rule (91 Fed. Reg. 20902) moving the Title II web-accessibility compliance date for public entities
serving 50,000 or more from 2026-04-24 to 2027-04-26. A document title is a WCAG 2.4.2 / PDF/UA basic. In
a PDF it is mostly written by the software that makes the file, so a drop in titles could come from
governments switching software (mix) or from the same software being used differently (practice).

## Data and method
- The same `title2-pdf-census` v0.2.2 row file (crawl started 2026-10-16T23:55:01Z): rows with `result`
  "ok" and a `created` date, repeated links kept as in the pooled analysis. `title` = non-blank /Title in
  the document information dictionary (`census.py` `analyze_pdf`). The row file is not published because
  its rows name sites; `census.py` regenerates such a file.
- Windows by `created`, inclusive: PRE 2025-04-20..2026-04-19, POST 2026-04-20..2026-10-16; R3
  2026-01-20..04-19, A3 2026-04-20..07-19; placebo PRE0 2024-04-20..2025-04-19, POST0
  2025-04-20..2025-10-16.
- Six software groups from `producer_family`, fixed before counting: office (word + office-other),
  adobe, print-to-pdf, scanner, unknown (no Producer or Creator), rest (libreoffice, google-docs,
  generator, other).
- Within part = sum over groups of (group's share of before-window files) × (its change in title
  share); mix part = total change − within. Site bootstrap: 2,000 resamples of governments (`qid`), seed
  20261024, percentile interval.
- The pre-registration and `title_mix.py` were committed first (037b987, 2026-10-24 00:23:31Z). A
  separate local job then ran the script on the row file (it finished at 00:29Z); this write-up grades
  its saved output. The pre-registration's header says "~00:35Z"; that is a slip, and the commit time is
  the reliable one. Treat it as an internal pre-registration.

**Totals reconcile to the published ones** (titled/files): PRE 488/1,081, POST 446/1,143, R3 185/390,
A3 157/396, PRE0 246/554, POST0 177/379.

## Titles by software group (titled/files, share)

| Group | PRE | POST | Change | R3 | A3 | PRE0 | POST0 |
|---|---|---|---|---|---|---|---|
| office | 108/276 (39.1%) | 89/303 (29.4%) | −9.8 | 39/94 (41.5%) | 26/90 (28.9%) | 41/116 (35.3%) | 40/104 (38.5%) |
| adobe | 177/409 (43.3%) | 155/431 (36.0%) | −7.3 | 75/166 (45.2%) | 57/158 (36.1%) | 97/226 (42.9%) | 60/130 (46.2%) |
| print-to-pdf | 67/73 (91.8%) | 58/68 (85.3%) | −6.5 | 19/21 (90.5%) | 18/19 (94.7%) | 27/34 (79.4%) | 32/35 (91.4%) |
| scanner | 17/85 (20.0%) | 21/95 (22.1%) | +2.1 | 6/33 (18.2%) | 6/30 (20.0%) | 20/60 (33.3%) | 4/25 (16.0%) |
| unknown | 8/37 (21.6%) | 9/44 (20.5%) | −1.2 | 5/13 (38.5%) | 4/26 (15.4%) | 2/11 (18.2%) | 1/10 (10.0%) |
| rest | 111/201 (55.2%) | 114/202 (56.4%) | +1.2 | 41/63 (65.1%) | 46/73 (63.0%) | 59/107 (55.1%) | 40/75 (53.3%) |
| **all** | 488/1,081 (45.1%) | 446/1,143 (39.0%) | −6.1 | 185/390 (47.4%) | 157/396 (39.6%) | 246/554 (44.4%) | 177/379 (46.7%) |

The software mix barely moved: office was 25.5% of PRE files and 26.5% of POST, adobe 37.8% and 37.7%,
scanner 7.9% and 8.3%.

## Decompositions (points)

| Comparison | Change | Within (same software) | Mix (different software) |
|---|---|---|---|
| PRE → POST | −6.1 | −5.3 | −0.8 |
| R3 → A3 | −7.8 | −7.6 | −0.2 |
| Placebo PRE0 → POST0 | +2.3 | +0.3 | +2.0 |

## Pre-registered predictions (point estimates decide; intervals reported)

| | Check | Result | Held? |
|---|---|---|---|
| T1 | PRE→POST mix part smaller than 2 points either way | −0.8 | yes |
| T2 | PRE→POST within part at most −3 points | −5.3 | yes |
| T3 | R3→A3 within part at most −3 points | −7.6 | yes |
| T4 | Of the 3 largest PRE groups, at least 2 lower in POST | adobe and office lower; rest higher (+1.2) | yes |
| T5 | Placebo PRE0→POST0 within part at least −2 points | +0.3 | yes |
| T6 | Site-bootstrap interval of PRE→POST within part wholly below 0 | −10.3 to −0.4 (752 sites) | yes, narrowly |

T6 held by less than half a point at the upper end, so the within-group drop is distinguishable from
zero at the site level, but not by much.

## Exploratory (not pre-registered)
- **Where the within part comes from.** Office-made files contribute −2.5 points and Adobe-made files
  −2.8 of the −5.3; print-to-pdf −0.4; scanner, unknown and rest together +0.4.
- **Other reference weights.** Using after-window (POST) weights instead of before-window weights, the
  split is within −5.4, mix −0.7 (worked from the table above). The conclusion does not depend on the
  reference choice.
- **Print drivers do write titles.** The pre-registration assumed that print drivers usually write no
  title. In this data print-to-pdf files had a title 92% of the time before and 85% after. The census
  stores only whether a title exists, not its text, so a print-job name such as a file name counts as a
  title. "Titled" here is a machine check, not a judgment that the title is meaningful.
- **The placebo year moved through mix.** A year earlier the title share rose 2.3 points, almost all of
  it from mix (+2.0), the opposite of the 2026 pattern.

## Limits
- **Within software is not within government.** This split holds software constant, not the
  government. [site-split-results.md](site-split-results.md) found that the parallel drop in *tagging*
  vanished among governments present in both windows, so it was more likely a change in which
  governments posted. The same could be true here: different governments using Word or Acrobat with
  different templates or settings would show up as a "within" change. A paired title check by
  government was not done.
- Six groups only. Office and adobe each hide many versions and settings, and later editing tools can
  rewrite the Producer string (a Word file fixed in Acrobat counts as adobe), so "within" can still
  include a mix change inside a group.
- Same limits as the parent result: a cross-section, not a panel (creation date is not posting date;
  survivorship; remediation can reset a creation date); metadata dates can be wrong; pooled over files;
  machine checks only (necessary, not sufficient, for accessibility; not a WCAG conformance judgment); no
  causal claim (the extension on 2026-04-20 and the original date on 2026-04-24 are four days apart); no
  government is named.
- Prior art: a search on 2026-10-24 found guidance on setting titles in each authoring tool, but no
  measurement of government PDF titles by producer software, or of a change in them around the 2026
  extension.
