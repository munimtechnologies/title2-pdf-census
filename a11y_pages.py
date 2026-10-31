"""a11y_pages: what do large US local governments' accessibility pages say?

The pre-registered test in results/a11y-pages/PREREG.md. The Title II census (results/v0.2.2)
found that 72.6% of the home pages of US cities and counties of 50,000+ link to a page about
accessibility or the ADA, but never read those pages. The DOJ's Title II rule adopts WCAG 2.1 AA,
and its April 2026 interim final rule moved the first compliance date from April 24, 2026 to
April 26, 2027. This script, for the same cohort:

  1. waits until results/a11y-pages/PREREG.md is on the repository's main branch and main's
     a11y_pages.py is byte for byte this file (gives up after about an hour);
  2. reads the cohort (results/v0.2.2/cohort.csv at commit 279e85e);
  3. reads each home page, picks its accessibility page by the census's link rules (same site
     only, ranked), reads that page and records which WCAG versions it names, whether it names
     Section 508 or Title II, and whether it gives the old (April 24, 2026) or the new (April 26,
     2027) compliance date; then grades H1-H5.

Reads public pages only, one site at a time with a pause between requests, honouring
robots.txt, under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond
short snippets around a WCAG version or a date, with email addresses and phone numbers removed.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import concurrent.futures
import csv
import hashlib
import html.parser
import io
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

__version__ = "0.1.0"

REPO_RAW = "https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/main/"
PREREG_PATH = "results/a11y-pages/PREREG.md"
SCRIPT_PATH = "a11y_pages.py"
COHORT_COMMIT = "279e85ecf05268d8883c5887292ef5acdf555cd6"
COHORT_URL = ("https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/%s/"
              "results/v0.2.2/cohort.csv" % COHORT_COMMIT)
UA = ("MV2-a11y-pages/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_COHORT, MAX_COHORT = 1600, 1700
MIN_HOMES = 950
MIN_PAGES = 500
MIN_TEXT = 200
MIN_VERSIONED = 200
MIN_DATED = 20
MIN_SIZE_GROUP = 80
BIG = 250000
H1_MIN_ONLY_20 = 0.15
H3_MIN_VERSIONED = 0.40
H4_MIN_OLD_ONLY = 0.30
H5_MIN_GAP = 0.05
MAX_TRIES = 3

TRIES = 40
PAUSE = 90

# The census's rules (census.py 0.2.3) for a link to a page about accessibility or the ADA,
# ranked by link_rank. "ADA" counts only in capitals and not before "County" (Ada County, Idaho).
A11Y_TEXT_RE = re.compile(r"(?i:accessib|section 508)|\bADA\b(?! County)")
SKIP_EXT = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".jpg", ".jpeg",
            ".png", ".gif", ".svg", ".mp3", ".mp4", ".txt", ".csv", ".xml", ".json", ".ics")
PDF_LIKE_RE = re.compile(r"/documentcenter/view/|/agendacenter/viewfile/|/archive\.aspx", re.I)

# A WCAG 2.x version: "WCAG 2.1", "WCAG2.0", "Web Content Accessibility Guidelines (WCAG)
# version 2.1", "WCAG 2.0 and 2.1", "WCAG 2.0, 2.1, and 2.2". A success-criterion number
# such as 2.1.1 is not a version.
V = r"2\.[0-2](?!\.?\d)"
VERSION_RE = re.compile(
    r"(?:\bWCAG|\bWeb\s+Content\s+Accessibility\s+Guidelines)\s*(?:\(WCAG\)\s*)?,?\s*"
    r"(?:version\s*|v\.?\s*)?(" + V + r"(?:\s*(?:,\s*(?:and|or)?|and|or|&|/|-)\s*(?:WCAG\s*)?"
    + V + r")*)", re.I)
WCAG_ANY_RE = re.compile(r"\bWCAG|\bWeb\s+Content\s+Accessibility\s+Guidelines", re.I)
S508_RE = re.compile(r"\bSection\s*508\b", re.I)
TITLE2_RE = re.compile(r"\bTitle\s+II\b", re.I)
OLD_DATE_RE = re.compile(r"\bApr(?:il|\.)?\s+24(?:th)?,?\s+2026\b|\b24\s+April,?\s+2026\b|"
                         r"\b0?4/24/(?:20)?26\b|\b2026-04-24\b", re.I)
NEW_DATE_RE = re.compile(r"\bApr(?:il|\.)?\s+26(?:th)?,?\s+2027\b|\b26\s+April,?\s+2027\b|"
                         r"\b0?4/26/(?:20)?27\b|\b2027-04-26\b", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?:\(?\b\d{3}\)?[\s.-]*)?\b\d{3}[\s.-]\d{4}\b")
OVERLAYS = (("userway", "userway"), ("accessibe", "accessibe"), ("accessibe", "acsbapp"),
            ("audioeye", "audioeye"), ("equalweb", "equalweb"), ("recite", "reciteme"))


# ---------------------------------------------------------------- fetching

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(data):
    """Bytes with CRLF turned into LF, so a line-ending change does not count as a difference."""
    return data.replace(b"\r\n", b"\n")


def fetch_bytes(url, tries=4, timeout=60):
    """GET a URL (the repository and the cohort), retrying; raises the last error."""
    err = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # network errors are retried, then raised
            err = e
            time.sleep(2 * (i + 1))
    raise err


def quote_url(url):
    p = urllib.parse.urlsplit(url)
    safe = "/%:@!$&'()*+,;=~?"
    return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(p.path, safe=safe),
                                    urllib.parse.quote(p.query, safe=safe), ""))


def http_get(url, max_bytes=3_000_000, timeout=20):
    """(status, final url, content type, body) of a public page; never raises (status 0)."""
    req = urllib.request.Request(quote_url(url), headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), r.read(max_bytes)
    except urllib.error.HTTPError as e:
        return e.code, url, "", b""
    except Exception:  # DNS, TLS, timeouts, resets
        return 0, url, "", b""


def robots_checker(get, delay, sleep):
    """allowed(url): each host's robots.txt is read once (401/403 means none allowed)."""
    robots = {}

    def allowed(url):
        p = urllib.parse.urlsplit(url)
        key = "%s://%s" % (p.scheme, p.netloc)
        if key not in robots:
            status, _, _, body = get(key + "/robots.txt")
            sleep(delay)
            rp = urllib.robotparser.RobotFileParser()
            if status == 200 and body:
                rp.parse(body.decode("utf-8", "replace").splitlines())
            elif status in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
            robots[key] = rp
        return robots[key].can_fetch(UA, url)
    return allowed


