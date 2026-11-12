# hc-pages: what do US health centres' accessibility pages say about Section 504 and its dates? (pre-registration)

Registered 2026-11-12, before any health centre website was read for this study.
Script: `hc_pages.py` 0.1.0 with its offline tests (`test_hc_pages.py`). It reads each site with
the unchanged `state_pages.py` 0.1.0 crawler (the rules of [results/state-pages](../state-pages/)),
which itself uses the unchanged `a11y_pages.py` 0.1.0 and `statement_check.py` 0.1.0 already in this
repository, and adds one reading of its own: the Section 504 patterns of a11y-statement-check 0.9.0
(github.com/munimtechnologies/a11y-statement-check), copied into `hc_pages.py`. Made by MV2 of Munim,
Inc. with AI agents; not yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0.
The frame comes from HRSA's public data downloads (U.S. Department of Health and Human Services,
Health Resources and Services Administration).

## Why

Section 504 of the Rehabilitation Act covers every recipient of HHS funding. HHS's 2024 rule (89 FR
40193, May 9, 2024; 45 CFR 84.84) adopts WCAG 2.1 Level AA for recipients' websites and mobile apps.
Its first web dates were May 11, 2026 (recipients with fifteen or more employees) and May 10, 2027
(fewer than fifteen). An HHS interim final rule published on May 11, 2026 (91 FR 25507) moved them by
a year, to May 11, 2027 and May 10, 2028 (45 CFR 84.84(b)(1) and (2) as amended, read on eCFR on
2026-11-12). Health centres funded or designated under HRSA's Health Center Program (Section 330
awardees and look-alikes, about 1,500 organisations) are HHS recipients, and most are private
nonprofits, so the ADA Title II rule that MV2's earlier censuses here studied does not usually
reach them; Section 504 does.

MV2's earlier censuses read US cities, counties and towns, school districts, state governments,
special districts and public colleges, never health care. For context, of the 1,657 cities and
counties of 50,000 or more: 815 of 1,195 home pages read (68.20%) link to an accessibility page; 494
of 1,195 (41.34%) load one of the six overlay marks below; and 179 of 808 pages read (22.15%) name
Title II. Searches on 2026-11-12 found consultants' and vendors' guides to the extension, and one
vendor report (an automated WCAG scan of about 300 websites of organisations under Section 504, 235
of them in health care), but no published count, page by page, of what health centres' accessibility
pages say: whether they name Section 504, which WCAG version they name, or which Section 504 date
they give. One guide gives the later date as May 11, 2028 rather than eCFR's May 10, 2028, so pages
giving May 11, 2028 are counted too (described, not graded).

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job downloads `Health_Center_Service_Delivery_and_LookAlike_Sites.csv` from
https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv
(HRSA's "Health Center Service Delivery and Look-Alike Sites" file, refreshed daily; one row per
site). Each column is matched by the long name or the short name of HRSA's data dictionary, without
regard to letter case or spacing. Three columns are needed: Health Center Number
(`HCP_MERGED_GRANT_LAL_KEY`), Site Web Address (`SITE_URL`) and Site Status Description
(`HCC_STATUS_DESC`); if one is missing, the job stops and no website is read. Three more are read if
present: Health Center Name (`HCP_ORG_NM`), Health Center Organization City (`HCP_ORG_CITY`) and
Health Center Organization State (`HCP_ORG_ST_ABBR`). No other column is read: the site's street
address, phone number, and the names of people in the file are never read into a row or written
anywhere.

A site counts when it has a Health Center Number and its status begins with "active" (any letter
case). Its web address is reduced to its host, in lower case, without one leading `www.`; a site with
no usable host is counted and left out, and so is a host on one of these sites, which are not a
health centre's own: `facebook.com`, `fb.com`, `instagram.com`, `linkedin.com`, `twitter.com`, `x.com`,
`youtube.com`, `google.com`, `yelp.com`, `linktr.ee`, `hrsa.gov` (and their subdomains). Each health
centre (Health Center Number) gets one host: the one its counted sites list most often (ties: the
alphabetically first). Where two health centres get the same host, the lower Health Center Number
keeps it and the other is counted. Rows that contain the publishing tool's blocked word are dropped
and counted. Each row's kind is `awardee` (number begins H80), `look_alike` (LAL) or `other`; kinds
are described, never graded. The job writes `frame.csv` and records the file's size and SHA-256.

