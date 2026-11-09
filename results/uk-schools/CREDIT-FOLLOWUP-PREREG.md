# school-credit: which vendor brand do England's unfinished school statements credit? (pre-registration of a follow-up)

Registered 2026-11-09, before the school-stock census (`PREREG.md` in this folder) has read any
school website, and before any page is read for this follow-up. Made by MV2 of Munim, Inc. with AI
agents; not yet checked by a person. This text and the data CC BY 4.0; code Apache-2.0.

## Why this follow-up exists

school-stock's prediction J2 says at least 80% of the hosts serving a statement with a
placeholder at `/accessibility-statement/` carry "the Juniper Websites credit". Its pinned script
(`school_stock.py` 0.1.0) looks for that credit with one pattern on the page's HTML:
"Juniper Websites", `juniperwebsites.co.uk` or `junipereducation.org`.

While preparing a later release of the checker on 2026-11-09, AI agents working in MV2's name
noticed that this pattern is narrower than the vendor. Juniper Websites is Juniper Education's
brand, formed from two school-website companies it bought in 2021: e4education and PrimarySite.
Live school statement pages built on the same template were seen crediting "School Website Design
by e4education" rather than "Juniper Websites". school-stock stores no page HTML, so its own
tables cannot be re-counted for the other two brands.

school-stock is graded exactly as it was registered; J2 keeps its pattern and its result is
published either way. This follow-up adds a separate, separately graded measure, fixed now, before
any data exist.

## Frame (fixed now)

The hosts in school-stock's published tables (`hosts-partN.csv`) whose row has `status` `ok` and
`placeholder` true: the hosts behind J1. Nothing else is read.

## Gates (nothing is read unless all hold)

- C0: school-stock's result is published and its gates P0, F1 and G1 held.
- C1: at least 50 placeholder hosts (J2's own minimum).
- C2: the re-read starts no more than 21 days after school-stock's crawl finished.

## Method

- Script: `school_credit.py` 0.1.0 with offline tests, committed to this repository before it reads
  anything. It reuses school-stock's request rules unchanged: `robots.txt` first, then
  `/accessibility-statement/` on the scheme and host in the table, 8 hosts at a time, one request
  at a time per host with a 1-second pause, one retry after 30 seconds on 429 or 503, the same
  user agent naming a11y-statement-check, MV2, Munim, Inc. and mv2@munimtech.com.
- Each host's page is read once. It counts as re-read when it passes school-stock's own `ok` test
  (200 with HTML, no redirect to a home page, at least 200 characters of visible text, mentions
  "accessib") and still carries a placeholder under the same pinned checker,
  `statement_template_check.py` 0.3.0 (release v0.3.0). That set is the graded set.
- Credits, each searched case-insensitively in the whole HTML, as school-stock did:
  - `juniper`: school-stock's own `JUNIPER_CREDIT_RE`, unchanged.
  - `e4education`: the word `e4education` (which also matches its web addresses).
  - `primarysite`: the word `primarysite` written as one word (its brand and web addresses; two
    words, "primary site", are not counted, because ordinary text uses them).
  - `family`: any of the three.
- Stored per host: status, whether the text's SHA-256 equals school-stock's `text_sha256`, the
  four credit flags, and the placeholder rule ids. No page text and no person's name is stored.

## Predictions (fixed now)

- K1: at least 90% of the graded set carry a `family` credit.
- K2: at least 10% of the graded set carry an `e4education` or `primarysite` credit and no
  `juniper` credit, that is, school-stock's J2 pattern misses at least one in ten.
- K3: at least 90% of the graded set's pages are unchanged since school-stock's read (same
  text SHA-256).

Each is graded only if the graded set has at least 50 hosts. The result is published whether the
predictions hold or not, next to school-stock's result, and J2's grade is never changed by it.

## Described, not graded

Hosts not re-read and why; pages whose text changed and whether they lost every placeholder; each
credit alone and in combination; `family` credit among placeholder pages that do and do not carry
the Juniper template's closing sentence.

## Limits

A credit in the HTML shows who built or once built the site, not who wrote the statement. A page
read a second time may have changed; K3 says how much. The three patterns are fixed here from the
brands' names and may miss other wording (such as a credit given only as an image).
