# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""planned_dates 0.1.0: how often does a UK accessibility statement give a planned review date that the census date reader took as its latest review?

Pre-registered in results/uk-planned/PREREG.md. The census date reader of council_stock.py 0.1.0
(used unchanged by the council-stock and govuk-stock censuses) takes any date after "reviewed
in / on" or "updated in / on" as a review date, so "It will be reviewed in March 2027" reads as a
review in March 2027. a11y-statement-check 0.7.0 leaves out a date right after "will be", "shall
be", "should be", "must be", "to be" or "next" (PLANNED_RE, copied here byte for byte).

The frame is every statement address the two censuses found (status ok in
results/uk-councils/hosts.csv and results/govuk-orgs/hosts.csv), one row per distinct address.
Each address is read once (robots.txt honoured, one request at a time per worker, a pause after
each) and its visible text is read twice: by the census reader as it is ("old") and by the same
reader with the planned dates left out ("new"). Both readings are of the same text, so any
difference comes from planned dates alone. No page text is stored except a short snippet around
each planned date (at most SNIPPET_CHARS characters), so a person can check it.

This counts what statements say; it does not test whether a website is accessible, and nothing
here calls an organisation in breach. Made by MV2 of Munim, Inc. with AI agents; not yet checked
by a person. Standard library only.
"""

import argparse
import collections
import concurrent.futures
import csv
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import council_stock as cs  # noqa: E402  (council_stock 0.1.0, unchanged on main)
import statement_template_check as stc  # noqa: E402  (a11y-statement-check 0.3.0, unchanged)

__version__ = "0.1.0"

PREREG_PATH = "results/uk-planned/PREREG.md"
TABLES = (("council", "results/uk-councils/hosts.csv"),
          ("govuk", "results/govuk-orgs/hosts.csv"))
# F1: the number of rows with status ok in each table, as published in COUNCIL-STOCK-RESULT.md
# and GOVUK-STOCK-RESULT.md.
TABLE_OK_ROWS = {"council": 284, "govuk": 202}
F1_MIN_URLS = 400
F1_MAX_URLS = 486
COUNCIL_STOCK_VERSION = "0.1.0"
RELEASE_070_URL = ("https://raw.githubusercontent.com/munimtechnologies/a11y-statement-check/"
                   "v0.7.0/skills/accessibility-statement-check/statement_template_check.py")
# Copied byte for byte from a11y-statement-check 0.7.0 (gate P0 checks the release still has it).
PLANNED_PATTERN = r"\b(?:will|shall|should|must|to|next)\s+(?:be\s+)?(?:next\s+)?$"
PLANNED_RE = re.compile(PLANNED_PATTERN, re.I)
PLANNED_WINDOW = 25
# Any sentence about a future review, whether or not the census reader takes a date from it
# (described, not graded).
FUTURE_RE = re.compile(r"\b(?:will|shall)\s+(?:next\s+)?(?:be\s+)?(?:next\s+)?"
                       r"(?:reviewed|updated|revised|review|update|revise)\b"
                       r"|\bdue\s+to\s+be\s+(?:reviewed|updated|revised)\b"
                       r"|\bnext\s+review\b", re.I)
SNIPPET_CHARS = 120
SNIPPET_BEFORE = 45
CRAWL_SEED = "uk-planned-2026-11"
RETRY_STATUSES = (429, 503)
RETRY_PAUSE = 30
STALE_BEFORE = cs.STALE_BEFORE  # "2025-11-01", as in both censuses

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
G1_MIN_READ = 0.80          # G1: share of frame addresses read again as a statement
Q1_MAX_PLANNED = 0.05       # Q1: share of read statements with a planned date the old reader took
Q2_MAX_FLIPPED = 0.01       # Q2: share of old-dated statements that go from current to stale/undated
Q2_MIN_PAGES = 100
Q3_MAX_PP = 1.5             # Q3: stale share, new minus old reader, per census, in points
Q3_MIN_PAGES = 100
Q4_MAX_NOT_PLANNED = 1      # Q4: snippets that, read by eye, are not a planned review or update

COLUMNS = ["url", "sources", "census_date", "census_sha256", "status", "retried", "text_chars",
           "text_sha256", "text_same", "old_review", "old_prepared", "old_date", "old_source",
           "new_review", "new_prepared", "new_date", "new_source", "planned_n", "planned_dates",
           "future_phrases"]
SNIPPET_COLUMNS = ["url", "date", "snippet"]


# ---------------------------------------------------------------- the two readings

def planned(flat, m):
    """True when the words right before a date phrase make it a planned date (0.7.0's rule)."""
    return bool(PLANNED_RE.search(flat[max(0, m.start() - PLANNED_WINDOW):m.start()]))


def new_dates(text):
    """council_stock.statement_dates with planned dates left out: (review, prepared, statement
    date, source) as ISO strings ('' when none)."""
    flat = " ".join(text.split())
    reviews = [d for d in (cs._date(m) for m in cs.REVIEW_RE.finditer(flat)
                           if not planned(flat, m)) if d]
    prepared = [d for d in (cs._date(m) for m in cs.PREPARED_RE.finditer(flat)
                            if not planned(flat, m)) if d]
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


def planned_matches(text):
    """[(ISO date, snippet)] for every date phrase the old reader takes but 0.7.0 leaves out."""
    flat = " ".join(text.split())
    out = []
    for rx in (cs.REVIEW_RE, cs.PREPARED_RE):
        for m in rx.finditer(flat):
            d = cs._date(m)
            if d and planned(flat, m):
                snip = flat[max(0, m.start() - SNIPPET_BEFORE):m.end()][-SNIPPET_CHARS:]
                if cs.GUARD_RE.search(snip):
                    snip = "[withheld]"
                out.append((d.isoformat(), snip))
    return out


def analyse(text):
    """Everything this study keeps about one statement's visible text."""
    o = cs.statement_dates(text)
    n = new_dates(text)
    pm = planned_matches(text)
    return {"text_chars": len(text), "text_sha256": cs.sha256(text.encode("utf-8")),
            "old_review": o[0], "old_prepared": o[1], "old_date": o[2], "old_source": o[3],
            "new_review": n[0], "new_prepared": n[1], "new_date": n[2], "new_source": n[3],
            "planned_n": len(pm), "planned_dates": ";".join(d for d, _ in pm),
            "future_phrases": len(FUTURE_RE.findall(" ".join(text.split()))),
            "snippets": pm}


# ---------------------------------------------------------------- the frame

def read_table(path):
    with open(path, "rb") as f:
        data = f.read()
    return list(csv.DictReader(io.StringIO(data.decode("utf-8")))), cs.sha256(data)


def build_frame(tables):
    """tables: [(source, rows)]. One item per distinct statement address with status ok (the
    first row's census date and text hash kept), sorted by address. Returns (items, counts)."""
    items = collections.OrderedDict()
    counts = {"ok_rows": {}, "withheld": 0}
    for source, rows in tables:
        oks = [r for r in rows if r.get("status") == "ok"]
        counts["ok_rows"][source] = len(oks)
        for r in oks:
            url = (r.get("statement_url") or "").strip()
            if not url.lower().startswith(("http://", "https://")) or cs.GUARD_RE.search(url):
                counts["withheld"] += 1
                continue
            if url not in items:
                items[url] = {"url": url, "sources": [], "census_date": r.get("statement_date", ""),
                              "census_sha256": r.get("text_sha256", "")}
            if source not in items[url]["sources"]:
                items[url]["sources"].append(source)
    out = []
    for url in sorted(items):
        it = dict(items[url])
        it["sources"] = ";".join(it["sources"])
        out.append(it)
    return out, counts


def frame_ok(items, counts):
    return (counts["ok_rows"] == TABLE_OK_ROWS
            and F1_MIN_URLS <= len(items) <= F1_MAX_URLS)


def crawl_order(items):
    return sorted(items, key=lambda r: cs.sha256((CRAWL_SEED + r["url"]).encode("utf-8")))


# ---------------------------------------------------------------- reading

def blank(item):
    out = dict(item)
    for c in COLUMNS:
        out.setdefault(c, "")
    out.update(status="", retried=0, text_chars=0, text_same=0, planned_n=0, future_phrases=0,
               snippets=[])
    return out


def read_one(item, get=stc.http_get, delay=1.0, sleep=time.sleep):
    """Read one statement address once (one retry after 429 or 503), robots.txt honoured."""
    out = blank(item)
    url = item["url"]
    allowed = stc.robots_checker(get)
    if not allowed(url):
        out["status"] = "robots"
        return out
    st, final, ctype, body = get(url)
    sleep(delay)
    if st in RETRY_STATUSES:
        out["retried"] = 1
        sleep(RETRY_PAUSE)
        st, final, ctype, body = get(url)
        sleep(delay)
    if st != 200:
        out["status"] = "http_%d" % st
        return out
    if not stc.is_html(ctype, body):
        out["status"] = "not_html"
        return out
    text = stc.visible_text(body, ctype)
    if not cs.is_statement(text):
        out.update(status="not_statement", text_chars=len(text))
        return out
    out.update(analyse(text))
    out["status"] = "ok"
    out["text_same"] = int(out["text_sha256"] == item.get("census_sha256", ""))
    return out


def _read_or_skip(item, deadline, kw):
    if deadline and time.time() > deadline:
        r = blank(item)
        r["status"] = "not_started"
        return r
    return read_one(item, **kw)


def crawl(items, workers=8, deadline=None, **kw):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_read_or_skip, it, deadline, kw) for it in items]
        for i, fut in enumerate(futures, 1):
            try:
                out.append(fut.result())
            except Exception as e:  # one address's crash is recorded, never fatal
                r = blank(items[i - 1])
                r["status"] = "crash"
                r["old_source"] = str(e)[:80]
                out.append(r)
            if i % 50 == 0:
                print("%d/%d addresses" % (i, len(futures)), flush=True)
    return out


