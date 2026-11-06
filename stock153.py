"""stock153 0.1.0: which US local governments still serve CivicPlus's stock accessibility page?

Pre-registered in results/stock-153/PREREG.md. MV2's template-pages re-read found 29 accessibility
pages that are still an unedited vendor template ("YOURMUNICIPALITY is committed to ..."); 28 are
on CivicPlus (CivicEngage) sites and all 28 sit at the same address, /153/Accessibility. That
re-read only saw pages the two censuses had found by following links from a home page, in their
samples. This check asks every website host in both census frames (results/a11y-pages/a11y-pages.csv,
governments of 50,000 or more, and results/small-pages/eligible.csv, 10,000 to 49,999) for that one
address, once, with the census's polite requests (robots.txt honoured, a pause after each
request), and flags the template's placeholders with template_check.py's unchanged rules. It
counts, among other things, templates that the census could not have found because the home page
does not link them.

A placeholder says nothing about whether a website is accessible. Made by MV2 of Munim, Inc. with
AI agents; not yet checked by a person. Apache-2.0.
"""

import argparse
import concurrent.futures
import csv
import io
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's requests, parser and statistics)
import template_check as tc  # noqa: E402  (the placeholder flags, unchanged)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/stock-153/PREREG.md"
PINNED = ("stock153.py", "template_check.py", "a11y_pages.py")
FRAMES = (("large", "results/a11y-pages/a11y-pages.csv"),
          ("small", "results/small-pages/eligible.csv"))
SAMPLE_PATH = "results/small-pages/rows.csv"
EXPECTED = {"large": 1657, "small": 3588, "sample": 2500}
PROBE_PATH = "/153/Accessibility"

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
F1_MIN, F1_MAX = 4800, 5245   # F1: website hosts in the frame
G1_MIN_ANSWERED = 0.80        # G1: hosts whose server answered (any HTTP status, or robots.txt)
S1_MIN_FLAGGED = 40           # S1: at least 40 hosts serve a placeholder at /153/Accessibility
S2_MIN_HIDDEN = 5             # S2: at least 5 of them are hidden from the census (see PREREG)
S3_MIN_SHARE = 0.20           # S3: at least 20% of CivicPlus stock accessibility pages are flagged
S3_MIN_PAGES = 50             # S3 is graded only with at least 50 such pages
S4_MIN_PROBED = 800           # S4 is graded only with at least 800 probed hosts in each cohort

BOOLS = tc.FLAGS + ("placeholder", "no_wcag", "stock", "civicplus", "a11y_text", "stock_page",
                    "census_page_153", "hidden")
COLUMNS = ["cohort", "qid", "name", "kind", "state", "population", "host", "probe_url", "dupes",
           "census", "census_page_153", "status", "final_url", "text_chars", "text_sha256",
           "civicplus", "a11y_text", "stock_page", "muni", "template_note", "contact_block",
           "bracket", "bracket_text", "placeholder", "no_wcag", "stock", "hidden"]
NOT_ANSWERED = ("", "http_0", "crash", "not_started")


# ---------------------------------------------------------------- the frame

def host_of(website):
    """(bare host, scheme://netloc) of a census website, or ("", "") if it has no usable host."""
    try:
        p = urllib.parse.urlsplit(ap.normalize_site(website))
        host = (p.hostname or "").lower()
    except ValueError:  # e.g. a withheld address
        return "", ""
    if "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host):
        return "", ""
    return (host[4:] if host.startswith("www.") else host), "%s://%s" % (p.scheme, p.netloc)


def census_info(row, cohort, sample):
    """(census, census_page_153): did the census read this government's home page, and was the
    accessibility page it found a /153/ page? Small-frame governments outside the census sample
    are 'not_sampled'."""
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
    return census, path.startswith("/153/")


def build_frame(large, small, sample_rows):
    """One row per website host: the large frame first, then the small one, each in qid order.
    Returns (frame, dropped) where dropped counts rows without a usable host."""
    sample = {r["qid"]: r for r in sample_rows}
    frame, seen, dropped = [], {}, 0
    for cohort, rows in (("large", large), ("small", small)):
        for r in sorted(rows, key=lambda r: r["qid"]):
            host, base = host_of(r.get("website", ""))
            if not host:
                dropped += 1
                continue
            if host in seen:
                seen[host]["dupes"] += 1
                continue
            census, page153 = census_info(r, cohort, sample)
            out = {"cohort": cohort, "qid": r["qid"], "name": r.get("name", ""),
                   "kind": r.get("kind", ""), "state": r.get("state", ""),
                   "population": r.get("population", ""), "host": host,
                   "probe_url": base + PROBE_PATH, "dupes": 0, "census": census,
                   "census_page_153": page153}
            seen[host] = out
            frame.append(out)
    return frame, dropped


# ---------------------------------------------------------------- reading one address