What was looked at before registering, none of it on a health centre site: web searches on
2026-11-12 (about 04:20-04:50 and 07:00-07:30 UTC); eCFR's text of 45 CFR 84.84; HRSA's data
downloads page (the file's name, size and refresh); an automated fetch of the CSV that stopped
because the file is over 10 MB (no row was read); the metadata workbook, which could not be read as
text; a third-party codebook of the file's columns (Penn State LionVu, `FQHC_Codebook.csv`), from
which the column names above are taken; and the README and earlier results of this repository. No
health centre page was fetched, and the CSV's real header has not been seen: if it uses neither name
for a needed column, the job stops at "frame not read" and a corrected script is registered openly.

## Method

- Order and size: the frame's hosts sorted by SHA-256 of the seed `hc-pages-2026-11-12` plus the
  host; at most 2,500 are read (if the frame is no larger, all of them). 24 sites at a time; within a
  site one request at a time with a 1-second pause after each. Sites not started within 150 minutes
  count as not started.
- Each host, exactly as in the state census (`state_pages.crawl_site`, unchanged): `robots.txt`
  first (a page it disallows is not requested), then the home page `http://<host>/`, or
  `http://www.<host>/` if the first gets no answer at all (redirects are followed). On a home page
  that answers 200 with HTML, the accessibility page is picked by the census's link rules unchanged
  (`a11y_pages.candidates`: same site only; ranked path names accessibility, then link text, then
  Section 508, then ADA), and up to 3 candidates are tried in that order. A page is read when it
  answers 200 with HTML and has at least 200 characters of visible text.
- Reading: the state census's reading unchanged (`a11y_pages.classify` and
  `statement_check.check_text`: WCAG versions and the highest, Section 508, Title II and its three
  dates, the vendor stock sentence, contact details, findings), plus a11y-statement-check 0.9.0's
  Section 504 reading: whether the page names Section 504, 45 CFR part 84, HHS or Health and Human
  Services; which of the four Section 504 web dates it gives (May 11, 2026; May 10, 2027; May 11,
  2027; May 10, 2028, in the written forms that tool reads); and old_504, a page that names Section
  504 and gives an old date and neither new one (that tool's old_504_date note). Also counted: Section
  1557 named, and May 11, 2028 given.
- A page is "Section 504 dated" when it names Section 504, 45 CFR part 84 or HHS and gives one of
  the four Section 504 web dates.
- Overlay marks on home pages, as in the city census: `userway`, `accessibe`, `acsbapp`,
  `audioeye`, `equalweb`, `reciteme` (six marks, five vendors).
- Graded units: distinct pages (page address without scheme, `www.`, letter case or a trailing
  slash; the first host in host order is kept) and distinct home sites (the host the home page ended
  on, without `www.`).
- Stored per host: the frame columns, statuses, the address and SHA-256 of the page read, the flags
  above, and short snippets around a WCAG version, an April date or a Section 504 date, with email
  addresses and phone numbers removed. No other page text and no person's name is stored.

## Gates

- P0: this file is on main, and main's `hc_pages.py`, `state_pages.py`, `a11y_pages.py` and
  `statement_check.py` are byte for byte the job's copies.
- C1 (checked on the frame before any website is read; if it fails, no website is requested): 700
  to 2,500 eligible hosts.
- Each prediction is graded only with enough data: HC1 and HC5 with at least 500 distinct home
  sites, HC2 and HC3 with at least 200 distinct pages, HC4 with at least 100 versioned pages
  (distinct pages that name a WCAG version).

## Predictions (fixed before any website is read)

- HC1 (at most 50% of distinct home sites link to an accessibility page on the same site). Large
  cities: 815 of 1,195 (68.20%). Health centres are smaller organisations without a shared
  government website platform, so fewer are predicted to link one.
- HC2 (at least 25% of distinct pages name Section 504, 45 CFR part 84 or HHS). Large cities named
  their own rule, Title II, on 179 of 808 pages (22.15%); health centres' pages are predicted to name
  theirs at least as often, since many fold the accessibility page into a nondiscrimination notice.
- HC3 (at most 5% of distinct pages give one of the four Section 504 web dates): few health centre
  pages are predicted to give any compliance date at all.
- HC4 (WCAG 2.1 is the most common highest version): more versioned pages name WCAG 2.1 as the
  highest than name 2.0, and more than name 2.2.
- HC5 (at most 30% of distinct home sites load one of the six overlay marks). Large cities: 494 of
  1,195 (41.34%), many through one government platform's bundled overlay; health centres are
  predicted to load overlays less often.

The result is published whether the predictions hold or not.

## Described, not graded

Home status and how it was reached; distinct home sites, pages and texts; how each page was found;
WCAG versions named; findings; overlays on home pages by vendor; Section 508; Section 1557; Title II
and its three dates; which combination of the four Section 504 dates each page that names Section
504 gives; old_504 (pages still giving only an old Section 504 date); May 11, 2028; the vendor stock
sentence; contact details; all of these by kind (awardee or look-alike) and by state.

## Limits

Only health centres with an active site and a usable web address in HRSA's file on the day the job
runs are read, by the host their sites list most often, and only one page per site, once, without
running JavaScript. An accessibility page linked only from another page, kept on another site,
published as a PDF, or behind a firewall that refuses this reader is missed, so a page not found is
not proof that a health centre has none. The link rules can pick a page about disability services,
patient rights or the ADA in general rather than the website; it is read and counted all the same,
as in the city census. "HHS" on a page may come from a complaint address rather than the web rule,
so HC2 counts what pages name, not what they claim. Which Section 504 date applies depends on a
health centre's number of employees, which this study does not know, so it grades only whether a
page gives any date and describes whether it still gives an old one. A version or date is what the
page says, not what the site meets. This counts what pages say; it does not test whether a website
is accessible, and nothing here calls a health centre in breach.
