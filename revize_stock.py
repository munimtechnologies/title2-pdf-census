"""revize_stock 0.1.0: which US local governments serve Revize's stock accessibility statement unfinished?

Pre-registered in results/stock-revize/PREREG.md. Sites built by the vendor Revize carry a stock
accessibility statement at /accessibility_statement/index.php ("1. Our Commitment We aim to follow
the Web Content Accessibility Guidelines (WCAG) 2.1, Level AA ..."). Its placeholders are written in
mixed case ("[Your Agency/Website Name]", "[Contact Email]", "[X business days]", ...), so
template_check.py, which looks for capitalised placeholders, does not flag them. This check asks
every website host in MV2's two census frames for that one address, once, with the census's polite
requests (robots.txt honoured, a pause after each request), and counts the stock statement and the
placeholders left in it.

A placeholder says nothing about whether a website is accessible. Made by MV2 of Munim, Inc. with
AI agents; not yet checked by a person. Apache-2.0.
"""

import argparse
import concurrent.futures
import csv
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's requests, parser and statistics)
import stock153 as s153  # noqa: E402  (host_of, unchanged)
import template_check as tc  # noqa: E402  (the older placeholder flags, for comparison only)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/stock-revize/PREREG.md"
PINNED = ("revize_stock.py", "stock153.py", "template_check.py", "a11y_pages.py")
FRAMES = (("large", "results/a11y-pages/a11y-pages.csv"),
          ("small", "results/small-pages/eligible.csv"))
SAMPLE_PATH = "results/small-pages/rows.csv"
EXPECTED = {"large": 1657, "small": 3588, "sample": 2500}
PROBE_PATH = "/accessibility_statement/index.php"

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
F1_MIN, F1_MAX = 4800, 5245   # F1: website hosts in the frame
G1_MIN_ANSWERED = 0.80        # G1: hosts whose server answered (any HTTP status, or robots.txt)
R1_MIN_STOCK = 30             # R1: at least 30 hosts serve the stock statement
R2_MIN_UNFILLED = 4           # R2: at least 4 still say "[Your Agency/Website Name]"
R3_MIN_SHARE = 0.15           # R3: at least 15% of stock statements keep a placeholder
R3_MIN_PAGES = 20             # R3 is graded only with at least 20 stock statements

# The stock statement: its first section heading followed by its first sentence.
STOCK_RE = re.compile(r"our commitment\s*:?\s*we aim to follow the\s*web content accessibility "
                      r"guidelines", re.I)
OPENER_RE = re.compile(r"is committed to ensuring digital accessibility for all users", re.I)
# The template's six placeholders, as published in it.
PH = (("ph_name", r"\[\s*your\s+agency\s*/\s*website\s+name\s*\]"),
      ("ph_date", r"\[\s*date\s*\]"),
      ("ph_email", r"\[\s*contact\s+email\s*\]"),
      ("ph_phone", r"\[\s*contact\s+phone\s*\]"),
      ("ph_address", r"\[\s*agency\s+address\s*\]"),
      ("ph_days", r"\[\s*x\s+business\s+days\s*\]"))
PH_RE = {k: re.compile(p, re.I) for k, p in PH}
PH_KEYS = tuple(k for k, _ in PH)
# Described only: other bracketed placeholders a template might leave, and a bare token.
OTHER_RE = re.compile(r"\[\s*(?:your|insert|enter|contact|agency|organi[sz]ation|company|name|"
                      r"website|phone|email|address|date|x)\b[^\]\n]{0,40}\]", re.I)
TOKEN_RE = re.compile(r"\b(?:WEBSITE_NAME|ORGANIZATION_NAME|COMPANY_NAME|AGENCY_NAME)\b")

BOOLS = PH_KEYS + ("revize", "stock_page", "opener", "placeholder", "unfilled", "other_bracket",
                   "token", "tc_placeholder", "census_page_rv", "hidden")
COLUMNS = ["cohort", "qid", "name", "kind", "state", "population", "host", "probe_url", "dupes",
           "census", "census_page_rv", "status", "final_url", "text_chars", "text_sha256",
           "revize", "stock_page", "opener"] + list(PH_KEYS) + [
           "placeholder", "unfilled", "n_placeholders", "other_bracket", "other_text", "token",
           "tc_placeholder", "hidden"]
NOT_ANSWERED = ("", "http_0", "crash", "not_started")


# ---------------------------------------------------------------- the frame

def census_info(row, cohort, sample):
    """(census, census_page_rv): did the census read this government's home page, and was the
    accessibility page it found an /accessibility_statement page? Small-frame governments
    outside the census sample are 'not_sampled'."""
    if cohort == "small":
        row = sample.get(row["qid"])
        if row is None:
            return "not_sampled", False
    census = "home_ok" if row.get("home") == "ok" else "home_failed"
    path = ""
    if row.get("page_status") == "ok":
        try:
            path = urllib.parse.urlsplit(row.get("page_url") or "").path.lower()
        except ValueError:
            path = ""
    return census, path.startswith("/accessibility_statement")


