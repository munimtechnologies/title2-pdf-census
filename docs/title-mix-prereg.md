# Pre-registration: is the post-extension drop in PDF titles a change in software or in practice?

MV2 of Munim, Inc. (made with AI agents). Written 2026-10-24 ~00:35Z, before any title count by
software group was taken, and committed with `title_mix.py` and its tests. The script is run on the
data by a separate local job filed at the same time; its results are read and graded in a later
session and published in docs/title-mix-results.md. Licence: CC BY 4.0.

## Why
[deadline-split-results.md](deadline-split-results.md) found that PDFs created in the six months after
DOJ moved the Title II date (2026-04-20) carried a document title less often than PDFs from the twelve
months before: 39.0% (446/1,143) vs 45.1% (488/1,081), -6.1 points (95% CI -10.2 to -2.0). A title is a
WCAG 2.4.2 / PDF/UA basic, and in a PDF it is mostly written by the software that makes the file (Word
copies the document's Title property; print drivers and scanners usually write none). So the drop could
be a change in which software governments used (mix) or a change in how the same software was used
(practice). This check splits the change into those two parts.

## Data (already collected, not re-crawled)
The same title2-pdf-census v0.2.2 row file (crawl started 2026-10-16T23:55:01Z). Rows with `result`
"ok" and a `created` date; repeated links kept as in the pooled analysis, so the totals must equal the
published ones: PRE 488/1,081 and POST 446/1,143 titled/files; R3 185/390 and A3 157/396; PRE0 246/554
and POST0 177/379. `title` is true when the document information dictionary has a non-blank /Title
(census.py `analyze_pdf`); XMP dc:title and DisplayDocTitle are not part of it.

## Windows (by `created`, inclusive)
PRE 2025-04-20..2026-04-19; POST 2026-04-20..2026-10-16; R3 2026-01-20..04-19; A3 2026-04-20..07-19;
placebo PRE0 2024-04-20..2025-04-19 and POST0 2025-04-20..2025-10-16 (the same split a year earlier).

## Software groups (fixed before counting)
From census.py's `producer_family` (Producer + Creator strings, first matching pattern): office = word +
office-other; adobe; print-to-pdf; scanner; unknown (no Producer or Creator); rest = libreoffice,
google-docs, generator and other.

## Measures
- Change = after-window title share minus before-window share.
- Within part = sum over groups with files in both windows of (the group's share of before-window
  files) x (its after-window title share minus its before-window title share). Mix part = change minus
  within. The two add up to the change exactly; a group missing from one window counts only in mix.
- Uncertainty for the PRE->POST within part: 2,000 bootstrap resamples of sites (`qid`, one per
  government) with replacement, seed 20261024; 2.5th and 97.5th percentiles.

## Predictions (point estimates decide; intervals reported)
- T1: PRE->POST mix part is smaller than 2 points either way (software mix barely moved).
- T2: PRE->POST within part is at most -3 points (most of the -6.1 drop is practice, not mix).
- T3: R3->A3 within part is at most -3 points.
- T4: of the three groups with the most PRE files, at least two have a lower POST title share.
- T5: placebo: PRE0->POST0 within part is at least -2 points (no such drop a year earlier).
- T6: the bootstrap interval of the PRE->POST within part lies wholly below zero.

What we already knew when writing these: the pooled numbers above, and three mix facts published with
the deadline split: Word/Office-made files were 24.1% of R3 files and 22.7% of A3 files, scanner-made
8.5% and 7.6%, Adobe-made 166 and 158 files. Those are why T1 expects a small mix part. No title count
by software group, and no group mix for PRE, POST, PRE0 or POST0, had been taken.

## Limits (known before running)
- Six groups only. Large groups like office and adobe hide different settings and versions, so "within"
  can still include a mix change inside a group. Producer strings can be rewritten by later editing
  tools (a Word file fixed in Acrobat is counted as adobe).
- One decomposition (before-window weights). A different reference (after-window or average weights)
  can split the change differently; the full group table is published so readers can redo it.
- Same limits as the pooled analysis: a cross-section (creation date is not posting date; survivorship;
  remediation can reset dates), pooled over files, machine checks only, no causal claim (the extension
  and the original 2026-04-24 date are four days apart). No government is named.
- Prior art: a search on 2026-10-24 found guidance on titles by authoring tool, but no measurement of
  government PDF titles by producer software, or of a change in them around the 2026 extension.
