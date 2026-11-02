# Do large US local governments update their accessibility pages before the Title II date? (pre-registration)

Written 2026-11-02, before any page was read again. Both waves run in 2027 with the exact code
committed beside this file (`statement_reread.py`, which uses `statement_check.py` and
`a11y_pages.py`). AI agents working for MV2 of Munim, Inc. wrote it; not yet checked by a person.
Text CC BY 4.0, code Apache-2.0.

## The question

The ADA Title II rule (28 CFR 35.200, 2024) adopts WCAG 2.1 Level AA for the websites of state and
local governments. The Justice Department's interim final rule of April 20, 2026 moved the first
compliance date, for governments of 50,000 people or more, from April 24, 2026 to **April 26,
2027**.

In October-November 2026 this repository's a11y-pages census
([results/a11y-pages](../a11y-pages/A11Y-PAGES-RESULT.md)) read the accessibility page linked from the
home page of each US city and county of 50,000 or more that it could reach: 808 pages. 283 of them
named only **WCAG 2.0**, and 280 carried one stock sentence, "We work to comply with Section 508 as
well as WCAG 2.0 A and AA referring to website accessibility standards" (258 of them with 2.0 as the
highest version named). The five of those checked were CivicPlus CivicEngage sites, whose help center says each
site's administrators can edit that page.

So most of these 2.0 promises are a default nobody has edited. Do the governments edit them as the
date nears, and after it passes?

## Panel

The 808 rows with `page_status` = `ok` in `results/a11y-pages/a11y-pages.csv` at commit
`ae117d0332fa1da570e2efc9ad8fda7e609c4275` (sha256 `56b82a41258e6144c9467f3c4a64d510ad353ecdb8d59909fe0c73bca8cffce6`).
A page is a **2026 stock page** when its 2026 `version_snippet` contains "We work to comply with
Section 508 as well as" (280 pages, as counted in the census note) and a **2026 2.0-only page** when
its 2026 `highest` is 2.0 (283 pages).

Each wave reads each page's 2026 address again (`page_url`, following redirects; robots.txt honoured;
one second's pause after each request) and classifies the visible text with `statement_check.check_text`,
which uses the census's own `a11y_pages.classify`. At the re-read, the stock sentence is looked for
anywhere in the text. A page is **readable** when it returns HTML with at least 200 characters of text.
Pages are not looked for again from the home page: a government that moved its statement to a new
address shows as unreadable or as whatever the old address now serves.

## Waves

| Wave | Window (UTC dates) | When |
|---|---|---|
| J | 2027-01-11 to 2027-02-28 | about three months before April 26, 2027 |
| M | 2027-05-03 to 2027-06-30 | just after it |

The script refuses to fetch anything outside its wave's window. Each wave runs once; if a wave's run
fails for a reason outside the code (the machine stops), it may be run again inside the window, and
every run is reported.

## Gates (a wave is graded only if all pass)

- **W** today's date is inside the wave's window.
- **P0** this file is on main and main's `statement_reread.py`, `statement_check.py` and
  `a11y_pages.py` are byte for byte the files that run.
- **G1** the panel file read from the pinned commit has 1,657 rows, 808 pages, 280 stock pages and
  283 2.0-only pages.
- **G2** at least 600 of the 808 pages are readable.

A single prediction is not graded (reported as "not graded") if its group has fewer than 200 readable
pages (P1-P3) or, for P4, if fewer than 600 pages are readable.

## Predictions

| | Measure (over the pages readable in the wave) | J holds if | M holds if |
|---|---|---|---|
| P1 | Of the 2026 stock pages, the share that still carry the stock sentence | at least 85% | at least 70% |
| P2 | Of the 2026 2.0-only pages, the share whose highest version is still 2.0 | at least 80% | at least 65% |
| P3 | Of the pages naming any version now, the share whose highest is 2.0 | at least 45% | at least 40% |
| P4 | Share naming Title II now minus the share of the same pages naming it in 2026 | (reported) | at least 3 points |

Why these: the stock sentence names WCAG 2.0, which WCAG 2.1 followed in 2018, and it was still on
280 pages after the rule's publication (April 2024) and the April 2026 extension, so the expectation
is inertia: most pages
unchanged three months out (P1, P2 for J), some movement right after the date (M thresholds lower).
P3 is the census's 55.71% (283 of 508) seen again; its thresholds allow for some movement. P4 says
governments that do edit their pages will tend to add Title II wording around the date (179 of the
808 pages named Title II in 2026).

## Reported, not graded

Status of every page; how many pages have text identical to 2026 (same sha256 of the visible text);
how many redirect to a new address; version moves (2.0 to 2.1, to none, and so on) for all pages, for
stock pages and for the 25 non-stock 2.0-only pages; pages carrying the stock sentence now but not
counted as stock in 2026; the 12 pages that gave only the old April 24, 2026 date in 2026 and what
they give now; how many pages now give April 26, 2027 or April 26, 2028.

## Limits

- Text only: a page that promises WCAG 2.1 AA says nothing about whether the site meets it, and a
  page that still says 2.0 may sit on a site that meets 2.1.
- The 808 pages are the census's reachable pages, not all 1,657 governments; 2026's robots and
  network failures are not retried.
- The stock sentence was counted in 2026 only in the snippet around each page's first version; the
  re-read looks at the whole text, so a 2026 page that carried it elsewhere could show as "stock now"
  without being a 2026 stock page. These are reported separately and do not enter P1.
- Pages built by JavaScript read as short or empty, as they did in 2026.

## Prior art

Checked 2026-11-02. The 2026 reports on government websites (AccessLumens, 221 cities; Accessible
Compliance Group, 15,481 sites; WPPersona, 2,412 sites; UAIS, 50 state home pages) are automated WCAG
scans at one point in time. None reads what accessibility statements promise, and none re-reads the
same governments' statements across the Title II date. The EU's Web Accessibility Directive has its
own rules for accessibility statements; work on those was not searched in depth, as it concerns a
different law and deadline.

## Code and tests

`statement_reread.py` 0.1.0 and `test_statement_reread.py`, which runs offline (the repository and
every page are faked) and checks that the gate counts above are the committed table's own.
Run: `python statement_reread.py --wave J --out-dir out`.
