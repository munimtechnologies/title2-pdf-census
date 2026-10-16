"""title2-pdf-census: how accessible are the PDFs that large US local governments publish?

Under the DOJ's ADA Title II rule (published 2024-04-24), state and local
governments serving 50,000 people or more must make their web content,
including PDFs, meet WCAG 2.1 AA by 2027-04-26. This tool takes that cohort
(cities and counties of 50,000+ with an official website on Wikidata), reads a
small sample of each one's public pages, and checks the PDFs linked there for
the structure screen readers rely on: tags, a document language, a title,
extractable text and figure alt text. Each PDF's creation date lets documents
made after the rule be compared with older ones. It also notes whether each
home page links to a page about accessibility or the ADA.

Machine checks only: passing them is necessary for an accessible PDF, never
sufficient, and nothing here is a WCAG conformance judgment.

Reads public pages only, one site at a time with a pause between requests,
honouring robots.txt, under a User-Agent that names Munim, Inc. and an email.
Stores no document text and no metadata titles, only structural facts.

Standard library plus pypdf. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import html.parser
import io
import json
import logging
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

__version__ = "0.2.2"

UA = ("MV2-title2-pdf-census/%s (Munim, Inc.; mv2@munimtech.com; "
      "reads public pages only)" % __version__)
RULE_DATE = "2024-04-24"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# Cities, counties, consolidated city-counties and towns of the US (and their
# direct subclasses, such as "county of Texas"), 50,000+ people, with a website.
COHORT_QUERY = """
SELECT ?item ?itemLabel ?typeLabel ?stateLabel (MAX(?pop) AS ?population) (SAMPLE(?site) AS ?website) WHERE {
  VALUES ?type { wd:Q1093829 wd:Q47168 wd:Q3301053 wd:Q15127012 }
  ?item wdt:P31/wdt:P279? ?type ;
        wdt:P17 wd:Q30 ;
        wdt:P1082 ?pop ;
        wdt:P856 ?site .
  FILTER(?pop >= 50000)
  OPTIONAL { ?item wdt:P131/wdt:P131? ?state . ?state wdt:P31 wd:Q35657 . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?item ?itemLabel ?typeLabel ?stateLabel
"""

# Links that are PDFs, or are served as PDFs by common local-government CMSs
# (CivicPlus Document Center, Agenda Center and Archive Center).
PDF_LINK_RE = re.compile(
    r"(\.pdf$)|(/documentcenter/view/)|(/agendacenter/viewfile/)|(/archive\.aspx\?adid=)", re.I)
SKIP_PAGE_EXT = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".doc", ".docx",
                 ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".mp3", ".mp4", ".mov", ".ics",
                 ".css", ".js", ".xml", ".rss", ".json", ".txt", ".csv")
# A home-page link to a page about accessibility or the ADA, by its URL path or
# its text. "ADA" counts only in capitals and not before "County" (Ada County, Idaho).
A11Y_PATH_RE = re.compile(r"accessib|section-?508", re.I)
A11Y_TEXT_RE = re.compile(r"(?i:accessib|section 508)|\bADA\b(?! County)")
CHECKS = ("tagged", "marked", "lang", "title", "display_doc_title", "image_only", "basic4")
# Characters left as they are when a link is percent-encoded: the URL delimiters and
# existing %xx escapes. Spaces and non-ASCII letters are encoded.
URL_SAFE = "/%:@!$&'()*+,;=~?"

Response = collections.namedtuple("Response", "status url ctype body truncated error")


# ---------------------------------------------------------------- fetching

def quote_url(url):
    """url with spaces and other characters urllib refuses percent-encoded in its path and
    query, as a browser does. 0.2.0 sent links as written, so every link with a space failed."""
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(p.path, safe=URL_SAFE),
                                    urllib.parse.quote(p.query, safe=URL_SAFE), ""))


def http_get(url, max_bytes, timeout=20):
    """GET url, reading at most max_bytes; never raises."""
    req = urllib.request.Request(quote_url(url), headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            chunks, size = [], 0
            while size <= max_bytes:
                chunk = r.read(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            body = b"".join(chunks)
            return Response(r.status, r.geturl(), r.headers.get("Content-Type", ""),
                            body[:max_bytes], len(body) > max_bytes, None)
    except urllib.error.HTTPError as e:
        return Response(e.code, url, "", b"", False, "http %d" % e.code)
    except Exception as e:  # DNS, TLS, timeouts, resets
        return Response(0, url, "", b"", False, ("%s: %s" % (type(e).__name__, e))[:200])


class LinkParser(html.parser.HTMLParser):
    """The href of every <a>, and the text inside it (texts[i] belongs to hrefs[i]),
    plus the href of the page's first <base> element, if it has one."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
        self.texts = []
        self.base = None
        self._open = None

    def handle_starttag(self, tag, attrs):
        if tag == "base" and self.base is None:
            for name, value in attrs:
                if name == "href" and value and value.strip():
                    self.base = value.strip()
        if tag == "a":
            self._open = None
            for name, value in attrs:
                if name == "href" and value:
                    self.hrefs.append(value.strip())
                    self.texts.append("")
                    self._open = len(self.hrefs) - 1

    def handle_endtag(self, tag):
        if tag == "a":
            self._open = None

    def handle_data(self, data):
        if self._open is not None:
            self.texts[self._open] += data


def parse_links(page):
    parser = LinkParser()
    try:
        parser.feed(page)
    except Exception:
        pass
    return parser


def page_base(parser, url):
    """The URL a page's relative links resolve against: its first <base href> (itself resolved
    against the page), else the page's own URL. Revize and other CMSs set <base href> to the
    site root; 0.2.1 ignored it, so relative links on their inner pages resolved under the
    page's folder and failed with 404."""
    if parser.base:
        base = urllib.parse.urljoin(url, parser.base)
        if urllib.parse.urlsplit(base).scheme in ("http", "https"):
            return base
    return url


def extract_links(page, base):
    """Absolute http(s) links of a page's <a href>s, without fragments, in order, deduplicated."""
    parser, out, seen = parse_links(page), [], set()
    base = page_base(parser, base)
    for href in parser.hrefs:
        url = urllib.parse.urldefrag(urllib.parse.urljoin(base, href))[0]
        if urllib.parse.urlsplit(url).scheme in ("http", "https") and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def accessibility_links(page, base):
    """Absolute links whose URL path or link text is about accessibility or the ADA."""
    parser, out = parse_links(page), []
    base = page_base(parser, base)
    for href, text in zip(parser.hrefs, parser.texts):
        url = urllib.parse.urldefrag(urllib.parse.urljoin(base, href))[0]
        if urllib.parse.urlsplit(url).scheme not in ("http", "https") or url in out:
            continue
        if A11Y_PATH_RE.search(urllib.parse.urlsplit(url).path) or A11Y_TEXT_RE.search(" ".join(text.split())):
            out.append(url)
    return out


def looks_like_pdf(url):
    parts = urllib.parse.urlsplit(url)
    path = parts.path + ("?" + parts.query if parts.query else "")
    return bool(PDF_LINK_RE.search(parts.path) or PDF_LINK_RE.search(path))


def bare_host(url):
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_site(url, base):
    """True if url is on base's host or one of its subdomains (ignoring www.)."""
    host, home = bare_host(url), bare_host(base)
    return bool(home) and (host == home or host.endswith("." + home))


def crawlable_page(url):
    path = urllib.parse.urlsplit(url).path.lower()
    return not path.endswith(SKIP_PAGE_EXT)


def is_html(resp):
    if "html" in resp.ctype.lower():
        return True
    head = resp.body[:300].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def decode(resp):
    m = re.search(r"charset=([\w-]+)", resp.ctype or "", re.I)
    try:
        return resp.body.decode(m.group(1) if m else "utf-8", "replace")
    except LookupError:
        return resp.body.decode("utf-8", "replace")


def sample(items, n, seed):
    """A reproducible pseudo-random choice of n items (stable order, no bias toward page order)."""
    def key(item):
        return hashlib.sha1((seed + "|" + item).encode("utf-8")).hexdigest()
    return sorted(items, key=key)[:n]


def robots_for(resp):
    """A RobotFileParser from a robots.txt response, using the usual conventions."""
    rp = urllib.robotparser.RobotFileParser()
    if resp.status == 200 and resp.body:
        rp.parse(resp.body.decode("utf-8", "replace").splitlines())
    elif resp.status in (401, 403):
        rp.disallow_all = True
    else:
        rp.allow_all = True
    return rp


def normalize_site(url):
    url = url.strip()
    if not re.match(r"https?://", url, re.I):
        url = "http://" + url
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", "", ""))


# ---------------------------------------------------------------- PDF checks

def resolve(obj):
    return obj.get_object() if hasattr(obj, "get_object") else obj


def truthy(obj):
    return getattr(resolve(obj), "value", resolve(obj)) is True


def pdf_date(raw):
    """'D:20240512103000-04'00'' -> '2024-05-12'; None if missing or implausible."""
    m = re.search(r"(\d{4})(\d{2})(\d{2})", str(raw or ""))
    if not m:
        return None
    y, mo, d = (int(g) for g in m.groups())
    if not (1993 <= y <= 2030 and 1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return "%04d-%02d-%02d" % (y, mo, d)


PRODUCER_FAMILIES = (
    ("word", r"microsoft.*word|word.*microsoft"),
    ("office-other", r"microsoft.*(excel|powerpoint|publisher)|microsoft.*office"),
    ("print-to-pdf", r"microsoft: print to pdf|skia/pdf|quartz pdfcontext|cairo|chrome"),
    ("scanner", r"canon|konica|ricoh|xerox|sharp|kyocera|lexmark|epson|paperport|scan|toshiba|brother|fujifilm|minolta|bizhub|imagerunner"),
    ("adobe", r"acrobat|adobe pdf library|distiller|indesign|illustrator|photoshop|pdfmaker"),
    ("libreoffice", r"libreoffice|openoffice"),
    ("google-docs", r"google docs|google"),
    ("generator", r"itext|pdfsharp|wkhtmltopdf|reportlab|tcpdf|fpdf|dompdf|aspose|crystal|ghostscript|pdflib|prince|telerik|devexpress|syncfusion|pdfium|qt "),
)


def producer_family(producer, creator=""):
    text = ("%s %s" % (producer or "", creator or "")).lower()
    if not text.strip():
        return "unknown"
    for name, pattern in PRODUCER_FAMILIES:
        if re.search(pattern, text):
            return name
    return "other"


def count_figures(root, cap=20000):
    """(figures, figures with non-empty /Alt, stopped at cap) in the structure tree."""
    tree = resolve(root.get("/StructTreeRoot"))
    if not isinstance(tree, dict):
        return 0, 0, False
    rolemap = resolve(tree.get("/RoleMap")) or {}
    stack, seen, figures, alts = [tree.get("/K")], 0, 0, 0
    while stack and seen < cap:
        node = resolve(stack.pop())
        seen += 1
        if isinstance(node, list):
            stack.extend(node)
            continue
        if not isinstance(node, dict):
            continue
        kind = str(node.get("/S", ""))
        if isinstance(rolemap, dict) and kind in rolemap:
            kind = str(resolve(rolemap[kind]))
        if kind == "/Figure":
            figures += 1
            if str(resolve(node.get("/Alt", "")) or "").strip():
                alts += 1
        kids = node.get("/K")
        if kids is not None:
            stack.append(kids)
    return figures, alts, seen >= cap


def analyze_pdf(data, text_pages=2):
    """Structural accessibility facts of one PDF (bytes). Raises if pypdf cannot read it."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    root = resolve(reader.trailer["/Root"])
    mark = resolve(root.get("/MarkInfo"))
    prefs = resolve(root.get("/ViewerPreferences"))
    info = reader.metadata or {}

    def meta(key):  # resolved first: an unresolved reference prints digits that look like a date
        return str(resolve(info.get(key)) or "")

    pages = len(reader.pages)
    chars = 0
    for i in range(min(text_pages, pages)):
        try:
            chars += len((reader.pages[i].extract_text() or "").strip())
        except Exception:
            pass
    figures, alts, capped = count_figures(root)
    created, modified = pdf_date(meta("/CreationDate")), pdf_date(meta("/ModDate"))
    producer, creator = meta("/Producer")[:80], meta("/Creator")[:80]
    row = {
        "pages": pages,
        "tagged": "/StructTreeRoot" in root,
        "marked": isinstance(mark, dict) and truthy(mark.get("/Marked")),
        "lang": bool(str(resolve(root.get("/Lang", "")) or "").strip()),
        "title": bool(meta("/Title").strip()),
        "display_doc_title": isinstance(prefs, dict) and truthy(prefs.get("/DisplayDocTitle")),
        "text_chars": chars,
        "image_only": pages > 0 and chars < 20,
        "figures": figures,
        "figures_alt": alts,
        "struct_capped": capped,
        "created": created or modified,
        "date_source": "creation" if created else ("mod" if modified else None),
        "producer": producer,
        "creator": creator,
        "producer_family": producer_family(producer, creator),
    }
    row["basic4"] = row["tagged"] and row["lang"] and row["title"] and not row["image_only"]
    return row


# ---------------------------------------------------------------- crawling

def crawl_site(row, get=http_get, pages=8, pdfs=8, delay=1.0, sleep=time.sleep,
               max_page_bytes=5_000_000, max_pdf_bytes=15_000_000, deadline=None):
    """Read one government's home page, a sample of its pages and the PDFs they link."""
    site = {k: row.get(k, "") for k in ("qid", "name", "kind", "state", "population", "website")}
    site.update(status="ok", pages_read=0, pdf_links=0, pdfs_tried=0, pdfs_ok=0, a11y_link=None)
    found = []
    if deadline and time.time() > deadline:
        site["status"] = "not_started"
        return site, found
    start = normalize_site(row["website"])
    robots = {}

    def allowed(url):
        host = urllib.parse.urlsplit(url)
        key = "%s://%s" % (host.scheme, host.netloc)
        if key not in robots:
            robots[key] = robots_for(get(key + "/robots.txt", 500_000))
            sleep(delay)
        return robots[key].can_fetch(UA, url)

    if not allowed(start):
        site["status"] = "robots_disallow"
        return site, found
    home = get(start, max_page_bytes)
    sleep(delay)
    if home.status != 200:
        site["status"] = "home_%s" % (home.status or (home.error or "error").split(":")[0])
        return site, found
    if not is_html(home):
        site["status"] = "home_not_html"
        return site, found
    base = home.url or start
    page = decode(home)
    links = extract_links(page, base)
    site["a11y_link"] = bool(accessibility_links(page, base))
    pdf_urls = [u for u in links if looks_like_pdf(u)]
    inner = [u for u in links if same_site(u, base) and not looks_like_pdf(u) and crawlable_page(u)
             and u.rstrip("/") != base.rstrip("/")]
    for url in sample(inner, pages, start):
        if deadline and time.time() > deadline:
            site["status"] = "deadline"
            break
        if not allowed(url):
            continue
        resp = get(url, max_page_bytes)
        sleep(delay)
        site["pages_read"] += 1
        if resp.status == 200 and is_html(resp):
            pdf_urls += [u for u in extract_links(decode(resp), resp.url or url) if looks_like_pdf(u)]
    pdf_urls = list(dict.fromkeys(pdf_urls))
    site["pdf_links"] = len(pdf_urls)
    for url in sample(pdf_urls, 2 * pdfs, start):
        if site["pdfs_ok"] >= pdfs or (deadline and time.time() > deadline):
            break
        if not allowed(url):
            continue
        resp = get(url, max_pdf_bytes)
        sleep(delay)
        site["pdfs_tried"] += 1
        rec = {"qid": site["qid"], "kind": site["kind"], "state": site["state"], "url": url,
               "host": bare_host(url), "same_site": same_site(url, base), "status": resp.status,
               "bytes": len(resp.body)}
        if resp.status != 200:
            rec["result"] = "http_error"
        elif resp.truncated:
            rec["result"] = "too_large"
        elif b"%PDF" not in resp.body[:1024]:
            rec["result"] = "not_pdf"
        else:
            try:
                rec.update(analyze_pdf(resp.body))
                rec["result"] = "ok"
                site["pdfs_ok"] += 1
            except Exception as e:
                rec["result"] = "parse_error"
                rec["error"] = ("%s: %s" % (type(e).__name__, e))[:200]
        found.append(rec)
    return site, found


def crawl(cohort, out_sites, out_pdfs, workers=24, deadline=None, **kw):
    """Crawl every site in the cohort in parallel (one site per worker), appending JSON lines."""
    order = sample([r["website"] for r in cohort], len(cohort), "order")
    by_site = {r["website"]: r for r in cohort}
    with open(out_sites, "w", encoding="utf-8") as fs, open(out_pdfs, "w", encoding="utf-8") as fp, \
            concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(crawl_site, by_site[w], deadline=deadline, **kw) for w in order]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                site, found = fut.result()
            except Exception as e:
                site, found = {"status": "crash", "error": str(e)[:200]}, []
            fs.write(json.dumps(site) + "\n")
            for rec in found:
                fp.write(json.dumps(rec) + "\n")
            fs.flush()
            fp.flush()
            if i % 50 == 0:
                print("%d/%d sites" % (i, len(futures)), flush=True)


# ---------------------------------------------------------------- cohort

def fetch_cohort(get=http_get):
    """The cohort from Wikidata; if the query with states times out, again without them."""
    simple = "\n".join(line for line in COHORT_QUERY.splitlines() if "OPTIONAL" not in line)
    simple = simple.replace(" ?stateLabel", "")
    for query in (COHORT_QUERY, simple):
        url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
        resp = get(url, 50_000_000, timeout=120)
        if resp.status == 200:
            return parse_cohort(json.loads(resp.body.decode("utf-8")))
        print("Wikidata query failed: %s %s" % (resp.status, resp.error), file=sys.stderr)
        time.sleep(10)
    raise RuntimeError("Wikidata query failed twice")


def parse_cohort(data):
    """Rows from the SPARQL JSON, one per website host (largest population kept)."""
    best = {}
    for b in data["results"]["bindings"]:
        def val(k):
            return b.get(k, {}).get("value", "")
        website = val("website")
        try:
            population = int(float(val("population")))
        except ValueError:
            continue
        host = bare_host(normalize_site(website))
        if not host:
            continue
        type_label = val("typeLabel").lower()
        kind = ("city-county" if "consolidated" in type_label else
                "county" if "county" in type_label else
                "town" if "town" in type_label else "city")
        row = {"qid": val("item").rsplit("/", 1)[-1], "name": val("itemLabel"), "kind": kind,
               "state": val("stateLabel"), "population": population, "website": website}
        if host not in best or population > best[host]["population"]:
            best[host] = row
    return sorted(best.values(), key=lambda r: (-r["population"], r["qid"]))


def write_csv(rows, path, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- summary

def wilson(k, n, z=1.96):
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def share(rows, key):
    n = len(rows)
    k = sum(1 for r in rows if r.get(key))
    return {"n": n, "k": k, "share": round(k / n, 4) if n else None, "ci95": wilson(k, n)}


def era(row):
    if not row.get("created"):
        return "undated"
    return "after_rule" if row["created"] >= RULE_DATE else "before_rule"


def summarize(sites, pdfs, min_site_pdfs=3):
    ok = [p for p in pdfs if p.get("result") == "ok"]
    groups = collections.defaultdict(list)
    for p in ok:
        groups[("era", era(p))].append(p)
        groups[("year", p["created"][:4] if p.get("created") else "undated")].append(p)
        groups[("kind", p.get("kind") or "")].append(p)
        groups[("producer", p.get("producer_family") or "unknown")].append(p)
    def table(dim):
        return {key: {c: share(rows, c) for c in ("tagged", "lang", "title", "image_only", "basic4")}
                for (d, key), rows in sorted(groups.items()) if d == dim}

    per_site = collections.defaultdict(list)
    for p in ok:
        per_site[p["qid"]].append(p)
    rated = {q: rows for q, rows in per_site.items() if len(rows) >= min_site_pdfs}
    site_rates = [sum(1 for r in rows if r["tagged"]) / len(rows) for rows in rated.values()]

    diffs = []
    for rows in per_site.values():
        pre = [r for r in rows if era(r) == "before_rule"]
        post = [r for r in rows if era(r) == "after_rule"]
        if pre and post:
            diffs.append(sum(r["tagged"] for r in post) / len(post) - sum(r["tagged"] for r in pre) / len(pre))

    figures = sum(p.get("figures", 0) for p in ok)
    return {
        "version": __version__,
        "rule_date": RULE_DATE,
        "sites": len(sites),
        "site_status": dict(collections.Counter(s.get("status", "") for s in sites).most_common()),
        "sites_with_ok_pdf": len(per_site),
        "home_a11y_link": share([s for s in sites if s.get("a11y_link") is not None], "a11y_link"),
        "pdfs_tried": len(pdfs),
        "pdf_results": dict(collections.Counter(p.get("result", "") for p in pdfs).most_common()),
        "overall": {c: share(ok, c) for c in CHECKS},
        "by_era": table("era"),
        "by_year": table("year"),
        "by_kind": table("kind"),
        "by_producer": table("producer"),
        "figures": {"total": figures, "with_alt": sum(p.get("figures_alt", 0) for p in ok),
                    "pdfs_with_figures": sum(1 for p in ok if p.get("figures"))},
        "sites_rated": {
            "min_pdfs": min_site_pdfs, "n": len(site_rates),
            "mean_tagged_share": round(sum(site_rates) / len(site_rates), 4) if site_rates else None,
            "none_tagged": sum(1 for x in site_rates if x == 0),
            "all_tagged": sum(1 for x in site_rates if x == 1),
        },
        "paired_era": {
            "sites": len(diffs),
            "mean_tagged_change": round(sum(diffs) / len(diffs), 4) if diffs else None,
            "improved": sum(1 for d in diffs if d > 0), "worse": sum(1 for d in diffs if d < 0),
            "same": sum(1 for d in diffs if d == 0),
        },
    }


def pct(cell):
    if not cell or cell["share"] is None:
        return "-"
    lo, hi = cell["ci95"]
    return "%.1f%% (%.1f-%.1f), n=%d" % (100 * cell["share"], 100 * lo, 100 * hi, cell["n"])


def report(summary):
    """Markdown results page from a summary."""
    lines = ["# title2-pdf-census results (v%s)" % summary["version"], "",
             "Machine checks of PDFs linked from US local-government websites (cities and counties "
             "of 50,000+, from Wikidata). Necessary, not sufficient, for accessibility; not a WCAG "
             "conformance judgment. Shares with 95% Wilson intervals.", "",
             "- Sites: %d; with at least one readable PDF: %d" % (summary["sites"], summary["sites_with_ok_pdf"]),
             "- Site outcomes: %s" % json.dumps(summary["site_status"]),
             "- Home page links to a page about accessibility or the ADA (by link text or URL): %s"
             % pct(summary.get("home_a11y_link")),
             "- PDFs tried: %d; outcomes: %s" % (summary["pdfs_tried"], json.dumps(summary["pdf_results"])), "",
             "## All readable PDFs", "", "| Check | Share |", "|---|---|"]
    names = {"tagged": "Tagged (structure tree)", "marked": "Marked", "lang": "Document language set",
             "title": "Title in metadata", "display_doc_title": "Shows title in window",
             "image_only": "Image only (no text on first 2 pages)",
             "basic4": "All four basics (tagged, language, title, has text)"}
    for c in CHECKS:
        lines.append("| %s | %s |" % (names[c], pct(summary["overall"][c])))
    for dim, title in (("by_era", "Before and after the rule (%s), by creation date" % summary["rule_date"]),
                       ("by_year", "By year created"), ("by_kind", "By kind of government"),
                       ("by_producer", "By the software that made the PDF")):
        lines += ["", "## " + title, "", "| Group | Tagged | Language | Title | Image only | All four |",
                  "|---|---|---|---|---|---|"]
        for key, cells in summary[dim].items():
            lines.append("| %s | %s |" % (key, " | ".join(
                pct(cells[c]) for c in ("tagged", "lang", "title", "image_only", "basic4"))))
    f, s, p = summary["figures"], summary["sites_rated"], summary["paired_era"]
    lines += ["", "## Figures", "",
              "%d figures tagged in %d PDFs; %d have alt text." % (f["total"], f["pdfs_with_figures"], f["with_alt"]),
              "", "## Sites", "",
              "Sites with at least %d readable PDFs: %d. Mean share tagged: %s. None tagged: %d. All tagged: %d."
              % (s["min_pdfs"], s["n"], s["mean_tagged_share"], s["none_tagged"], s["all_tagged"]),
              "", "Sites with PDFs from both before and after the rule: %d. Mean change in tagged share "
              "(after minus before): %s. Improved %d, worse %d, same %d."
              % (p["sites"], p["mean_tagged_change"], p["improved"], p["worse"], p["same"]), ""]
    return "\n".join(lines)


def site_table(sites, pdfs):
    """One row per site: PDFs checked and how many pass each check."""
    per_site = collections.defaultdict(list)
    for p in pdfs:
        if p.get("result") == "ok":
            per_site[p["qid"]].append(p)
    rows = []
    for s in sites:
        ok = per_site.get(s.get("qid"), [])
        row = dict(s)
        for c in ("tagged", "lang", "title", "image_only", "basic4"):
            row[c] = sum(1 for r in ok if r.get(c))
        rows.append(row)
    return sorted(rows, key=lambda r: (str(r.get("state")), str(r.get("name"))))


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cohort", help="write the cohort CSV from Wikidata")
    c.add_argument("--out", required=True)
    r = sub.add_parser("crawl", help="read the cohort's sites and check their PDFs")
    r.add_argument("--cohort", required=True)
    r.add_argument("--sites-out", required=True)
    r.add_argument("--pdfs-out", required=True)
    r.add_argument("--pages", type=int, default=8, help="inner pages read per site")
    r.add_argument("--pdfs", type=int, default=8, help="readable PDFs checked per site")
    r.add_argument("--workers", type=int, default=24)
    r.add_argument("--delay", type=float, default=1.0, help="seconds between requests to one site")
    r.add_argument("--limit", type=int, default=0, help="only the first N sites (0: all)")
    r.add_argument("--max-minutes", type=float, default=0)
    s = sub.add_parser("summarize", help="write summary.json, results.md and sites.csv")
    s.add_argument("--sites", required=True)
    s.add_argument("--pdfs", required=True)
    s.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    if args.cmd == "cohort":
        rows = fetch_cohort()
        write_csv(rows, args.out, ["qid", "name", "kind", "state", "population", "website"])
        print("%d governments in the cohort" % len(rows))
    elif args.cmd == "crawl":
        cohort = read_csv(args.cohort)
        if args.limit:
            cohort = cohort[:args.limit]
        deadline = time.time() + 60 * args.max_minutes if args.max_minutes else None
        crawl(cohort, args.sites_out, args.pdfs_out, workers=args.workers, deadline=deadline,
              pages=args.pages, pdfs=args.pdfs, delay=args.delay)
    else:
        sites, pdfs = read_jsonl(args.sites), read_jsonl(args.pdfs)
        summary = summarize(sites, pdfs)
        with open(args.out_dir.rstrip("/") + "/summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1)
        with open(args.out_dir.rstrip("/") + "/results.md", "w", encoding="utf-8") as f:
            f.write(report(summary))
        write_csv(site_table(sites, pdfs), args.out_dir.rstrip("/") + "/sites.csv",
                  ["qid", "name", "kind", "state", "population", "website", "status", "pages_read",
                   "pdf_links", "pdfs_tried", "pdfs_ok", "a11y_link", "tagged", "lang", "title",
                   "image_only", "basic4"])
        print(report(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
