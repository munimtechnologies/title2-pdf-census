"""doc-first-reach: does reading document-like pages first find PDFs that random page sampling misses?

Pre-registered in docs/doc-first-prereg.md (title2-pdf-census). Two arms, run one after the other
on each site, the same day:
  A  census.crawl_site (0.2.2): 8 inner pages sampled at random, as in the census
  B  site_check.crawl (0.1.1): document-like pages first, one level deeper, early stop
Both read at most 8 inner pages and check at most 2 PDFs (enough to tell whether a readable PDF
is reachable; fewer downloads).
Sets, from the census's second full run (results/v0.2.1/sites.csv):
  zero     every site read (status ok, pages_read > 0) where 0.2.1 found no PDF link
  control  a seeded sample of 100 sites where 0.2.1 found at least one PDF link
Outputs aggregates only (summary.json, summary.md); per-site rows stay in sites.jsonl.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import concurrent.futures
import csv
import json
import logging
import math
import os
import sys
import time

import census as c
import site_check as sc

PAGES, PDFS, CONTROL_N = 8, 2, 100


def select(rows):
    """(zero, control) site rows from a sites.csv of the census."""
    read = [r for r in rows if r["status"] == "ok" and int(r["pages_read"] or 0) > 0]
    zero = [r for r in read if int(r["pdf_links"] or 0) == 0]
    found = {r["website"]: r for r in read if int(r["pdf_links"] or 0) > 0}
    control = [found[w] for w in c.sample(list(found), CONTROL_N, "doc-first-control")]
    return zero, control


def mcnemar_p(b, c_):
    """Two-sided exact McNemar p from the discordant counts (binomial, p = 1/2)."""
    n = b + c_
    if n == 0:
        return 1.0
    k = min(b, c_)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def arm(site, found):
    return {"status": site["status"], "pages_read": site["pages_read"], "pdf_links": site["pdf_links"],
            "pdfs_tried": site["pdfs_tried"], "pdfs_ok": site["pdfs_ok"],
            "doc_pages_read": site.get("doc_pages_read"),
            "results": [r.get("result") for r in found]}


def one(row, group, delay):
    out = {"group": group, "website": row["website"]}
    try:
        out["A"] = arm(*c.crawl_site(row, pages=PAGES, pdfs=PDFS, delay=delay))
    except Exception as e:
        out["A"] = {"status": "crash", "error": str(e)[:200]}
    try:
        out["B"] = arm(*sc.crawl(row["website"], pages=PAGES, pdfs=PDFS, delay=delay))
    except Exception as e:
        out["B"] = {"status": "crash", "error": str(e)[:200]}
    return out


def tally(recs):
    """Paired counts for one set: sites where both arms read the home page."""
    both = [r for r in recs if r["A"].get("status") == "ok" and r["B"].get("status") == "ok"]
    out = {"sites": len(recs), "both_home_ok": len(both)}
    for key, test in (("links", lambda a: a["pdf_links"] > 0), ("readable", lambda a: a["pdfs_ok"] > 0)):
        a = [test(r["A"]) for r in both]
        b = [test(r["B"]) for r in both]
        only_a = sum(1 for x, y in zip(a, b) if x and not y)
        only_b = sum(1 for x, y in zip(a, b) if y and not x)
        out[key] = {"A": sum(a), "B": sum(b), "both": sum(1 for x, y in zip(a, b) if x and y),
                    "only_A": only_a, "only_B": only_b, "neither": sum(1 for x, y in zip(a, b) if not x and not y),
                    "mcnemar_p": mcnemar_p(only_a, only_b)}
    for name in ("A", "B"):
        out["pages_read_" + name] = sum(r[name]["pages_read"] for r in both)
    out["doc_pages_read_B"] = sum(r["B"]["doc_pages_read"] or 0 for r in both)
    return out


def share(k, n):
    return "%d of %d (%.1f%%)" % (k, n, 100.0 * k / n) if n else "%d of 0" % k


def report(summary):
    lines = ["# doc-first-reach results", "",
             "Arm A: census.crawl_site %s (random pages). Arm B: site_check.crawl %s (document-like pages "
             "first). At most %d inner pages and %d PDFs per arm. Run %s." % (
                 summary["census_version"], summary["site_check_version"], PAGES, PDFS, summary["ran"]), ""]
    for group in ("zero", "control"):
        t = summary[group]
        n = t["both_home_ok"]
        lines += ["## %s (%d sites, %d with both home pages read)" % (group, t["sites"], n), ""]
        for key in ("links", "readable"):
            x = t[key]
            lines.append("- %s: A %s, B %s; only A %d, only B %d; exact McNemar p = %.2g" % (
                "At least one PDF link" if key == "links" else "At least one readable PDF",
                share(x["A"], n), share(x["B"], n), x["only_A"], x["only_B"], x["mcnemar_p"]))
        lines.append("- Pages read: A %d, B %d (%d of B's document-like)" % (
            t["pages_read_A"], t["pages_read_B"], t["doc_pages_read_B"]))
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args(argv)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    with open(args.sites, encoding="utf-8", newline="") as f:
        zero, control = select(list(csv.DictReader(f)))
    print("zero", len(zero), "control", len(control), flush=True)
    jobs = [(r, "zero") for r in zero] + [(r, "control") for r in control]
    recs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool, \
            open(os.path.join(args.out_dir, "sites.jsonl"), "w", encoding="utf-8") as fout:
        futures = [pool.submit(one, r, g, args.delay) for r, g in jobs]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            rec = fut.result()
            recs.append(rec)
            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            if i % 25 == 0:
                print("%d/%d sites" % (i, len(futures)), flush=True)
    summary = {"census_version": c.__version__, "site_check_version": sc.__version__,
               "ran": time.strftime("%Y-%m-%d", time.gmtime()), "pages": PAGES, "pdfs": PDFS,
               "zero": tally([r for r in recs if r["group"] == "zero"]),
               "control": tally([r for r in recs if r["group"] == "control"])}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    text = report(summary)
    with open(os.path.join(args.out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
