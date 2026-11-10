# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""council_reread 0.1.0: two months on, do the UK council accessibility statements that council-stock read carry a newer date?

Pre-registered in results/uk-councils/REREAD-PREREG.md on 2026-11-10, before any page is read for
it. The panel is fixed: the 284 statements that council_stock.py 0.1.0 found and read on
2026-11-10 (results/uk-councils/hosts.csv, unchanged), 105 of them dated before 2025-11-01. In
wave J (2027-01-11 to 2027-01-31, and never outside it) each statement is read again at the
address saved in November (robots.txt honoured, one request at a time, a pause after each); if
that address no longer serves a statement, the council's home page is searched again with
council_stock.py's own reader. Every statement is read with the same pinned code as in November
(council_stock.py 0.1.0 and statement_template_check.py 0.3.0, compared by SHA-256 with the hashes
the November run recorded), so a changed date is a change on the page, not in the reader.

It counts what the statements say. It does not test whether a website is accessible, and nothing
here calls a council in breach. No page text is stored, only a hash, rule ids, dates and counts.
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Standard library only.
"""

import argparse
import collections
import concurrent.futures
import csv
import datetime
import hashlib
import io
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import council_stock as cs  # noqa: E402  (0.1.0, unchanged; it imports statement_template_check 0.3.0)

stc = cs.stc
__version__ = "0.1.0"

PREREG_PATH = "results/uk-councils/REREAD-PREREG.md"
TABLE_PATH = "results/uk-councils/hosts.csv"
RESULT_PATH = "results/uk-councils/result.json"
TABLE_SHA256 = "d2f696ed215882058bab2c6c3a58155a4332e9523193d472783cbe9dc5835905"
TABLE_BYTES = 99491
TABLE_ROWS = 379
PANEL_FOUND = 284               # statements read on 2026-11-10
PANEL_STALE = 105               # of them dated before cs.STALE_BEFORE (2025-11-01)
PINNED = (("council_stock.py", "0.1.0"), ("statement_template_check.py", "0.3.0"))
WAVE = "J"
WAVE_START = datetime.date(2027, 1, 11)
WAVE_END = datetime.date(2027, 1, 31)
CRAWL_SEED = "council-reread-2027-01"
NEW_STALE_BEFORE = "2026-01-01"  # more than a year before the wave

# Pre-registered (REREAD-PREREG.md). Changing any of these after the wave voids the test.
G1_MIN_REREAD = 0.80            # G1: share of the 284 statements read again
R1_MAX_NEWER = 0.20             # R1: share of re-read stale statements with a later date
R1_MIN_PAGES = 60
R2_MIN_OLD = 0.35               # R2: share of dated re-read statements dated before 2026-01-01
R2_MIN_PAGES = 150
R3_MAX_TO_22 = 0.15             # R3: share of re-read 2.1 statements that now name 2.2
R3_MIN_PAGES = 50

READ_KEYS = ("text_chars", "text_sha256", "placeholder", "placeholder_ids", "highest",
             "review_date", "prepared_date", "statement_date", "date_source")
BOOLS = ("retried", "robots_blocked", "url_changed", "text_changed", "placeholder", "newer",
         "date_lost")
COLUMNS = ["host", "name", "kind", "authorities", "nov_statement_date", "nov_highest",
           "nov_text_sha256", "nov_statement_url", "status", "found_by", "saved_status",
           "fallback_status", "retried", "robots_blocked", "statement_url", "url_changed",
           "text_chars", "text_sha256", "text_changed", "placeholder", "placeholder_ids",
           "highest", "review_date", "prepared_date", "statement_date", "date_source", "newer",
           "date_lost"]
GROUPS = ("stale", "due", "fresh", "undated")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- the panel

def read_table(path):
    """(rows, ok): November's hosts table, flags as booleans, and whether its bytes are the ones
    registered (line endings aside)."""
    with open(path, "rb") as f:
        data = f.read()
    rows = cs.typed(list(csv.DictReader(io.StringIO(data.decode("utf-8")))))
    ok = (TABLE_SHA256 in (sha256(data), sha256(cs.normalize(data)))
          and len(cs.normalize(data)) == TABLE_BYTES and len(rows) == TABLE_ROWS)
    return rows, ok


def panel(rows):
    """The statements read in November (status ok)."""
    return [r for r in rows if r.get("status") == "ok"]


def nov_group(r):
    """stale: dated before 2025-11-01; due: dated 2025-11-01 to 2025-12-31 (a year old during
    the wave); fresh: dated 2026 or later; undated: no date in November."""
    d = r.get("nov_statement_date") or ""
    if not d:
        return "undated"
    if d < cs.STALE_BEFORE:
        return "stale"
    if d < NEW_STALE_BEFORE:
        return "due"
    return "fresh"


def crawl_order(rows):
    return sorted(rows, key=lambda r: sha256((CRAWL_SEED + r["host"]).encode("utf-8")))


def pins_match(here):
    """True when council_stock.py and statement_template_check.py are the versions November ran,
    byte for byte (line endings aside), by the hashes in November's result.json."""
    try:
        with open(os.path.join(here, *RESULT_PATH.split("/")), encoding="utf-8") as f:
            ran = json.load(f)["files"]
        for name, version in PINNED:
            with open(os.path.join(here, name), "rb") as f:
                data = f.read()
            if ran.get(name) not in (sha256(data), sha256(cs.normalize(data))):
                return False
    except (OSError, ValueError, KeyError):
        return False
    return cs.__version__ == PINNED[0][1] and stc.__version__ == PINNED[1][1]


