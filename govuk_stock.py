# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""govuk_stock 0.1.0: accessibility statements of UK government organisations that run their own website.

Pre-registered in results/govuk-orgs/PREREG.md. The frame is built inside the same sealed job, by
a rule fixed in the plan, with the pinned govuk_frame.py 0.1.0: every organisation in GOV.UK's
organisations API (Open Government Licence v3.0) whose GOV.UK status is exempt, joining or
transitioning, and the website its GOV.UK content item names. The frame is saved and hashed before
any organisation's website is requested. Each distinct host is then read with the pinned reader of
council_stock.py 0.1.0 (unchanged on main): home page, its statement link, one hop from a page that
links to the statement, then /accessibility-statement and /accessibility; robots.txt honoured;
statement text read with statement_template_check.py 0.3.0 plus council_stock's date reader. No
page text is stored, only a hash, rule ids, dates and counts.

This counts what statements say; it does not test whether a website is accessible, and nothing
here calls an organisation in breach. Made by MV2 of Munim, Inc. with AI agents; not yet checked
by a person. Standard library only.
"""

import argparse
import collections
import csv
import hashlib
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import council_stock as cs  # noqa: E402  (council_stock 0.1.0, unchanged on main)
import govuk_frame as gf  # noqa: E402  (govuk_frame 0.1.0)
import statement_template_check as stc  # noqa: E402  (a11y-statement-check 0.3.0, unchanged)

__version__ = "0.1.0"

PREREG_PATH = "results/govuk-orgs/PREREG.md"
COUNCIL_STOCK_VERSION = "0.1.0"
GOVUK_FRAME_VERSION = "0.1.0"
CRAWL_SEED = "govuk-stock-2026-11"

# Frame gate F1 (PREREG.md): checked on the frame this job builds, before any website is read.
F1_MIN_ORGANISATIONS = 1000     # organisations read from GOV.UK's list
F1_MAX_FETCH_FAILED = 10        # content items that could not be read
F1_MAX_DROPPED = 2              # rows dropped by the publishing guard word
F1_MIN_HOSTS = 100              # distinct own hosts to read

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
G1_MIN_ANSWERED = 0.90          # G1: share of hosts whose server answered
O1_MIN_FOUND = 0.75             # O1: share of hosts where a statement was found and read
O2_MAX_PLACEHOLDER = 3          # O2: hosts whose statement keeps a 0.3.0 placeholder
O3_MIN_22 = 0.70                # O3: share of read statements naming WCAG 2.2 as the highest
O3_MIN_PAGES = 60
O4_MIN_STALE = 0.25             # O4: share of dated statements dated before cs.STALE_BEFORE
O4_MIN_PAGES = 60

ID_COLUMNS = ["host", "slug", "title", "organisation_type", "govuk_status", "organisations"]
COLUMNS = ID_COLUMNS + cs.COLUMNS[5:]   # status ... date_source, as in council_stock


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_frame_csv(path):
    with open(path, "rb") as f:
        data = f.read()
    return list(csv.DictReader(io.StringIO(data.decode("utf-8")))), data


def eligible(r):
    return (r.get("own_host") in (True, "True") and r.get("govuk_status") in gf.OWN_SITE_STATUSES
            and r.get("fetch") == "ok" and bool((r.get("host") or "").strip()))


def build_frame(rows):
    """(hosts, dropped): one row per distinct own host (first organisation by slug), with the
    number of organisations on it."""
    groups = collections.OrderedDict()
    dropped = 0
    for r in rows:
        if not eligible(r):
            continue
        if cs.GUARD_RE.search(" ".join((r.get("slug", ""), r.get("title", ""), r.get("host", "")))):
            dropped += 1
            continue
        groups.setdefault(r["host"].strip().lower(), []).append(r)
    out = []
    for h, rs in groups.items():
        first = min(rs, key=lambda r: r.get("slug", ""))
        out.append({"host": h, "slug": first.get("slug", ""), "title": first.get("title", ""),
                    "organisation_type": first.get("organisation_type", ""),
                    "govuk_status": first.get("govuk_status", ""), "organisations": len(rs)})
    return out, dropped


def frame_gate(info, hosts, dropped):
    """F1: the frame is complete enough to read (all from the frame job's own counts)."""
    return (int(info.get("organisations") or 0) >= F1_MIN_ORGANISATIONS
            and len(info.get("fetch_failed") or []) <= F1_MAX_FETCH_FAILED
            and int(info.get("dropped") or 0) + dropped <= F1_MAX_DROPPED
            and len(hosts) >= F1_MIN_HOSTS)


def crawl_order(hosts):
    return sorted(hosts, key=lambda r: sha256((CRAWL_SEED + r["host"]).encode("utf-8")))


def grade(rows, frame_ok=True):
    n = len(rows)
    ans = [r for r in rows if cs.answered(r)]
    found = [r for r in rows if cs.ok(r)]
    ph = [r for r in found if r.get("placeholder")]
    v22 = [r for r in found if r.get("highest") == "2.2"]
    dated = [r for r in found if r.get("statement_date")]
    old = [r for r in dated if cs.stale(r)]
    measures = {"F1_hosts": n,
                "G1_answered": cs.share(len(ans), n),
                "O1_found": cs.share(len(found), n),
                "O2_placeholder_hosts": len(ph),
                "O3_wcag22_of_found": cs.share(len(v22), len(found)),
                "O4_stale_of_dated": cs.share(len(old), len(dated))}
    gates = {"F1_frame": bool(frame_ok),
             "G1_answered": bool(n) and len(ans) / n >= G1_MIN_ANSWERED}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("O1", "O2", "O3", "O4")}
    preds = {"O1": len(found) / n >= O1_MIN_FOUND,
             "O2": len(ph) <= O2_MAX_PLACEHOLDER,
             "O3": (len(v22) / len(found) >= O3_MIN_22) if len(found) >= O3_MIN_PAGES else None,
             "O4": (len(old) / len(dated) >= O4_MIN_STALE) if len(dated) >= O4_MIN_PAGES else None}
    return measures, gates, preds


