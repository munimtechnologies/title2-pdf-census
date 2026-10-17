"""site_check: a one-website PDF self-check for ADA Title II, built on census.py.

Reads one website's home page and some of its pages (and any PDF links given),
checks each PDF for the four basics the census counts (tags, a document language,
a title, real text) and says in plain words what to fix in each one that fails.
Unlike the census, which samples pages at random so its shares stay unbiased, it
reads the pages that look like document lists first (Documents, Agendas, Forms,
Library and the like), so it finds a site's PDFs with fewer requests. If half its
pages turn up no PDF link, it reads the site's other pages first (0.1.2).

Same manners as census.py: public pages only, robots.txt honoured, a pause between
requests, a User-Agent that names Munim, Inc. and an email. Machine checks only:
passing them is necessary for an accessible PDF, never sufficient, and nothing here
is a WCAG conformance judgment or legal advice.

Usage:
    python site_check.py https://www.example.gov/ --md report.md --json report.json
    python site_check.py --pdf https://www.example.gov/docs/agenda.pdf --md report.md

Standard library plus pypdf. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import json
import logging
import re
import sys
import time
import urllib.parse

import census as c

__version__ = "0.1.2"

DEADLINES = ("Under the ADA Title II rule (DOJ, 2024-04-24; dates moved by the interim final rule "
             "of 2026-04-20), state and local governments serving 50,000 people or more must meet "
             "WCAG 2.1 AA, PDFs included, by 2027-04-26; smaller governments and special districts "
             "by 2028-04-26. Some older documents fall under the rule's exceptions; this check does "
             "not decide that.")
# The census's third full run (0.2.2, crawled 2026-10-16 to 2026-10-17), for comparison.
BASELINE = ("For comparison: of 5,412 PDFs from 926 US cities and counties of 50,000+ "
            "(title2-pdf-census, third full run, 2026-10-17), 60.5% were tagged and 22.0% "
            "passed all four basics.")
NO_PDFS = ("No PDF links were found on the pages read. Give PDF links directly, or read more pages.")

# Words in a link's text or URL path that suggest a page listing documents, including
# CivicPlus's DocumentCenter and AgendaCenter. Read before other pages.
DOC_RE = re.compile(r"(?<![a-z])(documents?|docs|documentcenter|agendacenter|pdfs?|forms?|agendas?|minutes|"
                    r"publications?|reports?|resources?|librar(?:y|ies)|downloads?|budgets?|plans?|policies|"
                    r"ordinances?|notices?|guidance|guides?|fact ?sheets?|archives?|files|meetings?)(?![a-z])",
                    re.I)

# Each basic a readable PDF can fail, most serious first: (key, label, what to do).
BASICS = (
    ("image_only", "No text (likely a scan)",
     "Screen readers get nothing at all. Publish the original digital file if there is one; "
     "otherwise run text recognition (OCR), tag the result and check it by hand."),
    ("tagged", "No tags",
     "Screen readers get no headings, lists, tables or reading order. From Word: File > Save As, "
     "choose PDF, Options, tick 'Document structure tags for accessibility', and save again. "
     "Otherwise add tags with a PDF editor's accessibility tools and check the reading order by hand."),
    ("lang", "No document language",
     "A screen reader may read it in the wrong language. Set it in the PDF's properties "
     "(Acrobat: File > Properties > Advanced > Language), or set the language in the source file "
     "before exporting."),
    ("title", "No title",
     "Browsers and screen readers announce the file name instead. Set a title in the source file "
     "(Word: File > Info > Properties > Title) or in the PDF (Acrobat: File > Properties > "
     "Description > Title)."),
)
LABELS = {key: label for key, label, _ in BASICS}
PRINT_NOTE = ("Made with print-to-PDF, whose output is seldom tagged (16.1% in the census): use the "
              "program's own Save as PDF or Export instead.")
SCANNER_NOTE = "Made by a scanner (4.5% of scanner output in the census was tagged)."


def failures(rec):
    """The basics a readable PDF record fails, most serious first."""
    return [key for key, _, _ in BASICS if (rec.get(key) if key == "image_only" else not rec.get(key))]


def notes(rec):
    """Other things worth fixing in a readable PDF record, in plain words."""
    out = []
    missing = rec.get("figures", 0) - rec.get("figures_alt", 0)
    if missing > 0:
        out.append("%d of %d tagged figures have no alt text." % (missing, rec["figures"]))
    if rec.get("title") and not rec.get("display_doc_title"):
        out.append("The window shows the file name, not the title "
                   "(Acrobat: File > Properties > Initial View > Show: Document Title).")
    family = rec.get("producer_family")
    if family == "print-to-pdf" and not rec.get("tagged"):
        out.append(PRINT_NOTE)
    elif family == "scanner":
        out.append(SCANNER_NOTE)
    return out


def pdf_record(url, resp):
    """One PDF's record from its response, as census.crawl_site makes it."""
    rec = {"url": url, "status": resp.status, "bytes": len(resp.body)}
    if resp.status != 200:
        rec["result"] = "http_error"
    elif resp.truncated:
        rec["result"] = "too_large"
    elif b"%PDF" not in resp.body[:1024]:
        rec["result"] = "not_pdf"
    else:
        try:
            rec.update(c.analyze_pdf(resp.body))
            rec["result"] = "ok"
        except Exception as e:
            rec["result"] = "parse_error"
            rec["error"] = ("%s: %s" % (type(e).__name__, e))[:200]
    return rec


