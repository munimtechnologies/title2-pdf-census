# state-pages: what do US state and territory governments' accessibility pages say? (pre-registration)

Registered 2026-11-11, before any state or territory government website was read for this study.
Script: `state_pages.py` 0.1.0 with its offline tests (`test_state_pages.py`). It reads each site with
the unchanged `a11y_pages.py` 0.1.0 (the rules of [results/a11y-pages](../a11y-pages/)) and
`statement_check.py` 0.1.0 already in this repository. Made by MV2 of Munim, Inc. with AI agents; not
yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0. The frame comes from
CISA's public .gov registry list (cisagov/dotgov-data, CC0-1.0).

## Why

The ADA Title II web rule (28 CFR 35.200, 2024) adopts WCAG 2.1 Level AA for state and local
governments. The Justice Department's interim final rule of April 20, 2026 moved the first compliance
date from April 24, 2026 to April 26, 2027 for public entities of 50,000 or more people, which
includes every state government. MV2's earlier censuses here read the accessibility pages of US
cities, counties and towns: for those of 50,000 or more, 283 of 508 pages that name a WCAG version
(55.71%) name WCAG 2.0 as the highest, 179 of 808 pages read (22.15%) name Title II, 280 of 808
(34.65%) carry a vendor's stock sentence ("We work to comply with Section 508 as well as WCAG 2.0 A
and AA"), and 815 of 1,195 home pages read (68.2%) link to an accessibility page. No state government
was in those censuses. Searches on 2026-11-11 found 2026 reports that scan government websites for
WCAG failures (Accessible Compliance Group, WPPersona, AccessLumens), but no published count, page by
page, of which WCAG version, rule or date state government accessibility pages name.

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job downloads `current-full.csv` from cisagov/dotgov-data (main branch, updated daily) and keeps
every row whose domain type is exactly `State or territory`, one row per distinct domain, sorted by
domain. Only the domain, organization, suborganization, city and state columns are kept; the list's
security contact email column is never copied into a row or written anywhere. Rows that contain the
publishing tool's blocked word are dropped and counted. Each row gets a kind from its organization
and suborganization names: court (court, courts or judicia...), legislature (legislat..., general
assembly, senate, house of representatives or delegates), otherwise executive or other. The job writes
`frame.csv` and records the source file's size and SHA-256.

The unit is a registered .gov domain, not an agency: an agency on a subdomain of a state portal
(for example a department under a state's own .gov domain) is not a separate row, some agencies use
domains outside .gov, and some domains only redirect to another site. This is the registry's own
list of state and territory domains, not a list of every state body.

What was looked at before registering, none of it on a state site: the list's header line and, through
an automated summary of two slices of the file, about a dozen state or territory rows (domains and
organization names only, for example agutah.gov, akcourts.gov, azdeq.gov, coleg.gov,
guamlegislature.gov, kansas911.gov, mnretire.gov and 10mbooknc.gov), plus a rough estimate that the
type has somewhere around 1,500 to 2,000 rows. The README summaries of the earlier city censuses
were read; no state government page was fetched.

## Method

- Order and size: the frame's domains sorted by SHA-256 of the seed `state-pages-2026-11-11` plus the
  domain; at most 2,000 are read (if the frame is no larger, all of them). 24 sites at a time; within
  a site one request at a time with a 1-second pause after each. Sites not started within 150 minutes
  count as not started.
- Each domain: `robots.txt` first (a page it disallows is not requested), then the home page
  `http://<domain>/`, or `http://www.<domain>/` if the first gets no answer at all (redirects are
  followed). On a home page that answers 200 with HTML, the accessibility page is picked by the
  census's link rules unchanged (`a11y_pages.candidates`: same site only; ranked path names
  accessibility, then link text, then Section 508, then ADA), and up to 3 candidates are tried in that
  order. A page is read when it answers 200 with HTML and has at least 200 characters of visible
  text.
- Reading: `a11y_pages.classify` (WCAG versions named and the highest, Section 508, Title II, April
  24, 2026 and April 26, 2027) and `statement_check.check_text` (the stock sentence, April 26, 2028,
  an email address or phone number, findings), both unchanged.
- Graded units: distinct pages (page address without scheme, `www.`, letter case or a trailing
  slash; the first domain in domain order is kept) and distinct home sites (the host the home page
  ended on, without `www.`), because several domains often lead to one site or one statewide page.
- Stored per domain: frame columns, statuses, the address and SHA-256 of the page read, the flags
  above, and short snippets around a WCAG version or a date with email addresses and phone numbers
  removed. No other page text and no person's name is stored.

## Gates

- P0: this file is on main, and main's `state_pages.py`, `a11y_pages.py` and `statement_check.py`
  are byte for byte the job's copies.
- C1 (checked on the frame before any website is read; if it fails, no website is requested): 1,000
  to 4,000 eligible domains.
- Each prediction is graded only with enough data: ST1 and ST2 with at least 100 versioned pages
  (distinct pages that name a WCAG version), ST3 and ST4 with at least 200 distinct pages, ST5 with at
  least 500 distinct home sites.

## Predictions (fixed before any website is read)

- ST1 (at most 40% of versioned pages name WCAG 2.0 as the highest version). Cities of 50,000 or
  more: 55.71%. This predicts that states, many of which have their own IT accessibility standards,
  are ahead of large cities.
- ST2 (WCAG 2.1 is the highest version on more versioned pages than 2.0, and on more than 2.2).
- ST3 (at most 22.15% of distinct pages name Title II), the large-city share: state pages are
  predicted to cite state law and Section 508 more than the federal rule.
- ST4 (at most 5% of distinct pages carry the stock sentence), against 34.65% for large cities,
  whose sentence comes from a local-government website vendor.
- ST5 (at least 70% of distinct home sites link to an accessibility page on the same site), against
  68.2% of large cities' home pages.

The result is published whether the predictions hold or not.

## Described, not graded

Home status and how it was reached; distinct home sites, pages and texts; how each page was found;
WCAG versions named; findings; overlay scripts on home pages; Section 508; an email address or phone
number; pages giving April 24, 2026, April 26, 2027 or April 26, 2028, and April 24, 2026 alone; all
of these by kind (court, legislature, executive or other) and by state or territory.

## Limits

Only what the registry lists as a state or territory domain on the day is read, and only one page per
site, once, without running JavaScript. An accessibility page linked only from another page, kept on
another site (many agency sites link to a statewide policy elsewhere), published as a PDF, or behind
a firewall that refuses this reader is missed, so a page not found is not proof that a site has none.
The link rules can pick a page about the ADA in general (for example an ADA coordinator page) rather
than the website; it is read and counted all the same, as in the city census. A version or date is
what the page says, not what the site meets. This counts what pages say; it does not test whether a
website is accessible, and nothing here calls a government in breach.
