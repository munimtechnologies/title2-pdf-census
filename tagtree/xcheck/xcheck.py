"""tagtree-xcheck: does a second, independent reader agree with tagtree-reach on the same PDFs?

tagtree-reach (tagtree.py 0.1.0) reads each PDF with pdfminer.six. Its results on US
local-government PDFs (results/tagtree-v1) had no second implementation behind them. This
re-runs the same seeded crawl (title2-pdf-census 0.2.2, the same 600 sites, the same per-site
choice of PDFs) and reads every chosen PDF twice, from the same bytes: once with tagtree, and
once with code written here on pypdf, which parses the file, walks the structure tree and reads
the content streams separately. It also re-runs tagtree's own tree walk on pdfminer's parse and
compares the MCIDs each walk reaches, page by page.

The pypdf reader counts text bytes (not characters: it does not decode fonts), so shares can
differ a little from tagtree's; the checks compare classes and flags, not exact counts.
Pre-registered in docs/tagtree-xcheck-prereg.md. Stores no document text, only counts.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import io
import json
import os
import subprocess
import sys
import time

__version__ = "0.1.0"

UA = ("MV2-tagtree-xcheck/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)
LEAK, MIN_CONTENT, MAX_PAGES, NODE_CAP, MAX_FORM_DEPTH = 0.05, 50, 3, 300_000, 12
WHITESPACE = b" \t\r\n"
TEXT_OPS = (b"Tj", b"TJ", b"'", b'"')
CLASSES = ("reachable", "untagged", "dangling", "artifact", "xobject", "named")
# Pre-registered thresholds (docs/tagtree-xcheck-prereg.md).
THRESHOLDS = {"X1_elements_equal": 0.95, "X2_walks_equal": 0.95, "X3_any_dangling_agree": 0.95,
              "X4_shell_agree": 0.90, "X5_leaky_agree": 0.90}


# ---------------------------------------------------------------- pypdf reader

def resolved(x):
    from pypdf.generic import IndirectObject
    return x.get_object() if isinstance(x, IndirectObject) else x


def raw(d, key):
    """A dictionary entry without resolving it (so references keep their object number)."""
    return d.raw_get(key) if key in d else None


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def pypdf_walk(root, page_ids, node_cap=NODE_CAP):
    """Depth-first walk from StructTreeRoot /K, kids in order, written for pypdf objects.
    Returns ({page index: set of MCIDs}, wildcard MCIDs (no /Pg anywhere above), stats)."""
    from pypdf.generic import IndirectObject
    reached = collections.defaultdict(set)
    wildcard = set()
    stats = {"elements": 0, "stm_refs": 0, "capped": False}
    visited = set()

    def record(mcid, pg):
        mcid = resolved(mcid)
        if not is_int(mcid):
            return
        if isinstance(pg, IndirectObject):
            if pg.idnum in page_ids:
                reached[page_ids[pg.idnum]].add(int(mcid))
        else:
            wildcard.add(int(mcid))

    stack = [(raw(root, "/K"), None)]
    while stack:
        obj, pg = stack.pop()
        if isinstance(obj, IndirectObject):
            if obj.idnum in visited:
                continue
            visited.add(obj.idnum)
            obj = obj.get_object()
        if isinstance(obj, list):
            stack.extend((kid, pg) for kid in reversed(obj))
        elif is_int(obj):
            record(obj, pg)
        elif isinstance(obj, dict):
            if "/S" in obj:
                stats["elements"] += 1
                if stats["elements"] > node_cap:
                    stats["capped"] = True
                    break
                stack.append((raw(obj, "/K"), raw(obj, "/Pg") if "/Pg" in obj else pg))
            elif "/MCID" in obj:
                if "/Stm" in obj:
                    stats["stm_refs"] += 1
                else:
                    record(raw(obj, "/MCID"), raw(obj, "/Pg") if "/Pg" in obj else pg)
    return reached, wildcard, stats


def string_bytes(s):
    if isinstance(s, bytes):
        return bytes(s)
    orig = getattr(s, "original_bytes", None)
    if orig is not None:
        return bytes(orig)
    return str(s).encode("latin-1", "replace")


def text_units(operator, operands):
    """Non-whitespace bytes shown by one text operator."""
    if operator == b"TJ":
        strings = [x for x in (operands[0] if operands else []) if isinstance(x, (str, bytes))]
    elif operands and isinstance(operands[-1], (str, bytes)):
        strings = [operands[-1]]
    else:
        strings = []
    return sum(1 for s in strings for b in string_bytes(s) if b not in WHITESPACE)


def classify(stack):
    """(class, mcid) for text inside a marked-content stack of (tag, mcid, named, form depth)."""
    if any(tag == "/Artifact" for tag, _, _, _ in stack):
        return "artifact", None
    with_mcid = [f for f in stack if f[1] is not None]
    if with_mcid:
        f = with_mcid[-1]
        return ("xobject", None) if f[3] > 0 else ("mcid", f[1])
    if any(f[2] for f in stack):
        return "named", None
    return "none", None


def read_content(ops, resources, reader, stack, out, depth=0, forms=()):
    """Walk content-stream operations, adding (class, mcid, units) to out; recurses into forms."""
    from pypdf.generic import ContentStream, IndirectObject
    for operands, operator in ops:
        if operator == b"BDC":
            props = resolved(operands[1]) if len(operands) > 1 else None
            mcid, named = None, False
            if isinstance(props, dict):
                m = resolved(raw(props, "/MCID"))
                mcid = int(m) if is_int(m) else None
            elif props is not None:
                named = True
            stack.append((str(operands[0]) if operands else "", mcid, named, depth))
        elif operator == b"BMC":
            stack.append((str(operands[0]) if operands else "", None, False, depth))
        elif operator == b"EMC":
            if stack:
                stack.pop()
        elif operator in TEXT_OPS:
            n = text_units(operator, operands)
            if n:
                kind, mcid = classify(stack)
                out.append((kind, mcid, n))
        elif operator == b"Do" and operands and depth < MAX_FORM_DEPTH:
            xobjects = resolved(resources.get("/XObject")) if resources else None
            if not isinstance(xobjects, dict) or operands[0] not in xobjects:
                continue
            ref = raw(xobjects, operands[0])
            key = ref.idnum if isinstance(ref, IndirectObject) else id(ref)
            x = resolved(ref)
            if key in forms or not isinstance(x, dict) or x.get("/Subtype") != "/Form":
                continue
            inner = resolved(x.get("/Resources")) if "/Resources" in x else resources
            read_content(ContentStream(x, reader).operations, inner, reader, stack, out,
                         depth + 1, forms + (key,))


def pdfminer_walk(data, max_pages=MAX_PAGES):
    """tagtree's own walk on pdfminer's parse: ({page index: set of MCIDs}, wildcard, elements)."""
    import tagtree
    from pdfminer.pdfdocument import PDFDocument
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
    order, wildcard, stats = tagtree.walk_tree(root, {p.pageid: i for i, p in enumerate(pages)})
    return {i: set(order.get(i, [])) for i in range(len(pages))}, set(wildcard), stats["elements"]


def analyze_x(data, max_pages=MAX_PAGES):
    """The pypdf reader's record for one PDF (bytes), plus whether both walks reach the same MCIDs."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt("")  # as pdfminer does: an empty user password opens most such files
    catalog = resolved(reader.trailer["/Root"])
    root = resolved(raw(catalog, "/StructTreeRoot"))
    if not isinstance(root, dict):
        return {"result": "no_struct_tree"}
    pages = list(reader.pages)[:max_pages]
    page_ids = {p.indirect_reference.idnum: i for i, p in enumerate(pages)
                if p.indirect_reference is not None}
    reached, wildcard, stats = pypdf_walk(root, page_ids)
    totals, shell = collections.Counter(), False
    for i, page in enumerate(pages):
        contents = page.get_contents()
        found = []
        if contents is not None:
            resources = resolved(page.get("/Resources")) or {}
            read_content(contents.operations, resources, reader, [], found)
        counts = collections.Counter()
        reach = reached.get(i, set()) | wildcard
        for kind, mcid, n in found:
            if kind == "mcid":
                counts["reachable" if mcid in reach else "dangling"] += n
            elif kind == "none":
                counts["untagged"] += n
            else:
                counts[kind] += n
        if counts["reachable"] == 0 and counts["untagged"] + counts["dangling"] >= MIN_CONTENT:
            shell = True
        totals.update(counts)
    content = totals["reachable"] + totals["untagged"] + totals["dangling"]
    row = {"result": "ok", "pages_analyzed": len(pages), "elements": stats["elements"],
           "capped": stats["capped"], "stm_refs": stats["stm_refs"], "wildcard_mcids": len(wildcard),
           **{k: totals[k] for k in CLASSES}, "content_units": content,
           "leak_share": round((totals["untagged"] + totals["dangling"]) / content, 4) if content else None,
           "shell": shell}
    try:
        other = pdfminer_walk(data, max_pages)
        mine = ({i: reached.get(i, set()) for i in range(len(pages))}, wildcard)
        row["walks_equal"] = other is not None and other[:2] == mine
    except Exception as e:
        row["walks_equal"], row["walk_error"] = None, "%s: %s" % (type(e).__name__, str(e)[:120])
    return row


