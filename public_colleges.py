# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""public_colleges 0.1.0: what do US public colleges' accessibility pages say, and which date?

The pre-registered test in results/public-colleges/PREREG.md. Public colleges and universities
are state or local government entities, so the ADA Title II web rule (28 CFR 35.200, WCAG 2.1
Level AA) covers their websites. The rule first gave large public entities April 24, 2026; the
Justice Department's interim final rule of April 20, 2026 moved that date to April 26, 2027 (and
the later date to April 26, 2028). MV2's earlier censuses in this repository read cities,
counties, towns, school districts, state governments and special districts, never colleges.
This script:

  1. waits until results/public-colleges/PREREG.md is on the repository's main branch and main's
     public_colleges.py, state_pages.py, a11y_pages.py and statement_check.py are byte for byte
     these files;
  2. reads the frame: the U.S. Department of Education's IPEDS directory file for 2024
     (HD2024.zip from nces.ed.gov, public U.S. government data), keeping every institution whose
     sector is public four-year (1) or public two-year (2) and that IPEDS marks as active this
     year, one row per distinct website host. Only the unit id, name, city, state, sector and the
     host of the website address are kept; no person's name, phone number or street address from
     the file is ever read into a row or written anywhere;
  3. reads every host (at most 2,500) in a fixed hash order with state_pages.crawl_site unchanged
     (home page, then the accessibility page picked by the census's link rules, read with
     a11y_pages.classify and statement_check.check_text), then grades PC1-PC5 on distinct pages
     and distinct home sites.

Reads public pages only, one site at a time per worker with a pause between requests, honouring
robots.txt, under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond short
snippets around a WCAG version or a 2026/2027 date, with email addresses and phone numbers
removed. This counts what pages say; it does not test whether a website is accessible, and nothing
here calls a college in breach.

Standard library only. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import argparse
import collections
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_pages as sp  # noqa: E402  (the state census's crawler, unchanged)

ap = sp.ap  # a11y_pages, unchanged
sc = sp.sc  # statement_check, unchanged

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/public-colleges/PREREG.md"
PINNED = ("public_colleges.py", "state_pages.py", "a11y_pages.py", "statement_check.py")
FRAME_URL = "https://nces.ed.gov/ipeds/datacenter/data/HD2024.zip"
FRAME_MEMBER = "hd2024.csv"
SECTORS = {"1": "public_4yr", "2": "public_2yr"}
NEEDED = ("UNITID", "INSTNM", "CITY", "STABBR", "WEBADDR", "SECTOR", "CYACTIVE")
GUARD_RE = sp.GUARD_RE

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_COHORT, MAX_COHORT = 1000, 2500
SAMPLE_N = 2500
SEED = "public-colleges-2026-11-12"
MIN_HOMES = 500
MIN_PAGES = 200
MIN_VERSIONED = 100
MIN_DATED = 20
PC1_MIN_LINKED = 0.75          # cities of 50,000+: 815 of 1,195 home pages read (68.20%)
PC2_MAX_ONLY_20 = 0.30         # cities of 50,000+: 283 of 508 versioned pages (55.71%)
PC4_MIN_TITLE2 = 0.20          # cities of 50,000+: 179 of 808 pages read (22.15%)
PC5_MIN_STALE_OF_DATED = 0.25  # cities of 50,000+: 12 of 17 dated pages gave only April 24, 2026

FRAME_COLUMNS = ["domain", "unitid", "organization", "city", "state", "kind"]
COLUMNS = FRAME_COLUMNS + [c for c in sp.COLUMNS if c not in sp.FRAME_COLUMNS]
DATE_LABELS = (("old_date", "2026-04-24"), ("new_date", "2027-04-26"), ("date_2028", "2028-04-26"))


# ---------------------------------------------------------------- frame

def clean(s):
    return " ".join(str(s or "").split())


def decode(data):
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:  # IPEDS files are often Windows-1252
        return data.decode("cp1252", "replace")


