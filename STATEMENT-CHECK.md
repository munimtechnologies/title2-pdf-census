# Statement check: is your accessibility page out of date?

`statement_check.py` is a free check for the accessibility page of a US city, county, state agency
or special district (or anyone else's). It reads what the page says and tells you, in plain words,
whether any of it is out of date for the ADA Title II web rule. It takes about a minute to run and
changes nothing on your site.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0. Not legal advice.

## Why

The Justice Department's 2024 Title II rule (28 CFR 35.200) adopts **WCAG 2.1 Level AA** for the
websites and apps of state and local governments. Its interim final rule of April 20, 2026
(91 FR 20902) moved the compliance dates by a year:

| Government | Old date | New date |
|---|---|---|
| 50,000 people or more | April 24, 2026 | **April 26, 2027** |
| Under 50,000 people, and special districts | April 26, 2027 | **April 26, 2028** |

This repository's census of the accessibility pages linked from the home pages of US cities and
counties of 50,000 or more ([results/a11y-pages](results/a11y-pages/A11Y-PAGES-RESULT.md)) read 808
pages. 283 of the pages that name a WCAG version name only **WCAG 2.0**, and 258 of those 283 carry
one stock sentence:

> We work to comply with Section 508 as well as WCAG 2.0 A and AA referring to website
> accessibility standards

That sentence is on 280 of the 808 pages. The five checked were CivicPlus CivicEngage sites, whose
help center says each site's administrators can edit the Accessibility page. So for most of these
governments the fix is a one-sentence edit.

## What it checks

| Finding | When |
|---|---|
| `wcag-2.0` | The highest WCAG version the page names is 2.0 (the rule adopts 2.1 AA). |
| `stock-sentence` | The page carries the stock sentence above. |
| `old-date` | The page gives April 24, 2026 and not April 26, 2027. |
| `small-2027` | With `--small` only: the page gives April 26, 2027 and not April 26, 2028. |

It also reports which WCAG versions the page names (by the census's own rules in `a11y_pages.py`,
so "success criterion 2.1.1" is not read as a version), whether it names Section 508 or Title II,
which of the three dates it gives, and whether an email address or phone number is on the page.
Notes (not findings) say when a page names no WCAG version, gives both the old and the new date,
has no email or phone, or has so little text that it is probably built by JavaScript.

What it does **not** do: test whether your site meets WCAG. A page that names WCAG 2.1 AA can sit on
a site with many barriers. Use an accessibility testing tool and testing with disabled users for
that.

## How to run it

You need Python 3.9 or later and two files from this repository in the same folder:
`statement_check.py` and `a11y_pages.py`. Nothing to install.

```
python statement_check.py https://www.example.gov/accessibility
python statement_check.py --find https://www.example.gov          # start from the home page
python statement_check.py --small https://www.example-town.gov/accessibility
python statement_check.py saved-page.html --json
```

`--find` picks the accessibility page from the home page's links by the census's rules (same site
only; a link whose address or text says "accessibility" first, then "Section 508", then "ADA").
Exit status: 0 no findings, 1 one or more findings, 2 the page could not be read.

A page carrying the stock sentence and the old date gives a report like this (abridged):

```
statement_check 0.1.0
WCAG versions named: 2.0 (highest 2.0)
Section 508 named: yes; Title II named: yes
dates given: April 24, 2026: yes; April 26, 2027: no; April 26, 2028: no
stock sentence: yes
FINDING wcag-2.0: It names WCAG 2.0 as its highest WCAG version. ...
FINDING stock-sentence: It carries the stock sentence ...
FINDING old-date: It gives April 24, 2026 as a compliance date and does not give April 26, 2027. ...
statement_check: 3 findings
```

## Politeness

For a URL it reads robots.txt first and stops if the page is disallowed, waits a second after each
request, and names itself as `MV2-statement-check/0.1.0 (Munim, Inc.; mv2@munimtech.com; reads public
pages only)`. Each run makes only a few requests: robots.txt once per host, the page itself, or with
`--find` the home page and at most three candidate pages.

## Tests

`python -m unittest test_statement_check` runs offline: every page comes from a fake fetcher.
