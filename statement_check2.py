"""statement_check2: statement_check, plus two checks for accessibility pages left as a template.

Everything statement_check.py reports (which WCAG version a page promises, the stock "We work to
comply with Section 508 as well as ..." sentence, the moved Title II dates, contact details), and:

  * template-placeholder: the page still carries text from a template that was never filled in:
    "YOURMUNICIPALITY", the note "only meant as a template", a NAME / TITLE / EMAIL / PHONE block
    in capitals, or a bracketed placeholder such as "[URL OF WEBSITE]". These are the flags that
    MV2's pre-registered template-pages study counts (template_check.check_text, unchanged);
  * stock-no-wcag: the stock sentence with the word WCAG missing ("... as well as 2.0 A and AA"),
    so the page names no standard at all. MV2's 2026 census of 1,042 accessibility pages of US
    governments of 10,000 to 49,999 people found 75 stock pages that name no WCAG version.

statement_check.py and template_check.py are pinned by pre-registered studies and stay unchanged;
this file only imports them. It checks what a page says, not whether the site meets WCAG, and it
is not legal advice.

Usage (same as statement_check.py):
  python statement_check2.py https://www.example.gov/accessibility
  python statement_check2.py --find https://www.example.gov
  python statement_check2.py saved-page.html --json
Exit status: 0 no findings, 1 one or more findings, 2 the page could not be read.

Needs statement_check.py, template_check.py and a11y_pages.py from this repository next to it.
Standard library only. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402
import statement_check as sc  # noqa: E402  (pinned; its rules are reused as they are)
import template_check as tc  # noqa: E402  (pinned; its placeholder flags are reused)

__version__ = "0.2.0"

KIND_WORDS = {"muni": "\"YOURMUNICIPALITY\"",
              "template_note": "the note \"only meant as a template\"",
              "contact_block": "a NAME / TITLE / EMAIL / PHONE block",
              "bracket": "a bracketed placeholder"}
PLACEHOLDER = ("It still carries template text that was never filled in: %s. The page looks like "
               "an unedited template; replace the placeholder with the government's own name, "
               "contact person and details.")
NO_WCAG = ("It carries the stock sentence with the word WCAG missing (\"... as well as 2.0 A and "
           "AA\"), so it names no accessibility standard at all. The ADA Title II rule (28 CFR "
           "35.200, 2024) adopts WCAG 2.1 Level AA; naming it fixes the promise (the site itself "
           "still has to meet it).")


def check_text(text, small=False):
    """statement_check's result for one page's visible text, plus the two template checks."""
    text = " ".join(text.replace("\xa0", " ").split())
    r = sc.check_text(text, small=small)
    t = tc.check_text(text)
    kinds = [k for k in tc.FLAGS if t[k]]
    r["placeholder"] = bool(kinds)
    r["placeholder_kinds"] = kinds
    r["placeholder_text"] = t["bracket_text"]
    r["stock_no_wcag"] = t["no_wcag"]
    if kinds:
        what = ", ".join(KIND_WORDS[k] for k in kinds)
        if t["bracket_text"]:
            what += " (%s)" % t["bracket_text"]
        r["findings"].append({"id": "template-placeholder", "text": PLACEHOLDER % what})
    if t["no_wcag"]:
        r["findings"].append({"id": "stock-no-wcag", "text": NO_WCAG})
    return r


def report_lines(r):
    lines = sc.report_lines(r)
    lines[0] = "statement_check2 %s (statement_check %s rules)" % (__version__, sc.__version__)
    if r["status"] == "ok":
        extra = ["template placeholder: %s" % (", ".join(r["placeholder_kinds"]) or "no"),
                 "stock sentence without the word WCAG: %s"
                 % ("yes" if r["stock_no_wcag"] else "no")]
        at = next(i for i, x in enumerate(lines) if x.startswith("email or phone on the page:"))
        lines[at + 1:at + 1] = extra
    lines[-1] = lines[-1].replace("statement_check:", "statement_check2:", 1)
    return lines


def main(argv=None, get=sc.http_get, sleep=time.sleep, out=None, stdin=None):
    out = out or sys.stdout
    parser = argparse.ArgumentParser(prog="statement_check2.py",
                                     description=__doc__.split("\n")[0])
    parser.add_argument("source", help="an accessibility page's URL, a saved HTML file, "
                                       "or - to read HTML from standard input")
    parser.add_argument("--find", action="store_true",
                        help="SOURCE is a home page: find its accessibility page first")
    parser.add_argument("--small", action="store_true",
                        help="the government has under 50,000 people or is a special district")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="seconds to wait after each request (default 1)")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    r = {"version": __version__, "source": args.source, "page_url": "", "status": "ok"}
    if args.source == "-" or os.path.isfile(args.source):
        if args.find:
            r["status"] = "--find needs a home page URL, not a file"
            text = ""
        else:
            if args.source == "-":
                body = (stdin or sys.stdin.buffer).read()
            else:
                with open(args.source, "rb") as f:
                    body = f.read()
            text = ap.visible_text(ap.parse(body, ""))
    else:
        r["status"], r["page_url"], text = sc.read_url(args.source, find=args.find, get=get,
                                                       sleep=sleep, delay=args.delay)
    if r["status"] == "ok":
        r.update(check_text(text, small=args.small))
    if args.json:
        out.write(json.dumps(r, indent=1, ensure_ascii=True) + "\n")
    else:
        for line in report_lines(r):
            out.write(line + "\n")
    if r["status"] != "ok":
        return 2
    return 1 if r["findings"] else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