# ---------------------------------------------------------------- grading

def pct(k, n):
    return round(100.0 * k / n, 2) if n else None


def stale_share(rows, key):
    dated = [r for r in rows if r.get(key)]
    old = [r for r in dated if r[key] < STALE_BEFORE]
    return len(old), len(dated)


def grade(rows, frame_is_ok=True):
    """(measures, gates, predictions) from the rows (as written to rows.csv or read back)."""
    n = len(rows)
    read = [r for r in rows if r.get("status") == "ok"]
    plan = [r for r in read if int(r.get("planned_n") or 0) > 0]
    changed = [r for r in read if r.get("old_date") != r.get("new_date")]
    dated_old = [r for r in read if r.get("old_date")]
    flipped = [r for r in dated_old if r["old_date"] >= STALE_BEFORE
               and (not r.get("new_date") or r["new_date"] < STALE_BEFORE)]
    by_source = {}
    for src, _ in TABLES:
        rs = [r for r in read if src in (r.get("sources") or "").split(";")]
        ko, no = stale_share(rs, "old_date")
        kn, nn = stale_share(rs, "new_date")
        po, pn = pct(ko, no), pct(kn, nn)
        by_source[src] = {"read": len(rs), "old_stale": ko, "old_dated": no, "old_pct": po,
                          "new_stale": kn, "new_dated": nn, "new_pct": pn,
                          "diff_pp": (round(abs(pn - po), 2) if po is not None and pn is not None
                                      else None)}
    measures = {"F1_urls": n,
                "G1_read": cs.share(len(read), n),
                "Q1_planned_of_read": cs.share(len(plan), len(read)),
                "changed_date_of_read": cs.share(len(changed), len(read)),
                "Q2_flipped_of_dated": cs.share(len(flipped), len(dated_old)),
                "Q3_by_census": by_source}
    gates = {"F1_frame": bool(frame_is_ok),
             "G1_read": bool(n) and len(read) / n >= G1_MIN_READ}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("Q1", "Q2", "Q3", "Q4")}
    q3_ok = all(v["old_dated"] >= Q3_MIN_PAGES and v["new_dated"] >= Q3_MIN_PAGES
                for v in by_source.values())
    preds = {"Q1": len(plan) / len(read) <= Q1_MAX_PLANNED,
             "Q2": (len(flipped) / len(dated_old) <= Q2_MAX_FLIPPED
                    if len(dated_old) >= Q2_MIN_PAGES else None),
             "Q3": (all(v["diff_pp"] <= Q3_MAX_PP for v in by_source.values()) if q3_ok else None),
             "Q4": None}  # graded by reading planned.csv (see PREREG.md)
    return measures, gates, preds


