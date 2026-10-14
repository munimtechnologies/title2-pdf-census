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

## Results

The first full run is queued; results will be published here with the data.

## Licence and credits

Code: Apache-2.0. Data and results: CC BY 4.0. Cohort data from [Wikidata](https://www.wikidata.org) (CC0). Uses [pypdf](https://github.com/py-pdf/pypdf) (BSD-3-Clause).

Made by MV2 of Munim, Inc. with AI agents. Contact: munimversion2@gmail.com. If you run one of these sites and want it left out of future runs, email us and we will exclude it.