# ---------------------------------------------------------------- one statement

def start(row):
    return {"host": row["host"], "name": row.get("name", ""), "kind": row.get("kind", ""),
            "authorities": row.get("authorities", ""),
            "nov_statement_date": row.get("statement_date", ""),
            "nov_highest": row.get("highest", ""), "nov_text_sha256": row.get("text_sha256", ""),
            "nov_statement_url": row.get("statement_url", ""), "status": "", "found_by": "",
            "saved_status": "", "fallback_status": "", "retried": False, "robots_blocked": False,
            "statement_url": "", "url_changed": False, "text_chars": 0, "text_sha256": "",
            "text_changed": False, "placeholder": False, "placeholder_ids": "", "highest": "",
            "review_date": "", "prepared_date": "", "statement_date": "", "date_source": "",
            "newer": False, "date_lost": False}


def read_saved(url, get, allowed, delay, sleep):
    """(status, retried, robots_blocked, final_url, text) for November's address; text is ''
    unless it still serves a statement (council_stock's test, unchanged)."""
    if not url or url == "[withheld]":
        return "", False, False, "", ""
    if not allowed(url):
        return "robots", False, True, "", ""
    s, f, c, b = get(url)
    sleep(delay)
    retried = False
    if s in cs.RETRY_STATUSES:
        retried = True
        sleep(cs.RETRY_PAUSE)
        s, f, c, b = get(url)
        sleep(delay)
    f = f or url
    if s != 200 or not stc.is_html(c, b):
        return str(s), retried, False, f, ""
    if urllib.parse.urlsplit(f).path in ("", "/"):
        return "home", retried, False, f, ""
    text = stc.visible_text(b, c)
    if not cs.is_statement(text):
        return "not_statement", retried, False, f, ""
    return "200", retried, False, f, text


def reread_one(row, get=stc.http_get, delay=1.0, sleep=time.sleep):
    """November's address first; if it no longer serves a statement, council_stock.read_one."""
    out = start(row)
    allowed = stc.robots_checker(get)
    st, retried, blocked, final, text = read_saved(row.get("statement_url", ""), get, allowed,
                                                   delay, sleep)
    out.update(saved_status=st, retried=retried, robots_blocked=blocked)
    if text:
        out.update(status="ok", found_by="saved",
                   statement_url="[withheld]" if cs.GUARD_RE.search(final) else final)
        d = cs.read_statement(text)
        out.update({k: d[k] for k in READ_KEYS})
    else:
        r = cs.read_one({k: row.get(k, "") for k in ("host", "name", "gss", "kind", "authorities")},
                        get=get, delay=delay, sleep=sleep)
        out["fallback_status"] = r["status"]
        out["retried"] = out["retried"] or bool(r.get("retried"))
        out["robots_blocked"] = out["robots_blocked"] or bool(r.get("robots_blocked"))
        if r["status"] == "ok":
            out.update(status="ok", found_by="rediscovered:" + r["found_by"],
                       statement_url=r["statement_url"])
            out.update({k: r[k] for k in READ_KEYS})
        else:
            out["status"] = "not_read"
    if out["status"] == "ok":
        out["url_changed"] = (out["statement_url"].rstrip("/")
                              != out["nov_statement_url"].rstrip("/"))
        out["text_changed"] = out["text_sha256"] != out["nov_text_sha256"]
        nov, now = out["nov_statement_date"], out["statement_date"]
        out["newer"] = bool(nov and now and now > nov)
        out["date_lost"] = bool(nov and not now)
    return out


