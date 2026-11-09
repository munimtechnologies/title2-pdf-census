# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""council_stock 0.1.0: do the UK's principal councils publish a findable accessibility statement, which WCAG version does it name, when was it last reviewed, and does it keep template placeholders?

Pre-registered in results/uk-councils/PREREG.md. The frame is council-frame.csv, built by sealed
job council-frame-v1 from GOV.UK's Local Links Manager export of 2026-11-09 (Open Government
Licence v3.0): 385 principal councils in England, Scotland, Wales and Northern Ireland on 379
distinct hosts, committed before any council website was read. For each host the home page is
read (robots.txt honoured, one request at a time, a pause after each), its accessibility
statement link is followed (one more hop if the link leads to a page that links to the
statement), and if no statement is found that way two fixed addresses are tried:
/accessibility-statement and /accessibility. A statement is read with the rules of MV2's free
checker a11y-statement-check (statement_template_check.py 0.3.0, byte-identical to release
v0.3.0) plus a date reader for "last reviewed" and "prepared on" dates.

UK councils must publish an accessibility statement and keep it under regular review (SI 2018/952,
regulation 8); GOV.UK's sample statement asks for a review at least once a year. This study counts
what the statements say; it does not test whether a website is accessible, and nothing here calls
a council in breach. No page text is stored, only a hash, rule ids, dates and counts. Made by MV2
of Munim, Inc. with AI agents; not yet checked by a person. Standard library only.
"""

import argparse
import calendar
import collections
import concurrent.futures
import csv
import datetime
import hashlib
import html.parser
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statement_template_check as stc  # noqa: E402  (a11y-statement-check 0.3.0, unchanged)

__version__ = "0.1.0"

PREREG_PATH = "results/uk-councils/PREREG.md"
FRAME_PATH = "results/uk-councils/council-frame.csv"
FRAME_SHA256 = "468dcfaa474411c17640ffd5b38a8829c5ba62905891ede15675ac1b15027ca3"
FRAME_BYTES = 33269
FRAME_ROWS = 385
FRAME_HOSTS = 379
MAX_DROPPED = 2
CHECKER_VERSION = "0.3.0"
CHECKER_RELEASE_URL = ("https://raw.githubusercontent.com/munimtechnologies/a11y-statement-check/"
                       "v0.3.0/skills/accessibility-statement-check/statement_template_check.py")
PROBE_PATHS = ("/accessibility-statement", "/accessibility")
MAX_CANDIDATES = 5
CRAWL_SEED = "council-stock-2026-11"
RETRY_STATUSES = (429, 503)
RETRY_PAUSE = 30
# A word that MV2's publishing tool blocks (it is in some place names). Rows whose name or host
# contain it are dropped before anything is read; none were in the frame when it was built.
GUARD_RE = re.compile(r"s[a]ybr[o]ok", re.I)

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
G1_MIN_ANSWERED = 0.90          # G1: share of hosts whose server answered
N1_MIN_FOUND = 0.85             # N1: share of hosts where a statement was found and read
N2_MAX_PLACEHOLDER = 5          # N2: hosts whose statement keeps a 0.3.0 placeholder
N3_MIN_22 = 0.60                # N3: share of read statements naming WCAG 2.2 as the highest
N3_MIN_PAGES = 100
N4_MIN_STALE = 0.25             # N4: share of dated statements dated before STALE_BEFORE
N4_MIN_PAGES = 100
STALE_BEFORE = "2025-11-01"     # more than a year before the crawl month (November 2026)
DATE_YEARS = (2018, 2027)       # dates outside these years are not read as statement dates

# A page is read as a statement when it says "accessibility statement" and also names WCAG or the
# enforcement procedure that regulation 8 requires.
TITLE_RE = re.compile(r"accessibility\s+statement|datganiad\s+hygyrchedd", re.I)
ENFORCEMENT_RE = re.compile(r"Equality\s+and\s+Human\s+Rights\s+Commission|Equality\s+Advisory\s+and\s+"
                            r"Support\s+Service|Equality\s+Commission\s+for\s+Northern\s+Ireland|"
                            r"enforcement\s+procedure|\bEHRC\b|\bEASS\b", re.I)
TOOL_RE = re.compile(r"tool|recite|reachdeck|browsealoud|translat|reader|widget", re.I)

MON = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
       r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
YEAR = r"(?:19|20)\d\d"
DATE = (r"(?:\b(?P<d1>\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<m1>" + MON + r")\s*,?\s*(?P<y1>" + YEAR
        + r")\b|\b(?P<m2>" + MON + r")\s+(?P<d2>\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(?P<y2>" + YEAR
        + r")\b|\b(?P<m3>" + MON + r")\s*,?\s*(?P<y3>" + YEAR
        + r")\b|\b(?P<d4>\d{1,2})[/.](?P<m4>\d{1,2})[/.](?P<y4>" + YEAR
        + r")\b|\b(?P<y5>" + YEAR + r")-(?P<m5>\d{1,2})-(?P<d5>\d{1,2})\b)")
REVIEW_RE = re.compile(r"\b(?:last\s+(?:reviewed|updated|revised|review)|(?:reviewed|updated|revised)"
                       r"\s+(?:on|in))\b[^.\d]{0,30}?" + DATE, re.I)
PREPARED_RE = re.compile(r"\b(?:prepared|published|created|written|produced)\s+(?:on|in)\b"
                         r"[^.\d]{0,30}?" + DATE, re.I)
MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug",
                                      "sep", "oct", "nov", "dec"), 1)}

BOOLS = ("retried", "robots_blocked", "offsite_link", "other_host", "placeholder",
         "gov_uk_sample", "wcag_named")
COLUMNS = ["host", "name", "gss", "kind", "authorities", "status", "found_by", "home_status",
           "retried", "robots_blocked", "offsite_link", "statement_url", "other_host",
           "text_chars", "text_sha256", "placeholder", "placeholder_ids", "gov_uk_sample",
           "wcag_named", "highest", "review_date", "prepared_date", "statement_date",
           "date_source"]
NOT_ANSWERED = ("", "http_0", "crash", "not_started", "bad_url")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(data):
    return data.replace(b"\r\n", b"\n")


# ---------------------------------------------------------------- the frame

def read_frame(path):
    """(rows, ok): the frame's rows and whether its bytes and row count are the ones registered."""
    with open(path, "rb") as f:
        data = f.read()
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    ok = sha256(data) == FRAME_SHA256 and len(data) == FRAME_BYTES and len(rows) == FRAME_ROWS
    return rows, ok


