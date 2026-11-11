# special-districts: what do US special districts' accessibility pages say, and which date do they give? (pre-registration)

Registered 2026-11-11, before any special district website was read for this study.
Script: `special_districts.py` 0.1.0 with its offline tests (`test_special_districts.py`). It reads
each site with the unchanged `state_pages.py` 0.1.0 crawler (the rules of
[results/state-pages](../state-pages/)), which itself uses the unchanged `a11y_pages.py` 0.1.0 and
`statement_check.py` 0.1.0 already in this repository. Made by MV2 of Munim, Inc. with AI agents; not
yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0. The frame comes from
CISA's public .gov registry list (cisagov/dotgov-data, CC0-1.0).

## Why

The ADA Title II web rule (28 CFR 35.200, 2024) adopts WCAG 2.1 Level AA for state and local
governments and gives two compliance dates: one for public entities of 50,000 or more people, and a
later one for smaller entities and for every special district government, whatever the population
it serves (ADA.gov explains that special districts have no Census population). The Justice
Department's interim final rule of April 20, 2026 (91 FR 20902) moved the first date from April 24,
2026 to April 26, 2027, and the special-district date from April 26, 2027 to April 26, 2028.

A special district (a water, sewer, fire, transit, park, library, hospital or similar district) that
gives April 24, 2026 on its accessibility page gives the large-government date, which never applied
to it; one that gives April 26, 2027 gives its old date, which is now the large-government date.
MV2's earlier censuses here read US cities, counties and towns, school districts and (planned) state
governments, never special districts. For context: of cities and counties of 50,000 or more, 283 of
508 pages that name a WCAG version (55.71%) name WCAG 2.0 as the highest, 179 of 808 pages read
(22.15%) name Title II, and 815 of 1,195 home pages read link to an accessibility page; of the 2,500
sampled governments of 10,000 to 49,999, 638 of 809 versioned pages (78.86%) name only WCAG 2.0, 94
of 1,042 pages (9.02%) name Title II, 1,053 of 1,942 home pages (54.22%) link to an accessibility or
ADA page, and only 3 pages give any compliance date. Searches on 2026-11-11 found the rule, ADA.gov
guidance and vendor pages selling websites to special districts, but no published count, page by
page, of what special districts' accessibility pages say or which compliance date they give.

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job downloads `current-full.csv` from cisagov/dotgov-data (main branch, updated daily) and keeps
every row whose domain type is exactly `Special district`, one row per distinct domain, sorted by
domain. Only the domain, organization, suborganization, city and state columns are kept; the list's
security contact email column is never copied into a row or written anywhere. Rows that contain the
publishing tool's blocked word are dropped and counted. Each row gets a rough kind from its
organization and suborganization names (first match wins: emergency, fire, water, transit, parks,
library, health, housing, otherwise other); kinds are described, never graded. The job writes
`frame.csv` and records the source file's size and SHA-256.