def doc_like(url, text=""):
    """True if a link's text or URL path suggests a page that lists documents."""
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    return bool(DOC_RE.search(" ".join(text.split())) or DOC_RE.search(path))


def page_links(page, url):
    """{absolute http(s) link: the text of every <a> pointing at it}, in page order, without
    fragments, resolved against the page's <base href> as census.extract_links does."""
    parser, out = c.parse_links(page), {}
    base = c.page_base(parser, url)
    for href, text in zip(parser.hrefs, parser.texts):
        u = urllib.parse.urldefrag(urllib.parse.urljoin(base, href))[0]
        if urllib.parse.urlsplit(u).scheme in ("http", "https"):
            out[u] = (out.get(u, "") + " " + " ".join(text.split())).strip()
    return out


def crawl(site_url, get=c.http_get, pages=8, pdfs=8, delay=1.0, sleep=time.sleep,
          max_page_bytes=5_000_000, max_pdf_bytes=15_000_000):
    """Read a website's home page and up to `pages` of its pages, document-like pages first
    (and the document-like pages they link to), stopping early once there are twice `pdfs`
    PDF links; then check up to `pdfs` readable PDFs from them. If half the pages are read
    and no PDF link has turned up, the other pages are read first. Returns (site, PDF records)."""
    start = c.normalize_site(site_url)
    site = {"website": start, "status": "ok", "pages_read": 0, "doc_pages_read": 0, "pdf_links": 0,
            "pdfs_tried": 0, "pdfs_ok": 0, "a11y_link": None, "fell_back": False}
    found, robots = [], {}

    def allowed(url):
        parts = urllib.parse.urlsplit(url)
        key = "%s://%s" % (parts.scheme, parts.netloc)
        if key not in robots:
            robots[key] = c.robots_for(get(key + "/robots.txt", 500_000))
            sleep(delay)
        return robots[key].can_fetch(c.UA, url)

    if not allowed(start):
        site["status"] = "robots_disallow"
        return site, found
    home = get(start, max_page_bytes)
    sleep(delay)
    if home.status != 200:
        site["status"] = "home_%s" % (home.status or (home.error or "error").split(":")[0])
        return site, found
    if not c.is_html(home):
        site["status"] = "home_not_html"
        return site, found
    base = home.url or start
    page = c.decode(home)
    site["a11y_link"] = bool(c.accessibility_links(page, base))
    pdf_urls, docs, others, queued = [], [], [], {base.rstrip("/")}

    def take(page, url, first):
        links = page_links(page, url)
        pdf_urls.extend(u for u in links if c.looks_like_pdf(u))
        new_others = []
        for u, text in links.items():
            if (c.looks_like_pdf(u) or not c.same_site(u, base) or not c.crawlable_page(u)
                    or u.rstrip("/") in queued):
                continue
            queued.add(u.rstrip("/"))
            if doc_like(u, text):
                docs.append(u)
            else:
                new_others.append(u)
        # The home page's other links are sampled as the census does; deeper ones come after.
        others.extend(c.sample(new_others, len(new_others), start) if first else new_others)

    take(page, base, True)
    half = (pages + 1) // 2
    while site["pages_read"] < pages and (docs or others) and len(set(pdf_urls)) < 2 * pdfs:
        # 0.1.1 read every document-like page before any other, and on some sites spent all its
        # pages on document-like pages without a PDF link while random pages had them. Once half
        # the pages are read with no PDF link, the other pages go first.
        dry = site["pages_read"] >= half and not pdf_urls
        is_doc = bool(docs) and not (dry and others)
        if docs and not is_doc:
            site["fell_back"] = True
        url = docs.pop(0) if is_doc else others.pop(0)
        if not allowed(url):
            continue
        resp = get(url, max_page_bytes)
        sleep(delay)
        site["pages_read"] += 1
        site["doc_pages_read"] += is_doc
        if resp.status == 200 and c.is_html(resp):
            take(c.decode(resp), resp.url or url, False)
    pdf_urls = list(dict.fromkeys(pdf_urls))
    site["pdf_links"] = len(pdf_urls)
    for url in c.sample(pdf_urls, 2 * pdfs, start):
        if site["pdfs_ok"] >= pdfs:
            break
        if not allowed(url):
            continue
        rec = pdf_record(url, get(url, max_pdf_bytes))
        sleep(delay)
        site["pdfs_tried"] += 1
        site["pdfs_ok"] += rec["result"] == "ok"
        found.append(rec)
    return site, found


