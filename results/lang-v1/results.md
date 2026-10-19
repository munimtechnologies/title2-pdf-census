# lang-census results (machine summary)

PDFs checked 4339; ok 4339; text language determined 2878 (English 2813, other 65 on 46 sites).

## Pre-registered predictions

| Prediction | Measured | Held? |
|---|---|---|
| L1: 50%+ of non-English PDFs have a missing, unusable or other /Lang | 57 of 65, 87.7% (77.5-93.6) | yes |
| L2: 30%+ of non-English PDFs declared English name the text language locally | 16 of 38, 42.1% (27.9-57.8) | yes |
| L3: under 2% of English PDFs declare another language | 3 of 2813, 0.1% (0.0-0.3) | yes |
| L4: under 3% of /Lang values are not BCP 47-shaped | 3 of 2795, 0.1% (0.0-0.3) | yes |
| K: 90%+ detector agreement on confident chunks | 63709 of 64464, 98.8% (98.7-98.9) | yes |

L1 site-resampled 95% interval: [0.7571, 0.9701]

## Exploratory (no prediction)

- Text languages: {"en": 2813, "undetermined": 1428, "es": 54, "mixed": 33, "vi": 4, "ko": 2, "ru": 2, "fr": 1, "pt": 1, "tl": 1}
- Non-English, text language:declared: {"es:match": 4, "es:none": 18, "es:other": 32, "fr:match": 1, "ko:other": 2, "pt:other": 1, "ru:match": 1, "ru:none": 1, "tl:other": 1, "vi:match": 2, "vi:other": 2}
- Non-English declared as: {"en": 38}
- English, declared: {"match": 1936, "none": 873, "other": 3, "unusable": 1}
- Non-English by producer family [PDFs, wrong]: {"adobe": [34, 27], "generator": [1, 1], "other": [8, 8], "print-to-pdf": [4, 4], "unknown": [3, 3], "word": [15, 14]}
- Non-English tagged or not [PDFs, wrong]: {"tagged": [50, 42], "untagged": [15, 15]}
- Mixed-language PDFs, declared: {"None": 14, "en": 19}
- Malformed /Lang values: {"EN_US": 3}
- /Lang given as a name: 0
- /Lang set, all checked PDFs: 2795 of 4339, 64.4% (63.0-65.8)