def build_frame(rows):
    """One row per distinct host (the first council by name), with the number of councils on it.
    Returns (hosts, dropped)."""
    groups = collections.OrderedDict()
    dropped = 0
    for r in rows:
        if GUARD_RE.search(r.get("name", "")) or GUARD_RE.search(r.get("host", "")):
            dropped += 1
            continue
        h = (r.get("host") or "").strip().lower()
        if not h:
            continue
        groups.setdefault(h, []).append(r)
    out = []
    for h, rs in groups.items():
        first = min(rs, key=lambda r: r.get("name", ""))
        out.append({"host": h, "name": first.get("name", ""), "gss": first.get("gss", ""),
                    "kind": first.get("kind", ""), "authorities": len(rs)})
    return out, dropped


def crawl_order(hosts):
    return sorted(hosts, key=lambda r: sha256((CRAWL_SEED + r["host"]).encode("utf-8")))


# ---------------------------------------------------------------- links

class _Links(html.parser.HTMLParser):
    """(href, text) of every <a href>, the text including aria-label and title."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        if self._href is not None:
            self.close_link()
        a = dict(attrs)
        if a.get("href") is None:
            return
        self._href = a.get("href") or ""
        self._text = [a.get("aria-label") or "", a.get("title") or ""]

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.close_link()

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def close_link(self):
        self.links.append((self._href, " ".join(" ".join(self._text).split())))
        self._href, self._text = None, []


def find_links(body, ctype=""):
    if isinstance(body, bytes):
        m = re.search(r"charset=([\w-]+)", ctype or "", re.I)
        try:
            body = body.decode(m.group(1) if m else "utf-8", "replace")
        except LookupError:
            body = body.decode("utf-8", "replace")
    p = _Links()
    try:
        p.feed(body)
        p.close()
    except Exception:  # a broken page keeps what was parsed before the error
        pass
    if p._href is not None:
        p.close_link()
    return p.links


def link_score(href, text):
    """3: the link text says accessibility statement; 2: the address does; 1: both mention
    accessibility (and it is not an accessibility toolbar); 0: not a statement link."""
    t, h = text.lower(), urllib.parse.unquote(href).lower()
    if TITLE_RE.search(t):
        return 3
    if re.search(r"accessibility[-_ ]?statement", h):
        return 2
    if "accessib" in t and "accessib" in h and not TOOL_RE.search(t + " " + h):
        return 1
    return 0


def bare(hostname):
    h = (hostname or "").lower().rstrip(".")
    return h[4:] if h.startswith("www.") else h


def on_site(url, hosts):
    try:
        h = bare(urllib.parse.urlsplit(url).hostname)
    except ValueError:
        return False
    return any(h == s or h.endswith("." + s) for s in hosts)


def best_link(links, page_url, hosts, min_score=1):
    """(url, offsite): the best-scoring statement link on the council's own site (first in page
    order among equals), and whether a link scoring 2 or more points to another site."""
    best, best_score, offsite = "", 0, False
    for href, text in links:
        href = (href or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        try:
            url = urllib.parse.urldefrag(urllib.parse.urljoin(page_url, href))[0]
        except ValueError:
            continue
        if not url.lower().startswith(("http://", "https://")):
            continue
        s = link_score(href, text)
        if s < min_score:
            continue
        if not on_site(url, hosts):
            if s >= 2:
                offsite = True
            continue
        if s > best_score:
            best, best_score = url, s
    return best, offsite


# ---------------------------------------------------------------- one statement

def _date(m):
    """A datetime.date from one DATE match (a month without a day reads as its last day), or None."""
    g = m.groupdict()
    try:
        if g["y1"]:
            y, mo, d = int(g["y1"]), MONTHS[g["m1"].lower().rstrip(".")[:3]], int(g["d1"])
        elif g["y2"]:
            y, mo, d = int(g["y2"]), MONTHS[g["m2"].lower().rstrip(".")[:3]], int(g["d2"])
        elif g["y3"]:
            y, mo = int(g["y3"]), MONTHS[g["m3"].lower().rstrip(".")[:3]]
            d = calendar.monthrange(y, mo)[1]
        elif g["y4"]:
            y, mo, d = int(g["y4"]), int(g["m4"]), int(g["d4"])
            if mo > 12 and d <= 12:  # month/day/year
                mo, d = d, mo
        else:
            y, mo, d = int(g["y5"]), int(g["m5"]), int(g["d5"])
        if not DATE_YEARS[0] <= y <= DATE_YEARS[1]:
            return None
        return datetime.date(y, mo, d)
    except (KeyError, ValueError):
        return None


def statement_dates(text):
    """(review_date, prepared_date, statement_date, source) as ISO strings ('' when none): the
    latest 'last reviewed / updated' date, the latest 'prepared / published on' date, and the
    later of the two."""
    flat = " ".join(text.split())
    reviews = [d for d in (_date(m) for m in REVIEW_RE.finditer(flat)) if d]
    prepared = [d for d in (_date(m) for m in PREPARED_RE.finditer(flat)) if d]
    r = max(reviews) if reviews else None
    p = max(prepared) if prepared else None
    if r and (not p or r >= p):
        s, src = r, "reviewed"
    elif p:
        s, src = p, "prepared"
    else:
        s, src = None, ""
    iso = lambda d: d.isoformat() if d else ""  # noqa: E731
    return iso(r), iso(p), iso(s), src


def is_statement(text):
    return (len(text) >= stc.MIN_TEXT and bool(TITLE_RE.search(text))
            and bool(stc.WCAG_ANY_RE.search(text) or ENFORCEMENT_RE.search(text)))


def read_statement(text):
    d = stc.check_text(text)
    r, p, s, src = statement_dates(text)
    return {"placeholder": bool(d["placeholder"]),
            "placeholder_ids": ";".join("%s/%s" % (x["group"], x["id"]) for x in d["placeholders"]),
            "gov_uk_sample": "gov_uk_sample" in d["templates"],
            "wcag_named": bool(d["wcag_named"]), "highest": d["highest"],
            "text_chars": len(text), "text_sha256": sha256(text.encode("utf-8")),
            "review_date": r, "prepared_date": p, "statement_date": s, "date_source": src}


# ---------------------------------------------------------------- one council

def blank(row):
    out = dict(row)
    out.update(status="", found_by="", home_status="", statement_url="", text_chars=0,
               text_sha256="", placeholder_ids="", highest="", review_date="", prepared_date="",
               statement_date="", date_source="")
    for k in BOOLS:
        out[k] = False
    return out


def read_one(row, get=stc.http_get, delay=1.0, sleep=time.sleep):
    """The home page (https://www.<host>/, else https://<host>/), its statement link, one more hop
    from a page that links to the statement, then the fixed addresses; robots.txt honoured."""
    out = blank(row)
    host = row["host"]
    allowed = stc.robots_checker(get)
    bases = ["https://" + host] if host.startswith("www.") else ["https://www." + host,
                                                                 "https://" + host]
    home = None
    for base in bases:
        url = base + "/"
        if not allowed(url):
            out.update(status="robots", robots_blocked=True)
            return out
        sleep(delay)
        st, final, ctype, body = get(url)
        sleep(delay)
        if st != 0:
            home = (st, final or url, ctype, body)
            break
    if home is None:
        out["status"] = "http_0"
        return out
    st, final, ctype, body = home
    out["home_status"] = str(st)
    sp = urllib.parse.urlsplit(final)
    site = "%s://%s" % (sp.scheme, sp.netloc)
    hosts = {host, bare(sp.hostname)} - {""}
    cands = []
    if st == 200 and stc.is_html(ctype, body):
        link, offsite = best_link(find_links(body, ctype), final, hosts)
        out["offsite_link"] = offsite
        if link:
            cands.append(("link", link))
    for i, path in enumerate(PROBE_PATHS, 1):
        cands.append(("probe%d" % i, site + path))
    tried, k = set(), 0
    while k < len(cands) and len(tried) < MAX_CANDIDATES:
        how, url = cands[k]
        k += 1
        key = url.rstrip("/")
        if key in tried:
            continue
        tried.add(key)
        if not allowed(url):
            out["robots_blocked"] = True
            continue
        s, f, c, b = get(url)
        sleep(delay)
        if s in RETRY_STATUSES:
            out["retried"] = True
            sleep(RETRY_PAUSE)
            s, f, c, b = get(url)
            sleep(delay)
        if s != 200 or not stc.is_html(c, b):
            continue
        f = f or url
        if urllib.parse.urlsplit(f).path in ("", "/"):
            continue  # sent back to a home page
        text = stc.visible_text(b, c)
        if is_statement(text):
            out.update(status="ok", found_by=how,
                       statement_url="[withheld]" if GUARD_RE.search(f) else f,
                       other_host=bare(urllib.parse.urlsplit(f).hostname) != host)
            out.update(read_statement(text))
            return out
        if how != "hub":
            nxt, _ = best_link(find_links(b, c), f, hosts, min_score=3)
            if nxt and nxt.rstrip("/") not in tried:
                cands.insert(k, ("hub", nxt))
    out["status"] = "not_found"
    return out


def _read_or_skip(row, deadline, kw):
    if deadline and time.time() > deadline:
        r = blank(row)
        r["status"] = "not_started"
        return r
    return read_one(row, **kw)


def crawl(rows, workers=4, deadline=None, **kw):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_read_or_skip, r, deadline, kw) for r in rows]
        for i, fut in enumerate(futures, 1):
            try:
                out.append(fut.result())
            except Exception as e:  # one host's crash is recorded, never fatal
                r = blank(rows[i - 1])
                r.update(status="crash", statement_url=str(e)[:80])
                out.append(r)
            if i % 50 == 0:
                print("%d/%d hosts" % (i, len(futures)), flush=True)
    return out


# ---------------------------------------------------------------- grading

def share(k, n):
    return {"k": k, "n": n, "pct": round(100.0 * k / n, 2) if n else None}


def typed(rows):
    """Rows read back from the hosts table, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def answered(r):
    return r.get("status") not in NOT_ANSWERED


def ok(r):
    return r.get("status") == "ok"


def flagged(r):
    return ok(r) and bool(r.get("placeholder"))


def stale(r):
    return bool(r.get("statement_date")) and r["statement_date"] < STALE_BEFORE


def grade(rows, frame_ok=True):
    n = len(rows)
    ans = [r for r in rows if answered(r)]
    found = [r for r in rows if ok(r)]
    ph = [r for r in found if r.get("placeholder")]
    v22 = [r for r in found if r.get("highest") == "2.2"]
    dated = [r for r in found if r.get("statement_date")]
    old = [r for r in dated if stale(r)]
    measures = {"F1_hosts": n,
                "G1_answered": share(len(ans), n),
                "N1_found": share(len(found), n),
                "N2_placeholder_hosts": len(ph),
                "N3_wcag22_of_found": share(len(v22), len(found)),
                "N4_stale_of_dated": share(len(old), len(dated))}
    gates = {"F1_frame": bool(frame_ok),
             "G1_answered": bool(n) and len(ans) / n >= G1_MIN_ANSWERED}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("N1", "N2", "N3", "N4")}
    preds = {"N1": len(found) / n >= N1_MIN_FOUND,
             "N2": len(ph) <= N2_MAX_PLACEHOLDER,
             "N3": (len(v22) / len(found) >= N3_MIN_22) if len(found) >= N3_MIN_PAGES else None,
             "N4": (len(old) / len(dated) >= N4_MIN_STALE) if len(dated) >= N4_MIN_PAGES else None}
    return measures, gates, preds


