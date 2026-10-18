# tagtree-reach results (v0.1.0)

Tagged PDFs linked from US local-government websites (cities and counties of 50,000+): how much of the text on their first 3 pages is reachable from the structure tree that screen readers follow. Machine checks only; not a WCAG conformance judgment.

- Sites crawled: 600; PDFs analysed: 766; eligible: 753 from 308 sites
- Results: {"ok": 766}
- Characters (eligible PDFs): {"reachable": 2462472, "untagged": 80141, "dangling": 24047, "artifact": 65903, "xobject": 3705, "named": 2877}

## Pre-registered predictions

| Prediction | Measured | Met |
|---|---|---|
| P1: 10%+ of tagged PDFs leave 5%+ of page text unreachable | 6.5% (5.0-8.5), n=753; site-clustered CI [0.0471, 0.0854] | False |
| P2: Word-made PDFs are leaky 10+ points less often | Word 3.6% (1.9-6.5), n=280; others 8.2% (6.1-11.1), n=473; difference 0.0468 | False |
| P3: 2%+ have a text page with nothing reachable | 4.2% (3.0-5.9), n=753 | True |
| P4: median page discordance (tag vs stream order) is 0.05 or less | 0.0 over 1420 pages | True |

## Exploratory (no prediction)

- Mean leak share: 0.0427
- Any dangling MCID text: 3.0% (2.0-4.5), n=753
- Any untagged text: 6.9% (5.3-8.9), n=753
- Same-column upward jump in tag order: 11.4% (9.3-13.9), n=753
- Pages with discordance over 0.2: 138 of 1420

## By the software that made the PDF

| Producer | Leaky | Median leak share |
|---|---|---|
| adobe | 7.0% (4.8-10.2), n=342 | 0.0 |
| generator | 11.1% (2.0-43.5), n=9 | 0.0 |
| libreoffice | 0.0% (0.0-79.3), n=1 | 0.0 |
| office-other | 0.0% (0.0-8.0), n=44 | 0.0 |
| other | 14.9% (7.4-27.7), n=47 | 0.0 |
| print-to-pdf | 25.0% (8.9-53.2), n=12 | 0.0 |
| scanner | 16.7% (3.0-56.4), n=6 | 0.0 |
| unknown | 25.0% (8.9-53.2), n=12 | 0.0 |
| word | 3.6% (1.9-6.5), n=280 | 0.0 |