def analyze_x_file(path, timeout=90):
    """analyze_x in a child process, so a hang or crash costs one PDF, not the run."""
    try:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "analyze", path],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"result": "timeout"}
    if p.returncode != 0 or not p.stdout.strip():
        return {"result": "parse_error", "error": (p.stderr.strip().splitlines() or [""])[-1][:200]}
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except ValueError:
        return {"result": "parse_error", "error": "no JSON from the child process"}


# ---------------------------------------------------------------- comparison

def eligible(d):
    """tagtree-reach's eligibility, on tagtree's own record."""
    return d.get("result") == "ok" and not d.get("capped") and d.get("content_chars", 0) >= MIN_CONTENT


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def agree(pairs, test):
    k = sum(1 for d in pairs if test(d))
    return {"n": len(pairs), "k": k, "share": round(k / len(pairs), 4) if pairs else None,
            "ci95": wilson(k, len(pairs))}


def compare(docs):
    """X1-X5 over PDFs that tagtree-reach would count and the pypdf reader read without error."""
    el = [d for d in docs if eligible(d)]
    pairs = [d for d in el if (d.get("x") or {}).get("result") == "ok"]
    walked = [d for d in pairs if d["x"].get("walks_equal") is not None]
    x = {
        "X1_elements_equal": agree(pairs, lambda d: d["x"]["elements"] == d["elements"]),
        "X2_walks_equal": agree(walked, lambda d: d["x"]["walks_equal"]),
        "X3_any_dangling_agree": agree(pairs, lambda d: (d["x"]["dangling"] > 0) == (d["dangling"] > 0)),
        "X4_shell_agree": agree(pairs, lambda d: d["x"]["shell"] == d["shell"]),
        "X5_leaky_agree": agree(pairs, lambda d: d["x"]["leak_share"] is not None
                                and (d["x"]["leak_share"] >= LEAK) == (d["leak_share"] >= LEAK)),
    }
    for name, c in x.items():
        c["met"] = None if c["share"] is None else c["share"] >= THRESHOLDS[name]
    leaky = agree(el, lambda d: d["leak_share"] >= LEAK)
    shells = agree(el, lambda d: d["shell"])
    return {
        "version": __version__,
        "pdfs": len(docs),
        "tagtree_results": dict(collections.Counter(d.get("result") for d in docs)),
        "x_results": dict(collections.Counter((d.get("x") or {}).get("result") for d in el)),
        "eligible": len(el), "pairs": len(pairs), "walk_errors": len(pairs) - len(walked),
        "checks": x,
        "recrawl_tagtree": {"leaky": leaky, "shell": shells,
                            "v1": {"leaky": [49, 753], "shell": [32, 753]}},
        "disagreements": [public(d) for d in pairs if not all(
            test(d) for test in (lambda d: d["x"]["elements"] == d["elements"],
                                 lambda d: d["x"].get("walks_equal") is not False,
                                 lambda d: (d["x"]["dangling"] > 0) == (d["dangling"] > 0),
                                 lambda d: d["x"]["shell"] == d["shell"]))],
    }


