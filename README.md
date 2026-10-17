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

The same manners apply: public pages only, robots.txt honoured, a pause between requests. The same limits apply too: machine checks of four basics, not a WCAG conformance judgment or legal advice. It finds links with the census's own code, so the 0.2.2 fix below (links on pages that set `<base href>`) applies to it as well. Unlike the census, it does not pick pages at random: since 0.1.1 it reads pages that look like document lists first (Documents, Agendas, Forms, Library, CivicPlus's DocumentCenter and the like, by link text or address), follows such links one level further, and stops once it has twice as many PDF links as PDFs to check. Its first version sampled pages as the census does and found no PDF at all on section508.gov or ada.gov. Since 0.1.2, once half its pages are read with no PDF link, it reads the site's other pages first (see the test below). The `.actor/` folder packages it as an [Apify](https://apify.com) Actor (`actor_main.py`), so it can also run without installing anything. Smoke runs on the Actor's example sites: [docs/smoke-tests.md](docs/smoke-tests.md).

## Test: does reading document pages first find more PDFs?

A paired test of site_check 0.1.1 against the census's random page sampling, with five predictions written down before it ran ([docs/doc-first-prereg.md](docs/doc-first-prereg.md)). Results, scored prediction by prediction: [docs/doc-first-results.md](docs/doc-first-results.md); files in [results/doc-first/](results/doc-first/); code in `doc_first_reach.py`; `test_doc_first_reach.py` recomputes every number quoted here.

- **Four of the five predictions held.** On the local-government sites where the second full run read pages but found no PDF link, reading document-like pages first found one on 60 of 127 sites, against 2 for random pages (exact McNemar p = 1.1e-16).
- **One failed.** On sites where random pages already found PDFs, site_check 0.1.1 reached a readable PDF less often (88 of 97 against 92 of 97), 4.1 points worse, more than the 2 points the pre-registration allowed. At most of the sites it missed, every page it read was document-like and none linked a PDF.
- **What changed:** site_check 0.1.2 falls back to the other pages once half its pages turn up no PDF link. It is tested on 200 control sites the first test did not use, again with predictions written down first: [docs/doc-first-v2-prereg.md](docs/doc-first-v2-prereg.md). The Apify Actor is not published until that test is scored.

## Results: third full run (0.2.2, crawled 2026-10-16 to 2026-10-17)

Files: [results/v0.2.2/](results/v0.2.2/) (`summary.json`, `results.md`, `sites.csv`, `cohort.csv`, `link-counts.json`, `space-and-404.json`, `code-sha256.txt`). `test_results_v022.py` recomputes every number below from them. This is the cleanest of the three runs, so it is now the headline; the two earlier runs stay below as they were published.

**Read this first: what this run fixed, and what it still misses.** 0.2.2 follows `<base href>`, and links with a space now come back 404 about as often as the rest: 25 of the 980 links with a space (2.6%) against 132 of the 5,269 without one (2.5%); in the second run it was 536 of 1,242 against 211 of 5,391. HTTP errors of all kinds fell from 899 to 398. What it still misses: sites that disallow crawlers are not read, and the census reads at most 8 PDFs from at most 8 pages per site, picked at random, so sites whose PDFs sit deeper than two clicks give few or none. A paired test of site_check's document-pages-first reading on such sites is pre-registered in [docs/doc-first-prereg.md](docs/doc-first-prereg.md). Its results are above.