def domain_of(web):
    """The host of an IPEDS website address, lower case, without one leading 'www.'; '' if none."""
    s = clean(web)
    if not s or " " in s:
        return ""
    if not re.match(r"[a-z][a-z0-9+.-]*://", s, re.I):
        s = "http://" + s
    try:
        host = (urllib.parse.urlsplit(s).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    if "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host):
        return ""
    return host


def csv_from_zip(data, member=FRAME_MEMBER):
    """(bytes, name) of the directory CSV inside the IPEDS zip; KeyError if it is not there."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = {n.lower().rsplit("/", 1)[-1]: n for n in z.namelist()}
        if member not in names:
            raise KeyError("%s not in the archive (%s)" % (member, ", ".join(sorted(names))[:120]))
        return z.read(names[member]), names[member]


def _unit_key(r):
    return (len(r["unitid"]), r["unitid"])


def parse_frame(data):
    """(rows, info): one row per distinct website host of an active public 4-year or 2-year
    institution, sorted by host. Where several institutions share a host, the lowest unit id is
    kept. Only the NEEDED columns are ever read; KeyError if one is missing."""
    reader = csv.reader(io.StringIO(decode(data)))
    header = [clean(h).upper() for h in next(reader, [])]
    missing = [c for c in NEEDED if c not in header]
    if missing:
        raise KeyError("columns missing: " + " ".join(missing))
    idx = {c: header.index(c) for c in NEEDED}

    def col(rec, c):
        i = idx[c]
        return clean(rec[i]) if i < len(rec) else ""

    sectors = collections.Counter()
    eligible = []
    total = inactive = no_site = dropped = 0
    for rec in reader:
        if not any(x.strip() for x in rec):
            continue
        total += 1
        sector = col(rec, "SECTOR")
        sectors[sector] += 1
        if sector not in SECTORS:
            continue
        if col(rec, "CYACTIVE") != "1":
            inactive += 1
            continue
        domain = domain_of(col(rec, "WEBADDR"))
        if not domain:
            no_site += 1
            continue
        row = {"domain": domain, "unitid": col(rec, "UNITID"), "organization": col(rec, "INSTNM"),
               "city": col(rec, "CITY"), "state": col(rec, "STABBR").upper(),
               "kind": SECTORS[sector]}
        if GUARD_RE.search(" ".join(row.values())):
            dropped += 1
            continue
        eligible.append(row)
    rows, seen, shared = [], set(), 0
    for row in sorted(eligible, key=_unit_key):
        if row["domain"] in seen:
            shared += 1
            continue
        seen.add(row["domain"])
        rows.append(row)
    rows.sort(key=lambda r: r["domain"])
    return rows, {"source_rows": total, "sectors": dict(sorted(sectors.items())),
                  "inactive": inactive, "no_site": no_site, "shared_host": shared,
                  "dropped": dropped, "eligible": len(rows)}


def sample(rows, n=SAMPLE_N, seed=SEED):
    """The first n rows in the order of SHA-256(seed + domain): fixed before any page is read."""
    return sp.sample(rows, n=n, seed=seed)


# ---------------------------------------------------------------- grading

def date_set(r):
    """Which of the three Title II dates a page gives, e.g. '2026-04-24+2027-04-26', or 'none'."""
    got = [label for key, label in DATE_LABELS if r.get(key)]
    return "+".join(got) if got else "none"


def stale(r):
    """A page that gives April 24, 2026 and neither later date."""
    return bool(r.get("old_date")) and not r.get("new_date") and not r.get("date_2028")


def grade(rows):
    homes = sp.distinct_homes(rows)
    linked = sum(1 for r in homes if int(r.get("candidates") or 0) > 0)
    pages = sp.distinct_pages(rows)
    versioned = [r for r in pages if r.get("highest")]
    by_high = {v: sum(1 for r in versioned if r["highest"] == v) for v in ("2.0", "2.1", "2.2")}
    title2 = sum(1 for r in pages if r.get("title2"))
    dated = [r for r in pages if date_set(r) != "none"]
    n_stale = sum(1 for r in dated if stale(r))
    measures = {"PC1_linked_of_homes": ap.share(linked, len(homes)),
                "PC2_only_2.0_of_versioned": ap.share(by_high["2.0"], len(versioned)),
                "PC3_highest_counts": by_high,
                "PC4_title2_of_pages": ap.share(title2, len(pages)),
                "PC5_stale_of_dated": ap.share(n_stale, len(dated))}
    enough_v = len(versioned) >= MIN_VERSIONED
    preds = {"PC1": (linked / len(homes) >= PC1_MIN_LINKED) if len(homes) >= MIN_HOMES else None,
             "PC2": (by_high["2.0"] / len(versioned) <= PC2_MAX_ONLY_20) if enough_v else None,
             "PC3": (by_high["2.1"] > by_high["2.0"] and by_high["2.1"] > by_high["2.2"])
                    if enough_v else None,
             "PC4": (title2 / len(pages) >= PC4_MIN_TITLE2) if len(pages) >= MIN_PAGES else None,
             "PC5": (n_stale / len(dated) >= PC5_MIN_STALE_OF_DATED)
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
                "2.1": sum(1 for r in rs if r.get("highest") == "2.1"),
                "2.2": sum(1 for r in rs if r.get("highest") == "2.2"),
                "title2": sum(1 for r in rs if r.get("title2")),
                "dated": sum(1 for r in rs if date_set(r) != "none"),
                "stale": sum(1 for r in rs if stale(r))}
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
            if b"PC5" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def result_text(result):
    lines = ["public_colleges %s" % result["version"],
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
        print("public_colleges: %s" % status)
        return 0 if status == "graded" else 1

    ok, result["prereg_attempts"] = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("stopped: the pre-registration and pinned files are not on main")
    try:
        data = fetch(FRAME_URL, tries=4, timeout=120)
        table, member = csv_from_zip(data)
        rows, info = parse_frame(table)
    except Exception as e:  # recorded; nothing is crawled
        result["error"] = str(e)[:200]
        return finish("stopped: frame not read")
    result["frame"] = dict(info, bytes=len(data), sha256=ap.sha256(data), url=FRAME_URL,
                           member=member, member_sha256=ap.sha256(table),
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
    unit = {r["domain"]: r["unitid"] for r in cohort}
    for r in out_rows:
        r["unitid"] = unit.get(r.get("domain", ""), "")
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