TAGTREE_FIELDS = ("url_sha256", "producer_family", "result", "pages_analyzed", "elements", "reachable",
                  "untagged", "dangling", "artifact", "xobject", "named", "content_chars",
                  "leak_share", "shell")


def public(d):
    row = {k: d.get(k) for k in TAGTREE_FIELDS}
    row["x"] = {k: v for k, v in (d.get("x") or {}).items() if k != "error"}
    return row


def pct(c):
    if not c or c["share"] is None:
        return "n/a"
    return "%.1f%% (%d of %d)" % (100 * c["share"], c["k"], c["n"])


def report(s):
    out = ["# tagtree-xcheck results (v%s)" % s["version"], "",
           "tagtree-reach (pdfminer.six) and an independent pypdf reader on the same bytes of the same "
           "local-government PDFs. Machine checks only.", "",
           "- PDFs analysed: %d; eligible for tagtree-reach: %d; read by both: %d; walk errors: %d" % (
               s["pdfs"], s["eligible"], s["pairs"], s["walk_errors"]),
           "- tagtree results: %s; pypdf results on eligible PDFs: %s" % (
               json.dumps(s["tagtree_results"]), json.dumps(s["x_results"])), "",
           "## Pre-registered checks", "", "| Check | Agreement | Threshold | Met |", "|---|---|---|---|"]
    for name, c in s["checks"].items():
        out.append("| %s | %s | %.0f%% | %s |" % (name, pct(c), 100 * THRESHOLDS[name], c["met"]))
    r = s["recrawl_tagtree"]
    out += ["", "## The re-crawl itself (exploratory)", "",
            "- Leaky (tagtree): %s; first run 49 of 753" % pct(r["leaky"]),
            "- Shell (tagtree): %s; first run 32 of 753" % pct(r["shell"]),
            "- Disagreements listed in summary.json: %d" % len(s["disagreements"])]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- run

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="print the pypdf reader's record for one PDF as JSON")
    a.add_argument("path")
    r = sub.add_parser("run", help="re-run tagtree-reach's crawl, reading each PDF with both readers")
    r.add_argument("--census", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--sites", type=int, default=600)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--max-minutes", type=float, default=150)
    s = sub.add_parser("summarize")
    s.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    if args.cmd == "analyze":
        import logging
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        with open(args.path, "rb") as f:
            print(json.dumps(analyze_x(f.read())))
        return 0
    import tagtree
    if args.cmd == "run":
        import importlib.util
        spec = importlib.util.spec_from_file_location("census", args.census)
        census = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(census)
        if census.__version__ != "0.2.2" or tagtree.__version__ != "0.1.0":
            print("need census 0.2.2 and tagtree 0.1.0", file=sys.stderr)
            return 1
        census.UA = UA  # robots.txt is checked for this agent
        first = tagtree.analyze_file

        def both(path, timeout=90):
            rec = first(path, timeout)
            rec["x"] = analyze_x_file(path, timeout)
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
        # The same sample as tagtree-reach-v1: same seed, sites, pages, PDFs per page and per site.
        tagtree.crawl(census, cohort, args.sites, args.out_dir, args.workers, 8, 8, 3, 1.0, args.max_minutes)
        return 0
    with open(os.path.join(args.out_dir, "docs-private.jsonl"), encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]
    summary = compare(docs)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(args.out_dir, "pairs-public.jsonl"), "w", encoding="utf-8") as f:
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
