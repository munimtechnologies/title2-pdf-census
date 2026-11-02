"""small_pages: what do the accessibility pages of smaller US local governments say?

The pre-registered test in results/small-pages/PREREG.md. The 2026 census in results/a11y-pages
read the accessibility pages of US cities and counties of 50,000 or more. Governments of under
50,000 people had April 26, 2027 as their Title II date until the Justice Department's interim
final rule of April 20, 2026 moved it to April 26, 2028. This script, for US cities, counties,
consolidated city-counties and towns of 10,000 to 49,999 people with an official website on
Wikidata:

  1. waits until results/small-pages/PREREG.md is on the repository's main branch and main's
     small_pages.py, a11y_pages.py and statement_check.py are byte for byte these files (gives
     up after about an hour);
  2. reads the cohort from Wikidata (the query below), leaves out every government and website
     in the 50,000+ cohort (results/v0.2.2/cohort.csv at commit 279e85e), and takes a fixed
     sample of at most 2,500 in a pre-registered hash order;
  3. reads each home page, picks its accessibility page by the census's link rules
     (a11y_pages.candidates), reads that page with the census's rules (a11y_pages.classify) and
     with statement_check.check_text(small=True), then grades S1-S5.

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
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's own rules)
import statement_check as sc  # noqa: E402  (the free check, run with --small)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/small-pages/PREREG.md"
PINNED = ("small_pages.py", "a11y_pages.py", "statement_check.py")
BIG_COHORT_URL = ap.COHORT_URL
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_POP, MAX_POP = 10000, 50000
MIN_COHORT, MAX_COHORT = 1500, 9000
SAMPLE_N = 2500
SEED = "small-pages-2026-11-02"
MIN_HOMES = 1000
MIN_PAGES = 400
MIN_VERSIONED = 200
MIN_DATED = 15
S1_MIN_ONLY_20 = 0.5571   # the 50,000+ census: 283 of 508 versioned pages
S2_MIN_STOCK = 0.3465     # the 50,000+ census: 280 of 808 pages read
S3_MAX_TITLE2 = 0.2215    # the 50,000+ census: 179 of 808 pages read
S4_MAX_LINKED = 0.682     # the 50,000+ census: 815 of 1,195 home pages read
S5_MIN_SMALL_2027 = 0.40

# The census's query (census.py 0.2.3) with the population band changed: statements of
# 10,000 or more are kept, and an item whose largest kept population is 50,000 or more is
# dropped, so every item's largest population is 10,000 to 49,999.
COHORT_QUERY = """
SELECT ?item ?itemLabel ?typeLabel ?stateLabel (MAX(?pop) AS ?population) (SAMPLE(?site) AS ?website) WHERE {
  VALUES ?type { wd:Q1093829 wd:Q47168 wd:Q3301053 wd:Q15127012 }
  ?item wdt:P31/wdt:P279? ?type ;
        wdt:P17 wd:Q30 ;
        wdt:P1082 ?pop ;
        wdt:P856 ?site .
  FILTER(?pop >= 10000)
  OPTIONAL { ?item wdt:P131/wdt:P131? ?state . ?state wdt:P31 wd:Q35657 . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?item ?itemLabel ?typeLabel ?stateLabel
HAVING (MAX(?pop) < 50000)
"""

COHORT_COLUMNS = ["qid", "name", "kind", "state", "population", "website"]
COLUMNS = ["qid", "name", "kind", "state", "population", "website", "home", "overlay",
           "candidates", "tries", "page_status", "page_rank", "page_url", "text_chars",
           "text_sha256", "wcag_any", "versions", "highest", "section508", "title2", "old_date",
           "new_date", "date_2028", "stock", "contact", "findings", "version_snippet",
           "date_snippet"]


# ---------------------------------------------------------------- cohort

def cohort_queries():
    """The query with states, then (if Wikidata times out) the same query without them."""
    simple = "\n".join(line for line in COHORT_QUERY.splitlines() if "OPTIONAL" not in line)
    return [COHORT_QUERY, simple.replace(" ?stateLabel", "")]


def fetch_cohort(fetch=ap.fetch_bytes, sleep=time.sleep):
    err = None
    for query in cohort_queries():
        url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
        try:
            return json.loads(fetch(url, tries=2, timeout=180).decode("utf-8"))
        except Exception as e:  # a timeout or a bad answer: try the simpler query
            err = e
            sleep(10)
    raise RuntimeError("Wikidata query failed: %s" % str(err)[:150])


def big_cohort(data):
    """(qids, website hosts) of the 50,000+ cohort, to leave out."""
    rows = ap.read_cohort(data)
    return ({r["qid"] for r in rows},
            {ap.bare_host(ap.normalize_site(r["website"])) for r in rows})


def parse_cohort(data, exclude_qids=(), exclude_hosts=()):
    """Rows from the SPARQL JSON, one per website host (largest population kept), as census.py
    0.2.3 makes them, leaving out the 50,000+ cohort's governments and websites."""
    best = {}
    for b in data["results"]["bindings"]:
        def val(k):
            return b.get(k, {}).get("value", "")
        try:
            population = int(float(val("population")))
        except ValueError:
            continue
        if not MIN_POP <= population < MAX_POP:
            continue
        website = val("website")
        host = ap.bare_host(ap.normalize_site(website)) if website else ""
        qid = val("item").rsplit("/", 1)[-1]
        if not host or qid in exclude_qids or host in exclude_hosts:
            continue
        type_label = val("typeLabel").lower()
        kind = ("city-county" if "consolidated" in type_label else
                "county" if "county" in type_label else
                "town" if "town" in type_label else "city")
        row = {"qid": qid, "name": val("itemLabel"), "kind": kind, "state": val("stateLabel"),
               "population": population, "website": website}
        if host not in best or population > best[host]["population"]:
            best[host] = row
    return sorted(best.values(), key=lambda r: (-r["population"], r["qid"]))


def sample(rows, n=SAMPLE_N, seed=SEED):
    """The first n rows in the order of SHA-256(seed + qid): fixed before any page is read."""
    def key(r):
        return hashlib.sha256((seed + r["qid"]).encode("utf-8")).hexdigest()
    return sorted(rows, key=key)[:n]


# ---------------------------------------------------------------- crawling

def read_page(text):
    """The census's reading of one page, plus what statement_check --small adds."""
    c = ap.classify(text)
    r = sc.check_text(text, small=True)
    c.update(stock=r["stock_sentence"], date_2028=r["date_2028_04_26"], contact=r["contact"],
             findings="+".join(f["id"] for f in r["findings"]))
    return c


def crawl_site(row, get=ap.http_get, delay=1.0, sleep=time.sleep, deadline=None):
    """As a11y_pages.crawl_site (same requests, same order), read with read_page."""
    out = {k: row.get(k, "") for k in COHORT_COLUMNS}
    out.update(home="", overlay="", candidates=0, tries=0, page_status="", page_rank="",
               page_url="", text_chars=0, text_sha256="")
    if deadline and time.time() > deadline:
        out["home"] = "not_started"
        return out
    start = ap.normalize_site(row["website"])
    allowed = ap.robots_checker(get, delay, sleep)
    if not allowed(start):
        out["home"] = "robots"
        return out
    status, final, ctype, body = get(start)
    sleep(delay)
    if status != 200:
        out["home"] = "http_%d" % status
        return out
    if not ap.is_html(ctype, body):
        out["home"] = "not_html"
        return out
    out["home"] = "ok"
    out["overlay"] = ap.overlays(body)
    cands, _, _ = ap.candidates(ap.parse(body, ctype), final or start)
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
                r = {k: cohort[i - 1].get(k, "") for k in COHORT_COLUMNS}
                r.update(home="crash", page_status=str(e)[:80])
                rows.append(r)
            if i % 100 == 0:
                print("%d/%d sites" % (i, len(futures)), flush=True)
    return rows


# ---------------------------------------------------------------- grading

def grade(rows):
    homes = [r for r in rows if r.get("home") == "ok"]
    linked = sum(1 for r in homes if int(r.get("candidates") or 0) > 0)
    pages = [r for r in rows if r.get("page_status") == "ok"]
    versioned = [r for r in pages if r["highest"]]
    only20 = sum(1 for r in versioned if r["highest"] == "2.0")
    stock = sum(1 for r in pages if r["stock"])
    title2 = sum(1 for r in pages if r["title2"])
    dated = [r for r in pages if r["old_date"] or r["new_date"] or r["date_2028"]]
    small2027 = sum(1 for r in dated if r["new_date"] and not r["date_2028"])
    measures = {"S1_only_2.0_of_versioned": ap.share(only20, len(versioned)),
                "S2_stock_of_pages": ap.share(stock, len(pages)),
                "S3_title2_of_pages": ap.share(title2, len(pages)),
                "S4_linked_of_homes": ap.share(linked, len(homes)),
                "S5_2027_without_2028_of_dated": ap.share(small2027, len(dated))}
    preds = {"S1": (only20 / len(versioned) >= S1_MIN_ONLY_20)
                   if len(versioned) >= MIN_VERSIONED else None,
             "S2": (stock / len(pages) >= S2_MIN_STOCK) if len(pages) >= MIN_PAGES else None,
             "S3": (title2 / len(pages) <= S3_MAX_TITLE2) if len(pages) >= MIN_PAGES else None,
             "S4": (linked / len(homes) < S4_MAX_LINKED) if len(homes) >= MIN_HOMES else None,
             "S5": (small2027 / len(dated) >= S5_MIN_SMALL_2027)
                   if len(dated) >= MIN_DATED else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    pages = [r for r in rows if r.get("page_status") == "ok"]

    def n(pred):
        return sum(1 for r in pages if pred(r))
    out = {"home": ap._tally(rows, "home"), "page_status": ap._tally(rows, "page_status"),
           "page_rank": ap._tally(pages, "page_rank"), "versions": ap._tally(pages, "versions"),
           "findings": ap._tally(pages, "findings"),
           "overlay_on_home": ap._tally([r for r in rows if r.get("home") == "ok"], "overlay"),
           "wcag_any": n(lambda r: r.get("wcag_any")),
           "section508": n(lambda r: r.get("section508")),
           "contact": n(lambda r: r.get("contact")),
           "date_2026_04_24": n(lambda r: r.get("old_date")),
           "date_2027_04_26": n(lambda r: r.get("new_date")),
           "date_2028_04_26": n(lambda r: r.get("date_2028")),
           "only_2026_04_24": n(lambda r: r.get("old_date") and not r.get("new_date")
                                and not r.get("date_2028")),
           "by_kind": {}}
    for kind in sorted({r.get("kind", "") for r in pages}):
        rs = [r for r in pages if r.get("kind", "") == kind]
        out["by_kind"][kind] = {"pages": len(rs),
                                "versioned": sum(1 for r in rs if r.get("highest")),
                                "only_2.0": sum(1 for r in rs if r.get("highest") == "2.0"),
                                "stock": sum(1 for r in rs if r.get("stock"))}
    return out


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
            if b"S5" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r.get("qid", "")):
            w.writerow({c: r.get(c, "") for c in columns})


def result_text(result):
    lines = ["small_pages %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("eligible", "sampled", "homes_ok", "pages_ok"):
        if k in result:
            lines.append("%s: %s" % (k, result[k]))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        for k in sorted(d):
            lines.append("%s: %s" % (k, d[k]))
    return "\n".join(lines)


def main(argv=None, fetch=ap.fetch_bytes, get=ap.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--max-minutes", type=float, default=120)
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
            json.dump(result, f, indent=1)
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("small_pages: %s" % status)
        return 0 if status == "graded" else 1

    ok, result["prereg_attempts"] = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("stopped: the pre-registration and pinned files are not on main")
    try:
        big_qids, big_hosts = big_cohort(fetch(BIG_COHORT_URL))
        data = fetch_cohort(fetch=fetch, sleep=sleep)
    except Exception as e:  # recorded; nothing is graded
        result["error"] = str(e)[:200]
        return finish("stopped: cohort not read")
    eligible = parse_cohort(data, big_qids, big_hosts)
    result["big_cohort_rows"] = len(big_qids)
    result["eligible"] = len(eligible)
    write_csv(os.path.join(args.out_dir, "eligible.csv"), eligible, COHORT_COLUMNS)
    result["gates"]["C1_cohort"] = MIN_COHORT <= len(eligible) <= MAX_COHORT
    if not result["gates"]["C1_cohort"]:
        return finish("stopped: cohort size outside the pre-registered range")
    cohort = sample(eligible)
    result["sampled"] = len(cohort)
    write_csv(os.path.join(args.out_dir, "cohort.csv"), cohort, COHORT_COLUMNS)
    deadline = time.time() + args.max_minutes * 60
    rows = crawl(cohort, workers=args.workers, deadline=deadline, get=get, delay=args.delay,
                 sleep=sleep)
    write_csv(os.path.join(args.out_dir, "rows.csv"), rows, COLUMNS)
    result["homes_ok"] = sum(1 for r in rows if r.get("home") == "ok")
    result["pages_ok"] = sum(1 for r in rows if r.get("page_status") == "ok")
    result["measures"], result["predictions"] = grade(rows)
    result["described"] = described(rows)
    return finish("graded")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
