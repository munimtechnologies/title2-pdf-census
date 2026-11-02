"""statement_reread: do the 808 accessibility pages read in 2026 say anything different in 2027?

The pre-registered test in results/statement-reread/PREREG.md. In October-November 2026 the
a11y-pages census (results/a11y-pages) read the accessibility pages linked from the home pages of
1,657 US cities and counties of 50,000 or more: 808 pages, of which 283 named only WCAG 2.0 and
280 carried the stock sentence "We work to comply with Section 508 as well as WCAG 2.0 A and AA
...". The ADA Title II rule adopts WCAG 2.1 AA, and its first compliance date (for these
governments) is April 26, 2027. This script re-reads the same 808 page addresses in two waves:

  J  2027-01-11 to 2027-02-28 (about three months before the date)
  M  2027-05-03 to 2027-06-30 (just after it)

and grades the predictions written for that wave. It refuses to fetch anything outside its
wave's window, until results/statement-reread/PREREG.md is on main, or unless main's copies of
statement_reread.py, statement_check.py and a11y_pages.py are byte for byte the files beside it.

Reads public pages only, honouring robots.txt, one request per page plus robots.txt, under the
User-Agent of statement_check.py, which names Munim, Inc. and an email. Stores no page text
beyond the short snippet around the first WCAG version named, with emails and phones removed.

Standard library only. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import concurrent.futures
import csv
import datetime
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a11y_pages as ap  # noqa: E402
import statement_check as sc  # noqa: E402

__version__ = "0.1.0"

REPO_RAW = "https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/main/"
PREREG_PATH = "results/statement-reread/PREREG.md"
PINNED = ("statement_reread.py", "statement_check.py", "a11y_pages.py")
PANEL_COMMIT = "ae117d0332fa1da570e2efc9ad8fda7e609c4275"
PANEL_URL = ("https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/%s/"
             "results/a11y-pages/a11y-pages.csv" % PANEL_COMMIT)
STOCK_2026 = "We work to comply with Section 508 as well as"  # as counted in results/a11y-pages

# Pre-registered (PREREG.md). Changing any of these after a wave has run voids that wave.
WAVES = {"J": ("2027-01-11", "2027-02-28"), "M": ("2027-05-03", "2027-06-30")}
PANEL_ROWS, PANEL_PAGES, PANEL_STOCK, PANEL_ONLY20 = 1657, 808, 280, 283
MIN_READABLE = 600
MIN_GROUP = 200
THRESHOLDS = {"J": {"P1": 0.85, "P2": 0.80, "P3": 0.45},
              "M": {"P1": 0.70, "P2": 0.65, "P3": 0.40, "P4": 0.03}}

TRIES, PAUSE = 40, 90

COLUMNS = ["qid", "name", "kind", "state", "population", "url_2026", "versions_2026",
           "highest_2026", "stock_2026", "title2_2026", "old_date_2026", "new_date_2026",
           "status", "final_url", "text_chars", "text_sha256", "same_text", "versions", "highest",
           "stock", "title2", "date_2026_04_24", "date_2027_04_26", "date_2028_04_26",
           "version_snippet"]


def truthy(v):
    return v is True or str(v) == "True"


def load_panel(data):
    """(all rows, the rows whose page was read in 2026) of the census table."""
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    pages = [r for r in rows if r.get("page_status") == "ok"]
    for r in pages:
        r["stock_2026"] = STOCK_2026 in (r.get("version_snippet") or "")
    return rows, pages


def reread(row, get=sc.http_get, sleep=time.sleep, delay=1.0):
    """One 2026 page read again, with what it says now."""
    out = {k: row.get(k, "") for k in ("qid", "name", "kind", "state", "population")}
    out.update(url_2026=row["page_url"], versions_2026=row.get("versions", ""),
               highest_2026=row.get("highest", ""), stock_2026=bool(row["stock_2026"]),
               title2_2026=truthy(row.get("title2")), old_date_2026=truthy(row.get("old_date")),
               new_date_2026=truthy(row.get("new_date")))
    status, final, text = sc.read_url(row["page_url"], get=get, sleep=sleep, delay=delay)
    if status == "ok" and len(text) < ap.MIN_TEXT:
        status = "short"
    out.update(status=status, final_url=final if status == "ok" else "", text_chars=len(text),
               text_sha256=ap.sha256(text.encode("utf-8")) if text else "")
    if status == "ok":
        c = sc.check_text(text)
        out.update(same_text=out["text_sha256"] == row.get("text_sha256"),
                   versions=c["versions"], highest=c["highest"], stock=c["stock_sentence"],
                   title2=c["title2"], date_2026_04_24=c["date_2026_04_24"],
                   date_2027_04_26=c["date_2027_04_26"], date_2028_04_26=c["date_2028_04_26"],
                   version_snippet=c["version_snippet"])
    return out


def reread_all(pages, workers=16, **kw):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(reread, r, **kw) for r in pages]
        for i, fut in enumerate(futures):
            try:
                out.append(fut.result())
            except Exception as e:  # one page's crash is recorded, never fatal
                r = pages[i]
                out.append({"qid": r.get("qid", ""), "name": r.get("name", ""),
                            "url_2026": r.get("page_url", ""), "stock_2026": r["stock_2026"],
                            "highest_2026": r.get("highest", ""),
                            "title2_2026": truthy(r.get("title2")),
                            "status": "crash: %s" % str(e)[:60]})
    return out


def grade(rows, wave):
    """(measures, predictions) for one wave, over the pages readable in it."""
    t = THRESHOLDS[wave]
    ok = [r for r in rows if r["status"] == "ok"]
    stock = [r for r in ok if r["stock_2026"]]
    only20 = [r for r in ok if r["highest_2026"] == "2.0"]
    versioned = [r for r in ok if r["highest"]]
    kept = sum(1 for r in stock if r["stock"])
    still20 = sum(1 for r in only20 if r["highest"] == "2.0")
    now20 = sum(1 for r in versioned if r["highest"] == "2.0")
    t2_then = sum(1 for r in ok if r["title2_2026"])
    t2_now = sum(1 for r in ok if r["title2"])
    measures = {"P1_stock_kept": ap.share(kept, len(stock)),
                "P2_only20_kept": ap.share(still20, len(only20)),
                "P3_only20_of_versioned_now": ap.share(now20, len(versioned)),
                "P4_title2_2026": ap.share(t2_then, len(ok)),
                "P4_title2_now": ap.share(t2_now, len(ok))}
    preds = {"P1": kept / len(stock) >= t["P1"] if len(stock) >= MIN_GROUP else None,
             "P2": still20 / len(only20) >= t["P2"] if len(only20) >= MIN_GROUP else None,
             "P3": now20 / len(versioned) >= t["P3"] if len(versioned) >= MIN_GROUP else None}
    if "P4" in t:
        preds["P4"] = (t2_now - t2_then) / len(ok) >= t["P4"] if len(ok) >= MIN_READABLE else None
    return measures, preds


def described(rows):
    """Reported, not graded."""
    ok = [r for r in rows if r["status"] == "ok"]

    def moves(rs):
        t = {}
        for r in rs:
            k = "%s->%s" % (r["highest_2026"] or "none", r["highest"] or "none")
            t[k] = t.get(k, 0) + 1
        return dict(sorted(t.items(), key=lambda kv: (-kv[1], kv[0])))
    old = [r for r in ok if r["old_date_2026"]]
    return {"status": ap._tally(rows, "status"),
            "same_text": sum(1 for r in ok if r["same_text"]),
            "moved_to_other_url": sum(1 for r in ok if r["final_url"].rstrip("/")
                                      != r["url_2026"].rstrip("/")),
            "moves_all": moves(ok),
            "moves_stock": moves([r for r in ok if r["stock_2026"]]),
            "moves_only20_not_stock": moves([r for r in ok if r["highest_2026"] == "2.0"
                                             and not r["stock_2026"]]),
            "stock_now_not_2026": sum(1 for r in ok if r["stock"] and not r["stock_2026"]),
            "old_date_2026_pages": len(old),
            "old_date_2026_now_old_only": sum(1 for r in old if r["date_2026_04_24"]
                                              and not r["date_2027_04_26"]),
            "old_only_now": sum(1 for r in ok if r["date_2026_04_24"]
                                and not r["date_2027_04_26"]),
            "date_2027_now": sum(1 for r in ok if r["date_2027_04_26"]),
            "date_2028_now": sum(1 for r in ok if r["date_2028_04_26"])}


def local_bytes(name):
    with open(os.path.join(HERE, name), "rb") as f:
        return f.read()


def wait_for_prereg(fetch=ap.fetch_bytes, sleep=time.sleep, tries=TRIES, pause=PAUSE):
    """(True, attempts) once main holds PREREG.md and the three pinned files, else (False, tries)."""
    local = {n: ap.normalize(local_bytes(n)) for n in PINNED}
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            same = all(ap.normalize(fetch(REPO_RAW + n + "?n=%d" % i)) == local[n]
                       for n in PINNED)
            if b"P1" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r.get("qid", "")):
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def result_text(result):
    lines = ["statement_reread %s wave %s (%s)" % (result["version"], result["wave"],
                                                   result["today"]),
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("panel_rows", "panel_pages", "readable"):
        if k in result:
            lines.append("%s: %s" % (k, result[k]))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    for k, v in sorted((result.get("described") or {}).items()):
        lines.append("%s: %s" % (k, v))
    return "\n".join(lines)


def main(argv=None, fetch=ap.fetch_bytes, get=sc.http_get, sleep=time.sleep, today=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--wave", required=True, choices=sorted(WAVES))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args(argv)
    today = today or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    result = {"version": __version__, "wave": args.wave, "today": today,
              "script_sha256": ap.sha256(local_bytes("statement_reread.py")), "gates": {}}

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("statement_reread: %s" % status)
        return 0 if status == "graded" else 2

    lo, hi = WAVES[args.wave]
    result["gates"]["W_window"] = lo <= today <= hi
    if not result["gates"]["W_window"]:
        return finish("outside wave %s's window (%s to %s); nothing fetched" % (args.wave, lo, hi))
    ok, polls = wait_for_prereg(fetch=fetch, sleep=sleep)
    result["gates"]["P0_prereg_public"] = ok
    result["polls"] = polls
    if not ok:
        return finish("pre-registration or pinned files not on main; nothing fetched")
    data = fetch(PANEL_URL)
    result["panel_sha256"] = ap.sha256(data)
    rows, pages = load_panel(data)
    result["panel_rows"], result["panel_pages"] = len(rows), len(pages)
    stock = sum(1 for r in pages if r["stock_2026"])
    only20 = sum(1 for r in pages if r.get("highest") == "2.0")
    result["gates"]["G1_panel"] = (len(rows), len(pages), stock, only20) == (
        PANEL_ROWS, PANEL_PAGES, PANEL_STOCK, PANEL_ONLY20)
    if not result["gates"]["G1_panel"]:
        result["panel_counts"] = [len(rows), len(pages), stock, only20]
        return finish("panel gate failed; nothing re-read")
    result["started_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out = reread_all(pages, workers=args.workers, get=get, sleep=sleep, delay=args.delay)
    result["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_rows(os.path.join(args.out_dir, "statement-reread-%s.csv" % args.wave), out)
    result["readable"] = sum(1 for r in out if r["status"] == "ok")
    result["gates"]["G2_readable"] = result["readable"] >= MIN_READABLE
    result["described"] = described(out)
    if not result["gates"]["G2_readable"]:
        return finish("readable gate failed; not graded")
    result["measures"], result["predictions"] = grade(out, args.wave)
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
