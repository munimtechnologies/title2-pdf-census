# transit-pages: what do US public transit authorities' accessibility pages say? (pre-registration)

Registered 2026-11-12, before any transit agency website was read for this study.
Script: `transit_pages.py` 0.1.0 with its offline tests (`test_transit_pages.py`). It reads each
site with the unchanged `state_pages.py` 0.1.0 crawler (the rules of
[results/state-pages](../state-pages/)), which itself uses the unchanged `a11y_pages.py` 0.1.0 and
`statement_check.py` 0.1.0 already in this repository. Made by MV2 of Munim, Inc. with AI agents; not
yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0. The frame comes from the
Federal Transit Administration's National Transit Database (NTD), published by the US Department of
Transportation on data.transportation.gov.

## Why

A public transit authority is a public entity under the ADA, so two sets of rules meet on its
website. The Transportation Department's rules for transit service (49 CFR part 37) cover
paratransit and information in accessible formats, and transit sites have long had "ADA" or
"Accessibility" pages about riding: lifts, paratransit eligibility, reduced fares. The Justice
Department's Title II web rule (28 CFR 35.200, 2024) adds WCAG 2.1 Level AA for the website itself;
the interim final rule of April 20, 2026 (91 FR 20902) moved its compliance dates from April 24,
2026 and April 26, 2027 to April 26, 2027 and April 26, 2028. Which date applies to a given
authority depends on how the rule counts it (every special district government gets the later
date; an authority that is part of a state, or of a city or county of 50,000 or more, may get the
earlier one), so this census does not judge whether a date a page gives is the right one.

MV2's earlier censuses here read US cities, counties and towns, school districts, states (planned)
and special-district .gov domains. In the special-district census (results/special-districts),
125 of 341 pages read (36.66%) name WCAG at all, 345 of 873 home sites (39.52%) link to an
accessibility page, 8 of 341 pages (2.35%) name Title II, 48 of 114 versioned pages (42.11%) name
WCAG 2.0 as the highest, and 2 of 341 pages (0.59%) give any of the three dates. For cities and
counties of 50,000 or more, 815 of 1,195 home sites (68.20%) link to an accessibility page; for
governments of 10,000 to 49,999, 1,053 of 1,942 (54.22%). Searches on 2026-11-12 found vendor scans
that count automated WCAG errors on transit sites (one 2026 report scanned 65 transit authorities),
but no published count, page by page, of what transit agencies' accessibility pages say: whether the
page a rider reaches from the home page is about the website at all, which WCAG version it names, or
whether it names Title II or its dates.

## Frame (a rule fixed now; built and saved by the job before any website is read)

The job downloads the 2024 NTD Annual Data "Reporter Agency Information" table (dataset `ccvf-fykn`)
as JSON from `https://data.transportation.gov/resource/ccvf-fykn.json?$limit=5000&$order=ntd_id` and
keeps every reporter whose organization type is exactly `Independent Public Agency or Authority of
Transit Service`. Each website cell becomes a host: a missing scheme is read as `http://`, the
port, path and a leading `www.` are dropped, and a cell that is empty, contains a space, is an IP
address or has no dot counts as no website. One row per distinct host, sorted by host; the first
agency by NTD ID names the row and `agencies` counts how many agencies share the host. Kept: host,
agency name, city, state, NTD ID, reporter type and the website cell. No street address or other
column is written anywhere. Rows that contain the publishing tool's blocked word are dropped and
counted. Each row gets a kind from its reporter type (`full`, `reduced`, `rural`, otherwise
`other`); kinds are described, never graded. The job writes `frame.csv` and records the source's
size and SHA-256.

The unit is a website host. Agencies of other organization types (city or county departments,
private non-profits, tribes, state departments and others) are left out, so this is the NTD's own
list of independent transit authorities, not a sample of every transit provider. Some authorities
also appear in the special-district census when they hold a .gov domain registered as a special
district; they are read again here, not removed.

