# title2-pdf-census

**How accessible are the PDFs that large US local governments publish, six months before their ADA Title II deadline?**

The U.S. Department of Justice's ADA Title II rule (published 2024-04-24; deadlines moved by one year in April 2026) requires state and local governments serving **50,000 people or more** to make their web content, including PDF documents, meet **WCAG 2.1 AA by 2027-04-26**. Smaller governments and special districts have until 2028-04-26.

This tool takes that cohort and measures the basics:

1. **Cohort:** US cities, counties, consolidated city-counties and towns with a population of 50,000+ and an official website on Wikidata (one row per website).
2. **Crawl, public pages only:** for each site it reads robots.txt, the home page, up to 8 pages linked from it, and up to 8 PDFs linked from those pages. Requests to any one site are made one at a time with a 1-second pause, and robots.txt is honoured. The User-Agent names Munim, Inc. and gives an email address.
3. **Checks on each PDF** (machine-checkable structure that screen readers rely on):
   - **tagged**: has a structure tree (`/StructTreeRoot`)
   - **language**: the document language (`/Lang`) is set
   - **title**: a title is set in the metadata
   - **image only**: no extractable text on the first two pages (likely a scan without OCR)
   - **all four basics**: tagged, language and title set, and not image only
   - figures in the structure tree, and how many have alt text
   - the creation date, so **PDFs made after the rule can be compared with older ones**, overall and within the same site
   - the software that made it (Word, Acrobat, a scanner, print-to-PDF, ...)
4. **One check on each home page** (new in 0.2.0): does it link to a page about accessibility or the ADA? A link counts if its URL path contains "accessib" or "section-508", or its text contains "accessib", "Section 508" or "ADA" in capitals (not "ADA County"). This is a rough signal of whether residents can find an accessibility statement or a way to report a barrier; the rule itself does not require one.

## What it is not

Passing these checks is **necessary but not sufficient** for an accessible PDF: correct reading order, meaningful alt text, table headers and colour contrast need a person or deeper tools. Nothing here is a WCAG conformance judgment about any government, and no result says anyone is out of compliance. The sample is the PDFs reachable within two clicks of each home page, so it over-represents current documents such as agendas, minutes and notices. The home-page link check misses statements linked only from inner pages or footers rendered by script, and counts some links that are about physical access.

The tool stores **structural facts only**: no document text, no metadata titles, no personal data.

## Prior work

- Allyant's *PDF Accessibility Index 2025-2026* (March 2026) scanned 644,854 PDFs on 770+ websites across sectors and reported 97.12% of government PDFs inaccessible. It is a vendor report with proprietary data and no per-government or local-government breakdown.
- Accessible Compliance Group's *2026 State of Government Website Accessibility* scanned 15,481 government websites but excluded PDFs.
- The WebAIM Million tests home pages, not documents.

As far as we could find, this is the first **open, reproducible, per-government** measurement of PDF basics for the governments facing the 2027 deadline, and the first to ask whether **documents made since the rule** are better than older ones.

## Use

```
pip install "pypdf[crypto]"
python census.py cohort --out cohort.csv
python census.py crawl --cohort cohort.csv --sites-out sites.jsonl --pdfs-out pdfs.jsonl
python census.py summarize --sites sites.jsonl --pdfs pdfs.jsonl --out-dir .
python -m unittest -v
```

`summarize` writes `summary.json`, `results.md` (shares with 95% Wilson intervals) and `sites.csv` (one row per government).

## Check one website (site_check)

`site_check.py` runs the same checks on one website, or on a list of PDF links, and writes a plain-language report: which PDFs pass the four basics, and for each one that fails, what to fix (for example, the Word export option that adds tags, or where to set a title and a language). It is meant for the people who publish the PDFs: a city clerk, a web team or a consultant checking their own site before the deadline.

```
python site_check.py https://www.example.gov/ --md report.md --json report.json
python site_check.py --pdf https://www.example.gov/docs/agenda.pdf --md report.md
```