def crawl(rows, workers=4, deadline=None, **kw):
    def one(r):
        if deadline and time.time() > deadline:
            o = start(r)
            o["status"] = "not_started"
            return o
        return reread_one(r, **kw)

    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, r) for r in rows]
        for i, fut in enumerate(futures, 1):
            try:
                out.append(fut.result())
            except Exception as e:  # one host's crash is recorded, never fatal
                o = start(rows[i - 1])
                o.update(status="crash", fallback_status=str(e)[:80])
                out.append(o)
            if i % 50 == 0:
                print("%d/%d statements" % (i, len(futures)), flush=True)
    return out


# ---------------------------------------------------------------- grading

def typed(rows):
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def ok(r):
    return r.get("status") == "ok"


def stale_now(r):
    return bool(r.get("statement_date")) and r["statement_date"] < NEW_STALE_BEFORE


def grade(rows, pins_ok=True):
    n = len(rows)
    read = [r for r in rows if ok(r)]
    sp = [r for r in rows if nov_group(r) == "stale"]
    sr = [r for r in sp if ok(r)]
    newer = [r for r in sr if r.get("newer")]
    dated = [r for r in read if r.get("statement_date")]
    old = [r for r in dated if stale_now(r)]
    v21 = [r for r in read if r.get("nov_highest") == "2.1"]
    to22 = [r for r in v21 if r.get("highest") == "2.2"]
    measures = {"F1_panel": n, "F1_stale_panel": len(sp),
                "G1_reread": cs.share(len(read), n),
                "R1_newer_of_stale_reread": cs.share(len(newer), len(sr)),
                "R2_before_2026_of_dated": cs.share(len(old), len(dated)),
                "R3_to_wcag22_of_21": cs.share(len(to22), len(v21))}
    gates = {"F1_panel": bool(pins_ok) and n == PANEL_FOUND and len(sp) == PANEL_STALE,
             "G1_reread": bool(n) and len(read) / n >= G1_MIN_REREAD}
    if not all(gates.values()):
        return measures, gates, {"R1": None, "R2": None, "R3": None}
    preds = {"R1": (len(newer) / len(sr) <= R1_MAX_NEWER) if len(sr) >= R1_MIN_PAGES else None,
             "R2": (len(old) / len(dated) >= R2_MIN_OLD) if len(dated) >= R2_MIN_PAGES else None,
             "R3": (len(to22) / len(v21) <= R3_MAX_TO_22) if len(v21) >= R3_MIN_PAGES else None}
    return measures, gates, preds


