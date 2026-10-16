# Pre-registration: does reading document pages first find the PDFs random sampling misses?

Written 2026-10-16, before the job ran, and committed with site_check 0.1.1. The job fetches this
file and hashes it with its code. The job's code and results will be added next to this file and
scored against the predictions below, whatever they show.

## Why

The census reads 8 pages chosen at random from each home page's links, so its shares are not
skewed toward one kind of page. In its second full run (0.2.1), that found **no PDF link at all on
129 of the governments whose pages it read** (status ok, at least one inner page read). For the
census that is a known limit of a two-click random sample. For site_check, a self-check meant to
find a site's PDFs, it is a failure: its first version used the same sampling and returned empty
reports for section508.gov and ada.gov. Version 0.1.1 reads pages whose link text or address looks
like a document list (Documents, Agendas, Minutes, Forms, Library, Resources, CivicPlus's
DocumentCenter and AgendaCenter, and similar words) first, follows such links one level further,
and stops once it has twice as many PDF links as PDFs to check.

## Design

- **Sites.** *Zero set:* every row of `results/v0.2.1/sites.csv` with status `ok`, `pages_read` > 0
  and `pdf_links` = 0 (129 rows by our count). *Control set:* 100 rows with status `ok`,
  `pages_read` > 0 and `pdf_links` > 0, chosen by the census's seeded `sample()` (seed
  "doc-first-control").
- **Arms, run one after the other on each site the same day:** A = `census.crawl_site` 0.2.2
  (random pages; includes the `<base href>` fix, so A is not simply a repeat of 0.2.1), B =
  `site_check.crawl` 0.1.1. Both read at most 8 inner pages and check at most 2 PDFs, with a
  1-second pause between requests and robots.txt honoured.
- **Analysed:** sites where both arms read the home page. Outcomes: at least one PDF link found;
  at least one readable PDF. Paired comparison with an exact two-sided McNemar test.
- **Published:** aggregate counts only. Per-site rows are not published, and no government is
  named.

## Predictions

1. Zero set: B finds at least one PDF link at **30% or more** of the analysed sites.
2. Zero set: A finds at least one PDF link at **15% or fewer** of them (re-crawl variation plus the
   `<base href>` fix).
3. Zero set: B beats A on discordant pairs for "at least one PDF link", exact McNemar **p < 0.01**.
4. Control set: B reaches at least one readable PDF at least as often as A, **within 2 percentage
   points or better**.
5. Control set: B reads **fewer** inner pages in total than A (early stop).

## What would count against site_check 0.1.1

Prediction 1 or 3 failing means document-first reading does not rescue the empty sites, and the
Actor's description should not say it finds PDFs better. Prediction 4 failing means it trades away
sites where random sampling already worked, and 0.1.1 needs another look before the Actor is
published.

## Limits

Two arms on the same day are not simultaneous: a site can change or rate-limit between them (A
always runs first, which could favour or hurt B). Some sites keep documents behind search forms or
scripts that neither arm reads. "Document-like" is a word list written by AI agents working for
MV2 of Munim, Inc., not tuned on these sites.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (text).
