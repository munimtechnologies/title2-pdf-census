# public-colleges: what do US public colleges' accessibility pages say, and do they still give April 24, 2026? (pre-registration)

Registered 2026-11-12, before any college website was read for this study.
Script: `public_colleges.py` 0.1.0 with its offline tests (`test_public_colleges.py`). It reads
each site with the unchanged `state_pages.py` 0.1.0 crawler (the rules of
[results/state-pages](../state-pages/)), which itself uses the unchanged `a11y_pages.py` 0.1.0 and
`statement_check.py` 0.1.0 already in this repository. Made by MV2 of Munim, Inc. with AI agents; not
yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0. The frame comes from the
U.S. Department of Education's IPEDS directory file (public U.S. government data, National Center
for Education Statistics).

## Why

Public colleges and universities are state or local government entities, so the ADA Title II web
rule (28 CFR 35.200, 2024) covers their websites and adopts WCAG 2.1 Level AA. The rule first gave
public entities of 50,000 or more people April 24, 2026, and that was the date most public
universities (part of a state government) were told to meet. The Justice Department's interim final
rule of April 20, 2026 (91 FR 20902) moved that date to April 26, 2027, and the later date for
smaller entities and special districts to April 26, 2028. Since then, a page that gives April 24,
2026 and no later date gives a date that no longer applies to any public entity.

