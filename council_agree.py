# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""council_agree 0.1.0: do two automated censuses of UK council accessibility statements score the same page?

Pre-registered in results/uk-councils/AGREE-PREREG.md on 2026-11-10. It compares, council by
council, two open tables: Accessibility.build's "State of Accessibility Statements 2026" council
table (measured 2026-09-02, CC BY 4.0, https://accessibility.build/research), which scores each
statement it found against 8 mandatory elements, and MV2's council-stock table
(results/uk-councils/hosts.csv, read 2026-11-10, unchanged). Where both found a statement but at
different addresses, the address Accessibility.build scored is read once more (robots.txt
honoured, one request at a time per council, a pause after each) with the same pinned reader as
November (council_stock.py 0.1.0 and statement_template_check.py 0.3.0), to see whether it is the
statement itself or a page that links to it.

It compares what two automated readers saw. It does not test whether a website is accessible,
says nothing about whether a statement is true, and calls no council in breach. No page text is
stored, only addresses, counts, a version and a date. Made by MV2 of Munim, Inc. with AI agents;
not yet checked by a person. Standard library only.
"""

import argparse
import collections
import concurrent.futures
import csv
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

PREREG_PATH = "results/uk-councils/AGREE-PREREG.md"
TABLE_PATH = "results/uk-councils/hosts.csv"
RESULT_PATH = "results/uk-councils/result.json"
TABLE_SHA256 = "d2f696ed215882058bab2c6c3a58155a4332e9523193d472783cbe9dc5835905"
TABLE_BYTES = 99491
TABLE_ROWS = 379
PINNED = (("council_stock.py", "0.1.0"), ("statement_template_check.py", "0.3.0"))
A_URL = ("https://accessibility.build/api/research/accessibility-statements"
         "?table=councils&format=csv")
A_FILE = "accessibility-build-councils.csv"
A_COLUMNS = ["name", "host", "statementUrl", "percent", "verdict", "mandatoryPassed",
             "mandatoryTotal", "via"]
A_MIN_ROWS, A_MAX_ROWS = 150, 400
A_TOTAL = 8
CRAWL_SEED = "council-agree-2026-11"

# Pre-registered (AGREE-PREREG.md). Changing any of these after the run voids the test.
G1_MIN_BOTH = 120              # G1: councils both tables found a statement for
H1_MIN_DIFF = 0.60             # H1: low-score rows whose address differs from MV2's
H1_MIN_ROWS = 10
H2_MIN_SAME = 0.80             # H2: full-score rows whose address is MV2's
H2_MIN_ROWS = 60
H3_MIN_LINK = 0.60             # H3: re-read low-score pages that link to MV2's statement
H3_MIN_PAGES = 8
H4_MIN_DATED = 0.90            # H4: full-score, same-address rows where MV2's reader took a date
H4_MIN_ROWS = 50

GROUPS = ("low", "partial", "full")
BOOLS = ("both_found", "same_url", "reread", "robots_blocked", "retried", "answered_html",
         "final_is_ours", "is_statement", "links_to_ours")
COLUMNS = ["a_name", "a_host", "a_url", "a_passed", "a_total", "a_group", "a_verdict", "a_via",
           "match", "b_host", "b_status", "b_found_by", "b_url", "b_highest", "b_statement_date",
           "both_found", "same_url", "reread", "reread_status", "robots_blocked", "retried",
           "answered_html", "final_is_ours", "is_statement", "links_to_ours", "reread_chars",
           "reread_highest", "reread_statement_date"]


INTS = ("a_passed", "a_total", "reread_chars")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def typed(rows):
    """Rows read back from agree.csv, with flags as booleans and counts as numbers again."""
    out = []
    for r in rows:
        r = dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS})
        for k in INTS:
            r[k] = int(r.get(k) or 0)
        out.append(r)
    return out


# ---------------------------------------------------------------- the two tables

def read_b(path):
    """(rows, ok): MV2's November hosts table, flags as booleans, and whether its bytes are the
    ones registered (line endings aside)."""
    with open(path, "rb") as f:
        data = f.read()
    rows = cs.typed(list(csv.DictReader(io.StringIO(data.decode("utf-8")))))
    ok = (TABLE_SHA256 in (sha256(data), sha256(cs.normalize(data)))
          and len(cs.normalize(data)) == TABLE_BYTES and len(rows) == TABLE_ROWS)
    return rows, ok


def parse_a(data):
    """(rows, ok, dropped): Accessibility.build's council rows. ok when the header is the one
    registered, the row count is in range and every row is scored out of 8 with a whole number
    of elements. Rows naming the one word the publish lane refuses are dropped and counted."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], False, 0
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != A_COLUMNS:
        return [], False, 0
    rows, dropped, ok = [], 0, True
    for r in reader:
        if any(cs.GUARD_RE.search(r.get(k) or "") for k in ("name", "host", "statementUrl")):
            dropped += 1
            continue
        try:
            p, t = int(r["mandatoryPassed"]), int(r["mandatoryTotal"])
        except (TypeError, ValueError):
            ok = False
            continue
        if t != A_TOTAL or not 0 <= p <= t:
            ok = False
        rows.append(dict(r, passed=p, total=t))
    ok = ok and A_MIN_ROWS <= len(rows) + dropped <= A_MAX_ROWS
    return rows, ok, dropped


def a_copy(rows):
    """The Accessibility.build rows kept (all but dropped ones), in its own columns, as CSV."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(A_COLUMNS)
    for r in rows:
        w.writerow([r.get(c, "") for c in A_COLUMNS])
    return buf.getvalue().encode("utf-8")


def group(passed, total):
    """low: fewer than half the mandatory elements; full: all of them; partial: the rest."""
    if passed == total:
        return "full"
    if 2 * passed < total:
        return "low"
    return "partial"


def norm_url(url):
    """bare host + path, lower case, without a trailing slash, query or fragment ('' if none)."""
    url = (url or "").strip()
    if not url or url == "[withheld]":
        return ""
    try:
        p = urllib.parse.urlsplit(url)
        host = cs.bare(p.hostname)
    except ValueError:
        return ""
    if not host:
        return ""
    return host + urllib.parse.unquote(p.path).lower().rstrip("/")


def url_host(url):
    try:
        return cs.bare(urllib.parse.urlsplit((url or "").strip()).hostname)
    except ValueError:
        return ""


def find_b(a, by_host, b_rows):
    """(MV2 row, how) for one Accessibility.build row: the same host ('host'); else the host, or
    the nearest parent host, of the scored address ('url_host'); else the one MV2 row whose
    statement address has that host ('statement_host'); else (None, 'none')."""
    h = cs.bare((a.get("host") or "").strip())
    if h and h in by_host:
        return by_host[h], "host"
    uh = url_host(a.get("statementUrl"))
    if not uh:
        return None, "none"
    if uh in by_host:
        return by_host[uh], "url_host"
    parents = [r for k, r in by_host.items() if uh.endswith("." + k)]
    if parents:
        return max(parents, key=lambda r: len(r["host"])), "url_host"
    same = [r for r in b_rows if url_host(r.get("statement_url")) == uh]
    if len(same) == 1:
        return same[0], "statement_host"
    return None, "none"


def match(a_rows, b_rows):
    """One joined row per Accessibility.build row, matched by find_b. A second row on an MV2 host
    already taken is kept unmatched as 'duplicate'."""
    by_host = {r["host"]: r for r in b_rows}
    taken, out = set(), []
    for a in a_rows:
        b, how = find_b(a, by_host, b_rows)
        if b is not None and b["host"] in taken:
            b, how = None, "duplicate"
        j = {"a_name": a.get("name", ""), "a_host": a.get("host", ""),
             "a_url": a.get("statementUrl", ""), "a_passed": a["passed"], "a_total": a["total"],
             "a_group": group(a["passed"], a["total"]), "a_verdict": a.get("verdict", ""),
             "a_via": a.get("via", ""), "match": how, "b_host": "", "b_status": "",
             "b_found_by": "", "b_url": "", "b_highest": "", "b_statement_date": "",
             "reread_status": "", "reread_chars": 0, "reread_highest": "",
             "reread_statement_date": ""}
        for k in BOOLS:
            j[k] = False
        if b is not None:
            taken.add(b["host"])
            j.update(b_host=b["host"], b_status=b.get("status", ""),
                     b_found_by=b.get("found_by", ""), b_url=b.get("statement_url", ""),
                     b_highest=b.get("highest", ""),
                     b_statement_date=b.get("statement_date", ""))
            j["both_found"] = j["b_status"] == "ok"
            if j["both_found"]:
                j["same_url"] = (norm_url(j["a_url"]) != ""
                                 and norm_url(j["a_url"]) == norm_url(j["b_url"]))
        out.append(j)
    return out


# ---------------------------------------------------------------- one page

def links_to(body, ctype, page_url, target):
    """True when the page has a link whose address is target (by norm_url)."""
    want = norm_url(target)
    if not want:
        return False
    for href, _ in cs.find_links(body, ctype):
        href = (href or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        try:
            url = urllib.parse.urljoin(page_url, href)
        except ValueError:
            continue
        if norm_url(url) == want:
            return True
    return False


def reread(j, get=stc.http_get, delay=1.0, sleep=time.sleep):
    """Read the address Accessibility.build scored once, with November's pinned reader."""
    j = dict(j, reread=True)
    url = j["a_url"]
    if not norm_url(url) or not url.lower().startswith(("http://", "https://")):
        j["reread_status"] = "bad_url"
        return j
    allowed = stc.robots_checker(get)
    if not allowed(url):
        j.update(reread_status="robots", robots_blocked=True)
        return j
    sleep(delay)
    s, f, c, b = get(url)
    sleep(delay)
    if s in cs.RETRY_STATUSES:
        j["retried"] = True
        sleep(cs.RETRY_PAUSE)
        s, f, c, b = get(url)
        sleep(delay)
    j["reread_status"] = str(s)
    if s != 200 or not stc.is_html(c, b):
        return j
    f = f or url
    text = stc.visible_text(b, c)
    rd = cs.read_statement(text)
    j.update(answered_html=True, final_is_ours=norm_url(f) == norm_url(j["b_url"]),
             is_statement=cs.is_statement(text), links_to_ours=links_to(b, c, f, j["b_url"]),
             reread_chars=len(text), reread_highest=rd["highest"],
             reread_statement_date=rd["statement_date"])
    return j


def crawl_order(rows):
    return sorted(rows, key=lambda r: sha256((CRAWL_SEED + r["b_host"]).encode("utf-8")))


def crawl(rows, workers=4, deadline=None, **kw):
    out = []

    def one(j):
        if deadline and time.time() > deadline:
            return dict(j, reread=True, reread_status="not_started")
        return reread(j, **kw)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, j) for j in rows]
        for i, fut in enumerate(futures):
            try:
                out.append(fut.result())
            except Exception as e:  # one page's crash is recorded, never fatal
                out.append(dict(rows[i], reread=True, reread_status="crash:" + str(e)[:40]))
    return out


