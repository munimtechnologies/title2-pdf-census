# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""school_credit 0.1.0: which website company do England's unfinished school accessibility statements credit?

Pre-registered in results/uk-schools/CREDIT-FOLLOWUP-PREREG.md and its addendum
results/uk-schools/CREDIT-FOLLOWUP-ADDENDUM.md, both committed before this script read anything.
The frame is the hosts behind school-stock's J1: the rows of its published tables
(results/uk-schools/hosts-part1..4.csv) whose status is ok and that carry a placeholder. Each host's
/accessibility-statement/ is read once more with school-stock's own request rules (school_stock.py
0.1.0, unchanged: robots.txt first, one request at a time per host, a pause after each, one retry
after 30 seconds on 429 or 503) and the pinned checker (statement_template_check.py 0.3.0), and the
page's HTML is searched for five website companies' credits.

A credit in the HTML shows who built or once built a site, not who wrote its statement. Schools
are exempt from SI 2018/952 except for essential administrative content, so nothing here calls a
statement a breach. Only the host, status, flags and rule ids are stored: no page text and no
person's name. Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person. Standard
library only.
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
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import school_stock as ss  # noqa: E402  (0.1.0, unchanged)
import statement_template_check as stc  # noqa: E402  (0.3.0, unchanged)

__version__ = "0.1.0"

RES_DIR = "results/uk-schools"
PREREG_PATH = "results/uk-schools/CREDIT-FOLLOWUP-PREREG.md"
ADDENDUM_PATH = "results/uk-schools/CREDIT-FOLLOWUP-ADDENDUM.md"
RESULT_NOTE_PATH = "results/uk-schools/SCHOOL-STOCK-RESULT.md"
STOCK_RESULT_PATH = "results/uk-schools/result.json"
CHECKER_VERSION = "0.3.0"

# Pre-registered (CREDIT-FOLLOWUP-PREREG.md, CREDIT-FOLLOWUP-ADDENDUM.md).
MAX_DAYS = 21                   # C2: the re-read starts at most 21 days after school-stock's crawl
MIN_GRADED = 50                 # C1, and the minimum for grading each prediction
K1_MIN_FAMILY = 0.90            # K1: share of the graded set with a family credit
K2_MIN_MISSED = 0.10            # K2: e4education or primarysite credit and no juniper credit
K3_MIN_SAME = 0.90              # K3: share of the graded set whose text is unchanged
L1_MIN_GREENHOUSE = 0.80        # L1: greenhouse credit among the three-field group
L1_IDS = "gov-uk/email_address;gov-uk/phone;gov-uk/number_of_days"
US_TEMPLATE_IDS = ("school/your_school", "school/your_domain", "school/fake_phone")

_SEP = rb"(?:\s|&nbsp;|&#160;)+"
CREDIT_RES = (
    ("juniper", ss.JUNIPER_CREDIT_RE),  # school-stock's own pattern, unchanged
    ("e4education", re.compile(rb"e4education", re.I)),
    ("primarysite", re.compile(rb"primarysite", re.I)),
    ("greenhouse", re.compile(rb"greenhouseschoolwebsites|greenhouse" + _SEP + rb"school" + _SEP
                              + rb"websites", re.I)),
    ("finalsite", re.compile(rb"finalsite", re.I)),
)
CREDITS = tuple(name for name, _ in CREDIT_RES)
FAMILY = ("juniper", "e4education", "primarysite")

BOOLS = ("retried", "graded", "same_text") + CREDITS + ("family", "stock_template",
                                                       "stock_us_template", "l1_group")
COLUMNS = ["host", "status", "retried", "graded", "same_text"] + list(CREDITS) + [
    "family", "placeholder_ids", "stock_template", "stock_us_template", "l1_group"]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def credits(body):
    """Each company's credit found anywhere in the page's HTML, plus family (any Juniper brand)."""
    body = body or b""
    out = {name: bool(rx.search(body)) for name, rx in CREDIT_RES}
    out["family"] = any(out[k] for k in FAMILY)
    return out


# ---------------------------------------------------------------- the frame

