# doc-first-reach v2 results

Arm A: census.crawl_site 0.2.2 (random pages). Arm B: site_check 0.1.1 (document-like pages first). Arm C: site_check 0.1.2 (the same, then other pages once half the pages found no PDF link). At most 8 inner pages and 2 PDFs per arm. Run 2026-10-17.

## zero (129 sites, 125 with all three home pages read)

- At least one PDF link: A 2 of 125 (1.6%), B 59 of 125 (47.2%), C 46 of 125 (36.8%)
  - C against A: only C 45, only A 1; exact McNemar p = 1.3e-12
  - C against B: only C 1, only B 14; exact McNemar p = 0.00098
  - B against A: only B 58, only A 1; exact McNemar p = 2.1e-16
- At least one readable PDF: A 2 of 125 (1.6%), B 49 of 125 (39.2%), C 41 of 125 (32.8%)
  - C against A: only C 40, only A 1; exact McNemar p = 3.8e-11
  - C against B: only C 1, only B 9; exact McNemar p = 0.021
  - B against A: only B 48, only A 1; exact McNemar p = 1.8e-13
- Pages read: A 910, B 815 (670 document-like), C 817 (435 document-like); C fell back to other pages at 68 sites

## control2 (200 sites, 193 with all three home pages read)

- At least one PDF link: A 192 of 193 (99.5%), B 189 of 193 (97.9%), C 192 of 193 (99.5%)
  - C against A: only C 1, only A 1; exact McNemar p = 1
  - C against B: only C 4, only B 1; exact McNemar p = 0.38
  - B against A: only B 1, only A 4; exact McNemar p = 0.38
- At least one readable PDF: A 177 of 193 (91.7%), B 170 of 193 (88.1%), C 175 of 193 (90.7%)
  - C against A: only C 6, only A 8; exact McNemar p = 0.79
  - C against B: only C 6, only B 1; exact McNemar p = 0.12
  - B against A: only B 5, only A 12; exact McNemar p = 0.14
- Pages read: A 1524, B 567 (551 document-like), C 567 (531 document-like); C fell back to other pages at 10 sites

## smoke (2 sites, 2 with all three home pages read)

- At least one PDF link: A 2 of 2 (100.0%), B 2 of 2 (100.0%), C 2 of 2 (100.0%)
  - C against A: only C 0, only A 0; exact McNemar p = 1
  - C against B: only C 0, only B 0; exact McNemar p = 1
  - B against A: only B 0, only A 0; exact McNemar p = 1
- At least one readable PDF: A 2 of 2 (100.0%), B 2 of 2 (100.0%), C 2 of 2 (100.0%)
  - C against A: only C 0, only A 0; exact McNemar p = 1
  - C against B: only C 0, only B 0; exact McNemar p = 1
  - B against A: only B 0, only A 0; exact McNemar p = 1
- Pages read: A 16, B 6 (6 document-like), C 6 (6 document-like); C fell back to other pages at 0 sites

## smoke sites

- ada.gov: A pages 8, PDF links 1, readable PDFs 1; B pages 5, PDF links 4, readable PDFs 2; C pages 5, PDF links 4, readable PDFs 2
- section508.gov: A pages 8, PDF links 35, readable PDFs 2; B pages 1, PDF links 35, readable PDFs 2; C pages 1, PDF links 35, readable PDFs 2