def described(rows):
    """Reported, not graded."""
    read = [r for r in rows if ok(r)]
    groups = {}
    for g in GROUPS:
        rs = [r for r in rows if nov_group(r) == g]
        rd = [r for r in rs if ok(r)]
        groups[g] = {"panel": len(rs), "reread": len(rd),
                     "newer": sum(1 for r in rd if r.get("newer")),
                     "dated_now": sum(1 for r in rd if r.get("statement_date")),
                     "text_changed": sum(1 for r in rd if r.get("text_changed"))}
    kinds = {}
    for kind in sorted(set(r.get("kind", "") for r in rows)):
        rs = [r for r in rows if r.get("kind", "") == kind and nov_group(r) == "stale"]
        rd = [r for r in rs if ok(r)]
        kinds[kind] = {"stale": len(rs), "reread": len(rd),
                       "newer": sum(1 for r in rd if r.get("newer"))}
    newer = [r for r in read if r.get("newer")]
    return {
        "status": cs.tally(rows, "status"),
        "found_by": cs.tally(read, "found_by"),
        "saved_status": cs.tally(rows, "saved_status"),
        "fallback_status": cs.tally([r for r in rows if r.get("fallback_status")],
                                    "fallback_status"),
        "url_changed": sum(1 for r in read if r.get("url_changed")),
        "text_changed": sum(1 for r in read if r.get("text_changed")),
        "text_changed_same_date": sum(1 for r in read if r.get("text_changed")
                                      and r.get("statement_date") == r.get("nov_statement_date")),
        "date_lost": sum(1 for r in read if r.get("date_lost")),
        "date_earlier": sum(1 for r in read if r.get("statement_date")
                            and r.get("nov_statement_date")
                            and r["statement_date"] < r["nov_statement_date"]),
        "newer_month": cs.tally([{"m": r["statement_date"][:7]} for r in newer], "m"),
        "statement_year": cs.tally([{"y": r["statement_date"][:4]} for r in read
                                    if r.get("statement_date")], "y"),
        "highest": cs.tally(read, "highest"),
        "placeholder_hosts": sorted(r["host"] for r in read if r.get("placeholder")),
        "placeholder_ids": cs.tally_ids([r for r in read if r.get("placeholder")],
                                        "placeholder_ids"),
        "robots_blocked": sum(1 for r in rows if r.get("robots_blocked")),
        "retried": sum(1 for r in rows if r.get("retried")),
        "by_group": groups,
        "stale_by_kind": kinds,
    }


# ---------------------------------------------------------------- the run

def write_table(out_dir, rows):
    """reread.csv, sorted by host."""
    rows = sorted(rows, key=lambda r: r["host"])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([r.get(c, "") for c in COLUMNS])
    data = buf.getvalue().encode("utf-8")
    with open(os.path.join(out_dir, "reread.csv"), "wb") as f:
        f.write(data)
    return {"file": "reread.csv", "rows": len(rows), "bytes": len(data), "sha256": sha256(data)}


def result_text(result):
    lines = ["council_reread %s (wave %s)" % (result["version"], result["wave"]),
             "status: %s" % result["status"],
             "today: %s" % result["today"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("panel", "crawl", "table"):
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


def main(argv=None, get=stc.http_get, sleep=time.sleep, today=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-minutes", type=float, default=90)
    args = parser.parse_args(argv)
    today = today if today is not None else datetime.datetime.now(datetime.timezone.utc).date()
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "wave": WAVE, "today": today.isoformat(), "gates": {},
              "files": {}}
    for name in ("council_reread.py", "council_stock.py", "statement_template_check.py",
                 PREREG_PATH, TABLE_PATH):
        try:
            with open(os.path.join(here, *name.split("/")), "rb") as f:
                result["files"][name] = sha256(f.read())
        except OSError:
            result["files"][name] = ""

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("council_reread: %s" % status)
        return 0

    try:
        with open(os.path.join(here, *PREREG_PATH.split("/")), "rb") as f:
            prereg = f.read()
    except OSError:
        prereg = b""
    result["gates"]["P0_prereg"] = b"R3" in prereg
    result["gates"]["P0_pins"] = pins_match(here)
    result["gates"]["W1_window"] = WAVE_START <= today <= WAVE_END
    if not all(result["gates"].values()):
        return finish("not_run")  # no council website was read
    rows, table_ok = read_table(os.path.join(here, *TABLE_PATH.split("/")))
    pnl = panel(rows)
    result["panel"] = {"rows": len(rows), "found": len(pnl), "table_ok": table_ok,
                       "stale": sum(1 for r in pnl if cs.stale(r))}
    pins_ok = table_ok and len(pnl) == PANEL_FOUND and result["panel"]["stale"] == PANEL_STALE
    if not pins_ok:
        result["gates"]["F1_panel"] = False
        return finish("not_run")  # nothing was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(crawl_order(pnl), workers=args.workers, deadline=deadline, get=get, sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    result["table"] = write_table(args.out_dir, read)
    measures, gates, preds = grade(read, pins_ok)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(gates.values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
