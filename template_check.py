"""template_check 0.1.0: are US local governments' accessibility pages still an unedited template?

Pre-registered in results/template-pages/PREREG.md. Reads again, once, every accessibility page
that MV2's two earlier censuses read (results/a11y-pages/a11y-pages.csv, governments of 50,000 or
more, and results/small-pages/rows.csv, governments of 10,000 to 49,999), with the same polite
requests as a11y_pages.py (robots.txt honoured, one page per site, a pause after each request),
and flags placeholder text left over from a template: "YOURMUNICIPALITY", the note "only meant
as a template", a NAME / TITLE / EMAIL / PHONE block in capitals, or a bracketed placeholder such
as "[URL OF WEBSITE]". It also counts the stock sentence with the word WCAG missing ("as well as
2.0 A and AA").

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's requests, parser and statistics)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/template-pages/PREREG.md"
PINNED = ("template_check.py", "a11y_pages.py")
TABLES = (("large", "results/a11y-pages/a11y-pages.csv"),
          ("small", "results/small-pages/rows.csv"))
EXPECTED_PAGES = {"large": 808, "small": 1042}

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
MIN_REREAD = 0.80          # G1: each cohort's pages read again with text, of the pages in its table
MIN_FLAGGED = 10           # T3 and T5 are graded only with at least this many flagged pages
T1_MIN_SMALL = 0.01        # T1: at least 1.0% of the small cohort's pages carry a placeholder
T3_MIN_CIVICPLUS = 0.80    # T3: at least 80% of flagged pages carry CivicPlus markup
T4_MIN_NO_WCAG = 50        # T4: at least 50 small-cohort pages carry "as well as 2.0 A and AA"
T5_MIN_IN_GROUP = 0.80     # T5: at least 80% of flagged small pages were stock pages naming no version

# Pages already read live, or found by web search, before this plan was written (PREREG.md).
ALREADY_SEEN = {
    "small": ("Q1000065", "Q1003082", "Q109526", "Q1007032", "Q1007079", "Q1013038", "Q1000166",
              "Q1000642", "Q502210", "Q545119"),
    "large": ("Q835831", "Q1016633", "Q985298", "Q166304", "Q1876560", "Q185216"),
}

STOCK = "We work to comply with Section 508 as well as"
MUNI_RE = re.compile(r"\bYOUR ?MUNICIPALITY\b")
TEMPLATE_RE = re.compile(r"only meant as a template", re.I)
BLOCK_RE = re.compile(r"\bNAME\W{0,10}TITLE\W{0,10}EMAIL\W{0,10}PHONE\b")
BRACKET_RE = re.compile(r"\[[^\[\]]{0,40}?\b(?:INSERT [A-Z]|NAME OF\b|URL OF\b|(?:CITY|COUNTY|TOWN|"
                        r"VILLAGE|AGENCY|ORGANI[SZ]ATION|ENTITY) NAME\b|PHONE NUMBER\b|"
                        r"EMAIL ADDRESS\b|YOUR [A-Z]{3,})[^\[\]]{0,60}\]")
NO_WCAG_RE = re.compile(r"as well as 2\.0 A and AA")
FLAGS = ("muni", "template_note", "contact_block", "bracket")
BOOLS = FLAGS + ("placeholder", "no_wcag", "stock", "civicplus", "same_text")

COLUMNS = ["cohort", "qid", "name", "kind", "state", "page_url", "status", "final_url",
           "text_chars", "text_sha256", "old_sha256", "same_text", "civicplus", "muni",
           "template_note", "contact_block", "bracket", "bracket_text", "placeholder", "no_wcag",
           "stock", "old_highest", "old_stock"]


# ---------------------------------------------------------------- reading one page

def check_text(text):
    """The placeholder flags of one page's visible text."""
    b = BRACKET_RE.search(text)
    r = {"muni": bool(MUNI_RE.search(text)), "template_note": bool(TEMPLATE_RE.search(text)),
         "contact_block": bool(BLOCK_RE.search(text)), "bracket": bool(b),
         "bracket_text": ap.scrub(b.group(0))[:100] if b else "",
         "no_wcag": bool(NO_WCAG_RE.search(text)), "stock": STOCK in text}
    r["placeholder"] = any(r[k] for k in FLAGS)
    return r


def is_civicplus(body):
    low = body.lower()
    return b"civicplus" in low or b"civicengage" in low


def read_table(data, cohort):
    """The pages a census read (page_status ok), from its published per-site table."""
    rows = []
    for r in csv.DictReader(io.StringIO(data.decode("utf-8"))):
        if r.get("page_status") == "ok" and r.get("page_url"):
            rows.append({"cohort": cohort, "qid": r["qid"], "name": r["name"], "kind": r["kind"],
                         "state": r["state"], "page_url": r["page_url"],
                         "old_sha256": r.get("text_sha256", ""),
                         "old_highest": r.get("highest", ""), "old_stock": r.get("stock", "")})
    return rows


def read_one(row, get=ap.http_get, delay=1.0, sleep=time.sleep):
    """Read one page again: robots.txt first, then the page itself, as a11y_pages.py does."""
    out = dict(row)
    out.update(status="", final_url="", text_chars=0, text_sha256="", bracket_text="")
    for k in BOOLS:
        out[k] = ""
    url = row["page_url"]
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
    out["same_text"] = out["text_sha256"] == row.get("old_sha256", "")
    out["civicplus"] = is_civicplus(body)
    out.update(check_text(text))
    return out