The same manners apply: public pages only, robots.txt honoured, a pause between requests. The same limits apply too: machine checks of four basics, not a WCAG conformance judgment or legal advice. It finds links with the census's own code, so the 0.2.2 fix below (links on pages that set `<base href>`) applies to it as well. Unlike the census, it does not pick pages at random: since 0.1.1 it reads pages that look like document lists first (Documents, Agendas, Forms, Library, CivicPlus's DocumentCenter and the like, by link text or address), follows such links one level further, and stops once it has twice as many PDF links as PDFs to check. Its first version sampled pages as the census does and found no PDF at all on section508.gov or ada.gov. The `.actor/` folder packages it as an [Apify](https://apify.com) Actor (`actor_main.py`), so it can also run without installing anything.

## Results: second full run (0.2.1, crawled 2026-10-16)

Files: [results/v0.2.1/](results/v0.2.1/) (`summary.json`, `results.md`, `sites.csv`, `cohort.csv`, `link-counts.json`, `space-and-404.json`, `code-sha256.txt`). `test_results_v021.py` recomputes every number below from them.

**Read this first: this run has a known gap too, found in its own data.** 0.2.1 fixed the links with a space in their address (see the first run below), but 536 of the 1,242 links with a space (43.2%) returned 404 Not Found, against 211 of the 5,391 without one (3.9%), and the 404s cluster on whole sites. A hand check of one Revize-hosted county site showed why: its pages set `<base href>` to the site root and write links such as "Complaint Form 20.04.02.pdf", so a browser fetches them from the root, while 0.2.1 ignored `<base href>` and looked under each inner page's folder. 0.2.2 follows `<base href>`, and a third full run is queued. Until then, sites built this way are under-read in the numbers below.

- **Cohort:** the same 1,657 governments as the first run (Wikidata; again no state names).
- **Reach:** 1,190 home pages read; 260 sites disallow crawlers in robots.txt (or refuse to serve it, which counts the same) and were not read, 61 more than in the first run the same day. 5,285 PDFs were read from 922 sites, out of 6,633 tried.
- **All readable PDFs:** tagged 60.3% (59.0-61.6); document language set 56.2% (54.8-57.5); title in metadata 41.7% (40.4-43.1); image only 13.5% (12.6-14.4). **All four basics: 21.5% (20.4-22.6).** Within about a point of the first run.
- **The links with a space, now read:** of 652 such PDFs, tagged 55.2% (51.4-59.0) against 61.0% (59.6-62.4) for the 4,633 others; all four basics 16.9% (14.2-19.9) against 22.1% (21.0-23.4); image only 17.6% against 12.9%; scanner output 14.9% against 8.6%. They are somewhat less accessible, as the first run's gap suggested, but adding them moves the overall shares by about one point.
- **Made since the rule (created on or after 2024-04-24) against before:** tagged 66.2% (64.4-68.0) against 55.5% (53.5-57.5); all four basics 25.2% (23.6-26.9) against 17.3% (15.8-18.9). The metadata title barely moved: 42.5% (40.6-44.4) against 41.6% (39.6-43.5), and it is again the most common missing basic.
- **Within the same site:** 622 sites have PDFs from both periods. Their share tagged rose by +6.45 percentage points on average; it rose at 259 sites, fell at 213 and stayed the same at 150 (two-sided sign test on the 472 that changed, p = 0.04).
- **The software decides most of it:** PDFs saved from Word are tagged 94.0% (92.5-95.2) of the time; print-to-PDF output 15.4% (11.6-20.2); scanner output 5.0% (3.4-7.3), and 71.2% (67.0-75.0) of scanner PDFs are images with no text at all.
- **Figures:** 76,971 figures are tagged in 1,978 PDFs, and 11.9% of them have alt text.
- **Home pages:** 72.5% (69.9-75.0) link to a page about accessibility or the ADA.

The same caveats as the first run apply to the before/after comparison (below). The per-PDF records are not published: their file names and software strings were not checked for personal names. `space-and-404.json` holds the counts taken from them.

## Results: first full run (0.2.0, crawled 2026-10-16)

Files: [results/v0.2.0/](results/v0.2.0/) (`summary.json`, `results.md`, `sites.csv`, `cohort.csv`, `code-sha256.txt`). `test_results_v020.py` recomputes every number below from them.

**Read this first: the run has a known gap.** Version 0.2.0 sent each link exactly as written, and Python's HTTP client refuses a URL with a space in it. So all 1,572 PDF links with a space in their address failed, and not one of them was read: 1,572 of the 1,944 fetch errors. Files named like "Burn Ban Order 8272026.pdf" are often uploaded straight from a staff computer, so the PDFs below may lean toward documents that went through a publishing system. 0.2.1 encodes such links as a browser does; its run is above.

- **Cohort:** 1,657 governments with a website (Wikidata). The query with state names failed (HTTP 502) and the fallback has none, so there is no breakdown by state in this run.
- **Reach:** 1,264 home pages read; 199 sites disallow crawlers in robots.txt and were not read. 5,079 PDFs were read from 930 sites, out of 7,504 tried.
- **All readable PDFs:** tagged 61.2% (59.8-62.5); document language set 57.1% (55.7-58.4); title in metadata 42.6% (41.3-44.0); image only 12.7% (11.8-13.7). **All four basics: 22.4% (21.2-23.5).**
- **Made since the rule (created on or after 2024-04-24) against before:** tagged 66.6% (64.8-68.4) against 56.8% (54.8-58.8); all four basics 26.0% (24.3-27.7) against 18.2% (16.7-19.8). The metadata title did not move: 43.1% (41.2-45.0) against 42.9% (40.9-45.0). It is now the most common missing basic.
- **Within the same site:** 589 sites have PDFs from both periods. Their share tagged rose by +6.6 percentage points on average; it rose at 247 sites, fell at 198 and stayed the same at 144 (two-sided sign test on the 445 that changed, p = 0.02).
- **The software decides most of it:** PDFs saved from Word are tagged 94.3% (92.8-95.5) of the time; print-to-PDF output 11.5% (8.1-16.1); scanner output 5.0% (3.3-7.4), and 75.0% (70.7-78.9) of scanner PDFs are images with no text at all.
- **Figures:** 66,846 figures are tagged in 1,927 PDFs, and 13.8% of them have alt text.
- **Home pages:** 73.8% (71.3-76.2) link to a page about accessibility or the ADA.

What the before/after comparison can't say: a PDF's creation date isn't its publication date, re-saved files get new dates, and recent documents are a different mix (more agendas and notices) than the older ones still linked. The within-site comparison removes differences between governments, but not that mix.

## Changes

- **site_check 0.1.1:** reads pages that look like document lists first and follows them one level further, instead of sampling pages at random; stops early once it has enough PDF links; says so plainly when it finds no PDF links. The Actor's example input is now ada.gov plus the Justice Department's Title II web rule PDF (0.1.0's example, section508.gov, gave an empty report). census.py is unchanged (0.2.2).
- **0.2.2:** relative links resolve against the page's `<base href>`, as a browser does. 0.2.1 ignored it, so on sites that set it (Revize and others) links on inner pages pointed to the wrong folder and failed with 404. Results of the second full run (0.2.1) added. site_check uses the same link code, so it gets the fix too.
- **site_check 0.1.0:** one-website check with plain-language fixes, and an Apify Actor wrapper (`.actor/`, `actor_main.py`). census.py is unchanged (0.2.1).
- **0.2.1:** links are percent-encoded before they are fetched (spaces, non-ASCII letters), as a browser does; 0.2.0 failed on every link with a space. The contact address in the User-Agent and below is now mv2@munimtech.com. Results of the first full run (0.2.0) added.
- **0.2.0:** home-page check for a link to an accessibility or ADA page.
- **0.1.0:** first release.

## Licence and credits

Code: Apache-2.0. Data and results: CC BY 4.0. Cohort data from [Wikidata](https://www.wikidata.org) (CC0). Uses [pypdf](https://github.com/py-pdf/pypdf) (BSD-3-Clause).

Made by MV2 of Munim, Inc. with AI agents. Contact: mv2@munimtech.com. If you run one of these sites and want it left out of future runs, email us and we will exclude it.