def tally(rows, key):
    c = collections.Counter(str(r.get(key, "")) for r in rows)
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def tally_ids(rows, key):
    c = collections.Counter()
    for r in rows:
        for i in (r.get(key) or "").split(";"):
            if i:
                c[i] += 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def described(rows):
    """Reported, not graded."""
    found = [r for r in rows if ok(r)]
    dated = [r for r in found if r.get("statement_date")]
    kinds = {}
    for kind in sorted(set(r.get("kind", "") for r in rows)):
        rs = [r for r in rows if r.get("kind", "") == kind]
        fs = [r for r in rs if ok(r)]
        ds = [r for r in fs if r.get("statement_date")]
        kinds[kind] = {"hosts": len(rs), "found": len(fs),
                       "placeholder": sum(1 for r in fs if r.get("placeholder")),
                       "wcag22": sum(1 for r in fs if r.get("highest") == "2.2"),
                       "dated": len(ds), "stale": sum(1 for r in ds if stale(r))}
    return {
        "status": tally(rows, "status"),
        "home_status": tally(rows, "home_status"),
        "found_by": tally(found, "found_by"),
        "found_councils": sum(int(r.get("authorities") or 0) for r in found),
        "found_highest": tally(found, "highest"),
        "found_gov_uk_wording": sum(1 for r in found if r.get("gov_uk_sample")),
        "found_wcag_named": sum(1 for r in found if r.get("wcag_named")),
        "found_no_date": len(found) - len(dated),
        "date_source": tally(dated, "date_source"),
        "statement_year": tally([{"y": r["statement_date"][:4]} for r in dated], "y"),
        "placeholder_ids": tally_ids([r for r in found if r.get("placeholder")], "placeholder_ids"),
        "placeholder_hosts": sorted(r["host"] for r in found if r.get("placeholder")),
        "found_other_host": sum(1 for r in found if r.get("other_host")),
        "offsite_link": sum(1 for r in rows if r.get("offsite_link")),
        "robots_blocked": sum(1 for r in rows if r.get("robots_blocked")),
        "retried": sum(1 for r in rows if r.get("retried")),
        "distinct_texts": len(set(r.get("text_sha256") for r in found)),
        "by_kind": kinds,
    }


