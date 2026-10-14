#!/bin/sh
# title2-pdf-census, first full run: the cohort from Wikidata, the crawl (public pages
# only, robots.txt honoured, 1 s between requests to a site), then the summary.
# The crawl writes after every site, so a run cut short still summarizes.
set -u
cd "$(dirname "$0")"
mkdir -p /out
python census.py --version
python census.py cohort --out /out/cohort.csv || exit 1
python census.py crawl --cohort /out/cohort.csv --sites-out /out/sites.jsonl --pdfs-out /out/pdfs.jsonl \
  --pages 8 --pdfs 8 --workers 24 --delay 1.0 --max-minutes 200 || echo "crawl stopped early" >&2
python census.py summarize --sites /out/sites.jsonl --pdfs /out/pdfs.jsonl --out-dir /out