def build_frame(large, small, sample_rows):
    """One row per website host: the large frame first, then the small one, each in qid order
    (the stock-153 frame). Returns (frame, dropped): dropped counts rows without a usable host."""
    sample = {r["qid"]: r for r in sample_rows}
    frame, seen, dropped = [], {}, 0
    for cohort, rows in (("large", large), ("small", small)):
        for r in sorted(rows, key=lambda r: r["qid"]):
            host, base = s153.host_of(r.get("website", ""))
            if not host:
                dropped += 1
                continue
            if host in seen:
                seen[host]["dupes"] += 1
                continue
            census, page_rv = census_info(r, cohort, sample)
            out = {"cohort": cohort, "qid": r["qid"], "name": r.get("name", ""),
                   "kind": r.get("kind", ""), "state": r.get("state", ""),
                   "population": r.get("population", ""), "host": host,
                   "probe_url": base + PROBE_PATH, "dupes": 0, "census": census,
                   "census_page_rv": page_rv}
            seen[host] = out
            frame.append(out)
    return frame, dropped


# ---------------------------------------------------------------- one page

def check_text(text):
    """The stock-statement and placeholder flags of one page's visible text."""
    r = {k: bool(PH_RE[k].search(text)) for k in PH_KEYS}
    other = OTHER_RE.search(text)
    r.update(stock_page=bool(STOCK_RE.search(text)), opener=bool(OPENER_RE.search(text)),
             n_placeholders=sum(1 for k in PH_KEYS if r[k]),
             other_bracket=bool(other), other_text=other.group(0)[:60] if other else "",
             token=bool(TOKEN_RE.search(text)),
             tc_placeholder=bool(tc.check_text(text)["placeholder"]))
    r["placeholder"] = r["stock_page"] and r["n_placeholders"] > 0
    r["unfilled"] = r["stock_page"] and r["ph_name"]
    return r


def read_one(row, get=ap.http_get, delay=1.0, sleep=time.sleep):
    """robots.txt first, then the one address, as a11y_pages.py does."""
    out = dict(row)
    out.update(status="", final_url="", text_chars=0, text_sha256="", n_placeholders="",
               other_text="")
    for k in BOOLS:
        if k != "census_page_rv":
            out[k] = ""
    url = row["probe_url"]
    allowed = ap.robots_checker(get, delay, sleep)
    if not allowed(url):
        out["status"] = "robots"
        return out
    status, final, ctype, body = get(url)
    sleep(delay)
    if status != 200:
        out["status"] = "http_%d" % status
        return out
    if not ap.is_html(ctype, body):
        out["status"] = "not_html"
        return out
    text = ap.visible_text(ap.parse(body, ctype))
    out.update(final_url=final or url, text_chars=len(text),
               text_sha256=ap.sha256(text.encode("utf-8")))
    if len(text) < ap.MIN_TEXT:
        out["status"] = "short"
        return out
    out["status"] = "ok"
    out["revize"] = b"revize" in body.lower()
    out.update(check_text(text))
    out["hidden"] = bool(out["placeholder"] and row["census"] == "home_ok" and
                         not row["census_page_rv"])
    return out


def crawl(rows, workers=16, deadline=None, **kw):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_read_or_skip, r, deadline, kw) for r in rows]
        for i, fut in enumerate(futures, 1):
            try:
                out.append(fut.result())
            except Exception as e:  # one host's crash is recorded, never fatal
                r = dict(rows[i - 1])
                r.update(status="crash", final_url=str(e)[:80])
                out.append(r)
            if i % 250 == 0:
                print("%d/%d hosts" % (i, len(futures)), flush=True)
    return out


def _read_or_skip(row, deadline, kw):
    if deadline and time.time() > deadline:
        r = dict(row)
        r["status"] = "not_started"
        return r
    return read_one(row, **kw)


# ---------------------------------------------------------------- grading

