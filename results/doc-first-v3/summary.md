# doc-first-reach v3 results

Arm A: census.crawl_site 0.2.2 (16 random pages). Arm B: site_check 0.1.1 (8 pages, document-like first). Arm D: site_check 0.1.2 (16 pages, document-like first, then other pages once half the pages found no PDF link). At most 2 PDFs per arm. Run 2026-10-17.

## zero (129 sites, 122 with all three home pages read)

- At least one PDF link: A 58 of 122 (47.5%), B 56 of 122 (45.9%), D 70 of 122 (57.4%)
  - D against A: only D 24, only A 12; exact McNemar p = 0.065
  - D against B: only D 14, only B 0; exact McNemar p = 0.00012
  - B against A: only B 20, only A 22; exact McNemar p = 0.88
- At least one readable PDF: A 49 of 122 (40.2%), B 46 of 122 (37.7%), D 58 of 122 (47.5%)
  - D against A: only D 21, only A 12; exact McNemar p = 0.16
  - D against B: only D 14, only B 2; exact McNemar p = 0.0042
  - B against A: only B 19, only A 22; exact McNemar p = 0.76
- Pages read: A 1693, B 803 (664 document-like), D 1420 (790 document-like); D fell back to other pages at 52 sites

## control3 (200 sites, 195 with all three home pages read)

- At least one PDF link: A 194 of 195 (99.5%), B 183 of 195 (93.8%), D 193 of 195 (99.0%)
  - D against A: only D 0, only A 1; exact McNemar p = 1
  - D against B: only D 10, only B 0; exact McNemar p = 0.002
  - B against A: only B 0, only A 11; exact McNemar p = 0.00098
- At least one readable PDF: A 180 of 195 (92.3%), B 170 of 195 (87.2%), D 180 of 195 (92.3%)
  - D against A: only D 7, only A 7; exact McNemar p = 1
  - D against B: only D 12, only B 2; exact McNemar p = 0.013
  - B against A: only B 4, only A 14; exact McNemar p = 0.031
- Pages read: A 3025, B 671 (663 document-like), D 849 (807 document-like); D fell back to other pages at 9 sites

## smoke (2 sites, 2 with all three home pages read)

- At least one PDF link: A 2 of 2 (100.0%), B 2 of 2 (100.0%), D 2 of 2 (100.0%)
  - D against A: only D 0, only A 0; exact McNemar p = 1
  - D against B: only D 0, only B 0; exact McNemar p = 1
  - B against A: only B 0, only A 0; exact McNemar p = 1
- At least one readable PDF: A 2 of 2 (100.0%), B 2 of 2 (100.0%), D 2 of 2 (100.0%)
  - D against A: only D 0, only A 0; exact McNemar p = 1
  - D against B: only D 0, only B 0; exact McNemar p = 1
  - B against A: only B 0, only A 0; exact McNemar p = 1
- Pages read: A 32, B 6 (6 document-like), D 6 (6 document-like); D fell back to other pages at 0 sites

## weighted

- Read sites with a readable PDF, zero set and control3 weighted 129 : 1001: A 86.4%, B 81.5%, D 87.2%

## smoke sites

- ada.gov: A pages 16, PDF links 5, readable PDFs 2; B pages 5, PDF links 4, readable PDFs 2; D pages 5, PDF links 4, readable PDFs 2
- section508.gov: A pages 16, PDF links 36, readable PDFs 2; B pages 1, PDF links 35, readable PDFs 2; D pages 1, PDF links 35, readable PDFs 2
