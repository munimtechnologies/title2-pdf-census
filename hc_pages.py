# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""hc_pages 0.1.0: what do US health centres' accessibility pages say about Section 504?

The pre-registered test in results/hc-pages/PREREG.md. Health centres funded or designated under
HRSA's Health Center Program receive HHS funding, so HHS's 2024 Section 504 rule (45 CFR 84.84,
89 FR 40193) asks them to meet WCAG 2.1 Level AA on the web. Its first web dates were May 11, 2026
(fifteen or more employees) and May 10, 2027 (fewer than fifteen); an HHS interim final rule
published on May 11, 2026 (91 FR 25507) moved them to May 11, 2027 and May 10, 2028 (45 CFR
84.84(b) as amended, read on eCFR on 2026-11-12). MV2's earlier censuses in this repository read
public bodies under the ADA Title II rule, never health care. This script:

  1. waits until results/hc-pages/PREREG.md is on the repository's main branch and main's
     hc_pages.py, state_pages.py, a11y_pages.py and statement_check.py are byte for byte these
     files;
  2. reads the frame: HRSA's public daily file "Health Center Service Delivery and Look-Alike
     Sites" (data.hrsa.gov, CSV), keeping only active sites, then one website host per health
     centre (Health Center Number): the host its active sites list most often. Only the health
     centre number and name, the organisation's city and state, the site status and the host of
     the site web address are read; no street address, phone number or person's name from the file
     is ever read into a row or written anywhere;
  3. reads every host (at most 2,500) in a fixed hash order with state_pages.crawl_site unchanged
     (home page, then the accessibility page picked by the census's link rules), reading each page
     with the state census's rules plus a Section 504 reading copied from a11y-statement-check
     0.9.0, then grades HC1-HC5 on distinct pages and distinct home sites.

Reads public pages only, one site at a time per worker with a pause between requests, honouring
robots.txt, under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond short
snippets around a WCAG version or a date, with email addresses and phone numbers removed. This
counts what pages say; it does not test whether a website is accessible, and nothing here calls a
health centre in breach.

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_pages as sp  # noqa: E402  (the state census's crawler, unchanged)

ap = sp.ap  # a11y_pages, unchanged
sc = sp.sc  # statement_check, unchanged

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/hc-pages/PREREG.md"
PINNED = ("hc_pages.py", "state_pages.py", "a11y_pages.py", "statement_check.py")
FRAME_URL = ("https://data.hrsa.gov/DataDownload/DD_Files/"
             "Health_Center_Service_Delivery_and_LookAlike_Sites.csv")
GUARD_RE = sp.GUARD_RE

# The file's columns, by the long name or the short (physical) name of HRSA's data dictionary.
# The first three are needed; without one of them the job stops and no website is read.
FIELDS = (("number", ("Health Center Number", "HCP_MERGED_GRANT_LAL_KEY"), True),
          ("url", ("Site Web Address", "SITE_URL"), True),
          ("status", ("Site Status Description", "HCC_STATUS_DESC"), True),
          ("name", ("Health Center Name", "HCP_ORG_NM"), False),
          ("city", ("Health Center Organization City", "HCP_ORG_CITY"), False),
          ("state", ("Health Center Organization State", "HCP_ORG_ST_ABBR"), False))

# Hosts that are not a health centre's own site; a site address on one of them is left out.
OTHER_HOSTS = ("facebook.com", "fb.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
               "youtube.com", "google.com", "yelp.com", "linktr.ee", "hrsa.gov")

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_COHORT, MAX_COHORT = 700, 2500
SAMPLE_N = 2500
SEED = "hc-pages-2026-11-12"
MIN_HOMES = 500
MIN_PAGES = 200
MIN_VERSIONED = 100
HC1_MAX_LINKED = 0.50      # cities of 50,000+: 815 of 1,195 home pages read (68.20%)
HC2_MIN_S504 = 0.25        # cities of 50,000+, Title II: 179 of 808 pages read (22.15%)
HC3_MAX_DATED = 0.05
HC5_MAX_OVERLAY = 0.30     # cities of 50,000+: 494 of 1,195 home pages read (41.34%)

FRAME_COLUMNS = ["domain", "number", "organization", "city", "state", "kind", "sites"]

# HHS's Section 504 rule, as read by a11y-statement-check 0.9.0 (statement_template_check.py):
# the same patterns, copied here so this census does not depend on that repository.
def may_date_re(day, year):
    """May <day>, <year> as "May 11, 2026", "May 11th 2026", "11 May 2026", "05/11/2026",
    "5/11/26" or "2026-05-11" (month first in the numeric form, as on US pages)."""
    return re.compile(r"\bMay\.?\s+%d(?:th)?,?\s+%d\b|\b%d(?:th)?\s+(?:of\s+)?May,?\s+%d\b|"
                      r"\b0?5/%d/(?:20)?%02d\b|\b%d-05-%d\b"
                      % (day, year, day, year, day, year % 100, year, day), re.I)


SECTION_504_RE = re.compile(r"\bSec(?:tion|\.)\s*504\b|§\s*504\b|"
                            r"\b45\s*C\.?\s*F\.?\s*R\.?\s*(?:Part\s*|§+\s*)?84\b|"
                            r"\bHHS\b|\bHealth\s+(?:and|&)\s+Human\s+Services\b", re.I)
SECTION_1557_RE = re.compile(r"\bSec(?:tion|\.)\s*1557\b", re.I)
HHS504_DATES = (("2026_05_11", may_date_re(11, 2026)), ("2027_05_10", may_date_re(10, 2027)),
                ("2027_05_11", may_date_re(11, 2027)), ("2028_05_10", may_date_re(10, 2028)))
HHS504_OLD = ("2026_05_11", "2027_05_10")
HHS504_NEW = ("2027_05_11", "2028_05_10")
# Some guides give the later date as May 11, 2028; 45 CFR 84.84(b)(2) on eCFR says May 10, 2028.
# A page giving May 11, 2028 is counted on its own (described, not graded, not a "dated" page).
MAY_11_2028_RE = may_date_re(11, 2028)
DATE504_COLUMNS = ["d504_" + key for key, _ in HHS504_DATES]
BOOLS = sp.BOOLS + ("s504", "s1557", "old_504", "may11_2028") + tuple(DATE504_COLUMNS)
COLUMNS = (FRAME_COLUMNS + [c for c in sp.COLUMNS if c not in sp.FRAME_COLUMNS]
           + ["s504", "s1557"] + DATE504_COLUMNS + ["old_504", "may11_2028", "s504_snippet"])
TITLE2_DATES = (("old_date", "2026-04-24"), ("new_date", "2027-04-26"),
                ("date_2028", "2028-04-26"))


# ---------------------------------------------------------------- frame

def clean(s):
    return " ".join(str(s or "").split())


def decode(data):
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", "replace")


def domain_of(web):
    """The host of a site web address, lower case, without one leading 'www.'; '' if none."""
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


def other_host(host):
    return any(host == h or host.endswith("." + h) for h in OTHER_HOSTS)


def kind_of(number):
    n = clean(number).upper()
    if n.startswith("H80"):
        return "awardee"
    if n.startswith("LAL"):
        return "look_alike"
    return "other"


def columns_of(header):
    """{field: index} for the file's header; KeyError naming the needed fields that are missing."""
    norm = [clean(h).lower() for h in header]
    idx, missing = {}, []
    for field, names, needed in FIELDS:
        for name in names:
            if name.lower() in norm:
                idx[field] = norm.index(name.lower())
                break
        else:
            if needed:
                missing.append(names[0])
    if missing:
        raise KeyError("columns missing: " + "; ".join(missing))
    return idx


def parse_frame(data):
    """(rows, info): one row per distinct website host, from the host that each health centre's
    active sites list most often (ties: the alphabetically first host); where two health centres
    lead to one host, the lower Health Center Number keeps it. Sorted by host."""
    reader = csv.reader(io.StringIO(decode(data)))
    idx = columns_of(next(reader, []))

    def col(rec, field):
        i = idx.get(field)
        return clean(rec[i]) if i is not None and i < len(rec) else ""

    statuses = collections.Counter()
    hosts = collections.defaultdict(collections.Counter)
    facts, numbers = {}, set()
    total = active = no_site = other = 0
    for rec in reader:
        if not any(x.strip() for x in rec):
            continue
        total += 1
        number = col(rec, "number").upper()
        status = col(rec, "status")
        statuses[status] += 1
        if number:
            numbers.add(number)
        if not number or not status.lower().startswith("active"):
            continue
        active += 1
        facts.setdefault(number, {"organization": col(rec, "name"), "city": col(rec, "city"),
                                  "state": col(rec, "state").upper()})
        host = domain_of(col(rec, "url"))
        if not host:
            no_site += 1
            continue
        if other_host(host):
            other += 1
            continue
        hosts[number][host] += 1
    rows, seen, shared, dropped = [], set(), 0, 0
    for number in sorted(hosts):
        counts = hosts[number]
        host = sorted(counts, key=lambda h: (-counts[h], h))[0]
        if host in seen:
            shared += 1
            continue
        row = dict(domain=host, number=number, kind=kind_of(number),
                   sites=str(sum(counts.values())), **facts[number])
        if GUARD_RE.search(" ".join(row.values())):
            dropped += 1
            continue
        seen.add(host)
        rows.append(row)
    rows.sort(key=lambda r: r["domain"])
    return rows, {"source_rows": total, "statuses": dict(statuses.most_common(12)),
                  "centres": len(numbers), "active_sites": active,
                  "centres_active": len(facts), "active_no_site": no_site,
                  "active_other_host": other, "centres_with_host": len(hosts),
                  "shared_host": shared, "dropped": dropped, "eligible": len(rows)}


def sample(rows, n=SAMPLE_N, seed=SEED):
    """The first n rows in the order of SHA-256(seed + host): fixed before any page is read."""
    return sp.sample(rows, n=n, seed=seed)


# ---------------------------------------------------------------- reading

def read_504(text):
    """Whether a page names Section 504 / 45 CFR part 84 / HHS, Section 1557, and which of the four
    Section 504 web dates it gives; old_504 as a11y-statement-check 0.9.0's old_504_date note."""
    flat = " ".join(text.split())
    named = bool(SECTION_504_RE.search(flat))
    out = {"s504": named, "s1557": bool(SECTION_1557_RE.search(flat))}
    first = None
    for key, rx in HHS504_DATES:
        m = rx.search(flat)
        out["d504_" + key] = bool(m)
        if m and (first is None or m.start() < first.start()):
            first = m
    old = any(out["d504_" + k] for k in HHS504_OLD)
    new = any(out["d504_" + k] for k in HHS504_NEW)
    out["old_504"] = named and old and not new
    out["may11_2028"] = bool(MAY_11_2028_RE.search(flat))
    out["s504_snippet"] = ap.snippet(flat, first) if first else ""
    return out


_STATE_READ_PAGE = sp.read_page


def read_page(text):
    """The state census's reading of one page (unchanged), plus read_504."""
    c = _STATE_READ_PAGE(text)
    c.update(read_504(text))
    return c


def crawl(cohort, **kw):
    """state_pages.crawl with this census's read_page; the state module is restored afterwards."""
    sp.read_page = read_page
    try:
        return sp.crawl(cohort, **kw)
    finally:
        sp.read_page = _STATE_READ_PAGE


# ---------------------------------------------------------------- grading

def typed(rows):
    """Rows read back from rows.csv, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def dates_504(r):
    """Which Section 504 web dates a page gives, e.g. '2026-05-11+2027-05-11', or 'none'."""
    got = [k.replace("_", "-") for k, _ in HHS504_DATES if r.get("d504_" + k)]
    return "+".join(got) if got else "none"


def dated_504(r):
    """A page that names Section 504, 45 CFR part 84 or HHS and gives one of the four dates."""
    return bool(r.get("s504")) and dates_504(r) != "none"


def grade(rows):
    homes = sp.distinct_homes(rows)
    linked = sum(1 for r in homes if int(r.get("candidates") or 0) > 0)
    overlay = sum(1 for r in homes if r.get("overlay"))
    pages = sp.distinct_pages(rows)
    versioned = [r for r in pages if r.get("highest")]
    by_high = {v: sum(1 for r in versioned if r["highest"] == v) for v in ("2.0", "2.1", "2.2")}
    named = sum(1 for r in pages if r.get("s504"))
    dated = sum(1 for r in pages if dated_504(r))
    measures = {"HC1_linked_of_homes": ap.share(linked, len(homes)),
                "HC2_s504_of_pages": ap.share(named, len(pages)),
                "HC3_504_dated_of_pages": ap.share(dated, len(pages)),
                "HC4_highest_counts": by_high,
                "HC5_overlay_of_homes": ap.share(overlay, len(homes))}
    enough_h = len(homes) >= MIN_HOMES
    enough_p = len(pages) >= MIN_PAGES
    preds = {"HC1": (linked / len(homes) <= HC1_MAX_LINKED) if enough_h else None,
             "HC2": (named / len(pages) >= HC2_MIN_S504) if enough_p else None,
             "HC3": (dated / len(pages) <= HC3_MAX_DATED) if enough_p else None,
             "HC4": (by_high["2.1"] > by_high["2.0"] and by_high["2.1"] > by_high["2.2"])
                    if len(versioned) >= MIN_VERSIONED else None,
             "HC5": (overlay / len(homes) <= HC5_MAX_OVERLAY) if enough_h else None}
    return measures, preds


def title2_dates(r):
    got = [label for key, label in TITLE2_DATES if r.get(key)]
    return "+".join(got) if got else "none"


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
                "s504": sum(1 for r in rs if r.get("s504")),
                "dated_504": sum(1 for r in rs if dated_504(r)),
                "old_504": sum(1 for r in rs if r.get("old_504")),
                "title2": sum(1 for r in rs if r.get("title2"))}
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
        "section1557": n(lambda r: r.get("s1557")),
        "s504": n(lambda r: r.get("s504")),
        "dates_504": ap._tally([dict(r, d=dates_504(r)) for r in pages if r.get("s504")], "d"),
        "old_504": n(lambda r: r.get("old_504")),
        "may_11_2028": n(lambda r: r.get("may11_2028")),
        "title2": n(lambda r: r.get("title2")),
        "title2_dates": ap._tally([dict(r, d=title2_dates(r)) for r in pages], "d"),
        "stock": n(lambda r: r.get("stock")),
        "contact": n(lambda r: r.get("contact")),
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
            if b"HC5" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def result_text(result):
    lines = ["hc_pages %s" % result["version"],
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
        print("hc_pages: %s" % status)
        return 0 if status == "graded" else 1

    ok, result["prereg_attempts"] = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("stopped: the pre-registration and pinned files are not on main")
    try:
        data = fetch(FRAME_URL, tries=4, timeout=180)
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
    out_rows = crawl(cohort, workers=args.workers, deadline=deadline, get=get,
                     delay=args.delay, sleep=sleep)
    extra = {r["domain"]: r for r in cohort}
    for r in out_rows:
        src = extra.get(r.get("domain", ""), {})
        r.update(number=src.get("number", ""), sites=src.get("sites", ""))
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
