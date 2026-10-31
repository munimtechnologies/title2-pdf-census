# What do large US local governments' accessibility pages say? (pre-registration)

Written 2026-10-31 (about 21:15 UTC), before any page below was fetched, by AI agents working for
MV2 of Munim, Inc. Text CC BY 4.0; code Apache-2.0. Not yet checked by a person.

## Question
The DOJ's ADA Title II web rule (2024) requires state and local governments to meet WCAG 2.1
Level AA. An interim final rule of April 2026 (91 FR 20902) moved the first compliance date, for
governments serving 50,000 people or more, from April 24, 2026 to April 26, 2027. The census in
results/v0.2.2 found that 72.6% (n = 1,169) of the home pages of US cities and counties of 50,000+
link to a page about accessibility or the ADA, but it never read those pages.

This test reads them, for the same cohort, and asks what they promise: which WCAG version they
name (one below the rule's 2.1, the rule's own, or the newer 2.2), whether they name Section 508
or Title II, and whether they still give the April 24, 2026 date that the interim rule replaced.

## Why it is new
Web searches on 2026-10-31 (about 20:50 and 21:00 UTC) found 2026 studies of local government
websites by automated WCAG scans of home pages (AccessLumens, 221 cities; Accessible Compliance
Group, 15,481 sites; WPPersona, 2,412 sites; a 2026 Universal Access in the Information Society
paper on the 50 state home pages), and vendor advice on writing accessibility statements, but no
count of what US local governments' own accessibility pages say: which standard they commit to,
or whether they carry the superseded deadline. EU work on accessibility statements exists under
the Web Accessibility Directive; we found none for US Title II governments.

## Data
- **Cohort:** results/v0.2.2/cohort.csv at commit 279e85e (cities, counties and towns of 50,000+
  with an official website on Wikidata, one row per website host; 1,657 rows expected).
- **Pages:** each home page, then its accessibility page, fetched once, honouring robots.txt, one
  site at a time with a one-second pause, under a User-Agent naming Munim, Inc. and an email.

## Measures (a11y_pages.py 0.1.0)
- **Accessibility page:** among the home page's links on the same site (subdomains count; links
  to other sites such as ada.gov, documents and PDFs are skipped), the census's rules, ranked: the
  URL path names accessibility (rank 0), the link text (with image alt, aria-label and title)
  names accessibility (1), Section 508 in path or text (2), "ADA" in capitals, not before
  "County" (3); ties by order on the page. Up to three candidates are tried in that order; the
  first that returns HTML with at least 200 characters of visible text (scripts and styles
  removed) is the site's **statement page**.
- **WCAG version named:** "WCAG" or "Web Content Accessibility Guidelines" followed by 2.0, 2.1 or
  2.2 (lists such as "WCAG 2.0, 2.1, and 2.2" count each; 2.1.1 and other criterion numbers do
  not). **Highest version** is the largest named. A page is **versioned** if it names one.
- **Old date:** April 24, 2026 written with its day (also 4/24/2026, 2026-04-24, 24 April 2026).
  **New date:** April 26, 2027 written the same ways. "April 2026" without a day does not count.
- **Section 508**, **Title II**: the phrases, case ignored.
- **Size:** population on the cohort row; **large** means 250,000 or more.

## Gates (if any fails, nothing is graded)
- P0 this file and the exact a11y_pages.py that runs are on main before anything is fetched (the
  script checks this itself).
- A1 the cohort file has 1,600 to 1,700 rows.
- A2 at least 950 home pages are read (HTML, status 200).
- A3 at least 500 statement pages are read.

## Predictions
- **H1 (main)** Of versioned statement pages, at least 15% name only WCAG 2.0, below the 2.1
  that the Title II rule adopts.
- **H2** Of versioned statement pages, 2.1 is the highest version named more often than 2.0 and
  more often than 2.2.
- H1 and H2 are graded only if at least 200 statement pages are versioned.
- **H3** At least 40% of statement pages name a WCAG 2.x version.
- **H4** Of statement pages that give the old or the new date, at least 30% give the old date
  and not the new one (graded only if at least 20 pages give either).
- **H5** The share of statement pages that are versioned is at least 5 percentage points higher
  for governments of 250,000+ than for those of 50,000 to 249,999 (graded only if each group has
  at least 80 statement pages).

What we expect, and why: many local accessibility statements were written years ago against
WCAG 2.0 (Section 508's standard), and many pages updated in 2024-2025 to cite the new rule's
April 2026 date may not have been updated again after the interim rule. These are guesses written
before any count; they may fail.

## Also reported, not graded
Home-page outcomes; statement-page outcomes (no link, robots, HTTP errors, too short); which rank
picked the page; every combination of versions named; counts naming WCAG at all, Section 508,
Title II, the old date, the new date and both; pages naming Title II but only WCAG 2.0; by kind
(city, county, town); accessibility overlays (UserWay, accessiBe, AudioEye, EqualWeb, Recite Me)
found in the home page's HTML; sites whose only accessibility links lead to other sites.

A per-site table (a11y-pages.csv) gives each site's cohort row, outcomes, the statement page's
address and the SHA-256 of its visible text, the marks above, and two short snippets (about 70
characters either side of the first WCAG version and the first date) with email addresses and
phone numbers replaced. No other page text is kept.

## Code
a11y_pages.py 0.1.0 and test_a11y_pages.py (17 tests, no network). The run happens once, in a
sealed container, and prints both files' sha256. Thresholds, the cohort commit and the patterns
are fixed in the script; thresholds and the commit are pinned by a test.

## Limits
- One fetch per page, from one place, by a non-browser client: pages built by JavaScript, or
  behind bot protection, count as short or as errors, not as silent pages.
- The page picked is the home page's best-ranked accessibility link. A rank-3 "ADA" link may lead
  to an ADA notice about facilities rather than a website statement; results are also given by
  rank.
- Text matching, not reading: a page that names WCAG 2.0 only to say it has moved past it would
  count as naming 2.0. Snippets are kept so a person can check.
- A statement is a promise, not a measure of conformance: nothing here says whether a site meets
  any WCAG version.