def check_pdfs(urls, get=c.http_get, sleep=time.sleep, delay=1.0, max_pdf_bytes=15_000_000):
    """Fetch and check each PDF link (http or https), honouring each host's robots.txt."""
    robots, found = {}, []
    for url in dict.fromkeys(u.strip() for u in urls if u and u.strip()):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            found.append({"url": url, "result": "bad_url"})
            continue
        key = "%s://%s" % (parts.scheme, parts.netloc)
        if key not in robots:
            robots[key] = c.robots_for(get(key + "/robots.txt", 500_000))
            sleep(delay)
        if not robots[key].can_fetch(c.UA, url):
            found.append({"url": url, "result": "robots_disallow"})
            continue
        resp = get(url, max_pdf_bytes)
        sleep(delay)
        found.append(pdf_record(url, resp))
    return found


def run(site_url="", pdf_urls=(), pages=8, pdfs=8, get=c.http_get, sleep=time.sleep, delay=1.0,
        checked=None):
    """Check a website (its home page, some of its pages and the PDFs they link) and/or a list
    of PDF links. Returns a dict with the site, one row per PDF and a summary."""
    site, found = None, []
    if site_url:
        site, found = crawl(site_url, get=get, pages=pages, pdfs=pdfs, delay=delay, sleep=sleep)
    seen = {r["url"] for r in found}
    found += check_pdfs([u for u in pdf_urls if u.strip() not in seen], get=get, sleep=sleep,
                        delay=delay)
    rows = []
    for rec in found:
        row = dict(rec)
        if rec.get("result") == "ok":
            row["fails"] = failures(rec)
            row["notes"] = notes(rec)
        rows.append(row)
    ok = [r for r in rows if r.get("result") == "ok"]
    summary = {"pdfs_checked": len(ok), "pdfs_not_read": len(rows) - len(ok),
               "pass_all_four": sum(1 for r in ok if not r["fails"]),
               "fail": {key: sum(1 for r in ok if key in r["fails"]) for key, _, _ in BASICS}}
    return {"version": __version__, "census_version": c.__version__,
            "checked": checked or time.strftime("%Y-%m-%d", time.gmtime()),
            "site": site, "pdfs": rows, "summary": summary}


def name_of(url):
    """A short name for a PDF: the last part of its path, or the URL."""
    path = urllib.parse.urlsplit(url).path.rstrip("/")
    return urllib.parse.unquote(path.rsplit("/", 1)[-1]) or url


def link(url):
    """url encoded for a Markdown link: spaces and parentheses would end it early."""
    return c.quote_url(url).replace("(", "%28").replace(")", "%29")


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def yes(value):
    return "yes" if value else "no"


def status_line(result):
    s = result["summary"]
    return "%d PDFs checked; %d pass all four basics; %d could not be read." % (
        s["pdfs_checked"], s["pass_all_four"], s["pdfs_not_read"])