def described(rows):
    """Reported, not graded."""
    read = [r for r in rows if r.get("status") == "ok"]
    plan = [r for r in read if int(r.get("planned_n") or 0) > 0]
    years = collections.Counter()
    for r in plan:
        for d in (r.get("planned_dates") or "").split(";"):
            if d:
                years[d[:4]] += 1
    return {
        "status": cs.tally(rows, "status"),
        "retried": sum(1 for r in rows if int(r.get("retried") or 0)),
        "text_same_as_census": sum(1 for r in read if int(r.get("text_same") or 0)),
        "old_date_same_as_census": sum(1 for r in read
                                       if r.get("old_date") == r.get("census_date")),
        "future_phrase_pages": sum(1 for r in read if int(r.get("future_phrases") or 0) > 0),
        "planned_phrases": sum(int(r.get("planned_n") or 0) for r in read),
        "planned_year": dict(sorted(years.items())),
        "planned_pages_by_census": {src: sum(1 for r in plan
                                             if src in (r.get("sources") or "").split(";"))
                                    for src, _ in TABLES},
        "old_undated": sum(1 for r in read if not r.get("old_date")),
        "new_undated": sum(1 for r in read if not r.get("new_date")),
        "old_source": cs.tally([r for r in read if r.get("old_date")], "old_source"),
        "new_source": cs.tally([r for r in read if r.get("new_date")], "new_source"),
    }


