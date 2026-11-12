# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""transit_pages 0.1.0: what do US public transit authorities' accessibility pages say?

The pre-registered test in results/transit-pages/PREREG.md. A public transit authority is a public
entity under the ADA, so two different rules meet on its website: the Transportation Department's
rules for accessible transit service (49 CFR part 37: paratransit, accessible formats) and the
Justice Department's Title II web rule (28 CFR 35.200, WCAG 2.1 Level AA; compliance dates moved
by the interim final rule of April 20, 2026). MV2's earlier censuses in this repository read
cities, counties, towns, school districts, states and special-district .gov domains, but never the
transit agencies in the Federal Transit Administration's National Transit Database. This script:

  1. waits until results/transit-pages/PREREG.md is on the repository's main branch and main's
     transit_pages.py, state_pages.py, a11y_pages.py and statement_check.py are byte for byte
     these files;
  2. reads the frame: the 2024 NTD Annual Data "Reporter Agency Information" table
     (data.transportation.gov, dataset ccvf-fykn), keeping every reporter whose organization type
     is "Independent Public Agency or Authority of Transit Service" and that gives a website. One
     row per distinct website host (the first agency by NTD ID; how many agencies share it is
     counted). Only the NTD ID, agency name, reporter type, city, state and website are kept;
     no street address or other column is written anywhere;
  3. reads every host (at most 1,000) in a fixed hash order with state_pages.crawl_site
     unchanged (home page, then the accessibility page picked by the census's link rules, read
     with a11y_pages.classify and statement_check.check_text), labels each page's topic from its
     address (paratransit, website, accessibility, ADA, other), then grades TR1-TR5 on distinct
     pages and distinct home sites.

Reads public pages only, one site at a time per worker with a pause between requests, honouring
robots.txt, under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond short
snippets around a WCAG version or a 2026/2027 date, with email addresses and phone numbers
removed. This counts what pages say; it does not test whether a website is accessible, and nothing
here calls an agency in breach.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_pages as sp  # noqa: E402  (the state census's crawler, unchanged)

ap = sp.ap  # a11y_pages, unchanged
sc = sp.sc  # statement_check, unchanged

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/transit-pages/PREREG.md"
PINNED = ("transit_pages.py", "state_pages.py", "a11y_pages.py", "statement_check.py")
FRAME_URL = "https://data.transportation.gov/resource/ccvf-fykn.json?$limit=5000&$order=ntd_id"
FRAME_TYPE = "Independent Public Agency or Authority of Transit Service"
GUARD_RE = sp.GUARD_RE

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_COHORT, MAX_COHORT = 250, 600
SAMPLE_N = 1000
SEED = "transit-pages-2026-11-12"
MIN_HOMES = 150
MIN_PAGES = 100
MIN_VERSIONED = 40
TR1_MAX_WCAG = 0.35       # special-district .gov domains: 125 of 341 pages (36.66%)
TR2_MIN_LINKED = 0.50     # special districts: 345 of 873 home sites (39.52%)
TR3_MAX_TITLE2 = 0.10     # special districts: 8 of 341 pages (2.35%)
TR4_MAX_ONLY_20 = 0.40    # special districts: 48 of 114 versioned pages (42.11%)
TR5_MAX_DATED = 0.05      # special districts: 2 of 341 pages

KINDS = {"Full Reporter": "full", "Reduced Reporter": "reduced", "Rural Reporter": "rural"}
HOST_RE = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)+$")
IP_RE = re.compile(r"^\d+(?:\.\d+){3}$")

# A page's topic from its address only (reported, not graded). First match wins.
PARA_RE = re.compile(r"paratransit|dial-?a-?ride|demand-?response|access-?a-?ride|ada-?ride|"
                     r"ada-?service")
WEB_RE = re.compile(r"(?:web|site|digital|online)[-_]?accessib|"
                    r"accessib\w*[-_/](?:statement|web|site|digital|online)")
ACC_RE = re.compile(r"accessib")
ADA_RE = re.compile(r"(?:^|[^a-z])ada(?:[^a-z]|$)")

EXTRA = ["ntd_id", "reporter_type", "agencies", "url"]
FRAME_COLUMNS = sp.FRAME_COLUMNS + EXTRA
COLUMNS = FRAME_COLUMNS + [c for c in sp.COLUMNS if c not in sp.FRAME_COLUMNS] + ["page_topic"]
DATE_LABELS = (("old_date", "2026-04-24"), ("new_date", "2027-04-26"), ("date_2028", "2028-04-26"))


# ---------------------------------------------------------------- frame

