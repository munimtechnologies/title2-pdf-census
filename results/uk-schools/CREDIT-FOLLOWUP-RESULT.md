# school-credit result: which website companies England's unfinished school statements credit

Pre-registered in [CREDIT-FOLLOWUP-PREREG.md](CREDIT-FOLLOWUP-PREREG.md) (before school-stock read
any page) and its [addendum](CREDIT-FOLLOWUP-ADDENDUM.md) (after school-stock's result, before this
re-read). Run once by sealed job school-credit-v2 (22:06 to 22:16 UTC on 2026-11-09) with
`school_credit.py` 0.1.0, school-stock's own request rules (`school_stock.py` 0.1.0) and the pinned
checker `statement_template_check.py` 0.3.0. The run's table, result.json and result.txt are in
[credit-followup/](credit-followup/) unchanged, and `test_school_credit_result.py` at the root of
this repository re-grades every figure below from them. Made by MV2 of Munim, Inc. with AI agents;
not yet checked by a person. Code Apache-2.0; this text and the data CC BY 4.0.

**Two of the four predictions held (K3, L1) and two failed (K1, K2).**

**The 574 unfinished school statements that could be read again credit three website companies:
Juniper Education's school-website brands on 272 (47.39%), Greenhouse School Websites on 264
(45.99%) and Finalsite on 26 (4.53%)**; 12 (2.09%) credit none of the five names searched. No page
credits two of these companies.

The frame is the 667 hosts behind school-stock's J1 ([SCHOOL-STOCK-RESULT.md](SCHOOL-STOCK-RESULT.md)):
English school websites whose `/accessibility-statement/` kept a template placeholder on
2026-11-09. 574 of the 667 hosts were read again and still carry a placeholder (the graded set); 93
did not answer at all, and no page that was read had lost its placeholders.

## Predictions

| Prediction | Registered | Result | Held |
|---|---|---|---|
| K1: a Juniper-family credit (Juniper Websites, e4education or PrimarySite) | at least 90% | 272 of 574 (47.39%) | no |
| K2: an e4education or PrimarySite credit without the Juniper Websites credit | at least 10% | 0 of 574 (0.00%) | no |
| K3: same text as in school-stock's read | at least 90% | 563 of 574 (98.08%) | yes |
| L1: Greenhouse School Websites credit, among pages with the closing sentence, no Juniper credit and exactly GOV.UK's three sample fields | at least 80% (registered after one such page was seen) | 260 of 260 (100.00%) | yes |

All gates held: both registrations were on main, the checker and school-stock's script were the
pinned versions, school-stock's result and tables were published and matched, there were at least
50 hosts, and the re-read started within 21 days of school-stock's crawl.

## What failed and why

K1 assumed that nearly all of these pages came from one vendor. They do not: about half credit
Greenhouse School Websites, a different company.

K2 asked whether school-stock's Juniper credit pattern missed pages crediting the vendor's older
brands. It did not. Every page with an e4education credit (34) or a PrimarySite credit (12) also
carries the Juniper Websites credit. So school-stock's J2 (at least 80% of placeholder hosts with the
Juniper Websites credit) failed at 43.78% because the pages come from two companies, not because the
pattern was too narrow.

## Two companies, one closing sentence

Of the 526 graded pages with the template's closing sentence, 262 credit a Juniper brand and 264
credit Greenhouse School Websites; every one credits exactly one of the two. The sentence ("...
values diversity and inclusion and is committed to providing an accessible online experience") is
therefore not a sign of one vendor. On most Greenhouse pages the unfinished fields are GOV.UK's
own: all 260 graded pages that keep exactly GOV.UK's three sample fields ("[email address]",
"[phone number]" and "[number]") together with the closing sentence and no Juniper credit (L1's
group) credit Greenhouse School Websites.

Of the 48 graded pages without the closing sentence, 26 credit Finalsite, 10 a Juniper brand and 12
none. All 26 graded pages that keep a placeholder of the 2017 US template credit Finalsite, the US
company whose template MV2's district-stock count found on 1,067 US school-district hosts.

## Stability

563 of the 574 pages (98.08%) have the same text as in school-stock's read; 11 changed but still
keep a placeholder. The re-read was the same day, about eight hours after school-stock's crawl
finished, so this mostly
says the pages are stable from day to day, not that they are never fixed.

## Limits

A credit in a page's HTML shows who built or once built the site, not who wrote its statement or
who is responsible for keeping it up to date; that is the school's. The five credit patterns are
fixed in `school_credit.py` and may miss other wording, such as a credit given only as an image.
L1 was registered after one Greenhouse page had been seen, so it is weaker evidence than K1 to K3.
Schools are exempt from SI 2018/952 except for essential administrative content; a placeholder
says nothing about whether a website is accessible, and nothing here calls a school or a company
in breach.

## Reproduce

`python -m unittest discover -p test_school_credit_result.py` at the root of this repository
re-grades every measure and prediction from `credit-followup/hosts.csv` with the pinned scripts,
checks each figure in this note, and, with school-stock's tables present, checks that the re-read
covered exactly the hosts behind J1.