MV2's earlier censuses here read US cities, counties and towns, school districts, state governments
and special districts, never colleges. For context, of the 1,657 cities and counties of 50,000 or
more: 815 of 1,195 home pages read (68.20%) link to an accessibility page; 283 of 508 pages that name
a WCAG version (55.71%) name WCAG 2.0 as the highest; 179 of 808 pages read (22.15%) name Title II;
and 12 of 17 pages that give a compliance date (70.59%) give only April 24, 2026. Searches on
2026-11-12 found vendor guides to the rule for higher education and one vendor report (a survey of
300 public college administrators and a scan of 600 public-sector and higher education websites for
errors), but no published count, page by page, of what public colleges' accessibility pages say:
which WCAG version they name, whether they name Title II, or which compliance date they give.

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job downloads `HD2024.zip` from https://nces.ed.gov/ipeds/datacenter/data/HD2024.zip (the IPEDS
institutional characteristics directory file for 2024) and reads the member `HD2024.csv` (matched
without regard to letter case). Only seven columns are read: UNITID, INSTNM, CITY, STABBR, WEBADDR,
SECTOR and CYACTIVE. The file's other columns, including the chief administrator's name, the phone
number and the street address, are never read into a row or written anywhere. A row is eligible when
SECTOR is 1 (public, four-year or above) or 2 (public, two-year) and CYACTIVE is 1 (active in the
current year). The website address (WEBADDR) is reduced to its host, in lower case, without one
leading `www.`; a row with no usable host is counted and left out. Where several institutions share
a host (branch campuses listing their system's site), the lowest UNITID is kept and the others are
counted. Rows that contain the publishing tool's blocked word are dropped and counted. Each row's
kind is `public_4yr` or `public_2yr` from its sector; kinds are described, never graded. The job
writes `frame.csv` and records the archive's and the member's size and SHA-256. If the archive,
the member or one of the seven columns is missing, the job stops and no website is read.

What was looked at before registering, none of it on a college site: web searches on 2026-11-12
(about 00:50-01:10 UTC) and an automated summary of the vendor report page named above; automated
fetches that showed `HD2024.zip` and `HD2023.zip` are zip archives holding `HD2024.csv` and
`HD2023.csv` (the archives were not opened and no row of either file was read); the column names,
taken from a search summary of the jbryer/ipeds package's documentation; and the README of this
repository. No college page was fetched.

## Method

- Order and size: the frame's hosts sorted by SHA-256 of the seed `public-colleges-2026-11-12` plus
  the host; at most 2,500 are read (if the frame is no larger, all of them). 24 sites at a time;
  within a site one request at a time with a 1-second pause after each. Sites not started within
  150 minutes count as not started.
- Each host, exactly as in the state census (`state_pages.crawl_site`, unchanged): `robots.txt`
  first (a page it disallows is not requested), then the home page `http://<host>/`, or
  `http://www.<host>/` if the first gets no answer at all (redirects are followed). On a home page
  that answers 200 with HTML, the accessibility page is picked by the census's link rules unchanged
  (`a11y_pages.candidates`: same site only; ranked path names accessibility, then link text, then
  Section 508, then ADA), and up to 3 candidates are tried in that order. A page is read when it
  answers 200 with HTML and has at least 200 characters of visible text.
- Reading: `a11y_pages.classify` (WCAG versions named and the highest, Section 508, Title II, April
  24, 2026 and April 26, 2027) and `statement_check.check_text` (the vendor stock sentence, April 26,
  2028, an email address or phone number, findings), both unchanged.
- Graded units: distinct pages (page address without scheme, `www.`, letter case or a trailing
  slash; the first host in host order is kept) and distinct home sites (the host the home page ended
  on, without `www.`).
- Stored per host: the frame columns, statuses, the address and SHA-256 of the page read, the flags
  above, and short snippets around a WCAG version or an April 2026 or April 2027 date with email
  addresses and phone numbers removed. No other page text and no person's name is stored.

## Gates

- P0: this file is on main, and main's `public_colleges.py`, `state_pages.py`, `a11y_pages.py` and
  `statement_check.py` are byte for byte the job's copies.
- C1 (checked on the frame before any website is read; if it fails, no website is requested): 1,000
  to 2,500 eligible hosts.
- Each prediction is graded only with enough data: PC1 with at least 500 distinct home sites, PC2 and
  PC3 with at least 100 versioned pages (distinct pages that name a WCAG version), PC4 with at least
  200 distinct pages, PC5 with at least 20 dated pages (distinct pages that give April 24, 2026,
  April 26, 2027 or April 26, 2028).

## Predictions (fixed before any website is read)

- PC1 (at least 75% of distinct home sites link to an accessibility page on the same site). Large
  cities: 68.20%. Colleges are predicted to link more often, since many have a campus-wide footer
  link.
- PC2 (at most 30% of versioned pages name WCAG 2.0 as the highest version). Large cities: 55.71%.
- PC3 (WCAG 2.1 is the most common highest version): more versioned pages name WCAG 2.1 as the
  highest than name 2.0, and more than name 2.2.
- PC4 (at least 20% of distinct pages name Title II). Large cities: 22.15%.
- PC5 (of dated pages, at least 25% give April 24, 2026 and neither later date): at least a quarter
  of the colleges that give a date still give the one the interim final rule replaced. Large cities:
  12 of 17.

The result is published whether the predictions hold or not.

## Described, not graded

Home status and how it was reached; distinct home sites, pages and texts; how each page was found;
WCAG versions named; findings; overlay scripts on home pages; Section 508; the vendor stock sentence
("We work to comply with Section 508 as well as ..."); an email address or phone number; which
combination of the three dates each page gives; all of these by kind (four-year or two-year) and by
state.

## Limits

Only active public four-year and two-year institutions in the 2024 IPEDS directory are read, by the
website host IPEDS gives, and only one page per site, once, without running JavaScript. Branch
campuses that share their system's host are read once. An accessibility page linked only from
another page, kept on another site, published as a PDF, or behind a firewall that refuses this
reader is missed, so a page not found is not proof that a college has none. The link rules can pick
a page about disability services or the ADA in general rather than the website; it is read and
counted all the same, as in the city census. Which compliance date applies to a given college
depends on the public entity it belongs to (most public universities are part of a state, and some
community colleges belong to smaller local entities or special districts), so this study grades only
whether a page still gives the replaced date, not whether a page names the right later date. A page
giving April 24, 2026 may be quoting it in passing; the snippets let a reader check. A version or
date is what the page says, not what the site meets. This counts what pages say; it does not test
whether a website is accessible, and nothing here calls a college in breach.