- **Cohort:** the same 1,657 governments. This time the Wikidata query with state names worked: 1,656 of the 1,657 have a state. No breakdown by state is published yet.
- **Reach:** 1,169 home pages read; 267 sites disallow crawlers in robots.txt (or refuse to serve it, which counts the same) and were not read. 5,412 PDFs were read from 926 sites, out of 6,249 tried: more PDFs read than in either earlier run, from fewer tries.
- **All readable PDFs:** tagged 60.5% (59.2-61.8); document language set 56.6% (55.2-57.9); title in metadata 41.9% (40.6-43.2); image only 13.5% (12.6-14.4). **All four basics: 22.0% (20.9-23.1).** Within about a point of both earlier runs, so the gaps fixed along the way did not change the overall picture.
- **The links with a space:** of 892 such PDFs, 57.5% are tagged against 61.1% of the 4,520 others; all four basics 19.5% against 22.5%; image only 15.7% against 13.0%; scanner output 13.2% against 8.8%. They are still somewhat less accessible, but the gap in tagging is smaller than in the second run (55.2% against 61.0%), when many of them could not be fetched.
- **Made since the rule (created on or after 2024-04-24) against before:** tagged 66.2% (64.5-68.0) against 56.0% (54.1-58.0); all four basics 25.5% (23.9-27.1) against 18.2% (16.7-19.7). The metadata title barely moved: 42.5% (40.6-44.3) against 41.7% (39.8-43.6), and it is still the most common missing basic, as in both earlier runs.
- **Within the same site:** 632 sites have PDFs from both periods. Their share tagged rose by +6.74 percentage points on average; it rose at 267 sites, fell at 212 and stayed the same at 153 (two-sided sign test on the 479 that changed, p = 0.01).
- **The software decides most of it:** PDFs saved from Word are tagged 94.2% (92.7-95.4) of the time; print-to-PDF output 16.1% (12.3-20.9); scanner output 4.5% (3.0-6.6), and 72.4% (68.3-76.1) of scanner PDFs are images with no text at all.
- **Figures:** 71,226 figures are tagged in 2,021 PDFs, and 13.8% of them have alt text.
- **Home pages:** 72.6% (70.0-75.1) link to a page about accessibility or the ADA.

The caveats of the first run apply to the before/after comparison (below). The per-PDF records are not published: their file names and software strings were not checked for personal names. `space-and-404.json` holds the counts taken from them.

## Results: second full run (0.2.1, crawled 2026-10-16)

Files: [results/v0.2.1/](results/v0.2.1/) (`summary.json`, `results.md`, `sites.csv`, `cohort.csv`, `link-counts.json`, `space-and-404.json`, `code-sha256.txt`). `test_results_v021.py` recomputes every number below from them.

**Read this first: this run has a known gap too, found in its own data.** 0.2.1 fixed the links with a space in their address (see the first run below), but 536 of the 1,242 links with a space (43.2%) returned 404 Not Found, against 211 of the 5,391 without one (3.9%), and the 404s cluster on whole sites. A hand check of one Revize-hosted county site showed why: its pages set `<base href>` to the site root and write links such as "Complaint Form 20.04.02.pdf", so a browser fetches them from the root, while 0.2.1 ignored `<base href>` and looked under each inner page's folder. 0.2.2 follows `<base href>`; its run is above. Sites built this way are under-read in the numbers below.

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

- **site_check 0.1.2:** once half its pages are read with no PDF link, it reads the site's other pages first; 0.1.1 read every document-like page first and, on some sites, found no PDF link while random pages did. Its reports now compare with the third full run (0.2.2). The doc-first test's code, results and scoring added (`doc_first_reach.py`, results/doc-first/, docs/doc-first-results.md), and a second test pre-registered (docs/doc-first-v2-prereg.md). census.py is unchanged (0.2.2).
- **Third full run (0.2.2) published:** results/v0.2.2/ and test_results_v022.py; it is now the headline. census.py and site_check are unchanged (0.2.2 and 0.1.1).
- **site_check 0.1.1:** reads pages that look like document lists first and follows them one level further, instead of sampling pages at random; stops early once it has enough PDF links; says so plainly when it finds no PDF links. The Actor's example input is now ada.gov plus the Justice Department's Title II web rule PDF (0.1.0's example, section508.gov, gave an empty report). census.py is unchanged (0.2.2).
- **0.2.2:** relative links resolve against the page's `<base href>`, as a browser does. 0.2.1 ignored it, so on sites that set it (Revize and others) links on inner pages pointed to the wrong folder and failed with 404. Results of the second full run (0.2.1) added. site_check uses the same link code, so it gets the fix too.
- **site_check 0.1.0:** one-website check with plain-language fixes, and an Apify Actor wrapper (`.actor/`, `actor_main.py`). census.py is unchanged (0.2.1).
- **0.2.1:** links are percent-encoded before they are fetched (spaces, non-ASCII letters), as a browser does; 0.2.0 failed on every link with a space. The contact address in the User-Agent and below is now mv2@munimtech.com. Results of the first full run (0.2.0) added.
- **0.2.0:** home-page check for a link to an accessibility or ADA page.
- **0.1.0:** first release.

## Licence and credits

Code: Apache-2.0. Data and results: CC BY 4.0. Cohort data from [Wikidata](https://www.wikidata.org) (CC0). Uses [pypdf](https://github.com/py-pdf/pypdf) (BSD-3-Clause).

Made by MV2 of Munim, Inc. with AI agents. Contact: mv2@munimtech.com. If you run one of these sites and want it left out of future runs, email us and we will exclude it.