# ---------------------------------------------------------------- parsing

class Page(html.parser.HTMLParser):
    """Links (href, text with img alt, aria-label and title) and visible text of a page."""
    SKIP = ("script", "style", "noscript", "template", "svg")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.text, self.base = [], [], None
        self._open, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "base" and a.get("href") and self.base is None:
            self.base = a["href"]
        if tag in self.SKIP:
            self._skip += 1
        if tag == "a":  # an anchor without href is kept open too, so its </a> closes it
            self._open.append([a.get("href"), [a.get("aria-label") or "", a.get("title") or ""]])
        elif tag == "img" and self._open:
            self._open[-1][1].append(a.get("alt") or "")

    def handle_startendtag(self, tag, attrs):
        if tag == "img" and self._open:
            self._open[-1][1].append(dict(attrs).get("alt") or "")
        elif tag == "base":
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == "a" and self._open:
            href, parts = self._open.pop()
            if href is not None:
                self.links.append((href, " ".join(" ".join(parts).split())))

    def handle_data(self, data):
        if self._open:
            self._open[-1][1].append(data)
        if not self._skip:
            self.text.append(data)


def parse(body, ctype=""):
    m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
    try:
        text = body.decode(m.group(1) if m else "utf-8", "replace")
    except LookupError:
        text = body.decode("utf-8", "replace")
    p = Page()
    try:
        p.feed(text)
        p.close()
    except Exception:  # a broken page keeps what was parsed before the error
        pass
    for href, parts in p._open:  # links left open at the end of the page
        if href is not None:
            p.links.append((href, " ".join(" ".join(parts).split())))
    return p


def visible_text(p):
    return " ".join(" ".join(p.text).replace("\xa0", " ").split())


