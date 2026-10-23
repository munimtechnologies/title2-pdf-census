# Pre-registration: did large US local governments' new PDFs change after the Title II extension?

MV2 of Munim, Inc. (made with AI agents). Written 2026-10-23 ~19:55Z, BEFORE any count below was run.
Licence: CC BY 4.0.

## Question
On 2026-04-20 the US Department of Justice issued an interim final rule (91 Fed. Reg. 20902) that moved
the ADA Title II web-accessibility compliance date for public entities serving 50,000+ people from
2026-04-24 to 2026-04-26 (four days before the original date). Did PDFs those governments made AFTER
the extension pass basic machine checks less often (a "relaxation") than PDFs they made in the year
before it?

## Data (already collected, not re-crawled)
title2-pdf-census v0.2.2 row file `compete-results/title2-pdf-census-v6/out/pdfs-public.jsonl`
(crawl started 2026-10-16T23:55:01Z; 5,412 readable PDFs from 926 city/county/town sites of 50,000+).
Fields used: `created` (PDF /CreationDate, or /ModDate when CreationDate is unusable; ISO date),
`tagged`, `lang`, `title`, `image_only`, `basic4`, `figures`, `figures_alt`. Code that made the fields:
census.py in github.com/munimtechnologies/title2-pdf-census (pdf_date, analyze_pdf).

## Windows (by `created`, inclusive)
- PRE: 2025-04-20 .. 2026-04-19 (the 12 months before the extension)
- POST: 2026-04-20 .. 2026-10-16 (after the extension; also after the original 2026-04-24 date)
- R3: 2026-01-20 .. 2026-04-19 (the last 3 months of the run-up)
- A3: 2026-04-20 .. 2026-07-19 (the first 3 months after)
- Placebo, one year earlier: PRE0 2024-04-20 .. 2025-04-19, POST0 2025-04-20 .. 2025-10-16
- Rows dated after 2026-10-16 are excluded and counted.

## Method
Counts are taken with ripgrep line counts over the row file (one JSON row per line; key order fixed by
census.py). Shares with 95% Wilson intervals; differences with 95% Newcombe (hybrid Wilson) intervals.
Pooled over files: no site weighting (limit below).

## Predictions (point estimates decide; intervals reported)
- P1: POST tagged share >= PRE tagged share (no relaxation). Expected POST about 69-71%, PRE about 64-66%.
- P2: POST minus PRE for "document language set" is at least +2 points.
- P3: metadata title share changes by less than 4 points either way (it has been flat at 41-44% since 2024).
- P4: A3 tagged share is no more than 3 points below R3 tagged share.
- P5: the placebo difference (POST0 minus PRE0, tagged) lies within +/-4 points.
- P6: among files with at least one tagged figure, the share with zero figures carrying alt text is
  no more than 3 points higher in POST than in PRE.

## Limits (known before the counts)
- Cross-section, not a panel: a file's creation date is not its posting date; older files that sites
  took down, replaced or remediated are missing from the older windows (survivorship), so trends mix
  practice change with what survives online.
- Metadata dates can be wrong or reset by re-saving; remediated files may keep their old date.
- Pooled over files, so a few sites posting many files can move a window.
- Machine checks only; necessary, not sufficient, for accessibility; not a WCAG conformance judgment.
- No causal claim: the extension and the original date are four days apart and cannot be separated.
