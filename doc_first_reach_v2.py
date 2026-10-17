"""doc-first-reach v2: does site_check 0.1.2's fallback keep what document-first reading gained
and win back what it lost?

Pre-registered in docs/doc-first-v2-prereg.md (title2-pdf-census). Three arms on each site, the
same day:
  A  census.crawl_site (0.2.2): 8 inner pages sampled at random, as in the census
  B  site_check 0.1.1 (site_check_011.py): document-like pages first, one level deeper, early stop
  C  site_check 0.1.2: the same, but once half the pages are read with no PDF link, other pages first
A runs first; B and C follow in an order set per site by a hash. Each reads at most 8 inner pages
and checks at most 2 PDFs.
Sets, from the census's second full run (results/v0.2.1/sites.csv):
  zero      every site read (status ok, pages_read > 0) where 0.2.1 found no PDF link (as in v1)
  control2  200 sites where 0.2.1 found a PDF link, leaving out v1's 100 control sites
  smoke     ada.gov and section508.gov, the Actor's examples (reported, no prediction)
Outputs aggregates only (summary.json, summary.md), plus the two smoke sites; per-site rows stay
in sites.jsonl.

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
import site_check_011 as sc11

PAGES, PDFS, CONTROL_N, CONTROL2_N = 8, 2, 100, 200
SMOKE = ("https://www.ada.gov/", "https://www.section508.gov/")
ARMS = ("A", "B", "C")
PAIRS = (("C", "A"), ("C", "B"), ("B", "A"))
GROUPS = ("zero", "control2", "smoke")


def select(rows):
    """(zero, control2) site rows from a sites.csv of the census. control2 leaves out the 100
    control sites of the first test (seed "doc-first-control")."""
    read = [r for r in rows if r["status"] == "ok" and int(r["pages_read"] or 0) > 0]
    zero = [r for r in read if int(r["pdf_links"] or 0) == 0]
    found = {r["website"]: r for r in read if int(r["pdf_links"] or 0) > 0}
    used = set(c.sample(list(found), CONTROL_N, "doc-first-control"))
    rest = [w for w in found if w not in used]
    return zero, [found[w] for w in c.sample(rest, CONTROL2_N, "doc-first-control-2")]


def mcnemar_p(b, c_):
    """Two-sided exact McNemar p from the discordant counts (binomial, p = 1/2)."""
    n = b + c_
    if n == 0:
        return 1.0
    k = min(b, c_)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def order(website):
    """A first, then B and C in an order set by a hash of the website."""
    return "A" + "".join(c.sample(["B", "C"], 2, website))


def arm(site, found):
    return {"status": site["status"], "pages_read": site["pages_read"], "pdf_links": site["pdf_links"],
            "pdfs_tried": site["pdfs_tried"], "pdfs_ok": site["pdfs_ok"],
            "doc_pages_read": site.get("doc_pages_read"), "fell_back": site.get("fell_back"),
            "results": [r.get("result") for r in found]}


def one(row, group, delay):
    crawls = {"A": lambda: c.crawl_site(row, pages=PAGES, pdfs=PDFS, delay=delay),
              "B": lambda: sc11.crawl(row["website"], pages=PAGES, pdfs=PDFS, delay=delay),
              "C": lambda: sc.crawl(row["website"], pages=PAGES, pdfs=PDFS, delay=delay)}
    out = {"group": group, "website": row["website"], "order": order(row["website"])}
    for name in out["order"]:
        try:
            out[name] = arm(*crawls[name]())
        except Exception as e:
            out[name] = {"status": "crash", "error": str(e)[:200]}
    return out


def tally(recs):
    """Counts for one set, on sites where all three arms read the home page, with paired tests."""
    both = [r for r in recs if all(r[a].get("status") == "ok" for a in ARMS)]
    out = {"sites": len(recs), "all_home_ok": len(both)}
    for key, test in (("links", lambda a: a["pdf_links"] > 0), ("readable", lambda a: a["pdfs_ok"] > 0)):
        hit = {a: [test(r[a]) for r in both] for a in ARMS}
        out[key] = {a: sum(hit[a]) for a in ARMS}
        for x, y in PAIRS:
            only_x = sum(1 for p, q in zip(hit[x], hit[y]) if p and not q)
            only_y = sum(1 for p, q in zip(hit[x], hit[y]) if q and not p)
            out[key]["%s_vs_%s" % (x, y)] = {"only_" + x: only_x, "only_" + y: only_y,
                                             "mcnemar_p": mcnemar_p(only_x, only_y)}
    for a in ARMS:
        out["pages_read_" + a] = sum(r[a]["pages_read"] for r in both)
    for a in ("B", "C"):
        out["doc_pages_read_" + a] = sum(r[a]["doc_pages_read"] or 0 for r in both)
    out["fell_back_C"] = sum(1 for r in both if r["C"].get("fell_back"))
    return out


def share(k, n):
    return "%d of %d (%.1f%%)" % (k, n, 100.0 * k / n) if n else "%d of 0" % k


def smoke_line(r):
    parts = []
    for a in ARMS:
        x = r[a]
        if x.get("status") != "ok":
            parts.append("%s %s" % (a, x.get("status")))
        else:
            parts.append("%s pages %d, PDF links %d, readable PDFs %d" % (a, x["pages_read"], x["pdf_links"],
                                                                         x["pdfs_ok"]))
    return "- %s: %s" % (c.bare_host(r["website"]), "; ".join(parts))


def report(summary, smoke=()):
    lines = ["# doc-first-reach v2 results", "",
             "Arm A: census.crawl_site %s (random pages). Arm B: site_check %s (document-like pages first). "
             "Arm C: site_check %s (the same, then other pages once half the pages found no PDF link). "
             "At most %d inner pages and %d PDFs per arm. Run %s." % (
                 summary["census_version"], summary["site_check_011_version"], summary["site_check_version"],
                 PAGES, PDFS, summary["ran"]), ""]
    for group in GROUPS:
        t = summary[group]
        n = t["all_home_ok"]
        lines += ["## %s (%d sites, %d with all three home pages read)" % (group, t["sites"], n), ""]
        for key in ("links", "readable"):
            x = t[key]
            lines.append("- %s: A %s, B %s, C %s" % (
                "At least one PDF link" if key == "links" else "At least one readable PDF",
                share(x["A"], n), share(x["B"], n), share(x["C"], n)))
            for a, b in PAIRS:
                d = x["%s_vs_%s" % (a, b)]
                lines.append("  - %s against %s: only %s %d, only %s %d; exact McNemar p = %.2g" % (
                    a, b, a, d["only_" + a], b, d["only_" + b], d["mcnemar_p"]))
        lines.append("- Pages read: A %d, B %d (%d document-like), C %d (%d document-like); C fell back "
                     "to other pages at %d sites" % (t["pages_read_A"], t["pages_read_B"], t["doc_pages_read_B"],
                                                     t["pages_read_C"], t["doc_pages_read_C"], t["fell_back_C"]))
        lines.append("")
    if smoke:
        lines += ["## smoke sites", ""] + [smoke_line(r) for r in smoke] + [""]
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
        zero, control2 = select(list(csv.DictReader(f)))
    print("zero", len(zero), "control2", len(control2), "smoke", len(SMOKE), flush=True)
    jobs = ([(r, "zero") for r in zero] + [(r, "control2") for r in control2]
            + [({"website": u}, "smoke") for u in SMOKE])
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
               "site_check_011_version": sc11.__version__,
               "ran": time.strftime("%Y-%m-%d", time.gmtime()), "pages": PAGES, "pdfs": PDFS}
    for group in GROUPS:
        summary[group] = tally([r for r in recs if r["group"] == group])
    smoke = sorted((r for r in recs if r["group"] == "smoke"), key=lambda r: r["website"])
    summary["smoke_sites"] = smoke
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    text = report(summary, smoke)
    with open(os.path.join(args.out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