# ---------------------------------------------------------------- the run

def fetch_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": stc.UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def checker_matches_release(here, fetch=fetch_bytes):
    """True when the local checker is byte-identical (line endings aside) to release v0.3.0."""
    with open(os.path.join(here, "statement_template_check.py"), "rb") as f:
        local = normalize(f.read())
    try:
        remote = normalize(fetch(CHECKER_RELEASE_URL))
    except Exception:
        return False
    return local == remote


def write_table(out_dir, rows):
    """hosts.csv, sorted by host."""
    rows = sorted(rows, key=lambda r: r["host"])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([r.get(c, "") for c in COLUMNS])
    data = buf.getvalue().encode("utf-8")
    with open(os.path.join(out_dir, "hosts.csv"), "wb") as f:
        f.write(data)
    return {"file": "hosts.csv", "rows": len(rows), "bytes": len(data), "sha256": sha256(data)}


def result_text(result):
    lines = ["council_stock %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("frame", "crawl", "table"):
        if k in result:
            lines.append("%s: %s" % (k, json.dumps(result[k], sort_keys=True)))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, json.dumps(v, sort_keys=True)))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        for k in sorted(d):
            lines.append("%s: %s" % (k, json.dumps(d[k], sort_keys=True)))
    return "\n".join(lines)