The unit is a registered .gov domain, not a district: most special districts in the United States
have no .gov domain (many use .org, .com or a county's site), so this is the registry's own list of
special-district .gov domains, not a sample of all special districts. Districts that took a .gov
domain may be better resourced than the rest.

What was looked at before registering, none of it on a district site: the list's header line and,
through automated summaries of three slices of the file (2026-11-11, about 15:30-15:45 UTC), the
domain type values and about ten special district rows (domains and organization names only, for
example bart.gov, chicagoparkdistrict.gov, lacera.gov, tvfr.gov, wmfrdmn.gov, zone7waterca.gov and
911lucascountyoh.gov), plus a rough estimate from character positions that the type has about 1,100
to 1,300 rows. The README of this repository was read; no special district page was fetched.

## Method

- Order and size: the frame's domains sorted by SHA-256 of the seed `special-districts-2026-11-11`
  plus the domain; at most 3,000 are read (if the frame is no larger, all of them). 24 sites at a
  time; within a site one request at a time with a 1-second pause after each. Sites not started
  within 150 minutes count as not started.
- Each domain, exactly as in the state census (`state_pages.crawl_site`, unchanged): `robots.txt`
  first (a page it disallows is not requested), then the home page `http://<domain>/`, or
  `http://www.<domain>/` if the first gets no answer at all (redirects are followed). On a home page
  that answers 200 with HTML, the accessibility page is picked by the census's link rules unchanged
  (`a11y_pages.candidates`: same site only; ranked path names accessibility, then link text, then
  Section 508, then ADA), and up to 3 candidates are tried in that order. A page is read when it
  answers 200 with HTML and has at least 200 characters of visible text.
- Reading: `a11y_pages.classify` (WCAG versions named and the highest, Section 508, Title II, April
  24, 2026 and April 26, 2027) and `statement_check.check_text` (the vendor stock sentence, April 26,
  2028, an email address or phone number, findings), both unchanged.
- Graded units: distinct pages (page address without scheme, `www.`, letter case or a trailing
  slash; the first domain in domain order is kept) and distinct home sites (the host the home page
  ended on, without `www.`).
- Stored per domain: frame columns, statuses, the address and SHA-256 of the page read, the flags
  above, and short snippets around a WCAG version or an April 2026 or April 2027 date with email
  addresses and phone numbers removed. No other page text and no person's name is stored.

## Gates

- P0: this file is on main, and main's `special_districts.py`, `state_pages.py`, `a11y_pages.py` and
  `statement_check.py` are byte for byte the job's copies.
- C1 (checked on the frame before any website is read; if it fails, no website is requested): 800
  to 3,000 eligible domains.
- Each prediction is graded only with enough data: SD1 with at least 100 versioned pages (distinct
  pages that name a WCAG version), SD2 and SD3 with at least 200 distinct pages, SD4 with at least
  400 distinct home sites, SD5 with at least 10 dated pages (distinct pages that give April 24, 2026,
  April 26, 2027 or April 26, 2028).

## Predictions (fixed before any website is read)

- SD1 (at least 50% of versioned pages name WCAG 2.0 as the highest version). Large cities: 55.71%;
  governments of 10,000 to 49,999: 78.86%. Special districts are predicted to look like smaller
  governments, not like the states.
- SD2 (at most 15% of distinct pages name Title II). Large cities: 22.15%; smaller governments:
  9.02%.
- SD3 (at most 5% of distinct pages give April 26, 2028), the date that now applies to every
  special district.
- SD4 (at most 60% of distinct home sites link to an accessibility page on the same site). Large
  cities: 815 of 1,195; smaller governments: 54.22%.
- SD5 (of dated pages, at most half give April 26, 2028): most special districts that give a date
  are predicted to give a date that is not theirs today (April 24, 2026 or April 26, 2027).

The result is published whether the predictions hold or not.

## Described, not graded

Home status and how it was reached; distinct home sites, pages and texts; how each page was found;
WCAG versions named; findings; overlay scripts on home pages; Section 508; the vendor stock sentence
("We work to comply with Section 508 as well as ..."; large cities 280 of 808, smaller governments
698 of 1,042); an email address or phone number; which combination of the three dates each page
gives; all of these by kind and by state.

## Limits

Only what the registry lists as a special district .gov domain on the day is read, and only one page
per site, once, without running JavaScript. An accessibility page linked only from another page,
kept on another site, published as a PDF, or behind a firewall that refuses this reader is missed,
so a page not found is not proof that a site has none. The link rules can pick a page about the ADA
in general (for example an ADA coordinator or transit paratransit page) rather than the website; it
is read and counted all the same, as in the city census. A page giving April 24, 2026 may be quoting
the old large-government date in passing, not claiming it for the district; the snippets let a reader
check. A version or date is what the page says, not what the site meets. This counts what pages say;
it does not test whether a website is accessible, and nothing here calls a district in breach.