def load_stock(folder, tables):
    """(rows, ok): school-stock's published rows, and whether every table is the one its
    result.json lists (bytes and row count)."""
    rows, ok = [], bool(tables)
    for t in tables:
        path = os.path.join(folder, t["file"])
        if not os.path.exists(path):
            ok = False
            continue
        with open(path, "rb") as f:
            data = f.read()
        part = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
        ok = ok and sha256(data) == t["sha256"] and len(part) == t["rows"]
        rows.extend(part)
    return ss.typed(rows), ok


def frame_of(stock_rows):
    """The hosts behind J1: read and carrying a 0.3.0 placeholder."""
    return [r for r in stock_rows if ss.flagged(r)]


def l1_group(r):
    return (bool(r.get("juniper_template")) and not r.get("juniper_credit")
            and r.get("placeholder_ids") == L1_IDS)


def us_template(r):
    return any(i in US_TEMPLATE_IDS for i in (r.get("placeholder_ids") or "").split(";"))


def parse_utc(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)


# ---------------------------------------------------------------- one host

def blank(stock_row, status):
    out = {k: False for k in BOOLS}
    out.update(host=stock_row["host"], status=status, placeholder_ids="",
               stock_template=bool(stock_row.get("juniper_template")),
               stock_us_template=us_template(stock_row), l1_group=l1_group(stock_row))
    return out


def reread(stock_row, get=stc.http_get, delay=1.0, sleep=time.sleep):
    """school-stock's read_one, unchanged, with the HTML of the statement address kept so the
    credits can be searched."""
    url = (stock_row.get("base") or "") + ss.PROBE_PATH
    seen = {"body": b""}

    def keep(u):
        res = get(u)
        if u == url:
            seen["body"] = res[3] or b""
        return res

    r = ss.read_one({"host": stock_row["host"], "base": stock_row.get("base", "")},
                    get=keep, delay=delay, sleep=sleep)
    out = blank(stock_row, r["status"])
    out["retried"] = bool(r.get("retried"))
    if ss.ok(r):
        out.update(credits(seen["body"]))
        out["placeholder_ids"] = r["placeholder_ids"]
        out["graded"] = bool(r["placeholder"])
        out["same_text"] = r["text_sha256"] == stock_row.get("text_sha256")
    return out


def crawl(rows, workers=8, deadline=None, **kw):
    def one(row):
        if deadline and time.time() > deadline:
            return blank(row, "not_started")
        return reread(row, **kw)

    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, r) for r in rows]
        for row, fut in zip(rows, futures):
            try:
                out.append(fut.result())
            except Exception:  # one host's crash is recorded, never fatal
                out.append(blank(row, "crash"))
    return out


# ---------------------------------------------------------------- grading

def grade(rows, gates):
    g = [r for r in rows if r["graded"]]
    fam = [r for r in g if r["family"]]
    missed = [r for r in g if (r["e4education"] or r["primarysite"]) and not r["juniper"]]
    same = [r for r in g if r["same_text"]]
    lg = [r for r in g if r["l1_group"]]
    gh = [r for r in lg if r["greenhouse"]]
    measures = {"frame_hosts": len(rows), "graded_hosts": len(g),
                "K1_family": ss.share(len(fam), len(g)),
                "K2_missed_by_j2_pattern": ss.share(len(missed), len(g)),
                "K3_unchanged_text": ss.share(len(same), len(g)),
                "L1_greenhouse_of_three_field_group": ss.share(len(gh), len(lg))}
    if not all(gates.values()):
        return measures, {k: None for k in ("K1", "K2", "K3", "L1")}
    big = len(g) >= MIN_GRADED
    preds = {"K1": (len(fam) / len(g) >= K1_MIN_FAMILY) if big else None,
             "K2": (len(missed) / len(g) >= K2_MIN_MISSED) if big else None,
             "K3": (len(same) / len(g) >= K3_MIN_SAME) if big else None,
             "L1": (len(gh) / len(lg) >= L1_MIN_GREENHOUSE) if len(lg) >= MIN_GRADED else None}
    return measures, preds


def combo(r):
    names = [k for k in CREDITS if r[k]]
    return "+".join(names) if names else "none"