def markdown(result):
    """A plain-language report of one check."""
    site, rows, s = result["site"], result["pdfs"], result["summary"]
    where = c.bare_host(site["website"]) if site else "PDF links"
    lines = ["# PDF basics check: %s" % where, "",
             "Checked %s with site_check %s (title2-pdf-census %s). Machine checks of four basics "
             "screen readers rely on: tags, a document language, a title and real text. Passing them "
             "is necessary for an accessible PDF, never sufficient; this is not a WCAG conformance "
             "judgment or legal advice." % (result["checked"], result["version"], result["census_version"]),
             ""]
    if site:
        a11y = {True: "yes", False: "no", None: "not known"}[site.get("a11y_link")]
        lines += ["- Website: %s (%s)" % (site["website"], site["status"]),
                  "- Pages read besides the home page: %d; PDF links found: %d" % (site["pages_read"],
                                                                                  site["pdf_links"]),
                  "- Home page links to a page about accessibility or the ADA: %s" % a11y]
    lines += ["- %s" % status_line(result), ""]
    if site and site["status"] == "ok" and not site["pdf_links"]:
        lines += [NO_PDFS, ""]
    ok = [r for r in rows if r.get("result") == "ok"]
    if ok:
        lines += ["| PDF | Tags | Language | Title | Text | Made with |", "|---|---|---|---|---|---|"]
        for r in ok:
            lines.append("| [%s](%s) | %s | %s | %s | %s | %s |" % (
                cell(name_of(r["url"])), link(r["url"]), yes(r.get("tagged")), yes(r.get("lang")),
                yes(r.get("title")), yes(not r.get("image_only")), r.get("producer_family") or "unknown"))
        lines.append("")
    if any(r["fails"] for r in ok):
        lines += ["## What to fix", ""]
        for key, label, advice in BASICS:
            hit = [r for r in ok if key in r["fails"]]
            if hit:
                lines += ["### %s (%d of %d)" % (label, len(hit), len(ok)), "", advice, ""]
                lines += ["- %s" % cell(name_of(r["url"])) for r in hit]
                lines.append("")
    with_notes = [r for r in ok if r["notes"]]
    if with_notes:
        lines += ["## Also worth fixing", ""]
        for r in with_notes:
            lines.append("- %s: %s" % (cell(name_of(r["url"])), " ".join(r["notes"])))
        lines.append("")
    unread = [r for r in rows if r.get("result") != "ok"]
    if unread:
        lines += ["## Not read", ""]
        lines += ["- %s: %s" % (cell(r["url"]), r["result"]) for r in unread]
        lines.append("")
    lines += [BASELINE, "", DEADLINES, "",
              "Made by MV2 of Munim, Inc. with AI agents (site_check, Apache-2.0: "
              "https://github.com/munimtechnologies/title2-pdf-census). Questions: mv2@munimtech.com.", ""]
    return "\n".join(lines)


def dataset_rows(result):
    """One flat row per PDF, for a table or a spreadsheet."""
    out = []
    for r in result["pdfs"]:
        row = {"name": name_of(r["url"]), "url": r["url"], "result": r.get("result")}
        if r.get("result") == "ok":
            row.update(all_four=not r["fails"], tagged=bool(r.get("tagged")), lang=bool(r.get("lang")),
                       title=bool(r.get("title")), has_text=not r.get("image_only"),
                       fails=[LABELS[k] for k in r["fails"]], notes=r["notes"], pages=r.get("pages"),
                       figures=r.get("figures"), figures_alt=r.get("figures_alt"),
                       created=r.get("created"), producer_family=r.get("producer_family"))
        out.append(row)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("site", nargs="?", default="", help="website to check, e.g. https://www.example.gov/")
    ap.add_argument("--pdf", action="append", default=[], help="a PDF link to check (repeatable)")
    ap.add_argument("--pages", type=int, default=8, help="inner pages read (default 8)")
    ap.add_argument("--pdfs", type=int, default=8, help="readable PDFs checked from the site (default 8)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1)")
    ap.add_argument("--json", help="write the full result as JSON here")
    ap.add_argument("--md", help="write the report as Markdown here")
    args = ap.parse_args(argv)
    if not args.site and not args.pdf:
        ap.error("give a website or at least one --pdf")
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    result = run(args.site, args.pdf, pages=args.pages, pdfs=args.pdfs, delay=max(0.5, args.delay))
    text = markdown(result)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