def described(rows):
    """Reported, not graded."""
    found = [r for r in rows if cs.ok(r)]
    dated = [r for r in found if r.get("statement_date")]
    types = {}
    for t in sorted(set(r.get("organisation_type", "") for r in rows)):
        rs = [r for r in rows if r.get("organisation_type", "") == t]
        fs = [r for r in rs if cs.ok(r)]
        ds = [r for r in fs if r.get("statement_date")]
        types[t] = {"hosts": len(rs), "found": len(fs),
                    "placeholder": sum(1 for r in fs if r.get("placeholder")),
                    "wcag22": sum(1 for r in fs if r.get("highest") == "2.2"),
                    "dated": len(ds), "stale": sum(1 for r in ds if cs.stale(r))}
    return {
        "status": cs.tally(rows, "status"),
        "home_status": cs.tally(rows, "home_status"),
        "found_by": cs.tally(found, "found_by"),
        "found_organisations": sum(int(r.get("organisations") or 0) for r in found),
        "found_highest": cs.tally(found, "highest"),
        "found_gov_uk_wording": sum(1 for r in found if r.get("gov_uk_sample")),
        "found_no_date": len(found) - len(dated),
        "date_source": cs.tally(dated, "date_source"),
        "statement_year": cs.tally([{"y": r["statement_date"][:4]} for r in dated], "y"),
        "placeholder_ids": cs.tally_ids([r for r in found if r.get("placeholder")],
                                        "placeholder_ids"),
        "placeholder_hosts": sorted(r["host"] for r in found if r.get("placeholder")),
        "found_other_host": sum(1 for r in found if r.get("other_host")),
        "offsite_link": sum(1 for r in rows if r.get("offsite_link")),
        "robots_blocked": sum(1 for r in rows if r.get("robots_blocked")),
        "retried": sum(1 for r in rows if r.get("retried")),
        "distinct_texts": len(set(r.get("text_sha256") for r in found)),
        "by_type": types,
    }


def typed(rows):
    """Rows read back from hosts.csv: flags as booleans (cs.typed), organisations as an int."""
    return [dict(r, organisations=int(r.get("organisations") or 0)) for r in cs.typed(rows)]


def write_table(out_dir, rows):
    rows = sorted(rows, key=lambda r: r["host"])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([r.get(c, "") for c in COLUMNS])
    data = buf.getvalue().encode("utf-8")
    with open(os.path.join(out_dir, "hosts.csv"), "wb") as f:
        f.write(data)
    return {"file": "hosts.csv", "rows": len(rows), "bytes": len(data), "sha256": sha256(data)}


def result_text(result):
    text = cs.result_text(result)
    return text.replace("council_stock %s" % result["version"],
                        "govuk_stock %s" % result["version"], 1)


def main(argv=None, fetch=cs.fetch_bytes, get=stc.http_get, sleep=time.sleep,
         fetch_json=gf.fetch_json):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-minutes", type=float, default=120)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "checker_version": stc.__version__,
              "reader_version": cs.__version__, "frame_version": gf.__version__,
              "gates": {}, "files": {}}
    for name in ("govuk_stock.py", "govuk_frame.py", "council_stock.py",
                 "statement_template_check.py", PREREG_PATH):
        with open(os.path.join(here, *name.split("/")), "rb") as f:
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
        print("govuk_stock: %s" % status)
        return 0

    with open(os.path.join(here, *PREREG_PATH.split("/")), "rb") as f:
        prereg = f.read()
    result["gates"]["P0_prereg"] = b"O4" in prereg
    result["gates"]["P0_checker"] = (stc.__version__ == cs.CHECKER_VERSION
                                     and cs.__version__ == COUNCIL_STOCK_VERSION
                                     and gf.__version__ == GOVUK_FRAME_VERSION
                                     and cs.checker_matches_release(here, fetch))
    if not (result["gates"]["P0_prereg"] and result["gates"]["P0_checker"]):
        return finish("not_run")  # nothing was requested
    # The frame: GOV.UK's API only (govuk_frame.main writes govuk-frame.csv and .json).
    gf.main(args.out_dir, fetch=fetch_json, sleep=sleep)
    rows, data = read_frame_csv(os.path.join(args.out_dir, "govuk-frame.csv"))
    with open(os.path.join(args.out_dir, "govuk-frame.json"), encoding="utf-8") as f:
        info = json.load(f)
    hosts, dropped = build_frame(rows)
    frame_ok = frame_gate(info, hosts, dropped)
    result["frame"] = {"organisations": info.get("organisations"), "rows": len(rows),
                       "hosts": len(hosts), "dropped": int(info.get("dropped") or 0) + dropped,
                       "fetch_failed": len(info.get("fetch_failed") or []),
                       "bytes": len(data), "sha256": sha256(data)}
    if not frame_ok:
        result["gates"]["F1_frame"] = False
        return finish("not_run")  # no organisation's website was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = cs.crawl(crawl_order(hosts), workers=args.workers, deadline=deadline, get=get,
                    sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    result["table"] = write_table(args.out_dir, read)
    measures, gates, preds = grade(read, frame_ok)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(gates.values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
