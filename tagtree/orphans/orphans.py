"""tagtree-orphans: does tagtree-reach find text whose structure elements are cut off from the tree?

A screen reader reads a tagged PDF from the structure tree's root down. veraPDF issue #1629
(open, milestone 1.32.1) attaches a PDF whose page-1 MCIDs 15, 16 and 19 sit in the ParentTree,
but whose structure elements cannot be reached from StructTreeRoot; veraPDF 1.30.2 does not
report it. tagtree classes such text as "dangling". This runs tagtree.py, exactly as committed
for tagtree-reach, on that file and checks that the MCIDs it calls dangling are exactly the ones
the reporter named. Pre-registered in docs/tagtree-orphans-prereg.md. Stores counts only, no text.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import hashlib
import io
import json
import os
import sys
import urllib.request

__version__ = "0.1.0"

UA = "MV2-tagtree-orphans/%s (Munim, Inc.; mv2@munimtech.com)" % __version__
MAX_PAGES = 3  # as in tagtree-reach

CASES = [
    {"id": "verapdf-1629",
     "issue": "https://github.com/veraPDF/veraPDF-library/issues/1629",
     "url": "https://github.com/user-attachments/files/31915681/content_with_MCID_not_tagged.pdf",
     "page": 1, "orphan_mcids": [15, 16, 19]},
]


def split(chars, reach):
    """Text characters per MCID on one page, and those whose MCID the root-down walk never reached.
    chars are tagtree device tuples (kind, mcid, x0, x1, top, height)."""
    text, dangling = collections.Counter(), collections.Counter()
    for kind, mcid, *_ in chars:
        if kind == "mcid":
            text[str(mcid)] += 1
            if mcid not in reach:
                dangling[str(mcid)] += 1
    return {"text": dict(text), "dangling": dict(dangling)}


def mcid_pages(data, max_pages=MAX_PAGES):
    """split() for each of the first pages, keyed "1", "2", ...; None if there is no structure tree.
    Uses tagtree's own walk and device, the same steps as tagtree.analyze_tags."""
    import tagtree
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdftypes import resolve1

    doc = PDFDocument(PDFParser(io.BytesIO(data)))
    root = resolve1(doc.catalog.get("StructTreeRoot"))
    if not isinstance(root, dict):
        return None
    pages = []
    for page in PDFPage.create_pages(doc):
        pages.append(page)
        if len(pages) >= max_pages:
            break
    order, wildcard, _ = tagtree.walk_tree(root, {p.pageid: i for i, p in enumerate(pages)})
    rsrc = PDFResourceManager(caching=True)
    device = tagtree.make_device(rsrc)
    interp = PDFPageInterpreter(rsrc, device)
    out = {}
    for i, page in enumerate(pages):
        device.reset()
        interp.process_page(page)
        out[str(i + 1)] = split(device.chars, set(order.get(i, [])) | wildcard)
    return out


def judge(case, pages, record):
    """The pre-registered verdicts O1-O3 for one case."""
    if pages is None or record.get("result") != "ok":
        return {"O1_dangling_text": None, "O2_exact_mcids": None, "O3_counts_agree": None,
                "named_with_text": [], "dangling_mcids": []}
    p = pages.get(str(case["page"]), {"text": {}, "dangling": {}})
    with_text = sorted(m for m in case["orphan_mcids"] if p["text"].get(str(m), 0) > 0)
    got = sorted(int(m) for m in p["dangling"])
    total = sum(sum(pg["dangling"].values()) for pg in pages.values())
    return {
        "O1_dangling_text": record["dangling"] > 0 if with_text else None,
        "O2_exact_mcids": got == with_text if with_text else None,
        "O3_counts_agree": total == record["dangling"],
        "named_with_text": with_text,
        "dangling_mcids": got,
    }


def report(rows):
    out = ["# tagtree-reach on orphaned structure elements (orphans %s)" % __version__, "",
           "Machine checks only. Counts, not text.", "",
           "| Case | Result | Reach | Untag | Dangl | Named MCIDs with text | Dangling MCIDs (page) "
           "| O1 | O2 | O3 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rec, v = r.get("record", {}), r.get("verdicts", {})
        out.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], rec.get("result", r.get("result")), rec.get("reachable", ""),
            rec.get("untagged", ""), rec.get("dangling", ""), v.get("named_with_text", ""),
            v.get("dangling_mcids", ""), v.get("O1_dangling_text"), v.get("O2_exact_mcids"),
            v.get("O3_counts_agree")))
    return "\n".join(out) + "\n"


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


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

    os.makedirs(args.data_dir, exist_ok=True)
    rows = []
    for case in CASES:
        row = {"id": case["id"], "issue": case["issue"], "page": case["page"],
               "orphan_mcids": case["orphan_mcids"]}
        local = os.path.join(args.data_dir, case["id"] + ".pdf")
        if not os.path.exists(local):
            try:
                data = fetch(case["url"])
                with open(local, "wb") as f:
                    f.write(data)
            except Exception as e:
                rows.append(dict(row, result="download_error", error=str(e)[:200]))
                continue
        with open(local, "rb") as f:
            data = f.read()
        row["sha256"] = hashlib.sha256(data).hexdigest()
        row["record"] = tagtree.analyze_file(local, timeout=120)
        try:
            row["pages"] = mcid_pages(data)
        except Exception as e:
            row["pages"], row["pages_error"] = None, "%s: %s" % (type(e).__name__, str(e)[:200])
        row["verdicts"] = judge(case, row["pages"], row["record"])
        rows.append(row)

    summary = {"version": __version__, "tagtree_version": tagtree.__version__,
               "max_pages": MAX_PAGES, "cases": rows}
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    text = report(rows)
    with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
