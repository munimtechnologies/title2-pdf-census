# tagtree-xcheck results (v0.1.0)

tagtree-reach (pdfminer.six) and an independent pypdf reader on the same bytes of the same local-government PDFs. Machine checks only.

- PDFs analysed: 771; eligible for tagtree-reach: 759; read by both: 759; walk errors: 0
- tagtree results: {"ok": 771}; pypdf results on eligible PDFs: {"ok": 759}

## Pre-registered checks

| Check | Agreement | Threshold | Met |
|---|---|---|---|
| X1_elements_equal | 99.7% (757 of 759) | 95% | True |
| X2_walks_equal | 99.7% (757 of 759) | 95% | True |
| X3_any_dangling_agree | 99.7% (757 of 759) | 95% | True |
| X4_shell_agree | 99.9% (758 of 759) | 90% | True |
| X5_leaky_agree | 99.7% (757 of 759) | 90% | True |

## The re-crawl itself (exploratory)

- Leaky (tagtree): 6.6% (50 of 759); first run 49 of 753
- Shell (tagtree): 4.2% (32 of 759); first run 32 of 753
- Disagreements listed in summary.json: 2
