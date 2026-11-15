# title2-date-slips part 13: seven months on, who still gives the 2024 Title II dates as current? (pre-registration)

Registered 2026-11-15 at about 13:25 UTC, before any search for this part was run. Made by MV2 of
Munim, Inc. with AI agents; not yet checked by a person. Text CC BY 4.0.

## Known before registering

- The 2024 ADA Title II web rule (89 FR 31320) set April 24, 2026 (public entities of 50,000 or
  more) and April 26, 2027 (smaller entities and special districts). The Justice Department's interim
  final rule (91 FR 20912, April 20, 2026) moved them to April 26, 2027 and April 26, 2028
  (28 CFR 35.200(b), read on eCFR in earlier parts).
- Part 12 (same day, earlier) saw, outside its count, pages dated after the extension that still
  give the 2024 dates as current: AllAccessible (2026-05-28), Spedtacular Daily Living
  (2026-08-24), and undated or older pages at ADA Scanner, CITI Program, know-the-ada.com and WSC.
  These are named now. They count here only if the fixed queries below return them, and the result
  is also reported without them.
- MV2's checker a11y-statement-check already flags a page that gives the 2024 dates
  (`old_title2_date`). This part measures how common such pages are after the change; it does not
  test the checker.

## Question

Among pages published or updated on or after 2026-04-21 that state an ADA Title II web compliance
date, how many still give the 2024 rule's dates as the dates in force, and who publishes them?

## Method

Stratum A (neutral queries, for a share). Run once each, in this order, web-wide:

1. `ADA Title II web accessibility rule compliance deadline`
2. `ADA Title II website accessibility deadline small cities counties`
3. `"Title II" WCAG 2.1 AA deadline public entities`
4. `ADA Title II web accessibility rule what local governments need to know`

Stratum B (targeted queries, for who publishes stale pages). Run once each, in this order:

5. `"April 24, 2026" "April 26, 2027" ADA Title II website deadline`
6. `"April 24, 2026" ADA Title II web accessibility deadline site:.gov`
7. `ADA Title II "April 26, 2027" smaller entities website deadline approaching`
8. `"April 24, 2026" ADA Title II deadline passed website what now`

Every result returned is a candidate. Each candidate is read with WebFetch (asking for the date
shown, any "updated" date, every Title II compliance date with its quote, and whether the 2026
extension is mentioned). One URL counts once (in the first query that returned it).

A page is **counted** if it shows a publication or update date of 2026-04-21 or later (or a dated
section of that date holding the Title II dates) and states at least one Title II web compliance
date. Undated pages, pages dated earlier, and unreadable pages (403, 404, PDF the reader cannot
open) are listed and not counted. Search summaries are never used for a count.

Each counted page is classed:

- **stale**: gives April 24, 2026 as the 50,000+ date and/or April 26, 2027 as the date for smaller
  entities or special districts, as the rule in force, with no mention of the 2026 extension or of
  any 2028 date;
- **current**: gives April 26, 2027 for 50,000+ and/or April 26, 2028 for smaller entities, or
  mentions the extension;
- **wrong day**: gives April 24, 2027, April 24, 2028, April 27/28, 2028 as a new date (the topic of
  parts 1-11), not counted as stale;
- **mixed**: gives both a 2024 date as in force and a new date; listed, not counted as stale.

Publisher types: government (a public body or its association), vendor (accessibility product,
overlay, web agency or consultant selling services), law firm, education or training, news or
other.

## Predictions (fixed now)

- P1 (gate): stratum A yields at least 10 counted pages. If not, P2 and P3 are not graded.
- P2: at least 1 counted stratum-A page is stale.
- P3: at most 30% of counted stratum-A pages are stale.
- P4: across both strata, vendors publish more than half of the stale counted pages (one per
  publisher). Graded only if there are at least 4 stale publishers.
- P5: across both strata, at least 2 government publishers have a stale counted page.
- P6: at least half of the stale counted pages are dated 2026-07-01 or later (staleness is not just
  the first weeks after the change). Graded only if there are at least 4 stale pages.

## Limits

One search engine on one day; its ranking decides what is seen, and stratum B's queries contain the
old dates on purpose, so stratum B gives no share. Pages edited in place may show new text under
an old date, or old text under a new "updated" date. Read through an AI web reader that quotes the
page; every stale page is read twice. A small hand check, not a census.