# ---------------------------------------------------------------- grading

def share(k, n):
    return cs.share(k, n)


def grade(rows):
    """(measures, gates, predictions) from the joined rows (re-read rows included)."""
    both = [r for r in rows if r["both_found"]]
    low = [r for r in both if r["a_group"] == "low"]
    full = [r for r in both if r["a_group"] == "full"]
    low_diff = [r for r in low if not r["same_url"]]
    low_pages = [r for r in low_diff if r["answered_html"]]
    full_same = [r for r in full if r["same_url"]]
    measures = {
        "A_rows": len(rows),
        "matched": sum(1 for r in rows if r["b_host"]),
        "G1_both_found": len(both),
        "H1_low_diff": share(len(low_diff), len(low)),
        "H2_full_same": share(len(full_same), len(full)),
        "H3_low_links_to_ours": share(sum(1 for r in low_pages if r["links_to_ours"]),
                                      len(low_pages)),
        "H4_full_same_dated": share(sum(1 for r in full_same if r["b_statement_date"]),
                                    len(full_same)),
    }
    gates = {"G1_both_found": len(both) >= G1_MIN_BOTH}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("H1", "H2", "H3", "H4")}

    def pred(m, minimum, n_min):
        if m["n"] < n_min:
            return None
        return m["k"] / m["n"] >= minimum

    preds = {"H1": pred(measures["H1_low_diff"], H1_MIN_DIFF, H1_MIN_ROWS),
             "H2": pred(measures["H2_full_same"], H2_MIN_SAME, H2_MIN_ROWS),
             "H3": pred(measures["H3_low_links_to_ours"], H3_MIN_LINK, H3_MIN_PAGES),
             "H4": pred(measures["H4_full_same_dated"], H4_MIN_DATED, H4_MIN_ROWS)}
    return measures, gates, preds


