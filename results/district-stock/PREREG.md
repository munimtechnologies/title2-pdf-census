# Pre-registration: how many US school districts serve an unfinished accessibility statement template at `/accessibility-statement`? (district-stock)

Status: plan, committed on 2026-11-08 before any address in this study was read by its crawl.
The crawl starts only once this file, `district_stock.py` 0.1.0 and the five files it pins
(`district_pages.py`, `district_check.py`, `a11y_pages.py`, `statement_check.py`,
`template_check.py`, all unchanged) are on main, and it runs main's copies.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Apache-2.0 (code),
CC BY 4.0 (text and data). A placeholder says nothing about whether a website is accessible, and
nothing here is legal advice. No district or vendor is contacted about a page by MV2 without a
person checking it first.

## Why

MV2's [district-pages](../district-pages/DISTRICT-PAGES-RESULT.md) census sampled 2,500 of the
11,582 US public school district website hosts and read 933 accessibility pages that home pages
link to. 129 of them (13.83%) still carry a 2017 statement template's placeholders: "To help us
make the Your School website a positive place for everyone, we've been using the Web Content
Accessibility Guidelines (WCAG) 2.0", accessibility@yourschool.com and 555-555-5555. All 129 are
on sites with Finalsite markup (a school-website vendor), and **123 of the 129 sit at the same
address, `/accessibility-statement`** (39 in districts of 50,000 or more people, 84 under 50,000).

The census only read pages that the home page links to, and it sampled a fifth of the districts.
This study asks **every** host in the frame for that one address, as MV2's stock-153 study did for
city and county websites, where it found about eight times as many unfinished templates as link
following had.

Finalsite also publishes a newer sample statement (support article dated 2026-02-19) that starts
"[Your School] is committed to ensuring digital accessibility for people with disabilities", says
"[Your School] is built with WCAG 2.1 AA guidelines in mind" and keeps the same dummy phone number
and address. The census found no page with that line. Both templates are read with the census's
own rules, unchanged.

**Seen before this plan (disclosed).** The census table (`results/district-pages/rows.csv`) is
public and was read for this plan: which sampled districts had a placeholder page and at which
address. Web searches on 2026-11-07 and 2026-11-08 showed the 2017 text on individual school and
district pages (several at `/accessibility-statement`) and Finalsite's 2026 article. No address in
the frame was requested for this plan.

**Prior art, searched on 2026-11-08:** individual live pages, vendor guidance and template guides;
no count, survey or study of how many school districts publish either template unfinished. MV2's
district-pages census is the only count found, and it covers linked pages in a sample.

## Frame (fixed now)

The district-pages frame, rebuilt by the pinned `district_pages.py` from the same two federal
files: regular, open districts in the NCES Common Core of Data 2024-25 LEA directory with a
website and a population in the Census Bureau's SAIPE 2024 school-district file, one row per
website host. The district with LEAID 0903180 is dropped before anything is read: its name
contains a word that MV2's publishing tool blocks (it is not in the census sample either).

Each host keeps its census record from `results/district-pages/rows.csv` (its 2,500 rows must all
be read, gate G0): **not_sampled**, **home_failed**, **no_page** (home page read, no accessibility
page read), **found_here** (the page the census read was at `/accessibility-statement`) or
**found_elsewhere**, and whether the census counted a placeholder page for that district.

**Gate F1:** the frame has **11,000 to 11,700** hosts, **1,250 to 1,400** of them in districts of
50,000 or more people. Otherwise nothing is read.

## Reading (fixed now)

For each host, one request for `<scheme>://<host as listed in the CCD>/accessibility-statement`,
with the census's requests unchanged (`a11y_pages.py`): robots.txt read first and honoured,
redirects followed, a pause after each request, at most 8 hosts at a time, in a fixed shuffled
order. If the server answers 429 or 503, the address is asked once more after 30 seconds. The page
is read only if it answers 200 with HTML of 200 or more visible characters. Then, on the visible
text, with `district_check.check_text` (the census's rules, unchanged):

- **placeholder page**: any of the census's placeholder flags (for example "the Your School
  website", a "yourschool.com"-style address, 555-555-5555, "[Your School]", "within # business
  days", or the city-template flags of `template_check.py`).
- **Finalsite markup**: the page's HTML contains "finalsite" (any case).
- Described only: the 2017 template's sentence "a positive place for everyone" (filled in or not),
  the 2026 line "built with WCAG 2.1 AA guidelines in mind", the Accessibility Statement Generator
  credit, the highest WCAG version named, and Title II.

**Gate G1:** at least **80%** of hosts answered (any HTTP status, or a robots.txt that forbids the
address). Otherwise nothing is graded.

## Predictions (graded by `district_stock.grade`)

| | Prediction | Graded only if |
|---|---|---|
| **K1** | At least **400** hosts serve a placeholder page at `/accessibility-statement` | F1 and G1 |
| **K2** | Of the census-sampled hosts that serve a placeholder page there, at least **15%** are districts for which the census counted no placeholder page | at least **30** such hosts |
| **K3** | Of the hosts where the census read a placeholder page at this address, at least **90%** still serve one (hosts whose server did not answer, forbade the address or still answered 429 or 503 are left out) | at least **80** such hosts |
| **K4** | At least **95%** of placeholder pages carry Finalsite markup | at least **50** placeholder pages |

Reasons, written before reading: the census found 39 such pages among 800 sampled districts of
50,000 or more (frame 1,322) and 84 among 1,700 under 50,000 (frame 10,260); weighting by the
sampling rates gives about 570 in the frame from linked pages alone, before pages fixed since or
servers that do not answer (K1). Only a third of smaller districts' home pages linked to any
accessibility page under the census's rules, so some template pages must be unlinked (K2).
Templates left unfinished for years are unlikely to change in a week (K3). All 129 census pages
were on Finalsite sites (K4).

**Described, not graded:** status and census record by band; the share of answered hosts serving
a placeholder page, by band; placeholder pages by census record, placeholder kind, highest WCAG
version and state; pages with the 2017 sentence, with and without placeholders; pages with the 2026
line; Generator credits; pages with Finalsite markup; census placeholder pages whose text is
unchanged; how many addresses were asked twice.

## Honest limits

- One address per host, read once: a template under another address, on a school's own host or in
  a PDF is not found, so the counts are floors, and a district may fix its page at any time.
- A page served at an address is not necessarily linked: the study does not say whether visitors
  reach it.
- SAIPE populations are model-based estimates; districts sharing one host are counted once.
- The frame is regular, open districts with a website in the CCD; charter-only agencies,
  supervisory unions' member schools and private schools are not in it.

## After grading

`hosts-50k.csv` and `hosts-under50k.csv` (one row per host: status, a hash of the page text, the
flags; no page text), `result.json` and `result.txt` go to `results/district-stock/` with a result
note and a test that re-grades every figure from the saved tables. Results are published whether
the predictions hold or not.
