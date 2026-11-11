# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""special_districts 0.1.0: what do US special districts' accessibility pages say, and which date?

The pre-registered test in results/special-districts/PREREG.md. The ADA Title II web rule
(28 CFR 35.200) gives every "special district government" the later compliance date whatever
the population it serves; after the Justice Department's interim final rule of April 20, 2026
that date is April 26, 2028 (it was April 26, 2027). MV2's earlier censuses in this repository
read cities, counties, towns, school districts and (planned) state governments, but no special
district (water, fire, transit, park, library, hospital districts and the like). This script:

  1. waits until results/special-districts/PREREG.md is on the repository's main branch and
     main's special_districts.py, state_pages.py, a11y_pages.py and statement_check.py are
     byte for byte these files;
  2. reads the frame: every domain that CISA's public .gov registry list (cisagov/dotgov-data,
     current-full.csv, CC0-1.0) gives the domain type "Special district". Only the domain,
     organization, suborganization, city and state columns are kept; the list's security
     contact email column is never read into a row or written anywhere;
  3. reads every domain (at most 3,000) in a fixed hash order with state_pages.crawl_site
     unchanged (home page, then the accessibility page picked by the census's link rules, read
     with a11y_pages.classify and statement_check.check_text), then grades SD1-SD5 on distinct
     pages and distinct home sites.

Reads public pages only, one site at a time per worker with a pause between requests, honouring
robots.txt, under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond short
snippets around a WCAG version or a 2026/2027 date, with email addresses and phone numbers
removed. This counts what pages say; it does not test whether a website is accessible, and nothing
here calls a district in breach.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import argparse
import collections
import csv
import hashlib
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_pages as sp  # noqa: E402  (the state census's crawler, unchanged)

ap = sp.ap  # a11y_pages, unchanged
sc = sp.sc  # statement_check, unchanged

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/special-districts/PREREG.md"
PINNED = ("special_districts.py", "state_pages.py", "a11y_pages.py", "statement_check.py")
FRAME_URL = sp.FRAME_URL
FRAME_TYPE = "Special district"
GUARD_RE = sp.GUARD_RE

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_COHORT, MAX_COHORT = 800, 3000
SAMPLE_N = 3000
SEED = "special-districts-2026-11-11"
MIN_HOMES = 400
MIN_PAGES = 200
MIN_VERSIONED = 100
MIN_DATED = 10
SD1_MIN_ONLY_20 = 0.50        # cities of 50,000+: 283 of 508 (55.71%); 10,000-49,999: 638 of 809
SD2_MAX_TITLE2 = 0.15         # cities of 50,000+: 179 of 808; 10,000-49,999: 94 of 1,042
SD3_MAX_2028 = 0.05           # share of distinct pages that give April 26, 2028
SD4_MAX_LINKED = 0.60         # cities of 50,000+: 815 of 1,195; 10,000-49,999: 1,053 of 1,942
SD5_MAX_2028_OF_DATED = 0.50  # of distinct pages giving any of the three dates

# A rough kind from the organization name; reported, not graded. First match wins.
KINDS = (
    ("emergency", re.compile(r"\b911\b|\be-?911\b|emergency\s+(?:communication|service|"
                             r"management)|dispatch", re.I)),
    ("fire", re.compile(r"\bfire\b|\brescue\b", re.I)),
    ("water", re.compile(r"water|sewer|sanitat|irrigation|drainage|reclamation|utilit|levee|"
                         r"flood|conservanc", re.I)),
    ("transit", re.compile(r"transit|transport|\brail|airport|\bports?\b|aviation|\bbus\b|"
                           r"\btoll", re.I)),
    ("parks", re.compile(r"\bparks?\b|recreation|forest\s+preserve", re.I)),
    ("library", re.compile(r"librar", re.I)),
    ("health", re.compile(r"hospital|health|medical", re.I)),
    ("housing", re.compile(r"housing", re.I)),
)

FRAME_COLUMNS = sp.FRAME_COLUMNS
COLUMNS = sp.COLUMNS
DATE_LABELS = (("old_date", "2026-04-24"), ("new_date", "2027-04-26"), ("date_2028", "2028-04-26"))


# ---------------------------------------------------------------- frame

