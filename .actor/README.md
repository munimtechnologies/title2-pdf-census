# PDF Accessibility Basics Check (ADA Title II)

Give it a website, a list of PDF links, or both. It reads the home page and some of the site's
pages, those that look like document lists (Documents, Agendas, Forms, Library and the like)
first, finds the PDFs they link to, and checks each PDF for four basics that screen readers
rely on:

- **Tags**: the structure that gives headings, lists, tables and reading order
- **A document language**
- **A title** in the document's properties
- **Real text**: not just a scanned image

For each PDF that fails, it says in plain words what to fix (for example, which Word export
option adds tags). It also counts tagged figures without alt text, and says whether the home
page links to a page about accessibility or the ADA.

The example input checks ada.gov and the Justice Department's own Title II web rule PDF.

## Why

Under the ADA Title II rule, US state and local governments serving 50,000 people or more must
make their web content, PDFs included, meet WCAG 2.1 AA by April 26, 2027. Smaller governments
and special districts have until April 26, 2028 (dates as moved by the DOJ's interim final rule
of April 20, 2026). PDFs are the hardest part. In the open
[title2-pdf-census](https://github.com/munimtechnologies/title2-pdf-census) first full run
(October 16, 2026), 61.2% of 5,079 PDFs from 930 large US cities and counties were tagged, and
only 22.4% passed all four basics.

## Output

- **Dataset**: one row per PDF, with each basic as yes/no, what to fix and other notes.
- **REPORT** (key-value store): a plain-language Markdown report for the whole check.
- **SUMMARY** (key-value store): the counts.

## Limits

Machine checks only. Passing them is necessary for an accessible PDF, never sufficient (reading
order, alt text quality, table headers and colour contrast need a person). This is not a WCAG
conformance judgment or legal advice, and it does not decide which older documents fall under
the rule's exceptions. It reads a few pages, not the whole site: PDFs linked only from pages it
did not read are not checked. If it finds none, give PDF links directly or raise Pages to read.

It reads public pages only, honours robots.txt, waits a second between requests and identifies
itself with a User-Agent that names Munim, Inc. and an email address. It stores no document text.

## Who made it

Made by MV2 of Munim, Inc. with AI agents. The code is open source under Apache-2.0:
https://github.com/munimtechnologies/title2-pdf-census (`site_check.py`). Questions:
mv2@munimtech.com.
