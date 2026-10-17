"""tagtree-verapdf: does tagtree-reach agree with the veraPDF corpus's labels?

The veraPDF corpus (CC BY 4.0) holds small PDF/UA-1 test files. Each file's name gives the
ISO 14289-1 clause it tests and whether it should pass or fail (e.g. 7.1-t03-fail-a.pdf), and
its outline describes the test. This runs tagtree.py's reachability analysis on every PDF/UA-1
file at a fixed corpus commit, so the measure can be checked against known answers before its
results on government PDFs are trusted. Pre-registered in docs/tagtree-verapdf-prereg.md.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"

CORPUS = "veraPDF/veraPDF-corpus"
COMMIT = "bb75f4f0073d9350dfd058c0162a367e6fadf25e"
UA = "MV2-tagtree-verapdf/%s (Munim, Inc.; mv2@munimtech.com)" % __version__
NAME = re.compile(r"^(\d+(?:\.\d+)*)-t(\d+)-(pass|fail)-([a-z]+)\.pdf$")
SPECIFICITY = 0.90  # V3: share of analysed pass files with no unreachable text

# The "7.1 General" files as listed on GitHub at COMMIT, used if the tree API is unavailable.
FALLBACK = ["PDF_UA-1/7.1 General/7.1-t%s.pdf" % s for s in (
    "01-fail-a", "01-pass-a", "01-pass-b", "02-fail-a", "02-pass-a", "02-pass-b",
    "03-fail-a", "03-fail-b", "03-pass-a", "03-pass-b", "04-fail-a", "04-pass-a",
    "05-fail-a", "05-fail-b", "05-fail-c", "05-fail-d", "05-pass-a", "05-pass-b",
    "06-fail-a", "06-pass-a", "07-fail-a", "07-pass-a", "08-fail-a", "08-pass-a",
    "09-fail-a", "09-pass-a", "10-fail-a", "10-fail-b", "10-pass-a", "11-fail-a")]


def parse(path):
    """Clause, test number, expected verdict and variant from a corpus path, or None."""
    m = NAME.match(path.rsplit("/", 1)[-1])
    if not m:
        return None
    return {"clause": m.group(1), "test": int(m.group(2)), "verdict": m.group(3),
            "variant": m.group(4)}


def ua_paths(tree):
    """PDF/UA-1 test files in a GitHub git-tree response, sorted."""
    return sorted(e["path"] for e in tree.get("tree", [])
                  if e.get("type") == "blob" and e["path"].startswith("PDF_UA-1/")
                  and e["path"].lower().endswith(".pdf") and parse(e["path"]))


def unreachable(row):
    """Untagged + dangling characters, or None if the file was not analysed."""
    if row.get("result") != "ok":
        return None
    return row["untagged"] + row["dangling"]


def judge(rows):
    """The pre-registered verdicts V1-V3 over per-file rows."""
    t03 = [r for r in rows if r["clause"] == "7.1" and r["test"] == 3]
    fail = [r for r in t03 if r["verdict"] == "fail"]
    good = [r for r in t03 if r["verdict"] == "pass"]
    fail_ok = [r for r in fail if unreachable(r) is not None]
    good_ok = [r for r in good if unreachable(r) is not None]
    passes = [r for r in rows if r["verdict"] == "pass" and unreachable(r) is not None
              and r.get("content_chars", 0) > 0]
    clean = [r for r in passes if unreachable(r) == 0]
    spec = round(len(clean) / len(passes), 4) if passes else None
    return {
        "V1_t03_fail": {"files": len(fail), "analysed": len(fail_ok),
                        "with_unreachable": sum(1 for r in fail_ok if unreachable(r) > 0),
                        "met": (all(unreachable(r) > 0 for r in fail_ok) and len(fail_ok) == len(fail))
                        if fail_ok else None},
        "V2_t03_pass": {"files": len(good), "analysed": len(good_ok),
                        "with_unreachable": sum(1 for r in good_ok if unreachable(r) > 0),
                        "met": (all(unreachable(r) == 0 for r in good_ok) and len(good_ok) == len(good))
                        if good_ok else None},
        "V3_pass_specificity": {"analysed_with_text": len(passes), "clean": len(clean),
                                "share": spec, "met": None if spec is None else spec >= SPECIFICITY,
                                "leaky_files": [r["file"] for r in passes if unreachable(r) > 0]},
    }


def cell(x, limit=120):
    s = "" if x is None else str(x)
    s = s.replace("|", "/").replace("\n", " ")
    return s if len(s) <= limit else s[:limit - 3] + "..."


def report(summary, rows):
    v = summary["verdicts"]
    out = ["# tagtree-reach vs the veraPDF PDF/UA-1 corpus (validate %s, tagtree %s)" % (
               summary["version"], summary["tagtree_version"]), "",
           "veraPDF corpus %s at commit %s (CC BY 4.0), %d PDF/UA-1 files (list from %s). "
           "Machine checks only." % (CORPUS, COMMIT[:7], summary["files"], summary["list_source"]), "",
           "- Results: %s" % json.dumps(summary["results"]), "",
           "## Pre-registered checks", "",
           "| Check | Measured | Met |", "|---|---|---|",
           "| V1: every 7.1-t03 fail file has unreachable text | %d of %d analysed (%d files) | %s |" % (
               v["V1_t03_fail"]["with_unreachable"], v["V1_t03_fail"]["analysed"],
               v["V1_t03_fail"]["files"], v["V1_t03_fail"]["met"]),
           "| V2: no 7.1-t03 pass file has unreachable text | %d of %d analysed (%d files) | %s |" % (
               v["V2_t03_pass"]["with_unreachable"], v["V2_t03_pass"]["analysed"],
               v["V2_t03_pass"]["files"], v["V2_t03_pass"]["met"]),
           "| V3: %d%%+ of pass files with text have none unreachable | %s of %s (%s) | %s |" % (
               100 * SPECIFICITY, v["V3_pass_specificity"]["clean"],
               v["V3_pass_specificity"]["analysed_with_text"], v["V3_pass_specificity"]["share"],
               v["V3_pass_specificity"]["met"]),
           "", "## Every file", "",
           "| File | Result | Reach | Untag | Dangl | Artif | XObj | Named | Outline |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["file"], r.get("result"), r.get("reachable", ""), r.get("untagged", ""),
            r.get("dangling", ""), r.get("artifact", ""), r.get("xobject", ""), r.get("named", ""),
            cell(r.get("outline"))))
    return "\n".join(out) + "\n"


def outline_titles(path, limit=400):
    """The test's own description: its outline titles, joined."""
    from pypdf import PdfReader
    titles = []

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                t = getattr(it, "title", None)
                if t:
                    titles.append(str(t).strip())

    try:
        walk(PdfReader(path, strict=False).outline)
    except Exception as e:
        return "(outline unreadable: %s)" % type(e).__name__
    return " / ".join(titles)[:limit]


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def list_files():
    url = "https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (CORPUS, COMMIT)
    try:
        tree = json.loads(fetch(url).decode("utf-8"))
        paths = ua_paths(tree)
        if paths and not tree.get("truncated"):
            return paths, "git tree API"
        print("tree API gave %d paths, truncated=%s" % (len(paths), tree.get("truncated")),
              file=sys.stderr)
    except Exception as e:
        print("tree API failed: %s" % e, file=sys.stderr)
    return list(FALLBACK), "fallback list (7.1 General only)"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tagtree
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("pypdf").setLevel(logging.ERROR)

    paths, source = list_files()
    print("%d PDF/UA-1 files (%s)" % (len(paths), source), flush=True)
    os.makedirs(args.data_dir, exist_ok=True)
    rows = []
    for path in paths:
        local = os.path.join(args.data_dir, hashlib.sha1(path.encode("utf-8")).hexdigest() + ".pdf")
        row = {"file": path.rsplit("/", 1)[-1], "path": path, **parse(path)}
        if not os.path.exists(local):
            url = "https://raw.githubusercontent.com/%s/%s/%s" % (
                CORPUS, COMMIT, urllib.parse.quote(path))
            try:
                data = fetch(url)
                with open(local, "wb") as f:
                    f.write(data)
            except Exception as e:
                rows.append(dict(row, result="download_error", error=str(e)[:200]))
                continue
            time.sleep(0.2)
        with open(local, "rb") as f:
            row["sha256"] = hashlib.sha256(f.read()).hexdigest()
        row.update(tagtree.analyze_file(local, timeout=60))
        row["outline"] = outline_titles(local)
        rows.append(row)

    summary = {"version": __version__, "tagtree_version": tagtree.__version__,
               "corpus": CORPUS, "commit": COMMIT, "list_source": source, "files": len(paths),
               "results": dict(collections.Counter(r.get("result") for r in rows)),
               "verdicts": judge(rows)}
    with open(os.path.join(args.out_dir, "results.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    text = report(summary, rows)
    with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
