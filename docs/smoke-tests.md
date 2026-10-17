# site_check smoke tests

Small live runs of site_check on the Apify Actor's example sites, each in a sealed container on
MV2's job runner, before any publish step.

- **0.1.0 (2026-10-16): empty.** section508.gov and ada.gov: 4 pages read on each, 0 PDF links
  found, so 0 PDFs checked. 0.1.0 picked pages at random, as the census does, and none of the
  pages it picked linked a PDF. This is why 0.1.1 reads document-like pages first.
- **0.1.1 (2026-10-16): passed.** ada.gov: 8 pages read, all document-like, 5 PDF links found,
  4 PDFs checked, all 4 pass the four basics. section508.gov: 1 page read, 35 PDF links found,
  4 PDFs checked, 3 pass the four basics and 1 has no title.
- **0.1.2 (2026-10-17): passed**, as part of the second doc-first test
  ([doc-first-v2-results.md](doc-first-v2-results.md)), which checked at most 2 PDFs per site.
  ada.gov: 5 pages read, all document-like, 4 PDF links found, 2 PDFs read. section508.gov: 1
  page read, 35 PDF links found, 2 PDFs read. It did not need to fall back on either site. The
  test records whether each PDF could be read, not which basics it passes.

Made by MV2 of Munim, Inc. with AI agents. CC BY 4.0.
