"""district_stock 0.1.0: how many US school districts serve an unfinished accessibility statement template at /accessibility-statement?

Pre-registered in results/district-stock/PREREG.md. MV2's district-pages census (results/
district-pages) read 933 school-district accessibility pages found through home-page links and
found 129 still carrying a 2017 statement template's placeholders ("the Your School website",
accessibility@yourschool.com, 555-555-5555), all on sites with Finalsite markup; 123 of the 129
sit at the address /accessibility-statement. This check asks every website host in the census's
full frame (the NCES Common Core of Data 2024-25 districts with a SAIPE 2024 population, built by
the pinned district_pages.py) for that one address, once, with the census's polite requests
(robots.txt honoured, a pause after each request), and reads the page with the census's own
rules (district_check.py, unchanged).

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
import district_check as dc  # noqa: E402  (the district census's page rules, unchanged)
import district_pages as dp  # noqa: E402  (the district census's frame, unchanged)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/district-stock/PREREG.md"
PINNED = ("district_stock.py", "district_pages.py", "district_check.py", "a11y_pages.py",
          "statement_check.py", "template_check.py")
CENSUS_PATH = "results/district-pages/rows.csv"
CENSUS_ROWS = 2500
PROBE_PATH = "/accessibility-statement"
# One district's name contains a word that MV2's publishing tool blocks; it is dropped from the
# frame before anything is read (it is not in the census sample either).
DROP_LEAIDS = ("0903180",)
CRAWL_SEED = "district-stock-2026-11"
RETRY_STATUSES = (429, 503)
RETRY_PAUSE = 30

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
F1_MIN, F1_MAX = 11000, 11700           # F1: website hosts in the frame
F1_BIG_MIN, F1_BIG_MAX = 1250, 1400     # F1: hosts of districts of 50,000 or more people
G1_MIN_ANSWERED = 0.80                  # G1: hosts whose server answered
K1_MIN_HOSTS = 400                      # K1: hosts serving a placeholder page at the address
K2_MIN_UNCOUNTED = 0.15                 # K2: share of sampled such hosts the census did not count
K2_MIN_PAGES = 30
K3_MIN_KEPT = 0.90                      # K3: census placeholder pages here that still have one
K3_MIN_PAGES = 80
K4_MIN_MARKUP = 0.95                    # K4: placeholder pages carrying Finalsite markup
K4_MIN_PAGES = 50

# The 2017 template's first sentence ("To help us make the Your School website a positive place
# for everyone, we've been using the Web Content Accessibility Guidelines (WCAG) 2.0"), filled in
# or not. Described only.
T2017_RE = re.compile(r"a\s+positive\s+place\s+for\s+everyone", re.I)
FINALSITE_MARK = b"finalsite"

BOOLS = ("census_placeholder", "retried", "same_text", "finalsite_markup", "t2017", "t2026",
         "generator", "placeholder", "title2", "uncounted")
COLUMNS = ["leaid", "name", "state", "lea_type", "population", "band", "host", "base", "census",
           "census_placeholder", "status", "retried", "final_url", "text_chars", "text_sha256",
           "same_text", "finalsite_markup", "t2017", "t2026", "generator", "placeholder",
           "placeholder_kinds", "highest", "title2", "uncounted"]
NOT_ANSWERED = ("", "http_0", "crash", "not_started", "bad_url")
NOT_REACHED = NOT_ANSWERED + ("robots", "http_429", "http_503")
OUT_FILES = (("50k+", "hosts-50k.csv"), ("under50k", "hosts-under50k.csv"))


# ---------------------------------------------------------------- the frame

def base_of(website):
    """scheme://netloc of a CCD website, or '' if it cannot be parsed."""
    try:
        p = urllib.parse.urlsplit(ap.normalize_site(website or ""))
    except ValueError:
        return ""
    return "%s://%s" % (p.scheme, p.netloc) if p.netloc else ""


def read_census(data):
    """{LEAID: row} of the district-pages census table (its published rows.csv)."""
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig", errors="replace"))))
    return {r.get("leaid", ""): r for r in rows}


def census_info(leaid, census):
    """(record, census_placeholder, census_sha): what the district census saw for this district.

    record: not_sampled (not in the census sample), home_failed (its home page was not read),
    found_here (the page it read was at /accessibility-statement), found_elsewhere (another
    page) or no_page (home page read, no accessibility page read)."""
    c = census.get(leaid)
    if c is None:
        return "not_sampled", False, ""
    if c.get("home") != "ok":
        return "home_failed", False, ""
    if c.get("page_status") != "ok":
        return "no_page", False, ""
    try:
        path = urllib.parse.urlsplit(c.get("page_url") or "").path.rstrip("/").lower()
    except ValueError:
        path = ""
    record = "found_here" if path == PROBE_PATH else "found_elsewhere"
    return record, dp.truthy(c.get("placeholder")), c.get("text_sha256", "")