def typed(rows):
    """Rows read back from hosts.csv, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def answered(r):
    return r.get("status") not in NOT_ANSWERED


def stock(r):
    return r.get("status") == "ok" and bool(r.get("stock_page"))


def census_group(r):
    if r.get("census") == "not_sampled":
        return "not_sampled"
    if r.get("census") == "home_failed":
        return "home_failed"
    return "found_rv" if r.get("census_page_rv") else "hidden"


def grade(rows):
    n = len(rows)
    ans = [r for r in rows if answered(r)]
    st = [r for r in rows if stock(r)]
    ph = [r for r in st if r.get("placeholder")]
    unfilled = [r for r in st if r.get("unfilled")]
    measures = {"F1_hosts": n,
                "G1_answered": ap.share(len(ans), n),
                "R1_stock_hosts": len(st),
                "R2_unfilled_hosts": len(unfilled),
                "R3_placeholder_of_stock": ap.share(len(ph), len(st))}
    gates = {"F1_frame": F1_MIN <= n <= F1_MAX,
             "G1_answered": bool(n) and len(ans) / n >= G1_MIN_ANSWERED}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("R1", "R2", "R3")}
    preds = {"R1": len(st) >= R1_MIN_STOCK,
             "R2": len(unfilled) >= R2_MIN_UNFILLED,
             "R3": (len(ph) / len(st) >= R3_MIN_SHARE) if len(st) >= R3_MIN_PAGES else None}
    return measures, gates, preds


def described(rows):
    """Reported, not graded."""
    ok = [r for r in rows if r.get("status") == "ok"]
    st = [r for r in rows if stock(r)]
    ph = [r for r in st if r.get("placeholder")]
    out = {"status": {c: ap._tally([r for r in rows if r.get("cohort") == c], "status")
                      for c in ("large", "small")},
           "census": {c: ap._tally([r for r in rows if r.get("cohort") == c], "census")
                      for c in ("large", "small")},
           "ok_pages": len(ok),
           "stock_by_cohort": ap._tally(st, "cohort"),
           "stock_revize_markup": sum(1 for r in st if r.get("revize")),
           "stock_by_census_group": ap._tally([dict(r, g=census_group(r)) for r in st], "g"),
           "placeholder_by_cohort": ap._tally(ph, "cohort"),
           "placeholder_by_census_group": ap._tally([dict(r, g=census_group(r)) for r in ph],
                                                    "g"),
           "placeholder_counts": {k: sum(1 for r in st if r.get(k)) for k in PH_KEYS},
           "n_placeholders": ap._tally(ph, "n_placeholders"),
           "flagged_by_template_check": sum(1 for r in ph if r.get("tc_placeholder")),
           "ok_not_stock_with_placeholder": sum(1 for r in ok if not r.get("stock_page") and
                                                any(r.get(k) for k in PH_KEYS)),
           "ok_other_bracket": sum(1 for r in ok if r.get("other_bracket")),
           "ok_token": sum(1 for r in ok if r.get("token")),
           "opener_on_stock": sum(1 for r in st if r.get("opener")),
           "census_rv_not_stock_now": sum(1 for r in rows if r.get("census_page_rv")
                                          and not stock(r)),
           "flagged": []}
    for r in sorted(ph, key=lambda r: (r["cohort"], r["state"], r["name"], r["qid"])):
        out["flagged"].append([r["cohort"], r["qid"], r["name"], r["state"], r["kind"],
                               "+".join(k[3:] for k in PH_KEYS if r.get(k)), census_group(r)])
    return out


# ---------------------------------------------------------------- the run

def wait_for_prereg(here, fetch=ap.fetch_bytes, sleep=time.sleep, tries=ap.TRIES, pause=ap.PAUSE):
    """(True, attempts) once main holds PREREG.md and the pinned files, else (False, tries)."""
    local = {}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            local[name] = ap.normalize(f.read())
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            same = all(ap.normalize(fetch(REPO_RAW + name + "?n=%d" % i)) == local[name]
                       for name in PINNED)
            if b"R3" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: (r.get("cohort", ""), r.get("qid", ""))):
            w.writerow({c: r.get(c, "") for c in columns})


def result_text(result):
    lines = ["revize_stock %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for name, t in sorted((result.get("tables") or {}).items()):
        lines.append("table %s: rows=%s sha256=%s" % (name, t["rows"], t["sha256"][:12]))
    if "frame" in result:
        lines.append("frame: hosts=%s dropped=%s" % (result["frame"]["hosts"],
                                                     result["frame"]["dropped"]))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    for row in (result.get("described") or {}).get("flagged", []):
        lines.append("  flagged: %s" % " | ".join(row))
    return "\n".join(lines)


def main(argv=None, fetch=ap.fetch_bytes, get=ap.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--max-minutes", type=float, default=150)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "gates": {}, "files": {}, "tables": {}}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            result["files"][name] = ap.sha256(f.read())

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=False)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("revize_stock: %s" % status)
        return 0

    ok, attempts = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["prereg_attempts"] = attempts
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("not_run")  # no government page was read, so the test can run later
    tables = {}
    for name, path in FRAMES + (("sample", SAMPLE_PATH),):
        try:
            data = fetch(REPO_RAW + path + "?n=0")
        except Exception:
            data = b""
        rows = ap.read_cohort(data) if data else []
        result["tables"][name] = {"sha256": ap.sha256(data), "rows": len(rows)}
        tables[name] = rows
    result["gates"]["G0_tables"] = all(len(tables[k]) == v for k, v in EXPECTED.items())
    if not result["gates"]["G0_tables"]:
        return finish("not_run")
    frame, dropped = build_frame(tables["large"], tables["small"], tables["sample"])
    result["frame"] = {"hosts": len(frame), "dropped": dropped}
    if not F1_MIN <= len(frame) <= F1_MAX:
        result["gates"]["F1_frame"] = False
        return finish("not_run")  # nothing was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(frame, workers=args.workers, deadline=deadline, get=get, sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    write_csv(os.path.join(args.out_dir, "hosts.csv"), read, COLUMNS)
    measures, gates, preds = grade(read)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(gates.values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