def host_of(url):
    """The website's host without 'www.', or '' if the cell is not a usable web address."""
    if isinstance(url, dict):
        url = url.get("url", "")
    s = sp.clean(url)
    if not s or " " in s:
        return ""
    if not re.match(r"https?://", s, re.I):
        s = "http://" + s
    try:
        host = (urllib.parse.urlsplit(s).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    if not HOST_RE.match(host) or IP_RE.match(host):
        return ""
    return host


def kind_of(reporter_type):
    return KINDS.get(sp.clean(reporter_type), "other")


def parse_frame(data):
    """(rows, info): one row per distinct website host among reporters of FRAME_TYPE, sorted by
    host. The first agency by NTD ID names the row; 'agencies' counts the agencies sharing it."""
    records = json.loads(data.decode("utf-8-sig"))
    types = collections.Counter(sp.clean(r.get("organization_type")) for r in records)
    of_type = [r for r in records if sp.clean(r.get("organization_type")) == FRAME_TYPE]
    of_type.sort(key=lambda r: (sp.clean(r.get("ntd_id")), sp.clean(r.get("agency_name"))))
    by_host, no_url, dropped = {}, 0, 0
    for r in of_type:
        url = r.get("url", "")
        if isinstance(url, dict):
            url = url.get("url", "")
        host = host_of(url)
        if not host:
            no_url += 1
            continue
        row = {"domain": host, "organization": sp.clean(r.get("agency_name")),
               "suborganization": "", "city": sp.clean(r.get("city")),
               "state": sp.clean(r.get("state")).upper(), "ntd_id": sp.clean(r.get("ntd_id")),
               "reporter_type": sp.clean(r.get("reporter_type")), "url": sp.clean(url)}
        if GUARD_RE.search(" ".join(row.values())):
            dropped += 1
            continue
        if host in by_host:
            by_host[host]["agencies"] += 1
            continue
        row["kind"] = kind_of(row["reporter_type"])
        row["agencies"] = 1
        by_host[host] = row
    rows = sorted(by_host.values(), key=lambda r: r["domain"])
    return rows, {"source_rows": len(records), "types": dict(sorted(types.items())),
                  "of_type": len(of_type), "no_url": no_url, "dropped": dropped,
                  "eligible": len(rows), "agencies": sum(r["agencies"] for r in rows)}


def sample(rows, n=SAMPLE_N, seed=SEED):
    """The first n rows in the order of SHA-256(seed + host): fixed before any page is read."""
    def key(r):
        return hashlib.sha256((seed + r["domain"]).encode("utf-8")).hexdigest()
    return sorted(rows, key=key)[:n]


def page_topic(url):
    """What a page's address says it is about: paratransit, website, accessibility, ada, other."""
    if not url:
        return ""
    path = urllib.parse.urlsplit(url).path.lower()
    if PARA_RE.search(path):
        return "paratransit"
    if WEB_RE.search(path):
        return "website"
    if ACC_RE.search(path):
        return "accessibility"
    if ADA_RE.search(path):
        return "ada"
    return "other"


def merge(out_rows, frame_rows):
    """The crawler keeps only its own frame columns: put the NTD columns back, add the topic."""
    extra = {r["domain"]: r for r in frame_rows}
    merged = []
    for r in out_rows:
        r = dict(r)
        src = extra.get(r.get("domain"), {})
        for k in EXTRA + ["kind"]:
            r[k] = src.get(k, r.get(k, ""))
        r["page_topic"] = page_topic(r.get("page_url") or "")
        merged.append(r)
    return merged


# ---------------------------------------------------------------- grading

def date_set(r):
    """Which of the three Title II dates a page gives, e.g. '2026-04-24+2028-04-26', or 'none'."""
    got = [label for key, label in DATE_LABELS if r.get(key)]
    return "+".join(got) if got else "none"


def grade(rows):
    homes = sp.distinct_homes(rows)
    linked = sum(1 for r in homes if int(r.get("candidates") or 0) > 0)
    pages = sp.distinct_pages(rows)
    wcag = sum(1 for r in pages if r.get("wcag_any"))
    versioned = [r for r in pages if r.get("highest")]
    by_high = {v: sum(1 for r in versioned if r["highest"] == v) for v in ("2.0", "2.1", "2.2")}
    title2 = sum(1 for r in pages if r.get("title2"))
    dated = sum(1 for r in pages if date_set(r) != "none")
    measures = {"TR1_wcag_of_pages": ap.share(wcag, len(pages)),
                "TR2_linked_of_homes": ap.share(linked, len(homes)),
                "TR3_title2_of_pages": ap.share(title2, len(pages)),
                "TR4_only_2.0_of_versioned": ap.share(by_high["2.0"], len(versioned)),
                "TR5_dated_of_pages": ap.share(dated, len(pages)),
                "highest_counts": by_high}
    enough_p = len(pages) >= MIN_PAGES
    preds = {"TR1": (wcag / len(pages) <= TR1_MAX_WCAG) if enough_p else None,
             "TR2": (linked / len(homes) >= TR2_MIN_LINKED) if len(homes) >= MIN_HOMES else None,
             "TR3": (title2 / len(pages) <= TR3_MAX_TITLE2) if enough_p else None,
             "TR4": (by_high["2.0"] / len(versioned) <= TR4_MAX_ONLY_20)
                    if len(versioned) >= MIN_VERSIONED else None,
             "TR5": (dated / len(pages) <= TR5_MAX_DATED) if enough_p else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    pages = sp.distinct_pages(rows)
    homes = sp.distinct_homes(rows)

    def n(pred):
        return sum(1 for r in pages if pred(r))

    def group(rs):
        return {"pages": len(rs), "wcag_any": sum(1 for r in rs if r.get("wcag_any")),
                "versioned": sum(1 for r in rs if r.get("highest")),
                "only_2.0": sum(1 for r in rs if r.get("highest") == "2.0"),
                "title2": sum(1 for r in rs if r.get("title2")),
                "dated": sum(1 for r in rs if date_set(r) != "none")}

    def by(key):
        return {k: group([r for r in pages if r.get(key, "") == k])
                for k in sorted({r.get(key, "") for r in pages})}
    return {
        "domains": len(rows),
        "agencies": sum(int(r.get("agencies") or 0) for r in rows),
        "frame_kinds": ap._tally(rows, "kind"),
        "home": ap._tally(rows, "home"),
        "home_via": ap._tally([r for r in rows if r.get("home") == "ok"], "home_via"),
        "distinct_home_hosts": len(homes),
        "page_status": ap._tally(rows, "page_status"),
        "domain_pages_ok": sum(1 for r in rows if r.get("page_status") == "ok"),
        "distinct_pages": len(pages),
        "distinct_texts": len({r.get("text_sha256") or "" for r in pages}),
        "page_rank": ap._tally(pages, "page_rank"),
        "page_topic": ap._tally(pages, "page_topic"),
        "versions": ap._tally(pages, "versions"),
        "findings": ap._tally(pages, "findings"),
        "overlay_on_home": ap._tally(homes, "overlay"),
        "wcag_any": n(lambda r: r.get("wcag_any")),
        "section508": n(lambda r: r.get("section508")),
        "stock": n(lambda r: r.get("stock")),
        "contact": n(lambda r: r.get("contact")),
        "dates": ap._tally([dict(r, dates=date_set(r)) for r in pages], "dates"),
        "by_kind": by("kind"),
        "by_topic": by("page_topic"),
        "by_state": by("state"),
    }


def wait_for_prereg(here, fetch=ap.fetch_bytes, sleep=time.sleep, tries=ap.TRIES, pause=ap.PAUSE):
    """(True, attempts) once main holds PREREG.md and the four pinned files, else (False, tries)."""
    local = {}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            local[name] = ap.normalize(f.read())
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            same = all(ap.normalize(fetch(REPO_RAW + name + "?n=%d" % i)) == local[name]
                       for name in PINNED)
            if b"TR5" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def result_text(result):
    lines = ["transit_pages %s" % result["version"],
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
        print("transit_pages: %s" % status)
        return 0 if status == "graded" else 1

    ok, result["prereg_attempts"] = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("stopped: the pre-registration and pinned files are not on main")
    try:
        data = fetch(FRAME_URL, tries=4, timeout=120)
        rows, info = parse_frame(data)
    except Exception as e:  # recorded; nothing is crawled
        result["error"] = str(e)[:200]
        return finish("stopped: frame not read")
    result["frame"] = dict(info, bytes=len(data), sha256=ap.sha256(data), url=FRAME_URL,
                           retrieved_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    result["eligible"] = len(rows)
    sp.write_csv(os.path.join(args.out_dir, "frame.csv"), rows, FRAME_COLUMNS)
    result["gates"]["C1_frame"] = MIN_COHORT <= len(rows) <= MAX_COHORT
    if not result["gates"]["C1_frame"]:
        return finish("stopped: frame size outside the pre-registered range")
    cohort = sample(rows)
    result["sampled"] = len(cohort)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + args.max_minutes * 60
    out_rows = sp.crawl(cohort, workers=args.workers, deadline=deadline, get=get,
                        delay=args.delay, sleep=sleep)
    out_rows = merge(out_rows, rows)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    sp.write_csv(os.path.join(args.out_dir, "rows.csv"), out_rows, COLUMNS)
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