def build_frame(frame_rows, census):
    """The census frame (district_pages.build_frame) minus DROP_LEAIDS, with each district's
    census record. Returns (frame, dropped)."""
    out, dropped = [], 0
    for r in frame_rows:
        if r["leaid"] in DROP_LEAIDS:
            dropped += 1
            continue
        rec, cph, sha = census_info(r["leaid"], census)
        row = {k: r.get(k, "") for k in dp.FRAME_COLUMNS if k != "website"}
        row.update(base=base_of(r.get("website", "")), census=rec, census_placeholder=cph,
                   _census_sha=sha)
        out.append(row)
    return out, dropped


def crawl_order(frame):
    """A fixed shuffled order (SHA-256 of seed + LEAID), so neighbouring districts and the
    vendors' shared servers are not asked one after another."""
    return sorted(frame, key=lambda r: dp.hash_key(r["leaid"], CRAWL_SEED))


# ---------------------------------------------------------------- one page

def check_text(text, body=b""):
    """The district census's reading of one page (district_check, unchanged) plus the template
    markers this study describes."""
    d = dc.check_text(text)
    return {"finalsite_markup": FINALSITE_MARK in (body or b"").lower(),
            "t2017": bool(T2017_RE.search(text)), "t2026": bool(d["finalsite_line"]),
            "generator": bool(d["generator_line"]), "placeholder": bool(d["placeholder"]),
            "placeholder_kinds": d["placeholder_kinds"], "highest": d["highest"],
            "title2": bool(d["title2"])}


def read_one(row, get=ap.http_get, delay=1.0, sleep=time.sleep):
    """robots.txt first, then the one address (asked a second time, after a pause, only if the
    server answered 429 or 503)."""
    out = dict(row)
    out.update(status="", retried=False, final_url="", text_chars=0, text_sha256="",
               placeholder_kinds="", highest="")
    for k in BOOLS:
        if k not in ("census_placeholder", "retried"):
            out[k] = False
    if not row.get("base"):
        out["status"] = "bad_url"
        return out
    url = row["base"] + PROBE_PATH
    allowed = ap.robots_checker(get, delay, sleep)
    if not allowed(url):
        out["status"] = "robots"
        return out
    status, final, ctype, body = get(url)
    sleep(delay)
    if status in RETRY_STATUSES:
        out["retried"] = True
        sleep(RETRY_PAUSE)
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
    out.update(check_text(text, body))
    out["same_text"] = bool(row.get("_census_sha")) and out["text_sha256"] == row["_census_sha"]
    out["uncounted"] = bool(out["placeholder"] and row.get("census") != "not_sampled"
                            and not row.get("census_placeholder"))
    return out


