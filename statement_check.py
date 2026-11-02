"""statement_check: what does one accessibility statement promise, and is any of it out of date?

A free check for the accessibility page of a US state or local government (or anyone else's).
It reads the page's visible text and reports:

  * which WCAG versions it names, by the same rules as the census in results/a11y-pages
    (a11y_pages.classify): a page whose highest version is WCAG 2.0 promises less than the
    ADA Title II rule (28 CFR 35.200, 2024), which adopts WCAG 2.1 Level AA;
  * whether it carries the stock sentence "We work to comply with Section 508 as well as WCAG
    2.0 A and AA ...", found on 280 of the 808 pages the 2026 census read;
  * whether it gives April 24, 2026 as a compliance date without April 26, 2027 (the Justice
    Department's interim final rule of April 20, 2026 moved the dates: April 24, 2026 became
    April 26, 2027 for governments of 50,000 or more, and April 26, 2027 became April 26, 2028
    for smaller governments and special districts; use --small for those);
  * whether it names Section 508 or Title II, and whether an email address or phone number is
    on the page.

It checks only what the page's text says, not whether the site meets WCAG, and it is not legal
advice. It does not run JavaScript, so a page built by scripts may read as nearly empty.

Usage:
  python statement_check.py https://www.example.gov/accessibility
  python statement_check.py --find https://www.example.gov      (home page: find the page first)
  python statement_check.py saved-page.html --json
  python statement_check.py - < saved-page.html
Exit status: 0 no findings, 1 one or more findings, 2 the page could not be read.

Reads public pages only, honouring robots.txt, under a User-Agent that names Munim, Inc. Needs
a11y_pages.py from this repository next to it. Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's own rules)

__version__ = "0.1.0"

UA = ("MV2-statement-check/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)

STOCK_RE = re.compile(r"\bWe\s+work\s+to\s+comply\s+with\s+Section\s*508\s+as\s+well\s+as\b", re.I)
DATE_2028_RE = re.compile(r"\bApr(?:il|\.)?\s+26(?:th)?,?\s+2028\b|\b26\s+April,?\s+2028\b|"
                          r"\b0?4/26/(?:20)?28\b|\b2028-04-26\b", re.I)

WCAG20 = ("It names WCAG 2.0 as its highest WCAG version. The ADA Title II rule (28 CFR 35.200, "
          "2024) adopts WCAG 2.1 Level AA, so this page promises less than the rule requires. "
          "Naming WCAG 2.1 Level AA fixes the promise (the site itself still has to meet it).")
STOCK = ("It carries the stock sentence \"We work to comply with Section 508 as well as WCAG 2.0 "
         "A and AA ...\". MV2's 2026 census of the accessibility pages of US cities and counties of "
         "50,000 or more found it on 280 of the 808 pages read; the five checked were CivicPlus "
         "CivicEngage sites, whose help center says site administrators can edit this page. It is "
         "a one-sentence edit.")
OLD_DATE = ("It gives April 24, 2026 as a compliance date and does not give April 26, 2027. The "
            "Justice Department's interim final rule of April 20, 2026 moved that date (for "
            "governments of 50,000 or more) to April 26, 2027.")
SMALL_DATE = ("It gives April 26, 2027 and not April 26, 2028. For a government of under 50,000 "
              "people or a special district, the interim final rule of April 20, 2026 moved the "
              "date from April 26, 2027 to April 26, 2028; check which one the page means.")
BOTH_DATES = ("It gives both April 24, 2026 and April 26, 2027; check that the page says the "
              "older date was replaced.")
NO_VERSION = ("It names no WCAG version. The Title II rule does not require a statement, but "
              "naming WCAG 2.1 Level AA tells readers which standard the site is held to.")
WCAG_NO_VERSION = ("It mentions WCAG but names no version (2.0, 2.1 or 2.2); readers cannot "
                   "tell which standard it promises.")
NO_CONTACT = ("No email address or phone number appears on the page; a statement usually tells "
              "readers how to report a barrier (a contact form link would not show up here).")
SHORT = ("The page's text is very short (%d characters); it may be built by JavaScript, which "
         "this check does not run.")
DISCLAIMER = ("This checks only what the page says, not whether the site meets WCAG; it is not "
              "legal advice.")


def check_text(text, small=False):
    """What one page's visible text promises, with findings and notes."""
    text = " ".join(text.replace("\xa0", " ").split())
    c = ap.classify(text)
    d2028 = bool(DATE_2028_RE.search(text))
    stock = bool(STOCK_RE.search(text))
    contact = bool(ap.EMAIL_RE.search(text) or ap.PHONE_RE.search(text))
    findings, notes = [], []
    if c["highest"] == "2.0":
        findings.append({"id": "wcag-2.0", "text": WCAG20})
    if stock:
        findings.append({"id": "stock-sentence", "text": STOCK})
    if c["old_date"] and not c["new_date"]:
        findings.append({"id": "old-date", "text": OLD_DATE})
    elif c["old_date"]:
        notes.append(BOTH_DATES)
    if small and c["new_date"] and not d2028:
        findings.append({"id": "small-2027", "text": SMALL_DATE})
    if not c["highest"]:
        notes.append(WCAG_NO_VERSION if c["wcag_any"] else NO_VERSION)
    if not contact:
        notes.append(NO_CONTACT)
    if len(text) < ap.MIN_TEXT:
        notes.append(SHORT % len(text))
    return {"text_chars": len(text), "wcag_any": c["wcag_any"], "versions": c["versions"],
            "highest": c["highest"], "section508": c["section508"], "title2": c["title2"],
            "date_2026_04_24": c["old_date"], "date_2027_04_26": c["new_date"],
            "date_2028_04_26": d2028, "stock_sentence": stock, "contact": contact,
            "version_snippet": c["version_snippet"], "findings": findings, "notes": notes}