def tally(rows, key):
    return cs.tally(rows, key)


def described(rows, b_rows):
    """Reported, not graded."""
    both = [r for r in rows if r["both_found"]]
    diff = [r for r in both if not r["same_url"]]
    pages = [r for r in diff if r["answered_html"]]
    a_hosts = set(r["b_host"] for r in rows if r["b_host"])
    by_group = {}
    for g in GROUPS:
        bs = [r for r in both if r["a_group"] == g]
        ds = [r for r in bs if not r["same_url"]]
        ps = [r for r in ds if r["answered_html"]]
        by_group[g] = {"a_rows": sum(1 for r in rows if r["a_group"] == g), "both": len(bs),
                       "same_url": len(bs) - len(ds), "diff_url": len(ds),
                       "b_found_by_hub": sum(1 for r in bs if r["b_found_by"] == "hub"),
                       "b_dated": sum(1 for r in bs if r["b_statement_date"]),
                       "b_wcag22": sum(1 for r in bs if r["b_highest"] == "2.2"),
                       "reread_answered": len(ps),
                       "reread_is_statement": sum(1 for r in ps if r["is_statement"]),
                       "reread_links_to_ours": sum(1 for r in ps if r["links_to_ours"]),
                       "reread_final_is_ours": sum(1 for r in ps if r["final_is_ours"])}
    return {
        "match": tally(rows, "match"),
        "a_group": tally(rows, "a_group"),
        "a_verdict": tally(rows, "a_verdict"),
        "a_via": tally(rows, "a_via"),
        "a_passed": tally(rows, "a_passed"),
        "b_status_of_matched": tally([r for r in rows if r["b_host"]], "b_status"),
        "b_ok_not_in_a": sum(1 for r in b_rows if r.get("status") == "ok"
                             and r["host"] not in a_hosts),
        "by_group": by_group,
        "diff_url_b_found_by": tally(diff, "b_found_by"),
        "diff_url_by_via": tally(diff, "a_via"),
        "reread_status": tally([r for r in rows if r["reread"]], "reread_status"),
        "reread_robots_blocked": sum(1 for r in rows if r["robots_blocked"]),
        "reread_retried": sum(1 for r in rows if r["retried"]),
        "reread_is_statement_and_links": sum(1 for r in pages
                                             if r["is_statement"] and r["links_to_ours"]),
        "reread_not_statement_no_link": sum(1 for r in pages
                                            if not r["is_statement"] and not r["links_to_ours"]),
    }


