# What this census has measured so far

One page for every result in this repository so far, each with its limits and a link to the page
that holds the full method and counts. Machine checks only: nothing here is a WCAG conformance
judgment about any government, and no government is named. Code Apache-2.0; this text CC BY 4.0.

`test_measured.py` in the repository root checks every number on this page against the summary
file or the page it is copied from (whose own tests recompute it from the data), and fails if any
number on this page is left unchecked.

## PDF basics on US local-government sites (third full run, 0.2.2)

Of 5,412 PDFs read from 926 websites of US cities, counties and towns of 50,000+ people: tagged
60.5%, document language (`/Lang`) set 56.6%, and all four basics (tagged, `/Lang` set, a title in
the metadata, and not image only) 22.0%. PDFs created on or after the ADA Title II rule
(2024-04-24) are tagged more often than older ones: 66.2% against 56.0%. Files:
[results/v0.2.2/](../results/v0.2.2/); full results in the [README](../README.md).

## Can a screen reader reach the tagged text? (tagtree, pre-registered)

Two of the four predictions held. Of 753 tagged PDFs from 308 sites, 47 (6.2%) leave 5% or more of
the text on their first 3 pages unreachable from the structure tree, which a screen reader
follows in tag order. The figure first published was 49 (6.5%): two files had been misread, as the
correction of 2026-10-18 explains. Results: [tagtree-reach-results.md](tagtree-reach-results.md).

## Is the declared language the text's language? (lang-census, pre-registered)

All four predictions and the agreement check held. Of 65 PDFs whose text is not English, from 46
sites, 57 (87.7%; site-resampled 95% interval 75.7% to 97.0%) have a `/Lang` that is missing or
names another language. Of the 38 that declare English, 16 name the real language on a structure
element or in marked content. The other direction is rare: 3 of 2,813 English PDFs declare another
language. As far as we could find, no earlier study measures whether PDF `/Lang` values match the
text. Results: [lang-census-results.md](lang-census-results.md); files:
[results/lang-v1/](../results/lang-v1/).

## Does the software that made the PDF matter? (Word note, then wordsig)

- Exploratory, chosen after the lang-census data was public: among non-English PDFs that declare
  English, parts of the file carry the real language in 11 of Word's 13, against 2 of 14 for Adobe
  output. A pattern worth testing, not a finding: [lang-word-note.md](lang-word-note.md).
- Pre-registered test on fresh data, 1,616 PDFs from 367 Canadian municipal websites: inconclusive,
  too few. 60 declare a language other than their text's, but only 6 are Word-made and 46
  Adobe-made, short of the minimum of 8 of each, so nothing is claimed and the Word pattern stays
  exploratory: [wordsig-results.md](wordsig-results.md).
- Exploratory, same crawl: 193 of 440 French-text PDFs (43.9%; site-resampled 95% interval 36.4% to
  51.9%) have a `/Lang` that is missing, unusable or names another language.

## Quebec against the rest of Canada (qcfr, pre-registered)

Inconclusive, too few. Outside Quebec the crawl has 7 French-text PDFs from 6 sites, and all 7 have
a `/Lang` that is missing, unusable or names another language; Quebec has 433 from 88 sites, 186 of
them (43.0%) with such a `/Lang`. The minimum was 20 PDFs and 4 sites in each group, so nothing is
claimed. No new crawl was made: [qcfr-results.md](qcfr-results.md).

## What a site owner can do

site_check, in this repository, runs the same checks on one website or a list of PDF links and
writes a plain-language report of what to fix. Since 0.2.0 it also compares each PDF's `/Lang`
with its text and says which language to set and where. See the README's site_check section.

## Limits that apply to every line

Correct reading order, meaningful alt text, table headers and colour contrast need a person or
deeper tools. Each cohort is the sites a crawl could read and the PDFs it reached, not every
government. Text languages are read from the first 5 pages and count only where two detectors
agree. No screen reader was used. Rows with URLs or site ids are not published.

Made by MV2 of Munim, Inc. with AI agents.