What was looked at before registering, none of it on an agency site (2026-11-12, about 17:25-17:45
UTC, through automated summaries of the data portal's API): the table's field names from two sample
records (Riverside County Transportation Commission, an MPO giving rctc.org, and the Pueblo of
Isleta, a tribe giving a riometro.org page); the counts of reporters by organization type and
reporter type (436 of 2,914 reporters are independent public agencies or authorities of transit
service); and a count showing that 435 of those 436 give a website. No list of their websites was
read and no transit page was fetched.

## Method

- Order and size: the frame's hosts sorted by SHA-256 of the seed `transit-pages-2026-11-12` plus
  the host; at most 1,000 are read (if the frame is no larger, all of them). 24 sites at a time;
  within a site one request at a time with a 1-second pause after each. Sites not started within
  150 minutes count as not started.
- Each host, exactly as in the state census (`state_pages.crawl_site`, unchanged): `robots.txt`
  first (a page it disallows is not requested), then the home page `http://<host>/`, or
  `http://www.<host>/` if the first gets no answer at all (redirects are followed). On a home page
  that answers 200 with HTML, the accessibility page is picked by the census's link rules unchanged
  (`a11y_pages.candidates`: same site only; ranked path names accessibility, then link text, then
  Section 508, then ADA), and up to 3 candidates are tried in that order. A page is read when it
  answers 200 with HTML and has at least 200 characters of visible text.
- Reading: `a11y_pages.classify` (WCAG named at all, WCAG versions named and the highest, Section
  508, Title II, April 24, 2026 and April 26, 2027) and `statement_check.check_text` (the vendor
  stock sentence, April 26, 2028, an email address or phone number, findings), both unchanged.
- Topic (described, not graded), from the page's address only, first match wins: `paratransit`
  (paratransit, dial-a-ride, demand response, access-a-ride, ada-ride, ada-service), `website`
  (web, site, digital or online next to accessibility, or accessibility followed by statement, web,
  site, digital or online), `accessibility`, `ada` (ada as its own word), otherwise `other`.
- Graded units: distinct pages (page address without scheme, `www.`, letter case or a trailing
  slash; the first host in host order is kept) and distinct home sites (the host the home page
  ended on, without `www.`).
- Stored per host: frame columns, statuses, the address and SHA-256 of the page read, the flags
  above, the topic, and short snippets around a WCAG version or an April 2026 or April 2027 date
  with email addresses and phone numbers removed. No other page text and no person's name is stored.

## Gates

- P0: this file is on main, and main's `transit_pages.py`, `state_pages.py`, `a11y_pages.py` and
  `statement_check.py` are byte for byte the job's copies.
- C1 (checked on the frame before any website is read; if it fails, no website is requested): 250
  to 600 eligible hosts.
- Each prediction is graded only with enough data: TR1, TR3 and TR5 with at least 100 distinct
  pages, TR2 with at least 150 distinct home sites, TR4 with at least 40 versioned pages (distinct
  pages that name a WCAG version).

## Predictions (fixed before any website is read)

- TR1 (at most 35% of distinct pages name WCAG at all). Transit authorities' "Accessibility" and
  "ADA" links are predicted to lead mostly to pages about riding, not about the website.
- TR2 (at least 50% of distinct home sites link to an accessibility page on the same site), more
  than special districts (39.52%), because transit authorities have long published ADA rider pages.
- TR3 (at most 10% of distinct pages name Title II).
- TR4 (of versioned pages, at most 40% name WCAG 2.0 as the highest version).
- TR5 (at most 5% of distinct pages give any of the three Title II dates): April 24, 2026, April 26,
  2027 or April 26, 2028.

The result is published whether the predictions hold or not.

## Described, not graded

Home status and how it was reached; distinct home sites, pages and texts; how each page was found;
the topic of each page and every count below by topic; WCAG versions named; findings; overlay
scripts on home pages; Section 508; the vendor stock sentence ("We work to comply with Section 508 as
well as ..."); an email address or phone number; which combination of the three dates each page
gives; all of these by kind (reporter type) and by state; how many agencies the hosts read stand for.

## Limits

Only the NTD's independent transit authorities that reported for 2024 and gave a website are read,
and only one page per site, once, without running JavaScript. An accessibility page linked only from
another page, kept on another site, published as a PDF, or behind a firewall that refuses this
reader is missed, so a page not found is not proof that a site has none. A transit site may have both
a rider page and a website statement; the link rules read only the first that answers, so a rider
page read does not mean the site has no website statement. The topic is read from the address alone
and can be wrong. A page giving a date may be quoting the rule in passing, or giving its own "last
updated" day; the snippets let a reader check. A version or date is what the page says, not what the
site meets. This counts what pages say; it does not test whether a website is accessible, and
nothing here calls an agency in breach.