# ---------------------------------------------------------------- the run

def pins_match(here):
    """True when council_stock.py and statement_template_check.py are the versions November ran,
    byte for byte (line endings aside), by the hashes in November's result.json."""
    try:
        with open(os.path.join(here, *RESULT_PATH.split("/")), encoding="utf-8") as f:
            ran = json.load(f)["files"]
        for name, _ in PINNED:
            with open(os.path.join(here, name), "rb") as f:
                data = f.read()
            if ran.get(name) not in (sha256(data), sha256(cs.normalize(data))):
                return False
    except (OSError, ValueError, KeyError):
        return False
    return cs.__version__ == PINNED[0][1] and stc.__version__ == PINNED[1][1]


def write_table(out_dir, rows):
    """agree.csv, in Accessibility.build's row order."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([r.get(c, "") for c in COLUMNS])
    data = buf.getvalue().encode("utf-8")
    with open(os.path.join(out_dir, "agree.csv"), "wb") as f:
        f.write(data)
    return {"file": "agree.csv", "rows": len(rows), "bytes": len(data), "sha256": sha256(data)}


def result_text(result):
    lines = ["council_agree %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("a_table", "crawl", "table"):
        if k in result:
            lines.append("%s: %s" % (k, json.dumps(result[k], sort_keys=True)))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("measure %s: %s" % (k, json.dumps(v, sort_keys=True)))
    for k, v in sorted((result.get("predictions") or {}).items()):
        lines.append("prediction %s: %s" % (k, {True: "held", False: "failed",
                                               None: "not graded"}[v]))
    d = result.get("described") or {}
    for k in sorted(d):
        lines.append("%s: %s" % (k, json.dumps(d[k], sort_keys=True)))
    return "\n".join(lines)


def main(argv=None, get=stc.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-minutes", type=float, default=60)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "gates": {}, "files": {}}
    for name in ("council_agree.py", "council_stock.py", "statement_template_check.py",
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
        print("council_agree: %s" % status)
        return 0

    try:
        with open(os.path.join(here, *PREREG_PATH.split("/")), "rb") as f:
            prereg = f.read()
    except OSError:
        prereg = b""
    result["gates"]["P0_prereg"] = b"H4" in prereg
    result["gates"]["P0_pins"] = pins_match(here)
    b_rows, b_ok = read_b(os.path.join(here, *TABLE_PATH.split("/")))
    result["gates"]["F1_mv2_table"] = b_ok
    if not all(result["gates"].values()):
        return finish("not_run")  # nothing was read
    allowed = stc.robots_checker(get)
    a_ok, status, body = False, "robots", b""
    if allowed(A_URL):
        status, _, _, body = get(A_URL)
        if status in cs.RETRY_STATUSES:
            sleep(cs.RETRY_PAUSE)
            status, _, _, body = get(A_URL)
    a_rows, a_ok, dropped = parse_a(body) if status == 200 else ([], False, 0)
    kept = a_copy(a_rows)
    result["a_table"] = {"url": A_URL, "status": str(status), "bytes": len(body),
                         "sha256": sha256(body) if body else "", "rows": len(a_rows),
                         "dropped": dropped, "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                          time.gmtime()),
                         "copy": A_FILE, "copy_sha256": sha256(kept)}
    result["gates"]["A1_their_table"] = a_ok
    if not a_ok:
        return finish("not_run")  # no council page was read
    with open(os.path.join(args.out_dir, A_FILE), "wb") as f:
        f.write(kept)
    rows = match(a_rows, b_rows)
    todo = [r for r in rows if r["both_found"] and not r["same_url"]]
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    order = crawl_order(todo)
    results = crawl(order, workers=args.workers, deadline=deadline, get=get, sleep=sleep)
    done = {id(t): r for t, r in zip(order, results)}
    rows = [done.get(id(r), r) for r in rows]
    result["crawl"] = {"started_utc": started, "pages": len(todo), "workers": args.workers,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    result["table"] = write_table(args.out_dir, rows)
    measures, gates, preds = grade(rows)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(rows, b_rows))
    return finish("graded" if all(result["gates"].values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