def crawl(rows, workers=8, deadline=None, **kw):
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
            if i % 500 == 0:
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
    """Rows read back from the hosts tables, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def answered(r):
    return r.get("status") not in NOT_ANSWERED


def reached(r):
    return r.get("status") not in NOT_REACHED


def flagged(r):
    return r.get("status") == "ok" and bool(r.get("placeholder"))


def grade(rows):
    n = len(rows)
    big = sum(1 for r in rows if r.get("band") == "50k+")
    ans = [r for r in rows if answered(r)]
    ph = [r for r in rows if flagged(r)]
    sampled_ph = [r for r in ph if r.get("census") != "not_sampled"]
    unc = [r for r in sampled_ph if r.get("uncounted")]
    here = [r for r in rows if r.get("census") == "found_here" and r.get("census_placeholder")
            and reached(r)]
    kept = [r for r in here if flagged(r)]
    mark = [r for r in ph if r.get("finalsite_markup")]
    measures = {"F1_hosts": n, "F1_hosts_50k+": big,
                "G1_answered": ap.share(len(ans), n),
                "K1_placeholder_hosts": len(ph),
                "K2_uncounted_of_sampled": ap.share(len(unc), len(sampled_ph)),
                "K3_kept_of_census_here": ap.share(len(kept), len(here)),
                "K4_markup_of_placeholder": ap.share(len(mark), len(ph))}
    gates = {"F1_frame": F1_MIN <= n <= F1_MAX and F1_BIG_MIN <= big <= F1_BIG_MAX,
             "G1_answered": bool(n) and len(ans) / n >= G1_MIN_ANSWERED}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("K1", "K2", "K3", "K4")}
    preds = {"K1": len(ph) >= K1_MIN_HOSTS,
             "K2": (len(unc) / len(sampled_ph) >= K2_MIN_UNCOUNTED)
                   if len(sampled_ph) >= K2_MIN_PAGES else None,
             "K3": (len(kept) / len(here) >= K3_MIN_KEPT) if len(here) >= K3_MIN_PAGES else None,
             "K4": (len(mark) / len(ph) >= K4_MIN_MARKUP) if len(ph) >= K4_MIN_PAGES else None}
    return measures, gates, preds


def described(rows):
    """Reported, not graded."""
    ok = [r for r in rows if r.get("status") == "ok"]
    ph = [r for r in rows if flagged(r)]
    out = {"status": {}, "census": {}, "placeholder_of_answered": {}, "ok_pages": len(ok)}
    for b, _ in OUT_FILES:
        rs = [r for r in rows if r.get("band") == b]
        out["status"][b] = ap._tally(rs, "status")
        out["census"][b] = ap._tally(rs, "census")
        out["placeholder_of_answered"][b] = ap.share(sum(1 for r in rs if flagged(r)),
                                                     sum(1 for r in rs if answered(r)))
    here = [r for r in rows if r.get("census") == "found_here" and r.get("census_placeholder")]
    out.update(
        placeholder_by_census=ap._tally(ph, "census"),
        placeholder_kinds=ap._tally(ph, "placeholder_kinds"),
        placeholder_highest=ap._tally(ph, "highest"),
        placeholder_title2=sum(1 for r in ph if r.get("title2")),
        placeholder_t2017=sum(1 for r in ph if r.get("t2017")),
        placeholder_t2026=sum(1 for r in ph if r.get("t2026")),
        placeholder_generator=sum(1 for r in ph if r.get("generator")),
        t2017_pages=sum(1 for r in ok if r.get("t2017")),
        t2017_without_placeholder=sum(1 for r in ok if r.get("t2017") and not r.get("placeholder")),
        t2026_pages=sum(1 for r in ok if r.get("t2026")),
        markup_pages=sum(1 for r in ok if r.get("finalsite_markup")),
        census_here_placeholder=len(here),
        census_here_status=ap._tally(here, "status"),
        census_here_same_text=sum(1 for r in here if r.get("same_text")),
        retried=sum(1 for r in rows if r.get("retried")),
        placeholder_by_state=ap._tally(ph, "state"))
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
            if b"K4" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


def write_tables(out_dir, rows):
    """One CSV per population band (each stays under the publishing size limit), in LEAID order."""
    sizes = {}
    for b, name in OUT_FILES:
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
            w.writeheader()
            for r in sorted((r for r in rows if r.get("band") == b), key=lambda r: r["leaid"]):
                w.writerow({c: r.get(c, "") for c in COLUMNS})
        sizes[name] = os.path.getsize(path)
    return sizes


def result_text(result):
    lines = ["district_stock %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("ccd_file", "saipe_file", "census_rows", "frame", "table_bytes"):
        if k in result:
            lines.append("%s: %s" % (k, json.dumps(result[k], sort_keys=True)))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        for k in sorted(d):
            lines.append("%s: %s" % (k, json.dumps(d[k], sort_keys=True)))
    return "\n".join(lines)


def main(argv=None, fetch=ap.fetch_bytes, get=ap.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-minutes", type=float, default=200)
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
            json.dump(result, f, indent=1)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("district_stock: %s" % status)
        return 0

    ok, attempts = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["prereg_attempts"] = attempts
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("not_run")  # no district page was read, so the test can run later
    try:
        census = read_census(fetch(REPO_RAW + CENSUS_PATH + "?n=0"))
    except Exception:
        census = {}
    result["census_rows"] = len(census)
    result["gates"]["G0_census"] = len(census) == CENSUS_ROWS
    if not result["gates"]["G0_census"]:
        return finish("not_run")
    try:
        ccd_url, zbytes = dp.first(dp.CCD_URLS, fetch)
        ccd_rows = dp.read_ccd(zbytes)
        saipe_url, sbytes = dp.first(dp.SAIPE_URLS, fetch)
        pops = dp.parse_saipe(sbytes.decode("latin-1"))
    except Exception as e:  # recorded; nothing is read
        result["error"] = str(e)[:200]
        result["gates"]["G0_federal"] = False
        return finish("not_run")
    result["gates"]["G0_federal"] = True
    result.update(ccd_file=ccd_url.rsplit("/", 1)[-1], ccd_sha256=ap.sha256(zbytes),
                  saipe_file=saipe_url.rsplit("/", 1)[-1], saipe_sha256=ap.sha256(sbytes))
    frame, dropped = build_frame(dp.build_frame(ccd_rows, pops), census)
    big = sum(1 for r in frame if r["band"] == "50k+")
    result["frame"] = {"hosts": len(frame), "hosts_50k+": big, "dropped": dropped,
                       "census_sampled": sum(1 for r in frame if r["census"] != "not_sampled")}
    if not (F1_MIN <= len(frame) <= F1_MAX and F1_BIG_MIN <= big <= F1_BIG_MAX):
        result["gates"]["F1_frame"] = False
        return finish("not_run")  # nothing was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(crawl_order(frame), workers=args.workers, deadline=deadline, get=get,
                 sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    result["table_bytes"] = write_tables(args.out_dir, read)
    measures, gates, preds = grade(read)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(gates.values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