def read_one(row, get=ap.http_get, delay=1.0, sleep=time.sleep):
    """robots.txt first, then the one address, as a11y_pages.py does."""
    out = dict(row)
    out.update(status="", final_url="", text_chars=0, text_sha256="", bracket_text="")
    for k in BOOLS:
        if k not in ("census_page_153",):
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
    final = final or url
    out.update(final_url=final, text_chars=len(text), text_sha256=ap.sha256(text.encode("utf-8")))
    if len(text) < ap.MIN_TEXT:
        out["status"] = "short"
        return out
    out["status"] = "ok"
    out["civicplus"] = tc.is_civicplus(body)
    out["a11y_text"] = bool(re.search(r"accessib", text, re.I))
    try:
        final_path = urllib.parse.urlsplit(final).path.lower()
    except ValueError:
        final_path = ""
    out["stock_page"] = bool(out["civicplus"] and out["a11y_text"] and
                             final_path.startswith("/153/"))
    out.update(tc.check_text(text))
    out["hidden"] = bool(out["placeholder"] and row["census"] == "home_ok" and
                         not row["census_page_153"])
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


def probed(r):
    """The address itself got an HTTP answer (robots.txt did not stop the request)."""
    return answered(r) and r.get("status") != "robots"


def flagged(r):
    return r.get("status") == "ok" and bool(r.get("placeholder"))


def census_group(r):
    if r.get("census") == "not_sampled":
        return "not_sampled"
    if r.get("census") == "home_failed":
        return "home_failed"
    return "found_153" if r.get("census_page_153") else "hidden"


def grade(rows):
    n = len(rows)
    ans = [r for r in rows if answered(r)]
    flag = [r for r in rows if flagged(r)]
    hidden = [r for r in flag if r.get("hidden")]
    stock = [r for r in rows if r.get("status") == "ok" and r.get("stock_page")]
    stock_flag = [r for r in stock if r.get("placeholder")]
    probe = {c: [r for r in rows if r.get("cohort") == c and probed(r)] for c in ("large", "small")}
    pflag = {c: [r for r in probe[c] if flagged(r)] for c in probe}
    measures = {"F1_hosts": n,
                "G1_answered": ap.share(len(ans), n),
                "S1_flagged_hosts": len(flag),
                "S2_hidden_flagged_hosts": len(hidden),
                "S3_flagged_of_stock_pages": ap.share(len(stock_flag), len(stock)),
                "S4_flagged_of_probed_large": ap.share(len(pflag["large"]), len(probe["large"])),
                "S4_flagged_of_probed_small": ap.share(len(pflag["small"]), len(probe["small"]))}
    gates = {"F1_frame": F1_MIN <= n <= F1_MAX,
             "G1_answered": bool(n) and len(ans) / n >= G1_MIN_ANSWERED}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("S1", "S2", "S3", "S4")}
    s4_ok = all(len(probe[c]) >= S4_MIN_PROBED for c in probe)
    preds = {"S1": len(flag) >= S1_MIN_FLAGGED,
             "S2": len(hidden) >= S2_MIN_HIDDEN,
             "S3": (len(stock_flag) / len(stock) >= S3_MIN_SHARE)
                   if len(stock) >= S3_MIN_PAGES else None,
             "S4": (len(pflag["small"]) / len(probe["small"]) >
                    len(pflag["large"]) / len(probe["large"])) if s4_ok else None}
    return measures, gates, preds


def described(rows):
    """Reported, not graded."""
    ok = [r for r in rows if r.get("status") == "ok"]
    flag = [r for r in rows if flagged(r)]
    out = {"status": {c: ap._tally([r for r in rows if r.get("cohort") == c], "status")
                      for c in ("large", "small")},
           "census": {c: ap._tally([r for r in rows if r.get("cohort") == c], "census")
                      for c in ("large", "small")},
           "ok_pages": len(ok),
           "ok_civicplus": sum(1 for r in ok if r.get("civicplus")),
           "stock_pages": {c: sum(1 for r in ok if r.get("cohort") == c and r.get("stock_page"))
                           for c in ("large", "small")},
           "flagged_by_cohort": ap._tally(flag, "cohort"),
           "flagged_by_census_group": ap._tally([dict(r, g=census_group(r)) for r in flag], "g"),
           "flagged_by_kind": ap._tally(flag, "kind"),
           "flagged_by_state": ap._tally(flag, "state"),
           "flagged_not_civicplus": sum(1 for r in flag if not r.get("civicplus")),
           "flagged_not_stock_page": sum(1 for r in flag if not r.get("stock_page")),
           "flags": {k: sum(1 for r in flag if r.get(k)) for k in tc.FLAGS},
           "stock_sentence_on_stock_pages": sum(1 for r in ok if r.get("stock_page")
                                                and r.get("stock")),
           "no_wcag_on_stock_pages": sum(1 for r in ok if r.get("stock_page") and r.get("no_wcag")),
           "census_153_not_stock_now": sum(1 for r in rows if r.get("census_page_153")
                                           and not (r.get("status") == "ok"
                                                    and r.get("stock_page"))),
           "flagged": []}
    for r in sorted(flag, key=lambda r: (r["cohort"], r["state"], r["name"], r["qid"])):
        out["flagged"].append([r["cohort"], r["qid"], r["name"], r["state"], r["kind"],
                               "+".join(k for k in tc.FLAGS if r.get(k)), census_group(r)])
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
            if b"S4" in prereg and same:
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
    lines = ["stock153 %s" % result["version"],
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
        print("stock153: %s" % status)
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