# ---------------------------------------------------------------- reading a page

def http_get(url, max_bytes=3_000_000, timeout=20):
    """(status, final url, content type, body) of a public page; never raises (status 0)."""
    req = urllib.request.Request(ap.quote_url(url), headers={"User-Agent": UA,
                                                             "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), r.read(max_bytes)
    except urllib.error.HTTPError as e:
        return e.code, url, "", b""
    except Exception:  # DNS, TLS, timeouts, resets
        return 0, url, "", b""


def robots_checker(get, delay=1.0, sleep=time.sleep):
    """allowed(url): each host's robots.txt is read once (401/403 means none allowed)."""
    cache = {}

    def allowed(url):
        p = urllib.parse.urlsplit(url)
        key = "%s://%s" % (p.scheme, p.netloc)
        if key not in cache:
            status, _, _, body = get(key + "/robots.txt")
            sleep(delay)
            rp = urllib.robotparser.RobotFileParser()
            if status == 200 and body:
                rp.parse(body.decode("utf-8", "replace").splitlines())
            elif status in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
            cache[key] = rp
        return cache[key].can_fetch(UA, url)
    return allowed


def read_url(url, find=False, get=http_get, sleep=time.sleep, delay=1.0):
    """(status, page url, visible text); status is "ok" or why the page could not be read.

    With find=True, url is a home page and the accessibility page is picked by the census's
    link rules (same site only, ranked; up to three tries), as in a11y_pages.crawl_site.
    """
    url = url.strip()
    if find:
        url = ap.normalize_site(url)
    elif not re.match(r"https?://", url, re.I):
        url = "https://" + url
    allowed = robots_checker(get, delay, sleep)
    if not allowed(url):
        return "robots", url, ""
    status, final, ctype, body = get(url)
    sleep(delay)
    if status != 200:
        return "http_%d" % status, url, ""
    if not ap.is_html(ctype, body):
        return "not_html", url, ""
    page = ap.parse(body, ctype)
    if not find:
        return "ok", final or url, ap.visible_text(page)
    cands, _, _ = ap.candidates(page, final or url)
    result = "no_link"
    for cand, _rank in cands[:ap.MAX_TRIES]:
        if not allowed(cand):
            result = "robots"
            continue
        status, final2, ctype, body = get(cand)
        sleep(delay)
        if status != 200:
            result = "http_%d" % status
            continue
        if not ap.is_html(ctype, body):
            result = "not_html"
            continue
        text = ap.visible_text(ap.parse(body, ctype))
        if len(text) < ap.MIN_TEXT:
            result = "short"
            continue
        return "ok", final2 or cand, text
    return result, url, ""


# ---------------------------------------------------------------- report

def report_lines(r):
    def yn(b):
        return "yes" if b else "no"
    lines = ["statement_check %s" % __version__, "source: %s" % r["source"]]
    if r["status"] != "ok":
        lines.append("could not read the page: %s" % r["status"])
        lines.append("statement_check: not checked")
        return lines
    if r.get("page_url") and r["page_url"] != r["source"]:
        lines.append("page: %s" % r["page_url"])
    lines.append("text: %d characters" % r["text_chars"])
    lines.append("WCAG versions named: %s" % ("%s (highest %s)" % (r["versions"].replace("+", ", "),
                                                                    r["highest"])
                                               if r["highest"] else "none"))
    if r["version_snippet"]:
        lines.append("first version named in: ...%s..." % r["version_snippet"])
    lines.append("Section 508 named: %s; Title II named: %s" % (yn(r["section508"]),
                                                                 yn(r["title2"])))
    lines.append("dates given: April 24, 2026: %s; April 26, 2027: %s; April 26, 2028: %s"
                 % (yn(r["date_2026_04_24"]), yn(r["date_2027_04_26"]),
                    yn(r["date_2028_04_26"])))
    lines.append("stock sentence: %s" % yn(r["stock_sentence"]))
    lines.append("email or phone on the page: %s" % yn(r["contact"]))
    for f in r["findings"]:
        lines.append("FINDING %s: %s" % (f["id"], f["text"]))
    for n in r["notes"]:
        lines.append("note: %s" % n)
    lines.append(DISCLAIMER)
    k = len(r["findings"])
    lines.append("statement_check: %d finding%s" % (k, "" if k == 1 else "s"))
    return lines


def main(argv=None, get=http_get, sleep=time.sleep, out=None, stdin=None):
    out = out or sys.stdout
    parser = argparse.ArgumentParser(prog="statement_check.py",
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
        r["status"], r["page_url"], text = read_url(args.source, find=args.find, get=get,
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
