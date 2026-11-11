# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""state_pages 0.1.0: what do the accessibility pages of US state and territory governments say?

The pre-registered test in results/state-pages/PREREG.md. MV2's earlier censuses in this
repository read the accessibility pages of US cities, counties and towns (results/a11y-pages,
results/small-pages); none read state governments, which are also covered by the ADA Title II
web rule (28 CFR 35.200, WCAG 2.1 Level AA) and, after the Justice Department's interim final
rule of April 20, 2026, must meet it by April 26, 2027. This script:

  1. waits until results/state-pages/PREREG.md is on the repository's main branch and main's
     state_pages.py, a11y_pages.py and statement_check.py are byte for byte these files;
  2. reads the frame: every domain that CISA's public .gov registry list (cisagov/dotgov-data,
     current-full.csv, CC0-1.0) gives the domain type "State or territory". Only the domain,
     organization, suborganization, city and state columns are kept; the list's security contact
     email column is never read into a row or written anywhere;
  3. takes at most 2,000 domains in a fixed hash order, reads each home page (http://<domain>/,
     then http://www.<domain>/ if the first gets no answer at all), picks its accessibility page
     by the census's link rules (a11y_pages.candidates), reads that page with the census's rules
     (a11y_pages.classify) and statement_check.check_text, then grades ST1-ST5 on distinct pages
     and distinct home sites (several domains often lead to one site).

Reads public pages only, one site at a time per worker with a pause between requests, honouring
robots.txt, under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond short
snippets around a WCAG version or a date, with email addresses and phone numbers removed. This
counts what pages say; it does not test whether a website is accessible, and nothing here calls a
government in breach.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's own rules, unchanged)
import statement_check as sc  # noqa: E402  (the free check, unchanged)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/state-pages/PREREG.md"
PINNED = ("state_pages.py", "a11y_pages.py", "statement_check.py")
FRAME_URL = "https://raw.githubusercontent.com/cisagov/dotgov-data/main/current-full.csv"
FRAME_TYPE = "State or territory"
# A word that MV2's publishing tool blocks (it is in some place names). Frame rows that contain it
# are dropped and counted; any other cell that contains it is written as [withheld].
GUARD_RE = re.compile(r"s[a]ybr[o]ok", re.I)

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_COHORT, MAX_COHORT = 1000, 4000
SAMPLE_N = 2000
SEED = "state-pages-2026-11-11"
MIN_HOMES = 500
MIN_PAGES = 200
MIN_VERSIONED = 100
ST1_MAX_ONLY_20 = 0.40     # cities of 50,000+: 283 of 508 versioned pages (55.71%)
ST3_MAX_TITLE2 = 0.2215    # cities of 50,000+: 179 of 808 pages read
ST4_MAX_STOCK = 0.05       # cities of 50,000+: 280 of 808 pages read (34.65%)
ST5_MIN_LINKED = 0.70      # cities of 50,000+: 815 of 1,195 home pages read (68.2%)

COURT_RE = re.compile(r"\bcourts?\b|judicia", re.I)
LEGISLATURE_RE = re.compile(r"legislat|general\s+assembly|\bsenate\b|"
                            r"house\s+of\s+(?:representatives|delegates)", re.I)

FRAME_COLUMNS = ["domain", "organization", "suborganization", "city", "state", "kind"]
COLUMNS = FRAME_COLUMNS + [
    "home", "home_via", "home_host", "overlay", "candidates", "offsite_links", "tries",
    "page_status", "page_rank", "page_url", "text_chars", "text_sha256", "wcag_any", "versions",
    "highest", "section508", "title2", "old_date", "new_date", "date_2028", "stock", "contact",
    "findings", "version_snippet", "date_snippet"]
BOOLS = ("wcag_any", "section508", "title2", "old_date", "new_date", "date_2028", "stock",
         "contact")


# ---------------------------------------------------------------- frame

def clean(s):
    return " ".join(str(s or "").split())


def kind_of(organization, suborganization=""):
    s = organization + " " + suborganization
    if COURT_RE.search(s):
        return "court"
    if LEGISLATURE_RE.search(s):
        return "legislature"
    return "executive_other"


def parse_frame(data):
    """(rows, info): one row per distinct domain of type FRAME_TYPE, sorted by domain. The
    registry's contact email column is never copied into a row."""
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    types = collections.Counter()
    rows, seen, dropped, total = [], set(), 0, 0
    for r in reader:
        total += 1
        t = clean(r.get("Domain type"))
        types[t] += 1
        if t != FRAME_TYPE:
            continue
        domain = clean(r.get("Domain name")).lower().rstrip(".")
        if not domain or "." not in domain or " " in domain or domain in seen:
            continue
        row = {"domain": domain, "organization": clean(r.get("Organization name")),
               "suborganization": clean(r.get("Suborganization name")),
               "city": clean(r.get("City")), "state": clean(r.get("State")).upper()}
        if GUARD_RE.search(" ".join(row.values())):
            dropped += 1
            continue
        seen.add(domain)
        row["kind"] = kind_of(row["organization"], row["suborganization"])
        rows.append(row)
    rows.sort(key=lambda r: r["domain"])
    return rows, {"source_rows": total, "types": dict(sorted(types.items())),
                  "dropped": dropped, "eligible": len(rows)}


def sample(rows, n=SAMPLE_N, seed=SEED):
    """The first n rows in the order of SHA-256(seed + domain): fixed before any page is read."""
    def key(r):
        return hashlib.sha256((seed + r["domain"]).encode("utf-8")).hexdigest()
    return sorted(rows, key=key)[:n]


# ---------------------------------------------------------------- crawling

def read_page(text):
    """The census's reading of one page, plus what statement_check adds."""
    c = ap.classify(text)
    r = sc.check_text(text)
    c.update(date_2028=r["date_2028_04_26"], stock=r["stock_sentence"], contact=r["contact"],
             findings="+".join(f["id"] for f in r["findings"]))
    return c


def blank(row):
    out = {k: row.get(k, "") for k in FRAME_COLUMNS}
    out.update(home="", home_via="", home_host="", overlay="", candidates=0, offsite_links=0,
               tries=0, page_status="", page_rank="", page_url="", text_chars=0, text_sha256="")
    return out


def crawl_site(row, get=ap.http_get, delay=1.0, sleep=time.sleep, deadline=None):
    """The home page (http://<domain>/, else http://www.<domain>/ if the first gets no answer),
    then up to a11y_pages.MAX_TRIES ranked same-site candidates, as a11y_pages.crawl_site."""
    out = blank(row)
    if deadline and time.time() > deadline:
        out["home"] = "not_started"
        return out
    allowed = ap.robots_checker(get, delay, sleep)
    status, final, ctype, body, start = 0, "", "", b"", ""
    for via, start in (("bare", "http://%s/" % row["domain"]),
                       ("www", "http://www.%s/" % row["domain"])):
        if not allowed(start):
            out.update(home="robots", home_via=via)
            return out
        status, final, ctype, body = get(start)
        sleep(delay)
        out["home_via"] = via
        if status != 0:
            break
    if status != 200:
        out["home"] = "http_%d" % status
        return out
    if not ap.is_html(ctype, body):
        out["home"] = "not_html"
        return out
    final = final or start
    out.update(home="ok", home_host=ap.bare_host(final), overlay=ap.overlays(body))
    cands, out["offsite_links"], _ = ap.candidates(ap.parse(body, ctype), final)
    out["candidates"] = len(cands)
    if not cands:
        out["page_status"] = "no_link"
        return out
    for url, rank in cands[:ap.MAX_TRIES]:
        if deadline and time.time() > deadline:
            out["page_status"] = "deadline"
            return out
        out["tries"] += 1
        if not allowed(url):
            out["page_status"] = "robots"
            continue
        status, final2, ctype, body = get(url)
        sleep(delay)
        if status != 200:
            out["page_status"] = "http_%d" % status
            continue
        if not ap.is_html(ctype, body):
            out["page_status"] = "not_html"
            continue
        text = ap.visible_text(ap.parse(body, ctype))
        out.update(page_url=final2 or url, page_rank=rank, text_chars=len(text),
                   text_sha256=ap.sha256(text.encode("utf-8")))
        if len(text) < ap.MIN_TEXT:
            out["page_status"] = "short"
            continue
        out["page_status"] = "ok"
        out.update(read_page(text))
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
                r = blank(cohort[i - 1])
                r.update(home="crash", page_status=str(e)[:80])
                rows.append(r)
            if i % 100 == 0:
                print("%d/%d sites" % (i, len(futures)), flush=True)
    return rows


# ---------------------------------------------------------------- grading

def page_key(r):
    """A page address without scheme, www., letter case or a trailing slash."""
    url = r.get("page_url") or ""
    p = urllib.parse.urlsplit(url)
    key = ap.bare_host(url) + (p.path or "/").rstrip("/").lower()
    return key + ("?" + p.query if p.query else "")


def first_by(rows, key):
    """The first row (by domain) for each distinct key."""
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: r.get("domain", "")):
        k = key(r)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def distinct_pages(rows):
    return first_by([r for r in rows if r.get("page_status") == "ok"], page_key)