def described(rows):
    """Reported, not graded."""
    g = [r for r in rows if r["graded"]]
    oks_lost = [r for r in rows if r["status"] == "ok" and not r["graded"]]
    out = {"status": ss.tally(rows, "status"),
           "not_graded_by_status": ss.tally([r for r in rows if not r["graded"]], "status"),
           "ok_without_placeholder": len(oks_lost),
           "graded_text_changed": sum(1 for r in g if not r["same_text"]),
           "credit_combinations": ss.tally([dict(r, combo=combo(r)) for r in g], "combo"),
           "retried": sum(1 for r in rows if r["retried"])}
    for k in CREDITS + ("family",):
        out["graded_" + k] = sum(1 for r in g if r[k])
    for flag in ("stock_template", "l1_group", "stock_us_template"):
        sub = [r for r in g if r[flag]]
        out["graded_" + flag] = {"hosts": len(sub),
                                 "family": sum(1 for r in sub if r["family"]),
                                 "greenhouse": sum(1 for r in sub if r["greenhouse"]),
                                 "finalsite": sum(1 for r in sub if r["finalsite"])}
    rest = [r for r in g if not r["stock_template"]]
    out["graded_without_template_family"] = {"hosts": len(rest),
                                             "family": sum(1 for r in rest if r["family"])}
    out["graded_no_credit"] = sum(1 for r in g if not any(r[k] for k in CREDITS))
    return out


# ---------------------------------------------------------------- the run

def write_table(path, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in sorted(rows, key=lambda r: r["host"]):
        w.writerow([r.get(c, "") for c in COLUMNS])
    data = buf.getvalue().encode("utf-8")
    with open(path, "wb") as f:
        f.write(data)
    return {"file": os.path.basename(path), "rows": len(rows), "bytes": len(data),
            "sha256": sha256(data)}


def result_text(result):
    lines = ["school_credit %s" % result["version"], "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("crawl", "table"):
        if k in result:
            lines.append("%s: %s" % (k, json.dumps(result[k], sort_keys=True)))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, json.dumps(v, sort_keys=True)))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    for k, v in sorted((result.get("described") or {}).items()):
        lines.append("%s: %s" % (k, json.dumps(v, sort_keys=True)))
    return "\n".join(lines)


def read_text(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv=None, get=stc.http_get, sleep=time.sleep, now=None, root=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-minutes", type=float, default=45)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    root = root or here
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "checker_version": stc.__version__, "gates": {}, "files": {}}
    for name in ("school_credit.py", "school_stock.py", "statement_template_check.py"):
        with open(os.path.join(here, name), "rb") as f:
            result["files"][name] = sha256(f.read())

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("school_credit: %s" % status)
        return 0

    def at(rel):
        return os.path.join(root, *rel.split("/"))

    prereg, addendum = read_text(at(PREREG_PATH)), read_text(at(ADDENDUM_PATH))
    stock_raw = read_text(at(STOCK_RESULT_PATH))
    stock = json.loads(stock_raw) if stock_raw else {}
    sg = stock.get("gates") or {}
    rows, tables_ok = load_stock(at(RES_DIR), stock.get("tables") or [])
    frame = frame_of(rows)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    finished = (stock.get("crawl") or {}).get("finished_utc")
    gates = {
        "P0_registered": "K3" in prereg and "L1" in addendum,
        "P0_checker": stc.__version__ == CHECKER_VERSION and ss.__version__ == "0.1.0",
        "C0_published": (os.path.exists(at(RESULT_NOTE_PATH)) and stock.get("status") == "graded"
                         and all(sg.get(k) for k in ("P0_prereg", "P0_checker", "F1_frame",
                                                     "G1_answered"))
                         and tables_ok),
        "C1_hosts": len(frame) >= MIN_GRADED,
        "C2_within_21_days": bool(finished) and now <= parse_utc(finished) + datetime.timedelta(
            days=MAX_DAYS),
    }
    result["gates"] = gates
    result["frame_hosts"] = len(frame)
    if not all(gates.values()):
        return finish("not_run")  # no school website was read
    started = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    deadline = time.time() + 60 * args.max_minutes
    out = crawl(ss.crawl_order(frame), workers=args.workers, deadline=deadline, get=get,
                sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    result["table"] = write_table(os.path.join(args.out_dir, "hosts.csv"), out)
    measures, preds = grade(out, gates)
    result.update(measures=measures, predictions=preds, described=described(out))
    return finish("graded")


if __name__ == "__main__":
    sys.exit(main())