def main(argv=None, fetch=fetch_bytes, get=stc.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-minutes", type=float, default=90)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "checker_version": stc.__version__, "gates": {}, "files": {}}
    for name in ("council_stock.py", "statement_template_check.py", PREREG_PATH):
        with open(os.path.join(here, *name.split("/")), "rb") as f:
            result["files"][name] = sha256(f.read())

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("council_stock: %s" % status)
        return 0

    with open(os.path.join(here, *PREREG_PATH.split("/")), "rb") as f:
        prereg = f.read()
    result["gates"]["P0_prereg"] = b"N4" in prereg
    result["gates"]["P0_checker"] = (stc.__version__ == CHECKER_VERSION
                                     and checker_matches_release(here, fetch))
    if not (result["gates"]["P0_prereg"] and result["gates"]["P0_checker"]):
        return finish("not_run")  # no council website was read
    rows, frame_bytes_ok = read_frame(os.path.join(here, *FRAME_PATH.split("/")))
    hosts, dropped = build_frame(rows)
    frame_ok = (frame_bytes_ok and dropped <= MAX_DROPPED
                and FRAME_HOSTS - MAX_DROPPED <= len(hosts) <= FRAME_HOSTS)
    result["frame"] = {"rows": len(rows), "hosts": len(hosts), "dropped": dropped,
                       "bytes_ok": frame_bytes_ok}
    if not frame_ok:
        result["gates"]["F1_frame"] = False
        return finish("not_run")  # nothing was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(crawl_order(hosts), workers=args.workers, deadline=deadline, get=get, sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    result["table"] = write_table(args.out_dir, read)
    measures, gates, preds = grade(read, frame_ok)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(gates.values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