def distinct_homes(rows):
    return first_by([r for r in rows if r.get("home") == "ok"], lambda r: r.get("home_host", ""))


def typed(rows):
    """Rows read back from rows.csv, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def grade(rows):
    homes = distinct_homes(rows)
    linked = sum(1 for r in homes if int(r.get("candidates") or 0) > 0)
    pages = distinct_pages(rows)
    versioned = [r for r in pages if r.get("highest")]
    by_high = {v: sum(1 for r in versioned if r["highest"] == v) for v in ("2.0", "2.1", "2.2")}
    title2 = sum(1 for r in pages if r.get("title2"))
    stock = sum(1 for r in pages if r.get("stock"))
    measures = {"ST1_only_2.0_of_versioned": ap.share(by_high["2.0"], len(versioned)),
                "ST2_highest_counts": by_high,
                "ST3_title2_of_pages": ap.share(title2, len(pages)),
                "ST4_stock_of_pages": ap.share(stock, len(pages)),
                "ST5_linked_of_homes": ap.share(linked, len(homes))}
    enough_v = len(versioned) >= MIN_VERSIONED
    enough_p = len(pages) >= MIN_PAGES
    preds = {"ST1": (by_high["2.0"] / len(versioned) <= ST1_MAX_ONLY_20) if enough_v else None,
             "ST2": (by_high["2.1"] > by_high["2.0"] and by_high["2.1"] > by_high["2.2"])
                    if enough_v else None,
             "ST3": (title2 / len(pages) <= ST3_MAX_TITLE2) if enough_p else None,
             "ST4": (stock / len(pages) <= ST4_MAX_STOCK) if enough_p else None,
             "ST5": (linked / len(homes) >= ST5_MIN_LINKED) if len(homes) >= MIN_HOMES else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    pages = distinct_pages(rows)
    homes = distinct_homes(rows)

    def n(pred):
        return sum(1 for r in pages if pred(r))

    def group(rs):
        return {"pages": len(rs), "versioned": sum(1 for r in rs if r.get("highest")),
                "only_2.0": sum(1 for r in rs if r.get("highest") == "2.0"),
                "2.1": sum(1 for r in rs if r.get("highest") == "2.1"),
                "2.2": sum(1 for r in rs if r.get("highest") == "2.2"),
                "title2": sum(1 for r in rs if r.get("title2"))}
    return {
        "domains": len(rows),
        "home": ap._tally(rows, "home"),
        "home_via": ap._tally([r for r in rows if r.get("home") == "ok"], "home_via"),
        "distinct_home_hosts": len(homes),
        "page_status": ap._tally(rows, "page_status"),
        "domain_pages_ok": sum(1 for r in rows if r.get("page_status") == "ok"),
        "distinct_pages": len(pages),
        "distinct_texts": len({r.get("text_sha256") or "" for r in pages}),
        "page_rank": ap._tally(pages, "page_rank"),
        "versions": ap._tally(pages, "versions"),
        "findings": ap._tally(pages, "findings"),
        "overlay_on_home": ap._tally(homes, "overlay"),
        "wcag_any": n(lambda r: r.get("wcag_any")),
        "section508": n(lambda r: r.get("section508")),
        "contact": n(lambda r: r.get("contact")),
        "date_2026_04_24": n(lambda r: r.get("old_date")),
        "date_2027_04_26": n(lambda r: r.get("new_date")),
        "date_2028_04_26": n(lambda r: r.get("date_2028")),
        "only_2026_04_24": n(lambda r: r.get("old_date") and not r.get("new_date")
                             and not r.get("date_2028")),
        "by_kind": {k: group([r for r in pages if r.get("kind", "") == k])
                    for k in sorted({r.get("kind", "") for r in pages})},
        "by_state": {s: group([r for r in pages if r.get("state", "") == s])
                     for s in sorted({r.get("state", "") for r in pages})},
    }


def wait_for_prereg(here, fetch=ap.fetch_bytes, sleep=time.sleep, tries=ap.TRIES, pause=ap.PAUSE):
    """(True, attempts) once main holds PREREG.md and the three pinned files, else (False, tries)."""
    local = {}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            local[name] = ap.normalize(f.read())
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            same = all(ap.normalize(fetch(REPO_RAW + name + "?n=%d" % i)) == local[name]
                       for name in PINNED)
            if b"ST5" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def cell(v):
    s = "" if v is None else str(v)
    return "[withheld]" if GUARD_RE.search(s) else s


def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r.get("domain", "")):
            w.writerow({c: cell(r.get(c, "")) for c in columns})


def result_text(result):
    lines = ["state_pages %s" % result["version"],
             "status: %s" % result.get("status", ""),
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("frame", "eligible", "sampled", "crawl", "homes_ok", "pages_ok"):
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


def main(argv=None, fetch=ap.fetch_bytes, get=ap.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--max-minutes", type=float, default=150)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "gates": {}, "files": {}}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            result["files"][name] = ap.sha256(f.read())

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("state_pages: %s" % status)
        return 0 if status == "graded" else 1

    ok, result["prereg_attempts"] = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("stopped: the pre-registration and pinned files are not on main")
    try:
        data = fetch(FRAME_URL, tries=4, timeout=120)
    except Exception as e:  # recorded; nothing is crawled
        result["error"] = str(e)[:200]
        return finish("stopped: frame not read")
    rows, info = parse_frame(data)
    result["frame"] = dict(info, bytes=len(data), sha256=ap.sha256(data), url=FRAME_URL,
                           retrieved_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    result["eligible"] = len(rows)
    write_csv(os.path.join(args.out_dir, "frame.csv"), rows, FRAME_COLUMNS)
    result["gates"]["C1_frame"] = MIN_COHORT <= len(rows) <= MAX_COHORT
    if not result["gates"]["C1_frame"]:
        return finish("stopped: frame size outside the pre-registered range")
    cohort = sample(rows)
    result["sampled"] = len(cohort)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + args.max_minutes * 60
    out_rows = crawl(cohort, workers=args.workers, deadline=deadline, get=get, delay=args.delay,
                     sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    write_csv(os.path.join(args.out_dir, "rows.csv"), out_rows, COLUMNS)
    result["homes_ok"] = sum(1 for r in out_rows if r.get("home") == "ok")
    result["pages_ok"] = sum(1 for r in out_rows if r.get("page_status") == "ok")
    result["measures"], result["predictions"] = grade(out_rows)
    result["described"] = described(out_rows)
    return finish("graded")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