def is_html(ctype, body):
    if "html" in (ctype or "").lower():
        return True
    head = body[:300].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def bare_host(url):
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def same_site(url, base):
    host, home = bare_host(url), bare_host(base)
    return bool(home) and (host == home or host.endswith("." + home))


def normalize_site(url):
    url = url.strip()
    if not re.match(r"https?://", url, re.I):
        url = "http://" + url
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", "", ""))


def link_rank(url, text):
    """0 path names accessibility, 1 text names it, 2 Section 508, 3 ADA; None if no match."""
    path = urllib.parse.urlsplit(url).path
    if re.search(r"accessib", path, re.I):
        return 0
    if re.search(r"accessib", text, re.I):
        return 1
    if re.search(r"section-?508", path, re.I) or re.search(r"section 508", text, re.I):
        return 2
    if A11Y_TEXT_RE.search(text):
        return 3
    return None


def candidates(p, base):
    """(same-site page candidates ranked, links to other sites, document links) of a home page."""
    base = urllib.parse.urljoin(base, p.base) if p.base else base
    best, off, docs = {}, 0, 0
    for order, (href, text) in enumerate(p.links):
        url = urllib.parse.urldefrag(urllib.parse.urljoin(base, href.strip()))[0]
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            continue
        rank = link_rank(url, text)
        if rank is None:
            continue
        if not same_site(url, base):
            off += 1
            continue
        path = urllib.parse.urlsplit(url).path.lower()
        if path.endswith(SKIP_EXT) or PDF_LIKE_RE.search(url):
            docs += 1
            continue
        if url.rstrip("/") == base.rstrip("/"):
            continue
        if url not in best or (rank, order) < best[url]:
            best[url] = (rank, order)
    ranked = sorted(best, key=lambda u: best[u])
    return [(u, best[u][0]) for u in ranked], off, docs


def scrub(s):
    return PHONE_RE.sub("[phone]", EMAIL_RE.sub("[email]", s))


def snippet(text, m, width=70):
    return scrub(text[max(0, m.start() - width):m.end() + width])


def classify(text):
    """What one accessibility page says."""
    versions = set()
    first = None
    for m in VERSION_RE.finditer(text):
        versions.update(re.findall(r"2\.[0-2]", m.group(1)))
        first = first or m
    old, new = OLD_DATE_RE.search(text), NEW_DATE_RE.search(text)
    high = max(versions) if versions else ""
    return {"wcag_any": bool(WCAG_ANY_RE.search(text)),
            "versions": "+".join(sorted(versions)), "highest": high,
            "section508": bool(S508_RE.search(text)), "title2": bool(TITLE2_RE.search(text)),
            "old_date": bool(old), "new_date": bool(new),
            "version_snippet": snippet(text, first) if first else "",
            "date_snippet": snippet(text, old or new) if (old or new) else ""}


def overlays(body):
    low = body.lower()
    return "+".join(sorted({name for name, mark in OVERLAYS if mark.encode() in low}))


# ---------------------------------------------------------------- crawling

def crawl_site(row, get=http_get, delay=1.0, sleep=time.sleep, deadline=None):
    out = {k: row.get(k, "") for k in ("qid", "name", "kind", "state", "population", "website")}
    out.update(home="", overlay="", candidates=0, offsite_links=0, doc_links=0, page_url="",
               page_rank="", page_status="", tries=0, text_chars=0, text_sha256="")
    if deadline and time.time() > deadline:
        out["home"] = "not_started"
        return out
    start = normalize_site(row["website"])
    allowed = robots_checker(get, delay, sleep)
    if not allowed(start):
        out["home"] = "robots"
        return out
    status, final, ctype, body = get(start)
    sleep(delay)
    if status != 200:
        out["home"] = "http_%d" % status
        return out
    if not is_html(ctype, body):
        out["home"] = "not_html"
        return out
    out["home"] = "ok"
    out["overlay"] = overlays(body)
    cands, out["offsite_links"], out["doc_links"] = candidates(parse(body, ctype), final or start)
    out["candidates"] = len(cands)
    if not cands:
        out["page_status"] = "no_link"
        return out
    for url, rank in cands[:MAX_TRIES]:
        if deadline and time.time() > deadline:
            out["page_status"] = "deadline"
            return out
        out["tries"] += 1
        if not allowed(url):
            out["page_status"] = "robots"
            continue
        status, final, ctype, body = get(url)
        sleep(delay)
        if status != 200:
            out["page_status"] = "http_%d" % status
            continue
        if not is_html(ctype, body):
            out["page_status"] = "not_html"
            continue
        text = visible_text(parse(body, ctype))
        out.update(page_url=final or url, page_rank=rank, text_chars=len(text),
                   text_sha256=sha256(text.encode("utf-8")))
        if len(text) < MIN_TEXT:
            out["page_status"] = "short"
            continue
        out["page_status"] = "ok"
        out.update(classify(text))
        return out
    return out


