# statement_check2: is this accessibility page still an unedited template?

`statement_check2.py` is a free, standard-library Python check for the accessibility page of a
US state or local government (or anyone's). It reports everything
[statement_check](STATEMENT-CHECK.md) reports (which WCAG version the page promises, the stock
"We work to comply with Section 508 as well as ..." sentence, the Title II dates moved by the
April 20, 2026 interim final rule, contact details) and adds two findings:

| id | what it means | fix |
|---|---|---|
| `template-placeholder` | The page still carries template text that was never filled in: `YOURMUNICIPALITY`, the note "only meant as a template", a `NAME / TITLE / EMAIL / PHONE` block in capitals, or a bracketed placeholder such as `[URL OF WEBSITE]` or `[INSERT CITY NAME]`. | Replace the placeholder with the government's own name, contact person and details. |
| `stock-no-wcag` | The stock sentence with the word WCAG missing ("... as well as 2.0 A and AA"), so the page names no standard at all. MV2's census of 1,042 accessibility pages of US governments of 10,000 to 49,999 people found 75 stock pages naming no WCAG version. | Name WCAG 2.1 Level AA, the standard the ADA Title II rule (28 CFR 35.200, 2024) adopts. |

The placeholder flags are exactly the ones MV2's pre-registered
[template-pages](results/template-pages/PREREG.md) study counts (`template_check.check_text`).
`statement_check.py` and `template_check.py` are pinned by pre-registered studies and stay
unchanged; `statement_check2.py` only imports them.

```
python statement_check2.py https://www.example.gov/accessibility
python statement_check2.py --find https://www.example.gov      # find the page from the home page
python statement_check2.py --small saved-page.html --json      # under 50,000 people
```

Exit status: 0 no findings, 1 one or more findings, 2 the page could not be read. It needs
`statement_check.py`, `template_check.py` and `a11y_pages.py` next to it. It reads public pages
only, honours robots.txt and names Munim, Inc. in its User-Agent.

It checks only what the page's text says, not whether the site meets WCAG, and it is not legal
advice. A placeholder says nothing about whether a website is accessible; it says the statement
was never finished. Offline tests: `python -m unittest discover -p test_statement_check2.py`.

Apache-2.0. Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