# ---------------------------------------------------------------- the run

def planned_rule_matches_release(fetch=cs.fetch_bytes):
    """True when release v0.7.0 of a11y-statement-check still has this exact planned-date rule."""
    try:
        remote = fetch(RELEASE_070_URL)
    except Exception:
        return False
    line = ('PLANNED_RE = re.compile(r"%s", re.I)' % PLANNED_PATTERN).encode("utf-8")
    return line in remote and b"PLANNED_WINDOW = 25" in remote


def write_tables(out_dir, rows):
    """rows.csv (one row per address, sorted) and planned.csv (one row per planned date)."""
    rows = sorted(rows, key=lambda r: r["url"])
    files = {}
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([r.get(c, "") for c in COLUMNS])
    snips = io.StringIO()
    ws = csv.writer(snips, lineterminator="\n")
    ws.writerow(SNIPPET_COLUMNS)
    k = 0
    for r in rows:
        for d, s in r.get("snippets") or []:
            ws.writerow([r["url"], d, s])
            k += 1
    for name, text, n in (("rows.csv", buf.getvalue(), len(rows)),
                          ("planned.csv", snips.getvalue(), k)):
        data = text.encode("utf-8")
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)
        files[name] = {"rows": n, "bytes": len(data), "sha256": cs.sha256(data)}
    return files


def result_text(result):
    lines = ["planned_dates %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("frame", "crawl", "tables"):
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


def main(argv=None, fetch=cs.fetch_bytes, get=stc.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)),
                        help="the repository folder holding the plan and the two tables")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--max-minutes", type=float, default=60)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "reader_version": cs.__version__,
              "checker_version": stc.__version__, "gates": {}, "files": {}}

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("planned_dates: %s" % status)
        return 0

    with open(os.path.join(args.root, *PREREG_PATH.split("/")), "rb") as f:
        prereg = f.read()
    result["files"][PREREG_PATH] = cs.sha256(prereg)
    result["gates"]["P0_prereg"] = b"Q4" in prereg
    result["gates"]["P0_reader"] = (cs.__version__ == COUNCIL_STOCK_VERSION
                                    and stc.__version__ == cs.CHECKER_VERSION
                                    and cs.checker_matches_release(here, fetch))
    result["gates"]["P0_planned_rule"] = planned_rule_matches_release(fetch)
    if not all(result["gates"].values()):
        return finish("not_run")  # no statement was read
    tables = []
    for source, path in TABLES:
        rows, digest = read_table(os.path.join(args.root, *path.split("/")))
        result["files"][path] = digest
        tables.append((source, rows))
    items, counts = build_frame(tables)
    ok_frame = frame_ok(items, counts)
    result["frame"] = dict(counts, urls=len(items),
                           both=sum(1 for it in items if ";" in it["sources"]))
    if not ok_frame:
        result["gates"]["F1_frame"] = False
        return finish("not_run")  # nothing was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(crawl_order(items), workers=args.workers, deadline=deadline, get=get,
                 sleep=sleep, delay=args.delay)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers, "delay": args.delay}
    result["tables"] = write_tables(args.out_dir, read)
    measures, gates, preds = grade(read, ok_frame)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(result["gates"].values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