def crawl(cohort, workers=24, deadline=None, **kw):
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(crawl_site, r, deadline=deadline, **kw) for r in cohort]
        for i, fut in enumerate(futures, 1):
            try:
                rows.append(fut.result())
            except Exception as e:  # one site's crash is recorded, never fatal
                r = {k: cohort[i - 1].get(k, "") for k in ("qid", "name", "kind", "state",
                                                           "population", "website")}
                r.update(home="crash", page_status=str(e)[:80])
                rows.append(r)
            if i % 100 == 0:
                print("%d/%d sites" % (i, len(futures)), flush=True)
    return rows


# ---------------------------------------------------------------- grading

def read_cohort(data):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
    return [r for r in reader if r.get("qid") and r.get("website")]


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def share(k, n):
    return [k, n, round(k / n, 4) if n else None, wilson(k, n)]


def big(r):
    try:
        return int(float(r["population"])) >= BIG
    except (KeyError, ValueError):
        return False


def grade(rows):
    pages = [r for r in rows if r.get("page_status") == "ok"]
    versioned = [r for r in pages if r["highest"]]
    by_high = {v: sum(1 for r in versioned if r["highest"] == v) for v in ("2.0", "2.1", "2.2")}
    dated = [r for r in pages if r["old_date"] or r["new_date"]]
    old_only = sum(1 for r in dated if r["old_date"] and not r["new_date"])
    groups = {g: [r for r in pages if big(r) == (g == "big")] for g in ("big", "small")}
    v_share = {g: share(sum(1 for r in rs if r["highest"]), len(rs)) for g, rs in groups.items()}
    measures = {"H1_only_2.0_of_versioned": share(by_high["2.0"], len(versioned)),
                "H2_highest_counts": by_high,
                "H3_versioned_of_pages": share(len(versioned), len(pages)),
                "H4_old_only_of_dated": share(old_only, len(dated)),
                "H5_versioned_big": v_share["big"], "H5_versioned_small": v_share["small"]}
    enough = len(versioned) >= MIN_VERSIONED
    sizes_ok = all(len(rs) >= MIN_SIZE_GROUP for rs in groups.values())
    preds = {"H1": by_high["2.0"] / len(versioned) >= H1_MIN_ONLY_20 if enough else None,
             "H2": (by_high["2.1"] > by_high["2.0"] and by_high["2.1"] > by_high["2.2"])
                   if enough else None,
             "H3": len(versioned) / len(pages) >= H3_MIN_VERSIONED if pages else None,
             "H4": old_only / len(dated) >= H4_MIN_OLD_ONLY if len(dated) >= MIN_DATED else None,
             "H5": (v_share["big"][2] - v_share["small"][2] >= H5_MIN_GAP) if sizes_ok else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    pages = [r for r in rows if r.get("page_status") == "ok"]

    def count(key, rs=None):
        return _tally(rows if rs is None else rs, key)
    out = {"home": count("home"), "page_status": count("page_status"),
           "page_rank": count("page_rank", pages),
           "versions": count("versions", pages),
           "wcag_any": sum(1 for r in pages if r["wcag_any"]),
           "section508": sum(1 for r in pages if r["section508"]),
           "title2": sum(1 for r in pages if r["title2"]),
           "old_date": sum(1 for r in pages if r["old_date"]),
           "new_date": sum(1 for r in pages if r["new_date"]),
           "both_dates": sum(1 for r in pages if r["old_date"] and r["new_date"]),
           "title2_only_2.0": sum(1 for r in pages if r["title2"] and r["highest"] == "2.0"),
           "overlay_on_home": count("overlay", [r for r in rows if r.get("home") == "ok"]),
           "no_same_site_link_but_offsite": sum(1 for r in rows if r.get("page_status") == "no_link"
                                                and r.get("offsite_links")),
           "by_kind": {}}
    for kind in sorted({r["kind"] for r in pages}):
        rs = [r for r in pages if r["kind"] == kind]
        out["by_kind"][kind] = {"pages": len(rs),
                                "versioned": sum(1 for r in rs if r["highest"]),
                                "only_2.0": sum(1 for r in rs if r["highest"] == "2.0")}
    return out


def _tally(rs, key):
    t = {}
    for r in rs:
        k = str(r.get(key, ""))
        t[k] = t.get(k, 0) + 1
    return dict(sorted(t.items(), key=lambda kv: (-kv[1], kv[0])))


def wait_for_prereg(local_script, fetch=fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md and this exact script, else (False, tries)."""
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            script = fetch(REPO_RAW + SCRIPT_PATH + "?n=%d" % i)
            if b"H1" in prereg and normalize(script) == normalize(local_script):
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


COLUMNS = ["qid", "name", "kind", "state", "population", "website", "home", "overlay",
           "candidates", "offsite_links", "doc_links", "tries", "page_status", "page_rank",
           "page_url", "text_chars", "text_sha256", "wcag_any", "versions", "highest",
           "section508", "title2", "old_date", "new_date", "version_snippet", "date_snippet"]


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r.get("qid", "")):
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def result_text(result):
    lines = ["a11y_pages %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("cohort", "homes_ok", "pages_ok"):
        if k in result:
            lines.append("%s: %s" % (k, result[k]))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        for k in ("home", "page_status", "page_rank", "versions", "overlay_on_home"):
            lines.append("%s: %s" % (k, d[k]))
        lines.append("wcag_any %d, section508 %d, title2 %d, old_date %d, new_date %d, both %d, "
                     "title2 with only 2.0 %d" % (d["wcag_any"], d["section508"], d["title2"],
                                                   d["old_date"], d["new_date"], d["both_dates"],
                                                   d["title2_only_2.0"]))
        lines.append("by kind: %s" % d["by_kind"])
    return "\n".join(lines)


def main(argv=None, fetch=fetch_bytes, get=http_get, sleep=time.sleep):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--max-minutes", type=float, default=90)
    args = ap.parse_args(argv)
    with open(os.path.abspath(__file__), "rb") as f:
        local = f.read()
    result = {"version": __version__, "script_sha256": sha256(local), "gates": {}}

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("a11y_pages: %s" % status)
        return 0 if status == "graded" else 2

    ok, polls = wait_for_prereg(local, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    result["polls"] = polls
    if not ok:
        return finish("pre-registration not public; nothing fetched")
    data = fetch(COHORT_URL)
    result["cohort_sha256"] = sha256(data)
    cohort = read_cohort(data)
    result["cohort"] = len(cohort)
    result["gates"]["A1_cohort"] = MIN_COHORT <= len(cohort) <= MAX_COHORT
    if not result["gates"]["A1_cohort"]:
        return finish("cohort gate failed; nothing crawled")
    result["crawl_started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes if args.max_minutes else None
    rows = crawl(cohort, workers=args.workers, deadline=deadline, get=get, delay=args.delay,
                 sleep=sleep)
    result["crawl_finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_rows(os.path.join(args.out_dir, "a11y-pages.csv"), rows)
    result["homes_ok"] = sum(1 for r in rows if r.get("home") == "ok")
    result["pages_ok"] = sum(1 for r in rows if r.get("page_status") == "ok")
    result["gates"]["A2_homes"] = result["homes_ok"] >= MIN_HOMES
    result["gates"]["A3_pages"] = result["pages_ok"] >= MIN_PAGES
    result["described"] = described(rows)
    if not all(result["gates"].values()):
        return finish("crawl gate failed; not graded")
    result["measures"], result["predictions"] = grade(rows)
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
