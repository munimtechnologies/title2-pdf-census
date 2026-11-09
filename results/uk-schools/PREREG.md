# school-stock: unfinished accessibility statement templates on England's school websites (pre-registration)

Registered 2026-11-09, before any school website was read for this study. Script:
`school_stock.py` 0.1.0 with its offline tests (`test_school_stock.py`). Made by MV2 of Munim, Inc.
with AI agents; not yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0.

## Why

MV2's US censuses in this repository found vendor statement templates left unfinished at one
stock address: 235 of 5,243 US local-government hosts (stock-153, stock-revize) and 1,067 of
11,581 US school-district hosts (district-stock), where one vendor's 2017 template still says
"the Your School website". Nobody has counted the same thing in the UK.

While designing this study, web searches on 2026-11-09 surfaced statement pages on English school
websites built by Juniper Websites (Juniper Education, which says it runs the websites of over
7,500 schools). They follow one template at `/accessibility-statement/` and many keep its fields
unfilled: "This website is run by [School Name] and this statement applies to [Website Link and
Date]", "Email: [Accessibility Email Address]", "Phone: [School Phone Number]", "Mailing Address:
[School Mailing Address]", "This statement was first prepared on [Date]", and even on pages that
are otherwise filled in, "[School Name] is committed to making its website accessible". A longer
variant still carries its editing notes ("[This is a sample accessibility statement that you may
want to use. ... Prior to publication, please remove this text ..."). About 20 such pages were
seen before this plan and at least 10 kept a placeholder; they are inside the frame and are
counted like any other host. Searches found no count of unfinished statements on UK school
websites (the closest work, accessibility.build's 2026 review of 303 UK council statements,
scores which sections a statement has and counts no placeholders).

## Legal scope

The Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018
(SI 2018/952) do not apply to the websites of schools or nurseries (regulation 4(1)(c)), except
for content relating to essential online administrative functions. A school's statement is
therefore mostly voluntary. This study counts what schools that publish a statement at this
address left in it. It does not call a missing or unfinished school statement a breach, and a
placeholder says nothing about whether a website is accessible; it says the statement was never
finished.

## Frame (fixed before any page is read)

`uk_frame.py` 0.1.0 (sealed job uk-frame-v1) downloaded the Department for Education's Get
Information about Schools file `edubasealldata20261109.csv` (64,737,310 bytes, SHA-256
67557abd9844...; Open Government Licence v3.0) and kept every open establishment that lists a
website: 24,659 establishments on 23,802 distinct hosts (`www.` removed), in
`frame-part1.csv` (9,891 rows, SHA-256 fe6568ec3ee7...), `frame-part2.csv` (10,088 rows,
fbb89b0c61a9...) and `frame-part3.csv` (4,680 rows, e0b1e8ddc949...), with `frame.json`. Only
establishment fields are kept (no person's name, email or phone). Each host is asked once, for the
establishment with the lowest URN that lists it; the number of establishments on the host is
recorded. Rows containing one word that MV2's publishing tool blocks are dropped first (none were
in the frame when it was built; at most 5 may be).

## Method

- Order: hosts sorted by SHA-256 of the seed `school-stock-2026-11` plus the host, so one vendor's
  servers are not asked one host after another. 8 hosts at a time; for each host one request at a
  time with a 1-second pause after each.
- Per host: `robots.txt` first (no answer at all ends the host as `http_0`; 401 or 403 means
  nothing is allowed), then `/accessibility-statement/` on the scheme and host the GIAS file
  lists (http when none is given; redirects followed). A 429 or 503 is asked once more after 30
  seconds. The user agent names a11y-statement-check, MV2, Munim, Inc. and mv2@munimtech.com.
- A page counts as read (`ok`) when it answers 200 with HTML, did not redirect to a home page,
  has at least 200 characters of visible text and mentions "accessib".
- Rules: the page text is read with `statement_template_check.py 0.3.0`, byte-identical to
  `skills/accessibility-statement-check/statement_template_check.py` in a11y-statement-check
  release v0.3.0 (the job compares the two before reading anything). Its placeholder verdict is
  the graded measure. Juniper's own fields that 0.3.0 does not know ("[Website Link and Date]",
  "[Accessibility Email Address]", "[School Phone Number]", "[School Mailing Address]",
  "(School Name)", the sample notice and its editing notes) are reported as a separate,
  described measure and never graded.
- Markers (described): the template's closing sentence ("... values diversity and inclusion and is
  committed to providing an accessible online experience"), filled in or not; the vendor's credit
  ("School Website by Juniper Websites" or a link to the vendor) anywhere in the HTML; a
  statement naming the vendor's build address (`*.webN.juniperwebsites.co.uk`) instead of the
  school's; GOV.UK's compliance sentence ("This website is fully / partially / not compliant with
  the Web Content Accessibility Guidelines ...") and the highest WCAG version the page names.
- Stored: per host the status, final address, text length and SHA-256 of the text, rule ids and
  flags. No page text and no person's name is stored.

## Gates (nothing is graded unless all hold)

- P0: this file is on main and the checker matches the release.
- F1: the three frame parts match the hashes above, 24,659 rows, 23,802 hosts (fewer by at most
  the dropped rows).
- G1 (at least 80% of hosts answered): any HTTP status, including a robots.txt answer.

## Predictions (fixed before any page is read)

- J1 (at least 400 hosts) serve a page at `/accessibility-statement/` with a 0.3.0 placeholder.
- J2 (at least 80% of those pages carry the Juniper Websites credit), graded only with at least
  50 such pages.
- J3 (at least 40% of read pages carrying the Juniper template's closing sentence keep a 0.3.0
  placeholder), graded only with at least 100 such pages.
- J4 (at least 50% of read pages using GOV.UK's compliance sentence name WCAG 2.2 as the highest
  version), graded only with at least 200 such pages. GOV.UK's current sample statement names 2.2 AA;
  no published count was found of how many UK statements name it.

The result is published whether the predictions hold or not.

## Described, not graded

Status of every host; read pages; pages with the credit, the closing sentence, the long variant,
GOV.UK wording; highest WCAG version; placeholder rule ids; distinct page texts among placeholder
pages (trusts share sites); placeholder pages served from another host; establishments behind the
placeholder hosts; placeholder pages by region, phase and establishment type group; pages with a
Juniper field, and with one but no 0.3.0 placeholder; build-address pages.

## Limits

One address only: statements elsewhere on a site, or on a trust's site that the school's own
host does not redirect to, are not seen, so this is a floor for these templates, not a count of
school statements. Other vendors' templates are counted only where 0.3.0's rules see their fields.
The GIAS website field is what schools report and can be out of date. A page is read once, on one
day.