def crawl(rows, workers=16, deadline=None, **kw):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for r in rows:
            futures.append(pool.submit(_read_or_skip, r, deadline, kw))
        for i, fut in enumerate(futures, 1):
            try:
                out.append(fut.result())
            except Exception as e:  # one page's crash is recorded, never fatal
                r = dict(rows[i - 1])
                r.update(status="crash", final_url=str(e)[:80])
                out.append(r)
            if i % 100 == 0:
                print("%d/%d pages" % (i, len(futures)), flush=True)
    return out


def _read_or_skip(row, deadline, kw):
    if deadline and time.time() > deadline:
        r = dict(row)
        r["status"] = "not_started"
        return r
    return read_one(row, **kw)


# ---------------------------------------------------------------- grading

def typed(rows):
    """Rows read back from pages.csv, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def ok_pages(rows, cohort):
    return [r for r in rows if r.get("cohort") == cohort and r.get("status") == "ok"]


def in_group(r):
    """A small-cohort page that carried the stock sentence but named no WCAG version on 11-02."""
    return r.get("old_stock") == "True" and not r.get("old_highest")


def grade(rows, n_table):
    large, small = ok_pages(rows, "large"), ok_pages(rows, "small")
    lf = [r for r in large if r["placeholder"]]
    sf = [r for r in small if r["placeholder"]]
    flagged = lf + sf
    civ = sum(1 for r in flagged if r["civicplus"])
    no_wcag = sum(1 for r in small if r["no_wcag"])
    grouped = sum(1 for r in sf if in_group(r))
    measures = {"G1_reread_large": ap.share(len(large), n_table.get("large", 0)),
                "G1_reread_small": ap.share(len(small), n_table.get("small", 0)),
                "T1_placeholder_of_small": ap.share(len(sf), len(small)),
                "T2_placeholder_of_large": ap.share(len(lf), len(large)),
                "T3_civicplus_of_flagged": ap.share(civ, len(flagged)),
                "T4_no_wcag_of_small": ap.share(no_wcag, len(small)),
                "T5_in_group_of_flagged_small": ap.share(grouped, len(sf))}
    gate = all(n_table.get(c) and len(ok_pages(rows, c)) / n_table[c] >= MIN_REREAD
               for c in ("large", "small"))
    if not gate:
        return measures, False, {k: None for k in ("T1", "T2", "T3", "T4", "T5")}
    preds = {"T1": len(sf) / len(small) >= T1_MIN_SMALL,
             "T2": len(lf) / len(large) < len(sf) / len(small),
             "T3": (civ / len(flagged) >= T3_MIN_CIVICPLUS) if len(flagged) >= MIN_FLAGGED else None,
             "T4": no_wcag >= T4_MIN_NO_WCAG,
             "T5": (grouped / len(sf) >= T5_MIN_IN_GROUP) if len(sf) >= MIN_FLAGGED else None}
    return measures, True, preds


def described(rows):
    """Reported, not graded."""
    out = {"status": {}, "flagged": []}
    for cohort in ("large", "small"):
        rs = [r for r in rows if r.get("cohort") == cohort]
        out["status"][cohort] = ap._tally(rs, "status")
        ok = ok_pages(rows, cohort)
        seen = set(ALREADY_SEEN[cohort])

        def n(pred):
            return sum(1 for r in ok if pred(r))
        d = {k: n(lambda r, k=k: r[k]) for k in BOOLS}
        d["pages"] = len(ok)
        d["placeholder_not_seen_before"] = n(lambda r: r["placeholder"] and r["qid"] not in seen)
        d["placeholder_civicplus"] = n(lambda r: r["placeholder"] and r["civicplus"])
        d["placeholder_by_kind"] = ap._tally([r for r in ok if r["placeholder"]], "kind")
        out[cohort] = d
    for r in sorted((r for r in rows if r.get("status") == "ok" and r["placeholder"]),
                    key=lambda r: (r["cohort"], r["state"], r["name"])):
        out["flagged"].append([r["cohort"], r["name"], r["state"], r["kind"],
                               "+".join(k for k in FLAGS if r[k])])
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
            if b"T5" in prereg and same:
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
    lines = ["template_check %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for cohort, t in sorted((result.get("tables") or {}).items()):
        lines.append("table %s: pages=%s sha256=%s" % (cohort, t["pages"], t["sha256"][:12]))
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
        print("template_check: %s" % status)
        return 0

    ok, attempts = wait_for_prereg(here, fetch=fetch, sleep=sleep)
    result["prereg_attempts"] = attempts
    result["gates"]["P0_prereg_public"] = ok
    if not ok:
        return finish("not_run")  # no page was read, so the test can still be run later
    rows, n_table = [], {}
    for cohort, path in TABLES:
        try:
            data = fetch(REPO_RAW + path + "?n=0")
        except Exception:
            data = b""
        got = read_table(data, cohort) if data else []
        result["tables"][cohort] = {"sha256": ap.sha256(data), "pages": len(got)}
        n_table[cohort] = len(got)
        rows.extend(got)
    result["gates"]["G0_tables"] = n_table == EXPECTED_PAGES
    if not result["gates"]["G0_tables"]:
        return finish("not_run")  # no page was read, so the test can still be run later
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(rows, workers=args.workers, deadline=deadline, get=get, sleep=sleep)
    write_csv(os.path.join(args.out_dir, "pages.csv"), read, COLUMNS)
    measures, gate, preds = grade(read, n_table)
    result["gates"]["G1_reread"] = gate
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if gate else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
