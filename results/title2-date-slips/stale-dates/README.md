# Title II date slips, part 13: seven months on, who still gives the 2024 dates as current? (2026-11-15, pre-registered)

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Text and data CC BY 4.0.
Plan: [PREREG.md](PREREG.md), registered 2026-11-15 at about 13:25 UTC before any search for this part.
Every page read: [pages.csv](pages.csv).

## Headline

**On pages that carry a date after the April 2026 extension, the 2024 Title II dates are nearly
gone: 1 of 29.** The old dates live on in pages with no date or with a date from before the
extension, which this plan did not count.

- Eight fixed searches returned 52 different pages. 29 show a publication or update date of
  2026-04-21 or later and state a Title II compliance date (17 from the four neutral searches, 12
  from the four searches that contain the old dates).
- **28 of the 29 give the new dates** (April 26, 2027 for 50,000 or more, April 26, 2028 for
  smaller entities and special districts) or name the extension. None of the 29 gives a wrong new
  day (April 24, 2027 and the like, the topic of parts 1-11).
- **The one stale page** is ADA CodeFix's "ADA Title II Web Accessibility Rule: What's Required
  Now" (published March 12, 2026, updated June 10, 2026): "Smaller entities (under 50,000) have
  until April 26, 2027." It gives no date for larger entities ("now required to meet WCAG 2.1
  AA"), no 2028 date and no word of the extension. Read twice.
- **Outside the count, the old dates are on pages that show no date after April 20, 2026:**
  - UserWay's "ADA Compliance for Websites in 2026" (no date shown): a table with "Large public
    entities | 50,000 or more | April 24, 2026" and "Small public entities | Fewer than 50,000 |
    April 26, 2027", and "Organizations should continue preparing for the April 2026 deadline".
    Read twice.
  - The State of Nevada's Digital Accessibility page on the rule, from the Governor's Technology
    Office ("Last updated 02/19/2026"): "Compliance deadline: April 24, 2026" for governments of
    50,000 or more and April 26, 2027 for smaller ones and special districts, with no notice of a
    change. Read twice, on a page whose banner already announces the November 26-27, 2026 holiday
    closure.
  - Accessible.org's Title II fact sheet ("Updated March 10, 2025"), which the same publisher's own
    news post of April 17, 2026 contradicts.
  - The Georgia Technology Authority's post of February 18, 2026 ("nine (9) weeks away from ... April
    24, 2026") is a dated news item written before the change, so it is not an error.

## Predictions and results

| Prediction | Result | Held? |
|---|---|---|
| P1 (gate): the neutral searches yield at least 10 counted pages | 17 | yes |
| P2: at least 1 counted neutral-search page is stale | 1 (ADA CodeFix) | yes |
| P3: at most 30% of counted neutral-search pages are stale | 1 of 17 (5.9%) | yes |
| P4: vendors publish more than half of the stale pages (at least 4 stale publishers) | 1 stale publisher | not graded |
| P5: at least 2 government publishers have a stale counted page | 0 (the stale government page, Nevada, is dated before the change) | no |
| P6: at least half of the stale pages are dated 2026-07-01 or later (at least 4 stale pages) | 1 stale page | not graded |

Three predictions held, one failed and two could not be graded.

The plan said a page counts if it "shows" a date. Two pages show no date on screen but carry one
in their page data (UsableNet's compliance-deadline post, modified 2026-04-28; Dirigible Studio's
guide, 2026-10-09). Counted, they make 31 pages, still with 1 stale; P1-P3 do not change.

## What else the searches show

- **The neutral searches return vendors.** 15 of the 17 counted neutral-search pages are from
  accessibility vendors, web agencies or the vendor-linked Title II Center (titleii.org); 2 are
  law firms; none is a government body. Across both strata the only counted government page is the
  University of Illinois Chicago's news item (updated November 13, 2026).
- **Government pages were mostly unread or dated before the change.** Of the 13 government
  pages returned (counting public universities), 6 were not read (403 at UNC's School of
  Government, Kansas EBIT, SBA Advocacy and Mass.gov; the Federal Register page and the interim
  rule's PDF on ADA.gov, both dated April 20, 2026, were not fetched). ADA.gov's fact sheet and
  small entity guide show only 2024 dates (April 8 and May 22, 2024) above text that already gives
  the 2027 and 2028 dates; its Title II regulations page shows June 24, 2024 (its § 35.200 text
  lay beyond the part read); and Missouri's AT page showed no date in the part that could be read.
- None of the stale pages named in the plan as known before (AllAccessible, Spedtacular Daily
  Living, ADA Scanner, CITI Program, know-the-ada.com, WSC) was returned by these eight searches, so
  the result is the same with or without them.

## What this means

A frame that counts only pages dated after the change measures the wrong thing: the publishers
that update their pages give the new dates, and the stale pages are the ones nobody touched, so
they carry an old date or none. Part 12 found the same from the other side (3 of 4 publishers of
an old wrong date had posted no new date at all). Measuring how many public bodies still show the
2024 dates needs a fixed list of reference pages read whatever their date, such as each state's
central accessibility or IT-policy page. That is the plan for a later part.

## Use: a gap in MV2's checker

MV2's a11y-statement-check (version 0.10.2 on GitHub, read 2026-11-15) adds the note
`old_title2_date` when a page gives April 24, 2026 and neither April 26, 2027 nor April 26, 2028.
That condition keeps quiet on the most common stale form found here: UserWay's, Nevada's and
Accessible.org's pages all give the full 2024 pair, April 24, 2026 and April 26, 2027, and no 2028
date. ADA CodeFix's page, which gives April 26, 2027 only for smaller entities, is not caught
either. A fix is specified in MV2's plan for the checker's next patch, after 0.11.0: flag a page
that names Title II and gives April 24, 2026 with April 26, 2027, no 2028 date and no word of the
extension. The University of Illinois Chicago's page (April 24, 2026 and April 26, 2027, no 2028,
but "an extension") is the test that this does not flag a current page.

## Limits

Eight searches on one day through one search engine; its ranking decides what was seen, and four
of the searches contain the old dates on purpose, so they give no share. Pages edited in place can
show new text under an old date or old text under a new one; dates were taken as each page shows
them. 8 of 52 pages were not read: six returned 403 or 502, and two (the Federal Register's
bot-checked page and a PDF) were not fetched; both are dated before the cutoff. Pages were read through an
AI web reader that quotes the page; every stale page was read twice, the others once. Search
summaries were never used for a count, and one of them was wrong: it called Continual Engine's
page out of date, but the page (last updated September 2, 2026) gives April 26, 2027 and April 26,
2028. A small hand check, not a census.
