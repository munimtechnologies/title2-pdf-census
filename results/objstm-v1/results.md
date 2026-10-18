# objstm-census results (machine summary)

PDFs analysed 790; eligible 775; index check ok on 775; with object streams 715; with a wrong index 2; tagtree record changed by --xref-index 2.

## Pre-registered predictions

| Prediction | Measured | Held? |
|---|---|---|
| O1: under 5% of PDFs with object streams have a wrong index | 2 of 715, 0.3% (0.1-1.0) | yes |
| O2: 80%+ of those are Word output | 2 of 2, 100.0% (34.2-100.0) | yes |
| O3: at most 2 PDFs change their tagtree record | 2 | yes |

## Known files

- c8c71fae: {"eligible": true, "same_bytes": true, "index_wrong": 785, "expected": 785, "changed": true}
- 5b10b0e8: {"eligible": true, "same_bytes": true, "index_wrong": 3122, "expected": 3122, "changed": true}

## Exploratory (no prediction)

- By producer family [with object streams, wrong index]: {"adobe": [351, 0], "generator": [7, 0], "libreoffice": [1, 0], "office-other": [44, 0], "other": [12, 0], "print-to-pdf": [2, 0], "scanner": [6, 0], "unknown": [12, 0], "word": [280, 2]}
- Hybrid files: {"hybrid": [272, 2], "not_hybrid": [443, 0]}
- Word for Microsoft 365 against other Word: {"other_word": [143, 0], "word365": [137, 2]}
- Wrong index by creation year: {"2025": 2}
- Median share of compressed objects with a wrong index (files with any): 0.863
- tagtree 0.1.1 leaky: 50 of 775, 6.5% (4.9-8.4)
- tagtree 0.1.1 shell page: 31 of 775, 4.0% (2.8-5.6)
