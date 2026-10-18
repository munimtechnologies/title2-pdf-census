"""objstm-census: how often does a PDF's cross-reference stream give an object-stream member an
index that disagrees with the stream's own header, and does it change what tagtree reads?

tagtree-diag-v2 found that in two tagged PDFs saved by Word for Microsoft 365, most objects
stored in object streams have a cross-reference index that points at a different header slot
from the one listing their number; pdfminer.six 20260107 trusts the index and returned the wrong
objects, so tagtree 0.1.0 misread both files. tagtree 0.1.1 finds members by number.

This re-runs tagtree-reach's seeded crawl (title2-pdf-census 0.2.2: the same 600 sites, pages
and per-site choice of PDFs) with tagtree 0.1.1 and, for every chosen PDF, compares each
compressed object's cross-reference index with its slot in the object stream's header
(diag2.header_check, on pypdf). Where any disagree, it also reads the PDF with
`tagtree.py analyze --xref-index` (as 0.1.0 did) to see whether tagtree's record changes.

Pre-registered in docs/objstm-census-prereg.md. Stores no document text: counts and hashes, and,
in the private file only, URLs and Producer strings.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time

__version__ = "0.1.0"

UA = ("MV2-objstm-census/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)
LEAK, MIN_CONTENT = 0.05, 50  # tagtree's LEAK_THRESHOLD and MIN_CONTENT
# The record fields compared between tagtree 0.1.1 and --xref-index.
TAGTREE_KEYS = ("result", "elements", "wildcard_mcids", "reachable", "untagged", "dangling",
                "artifact", "content_chars", "leak_share", "shell", "page_discordance",
                "upward_jumps")
O_KEYS = ("compressed_objects", "streams", "index_ok", "index_wrong", "absent",
          "elements_index_wrong", "duplicate_numbers", "streams_with_wrong_index",
          "streams_header_ascending", "wrong_index_is_sorted_rank")
PUBLIC_FIELDS = ("url_sha256", "kind", "producer_family", "created", "result", "pages_analyzed",
                 "elements", "capped", "stm_refs", "wildcard_mcids", "reachable", "untagged",
                 "dangling", "artifact", "xobject", "named", "content_chars", "leak_share", "shell",
                 "page_discordance", "upward_jumps")
# The two files tagtree-diag-v2 read (results/diag-v2/diag2.json): bytes and index_wrong.
KNOWN = {
    "c8c71fae13ccf1cf19cd67e19caf9f6caccad3bb0c4dc520ad8939e3c0b425b7":
        ("58f6f62bc3de1b7c9090235cfb74ddf48bc9d68a27482dd9ab0d890d05394649", 785),
    "5b10b0e8850b95ae1ae47e646da889ea9a5cc8b2fc34ca1f9e36631a57363ac3":
        ("b2696d00fc5b69095cf2258436756f7cc388f07a22172f954014e5db9ef84bd5", 3122),
}
# Pre-registered thresholds (docs/objstm-census-prereg.md).
O1_MAX_SHARE = 0.05   # PDFs with object streams that have any index/header disagreement
O2_MIN_WORD = 0.80    # of those, the share whose producer family is Word
O3_MAX_CHANGED = 2    # eligible PDFs whose tagtree record changes with --xref-index


def err(e):
    return "%s: %s" % (type(e).__name__, str(e)[:160])


# ---------------------------------------------------------------- one PDF

def is_hybrid(data):
    """A classic cross-reference table that also points to a cross-reference stream."""
    return b"/XRefStm" in data


def check_bytes(data):
    """Index against header for every compressed object of one PDF (bytes), on pypdf."""
    import diag2
    found, objstm, headers, producer = diag2.pypdf_side(data)
    h = diag2.header_check(found, objstm, headers)
    row = {"result": "ok", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "hybrid": is_hybrid(data), "pypdf_elements": len(found)}
    row.update({k: h.get(k, 0) for k in O_KEYS})
    row["producer"] = producer
    row["word365"] = "Word for Microsoft 365" in producer
    return row


def check_file(path, timeout=120):
    """check_bytes in a child process, so a hang or crash costs one PDF, not the run."""
    cmd = [sys.executable, os.path.abspath(__file__), "check", path]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"result": "timeout"}
    if p.returncode != 0 or not p.stdout.strip():
        return {"result": "error", "error": (p.stderr.strip().splitlines() or [""])[-1][:200]}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except ValueError:
        return {"result": "error", "error": "no JSON from the child process"}


def differs(a, b):
    return any(a.get(k) != b.get(k) for k in TAGTREE_KEYS)


# ---------------------------------------------------------------- crawl

def run(census_path, out_dir, sites, workers, minutes):
    import importlib.util
    import tagtree
    spec = importlib.util.spec_from_file_location("census", census_path)
    census = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(census)
    if census.__version__ != "0.2.2" or tagtree.__version__ != "0.1.1":
        print("need census 0.2.2 and tagtree 0.1.1", file=sys.stderr)
        return 1
    census.UA = UA  # robots.txt is checked for this agent
    first = tagtree.analyze_file

    def both(path, timeout=90):
        rec = first(path, timeout)
        rec["o"] = check_file(path)
        if rec["o"].get("index_wrong"):
            rec["xref_index"] = first(path, timeout, xref_index=True)
        return rec

    tagtree.analyze_file = both  # run_site looks it up at call time
    cohort = None
    for wait in (60, 180, 300, 0):
        try:
            cohort = census.fetch_cohort()
            break
        except Exception as e:
            print("cohort failed (%s), waiting %d s" % (e, wait), file=sys.stderr)
            time.sleep(wait)
    if not cohort:
        return 1
    print("%d governments in the cohort" % len(cohort), flush=True)
    # The same sample as tagtree-reach-v1 and tagtree-xcheck-v1: same seed, sites, pages, PDFs.
    tagtree.crawl(census, cohort, sites, out_dir, workers, 8, 8, 3, 1.0, minutes)
    return 0


# ---------------------------------------------------------------- summary

def eligible(d):
    return d.get("result") == "ok" and not d.get("capped") and (d.get("content_chars") or 0) >= MIN_CONTENT


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def share(k, n):
    return {"k": k, "n": n, "share": round(k / n, 4) if n else None, "ci95": wilson(k, n)}


def counts(rows):
    """{key: [PDFs with object streams, of which with a wrong index]}"""
    out = collections.defaultdict(lambda: [0, 0])
    for key, d in rows:
        out[key][0] += 1
        out[key][1] += int(d["o"]["index_wrong"] > 0)
    return {k: v for k, v in sorted(out.items(), key=lambda kv: str(kv[0]))}


def summarize(docs):
    el = [d for d in docs if eligible(d)]
    checked = [d for d in el if d.get("o", {}).get("result") == "ok"]
    objstm = [d for d in checked if d["o"]["compressed_objects"] > 0]
    wrong = [d for d in objstm if d["o"]["index_wrong"] > 0]
    changed = [d for d in wrong if "xref_index" in d and differs(d, d["xref_index"])]
    word = sum(1 for d in wrong if d.get("producer_family") == "word")
    o1 = share(len(wrong), len(objstm))
    o2 = share(word, len(wrong))
    known = {}
    for d in docs:
        if d.get("url_sha256") in KNOWN:
            sha, expected = KNOWN[d["url_sha256"]]
            o = d.get("o", {})
            known[d["url_sha256"][:8]] = {
                "eligible": eligible(d), "same_bytes": o.get("sha256") == sha,
                "index_wrong": o.get("index_wrong"), "expected": expected,
                "changed": d in changed}
    fractions = [d["o"]["index_wrong"] / d["o"]["compressed_objects"] for d in wrong]
    return {
        "version": __version__,
        "pdfs": len(docs),
        "tagtree_results": dict(collections.Counter(d.get("result") for d in docs)),
        "eligible": len(el),
        "check_results": dict(collections.Counter(d.get("o", {}).get("result") for d in el)),
        "checked": len(checked),
        "with_object_streams": len(objstm),
        "with_wrong_index": len(wrong),
        "changed_by_xref_index": len(changed),
        "O1_wrong_share": dict(o1, met=None if o1["share"] is None else o1["share"] < O1_MAX_SHARE),
        "O2_word_share": dict(o2, met=None if o2["share"] is None else o2["share"] >= O2_MIN_WORD),
        "O3_changed": {"k": len(changed), "max": O3_MAX_CHANGED, "met": len(changed) <= O3_MAX_CHANGED},
        "known_files": known,
        "explore_by_family": counts((d.get("producer_family"), d) for d in objstm),
        "explore_hybrid": counts(("hybrid" if d["o"].get("hybrid") else "not_hybrid", d) for d in objstm),
        "explore_word365": counts((("word365" if d["o"].get("word365") else "other_word"), d)
                                  for d in objstm if d.get("producer_family") == "word"),
        "explore_wrong_created_year": dict(sorted(collections.Counter(
            (d.get("created") or "")[:4] or "none" for d in wrong).items())),
        "explore_wrong_fraction_median": round(statistics.median(fractions), 4) if fractions else None,
        "explore_elements_index_wrong": sum(d["o"].get("elements_index_wrong", 0) for d in wrong),
        "explore_leaky_0_1_1": share(sum(1 for d in el if (d.get("leak_share") or 0) >= LEAK), len(el)),
        "explore_shell_0_1_1": share(sum(1 for d in el if d.get("shell")), len(el)),
    }


def public(d):
    row = {k: d[k] for k in PUBLIC_FIELDS if k in d}
    if "o" in d:
        row["o"] = {k: v for k, v in d["o"].items() if k not in ("producer", "error")}
    if "xref_index" in d:
        row["xref_index"] = {k: d["xref_index"].get(k) for k in TAGTREE_KEYS}
    return row


def pct(c):
    if not c or c.get("share") is None:
        return "n/a"
    return "%d of %d, %.1f%% (%.1f-%.1f)" % (c["k"], c["n"], 100 * c["share"],
                                             100 * c["ci95"][0], 100 * c["ci95"][1])


def report(s):
    yes = {True: "yes", False: "**no**", None: "not testable"}
    lines = ["# objstm-census results (machine summary)", "",
             "PDFs analysed %d; eligible %d; index check ok on %d; with object streams %d; with a wrong "
             "index %d; tagtree record changed by --xref-index %d." % (
                 s["pdfs"], s["eligible"], s["checked"], s["with_object_streams"], s["with_wrong_index"],
                 s["changed_by_xref_index"]), "",
             "## Pre-registered predictions", "",
             "| Prediction | Measured | Held? |", "|---|---|---|",
             "| O1: under 5%% of PDFs with object streams have a wrong index | %s | %s |" % (
                 pct(s["O1_wrong_share"]), yes[s["O1_wrong_share"]["met"]]),
             "| O2: 80%%+ of those are Word output | %s | %s |" % (
                 pct(s["O2_word_share"]), yes[s["O2_word_share"]["met"]]),
             "| O3: at most 2 PDFs change their tagtree record | %d | %s |" % (
                 s["O3_changed"]["k"], yes[s["O3_changed"]["met"]]), "",
             "## Known files", ""]
    for h, k in s["known_files"].items():
        lines.append("- %s: %s" % (h, json.dumps(k)))
    lines += ["", "## Exploratory (no prediction)", "",
              "- By producer family [with object streams, wrong index]: %s" % json.dumps(s["explore_by_family"]),
              "- Hybrid files: %s" % json.dumps(s["explore_hybrid"]),
              "- Word for Microsoft 365 against other Word: %s" % json.dumps(s["explore_word365"]),
              "- Wrong index by creation year: %s" % json.dumps(s["explore_wrong_created_year"]),
              "- Median share of compressed objects with a wrong index (files with any): %s"
              % s["explore_wrong_fraction_median"],
              "- tagtree 0.1.1 leaky: %s" % pct(s["explore_leaky_0_1_1"]),
              "- tagtree 0.1.1 shell page: %s" % pct(s["explore_shell_0_1_1"]), ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="print the index check of one PDF as JSON")
    c.add_argument("path")
    r = sub.add_parser("run", help="re-run tagtree-reach's crawl with tagtree 0.1.1 and the index check")
    r.add_argument("--census", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--sites", type=int, default=600)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--max-minutes", type=float, default=150)
    s = sub.add_parser("summarize")
    s.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    if args.cmd == "check":
        try:
            with open(args.path, "rb") as f:
                row = check_bytes(f.read())
        except Exception as e:
            row = {"result": "error", "error": err(e)}
        print(json.dumps(row))
        return 0
    if args.cmd == "run":
        return run(args.census, args.out_dir, args.sites, args.workers, args.max_minutes)
    with open(os.path.join(args.out_dir, "docs-private.jsonl"), encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]
    summary = summarize(docs)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(args.out_dir, "objstm-public.jsonl"), "w", encoding="utf-8") as f:
        for d in docs:
            if eligible(d):
                f.write(json.dumps(public(d)) + "\n")
    text = report(summary)
    with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