def kind_of(organization, suborganization=""):
    s = organization + " " + suborganization
    for kind, rx in KINDS:
        if rx.search(s):
            return kind
    return "other"


def parse_frame(data):
    """(rows, info): one row per distinct domain of type FRAME_TYPE, sorted by domain. The
    registry's contact email column is never copied into a row."""
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    types = collections.Counter()
    rows, seen, dropped, total = [], set(), 0, 0
    for r in reader:
        total += 1
        t = sp.clean(r.get("Domain type"))
        types[t] += 1
        if t != FRAME_TYPE:
            continue
        domain = sp.clean(r.get("Domain name")).lower().rstrip(".")
        if not domain or "." not in domain or " " in domain or domain in seen:
            continue
        row = {"domain": domain, "organization": sp.clean(r.get("Organization name")),
               "suborganization": sp.clean(r.get("Suborganization name")),
               "city": sp.clean(r.get("City")), "state": sp.clean(r.get("State")).upper()}
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


# ---------------------------------------------------------------- grading

def date_set(r):
    """Which of the three Title II dates a page gives, e.g. '2026-04-24+2028-04-26', or 'none'."""
    got = [label for key, label in DATE_LABELS if r.get(key)]
    return "+".join(got) if got else "none"


def grade(rows):
    homes = sp.distinct_homes(rows)
    linked = sum(1 for r in homes if int(r.get("candidates") or 0) > 0)
    pages = sp.distinct_pages(rows)
    versioned = [r for r in pages if r.get("highest")]
    by_high = {v: sum(1 for r in versioned if r["highest"] == v) for v in ("2.0", "2.1", "2.2")}
    title2 = sum(1 for r in pages if r.get("title2"))
    d2028 = sum(1 for r in pages if r.get("date_2028"))
    dated = [r for r in pages if date_set(r) != "none"]
    dated_2028 = sum(1 for r in dated if r.get("date_2028"))
    measures = {"SD1_only_2.0_of_versioned": ap.share(by_high["2.0"], len(versioned)),
                "SD2_title2_of_pages": ap.share(title2, len(pages)),
                "SD3_2028_of_pages": ap.share(d2028, len(pages)),
                "SD4_linked_of_homes": ap.share(linked, len(homes)),
                "SD5_2028_of_dated": ap.share(dated_2028, len(dated)),
                "highest_counts": by_high}
    enough_p = len(pages) >= MIN_PAGES
    preds = {"SD1": (by_high["2.0"] / len(versioned) >= SD1_MIN_ONLY_20)
                    if len(versioned) >= MIN_VERSIONED else None,
             "SD2": (title2 / len(pages) <= SD2_MAX_TITLE2) if enough_p else None,
             "SD3": (d2028 / len(pages) <= SD3_MAX_2028) if enough_p else None,
             "SD4": (linked / len(homes) <= SD4_MAX_LINKED) if len(homes) >= MIN_HOMES else None,
             "SD5": (dated_2028 / len(dated) <= SD5_MAX_2028_OF_DATED)
                    if len(dated) >= MIN_DATED else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    pages = sp.distinct_pages(rows)
    homes = sp.distinct_homes(rows)

    def n(pred):
        return sum(1 for r in pages if pred(r))

    def group(rs):
        return {"pages": len(rs), "versioned": sum(1 for r in rs if r.get("highest")),
                "only_2.0": sum(1 for r in rs if r.get("highest") == "2.0"),
                "title2": sum(1 for r in rs if r.get("title2")),
                "dated": sum(1 for r in rs if date_set(r) != "none"),
                "date_2028": sum(1 for r in rs if r.get("date_2028"))}
    return {
        "domains": len(rows),
        "frame_kinds": ap._tally(rows, "kind"),
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
        "stock": n(lambda r: r.get("stock")),
        "contact": n(lambda r: r.get("contact")),
        "dates": ap._tally([dict(r, dates=date_set(r)) for r in pages], "dates"),
        "by_kind": {k: group([r for r in pages if r.get("kind", "") == k])
                    for k in sorted({r.get("kind", "") for r in pages})},
        "by_state": {s: group([r for r in pages if r.get("state", "") == s])
                     for s in sorted({r.get("state", "") for r in pages})},
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
            if b"SD5" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def result_text(result):
    lines = ["special_districts %s" % result["version"],
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
        print("special_districts: %s" % status)
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
