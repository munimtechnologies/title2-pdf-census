"""tagtree-reach: how much of a "tagged" PDF can a screen reader actually reach?

A tagged PDF carries a structure tree, and assistive technology reads the page in
the order of that tree. Text on the page that no structure element points to
(content that is neither tagged nor marked as an artifact, or marked content
whose ID the tree never references) is skipped or read out of context. Checkers
report this as pass/fail per document; this tool measures it as a share of the
page text, and also compares the tree's order with the order of the content
stream, for PDFs that large US local governments publish.

For each PDF it walks the structure tree from its root (as a screen reader
does), collects the marked-content IDs (MCIDs) it reaches on each of the first
pages, and classifies every visible character on those pages as reachable,
untagged (no MCID), dangling (an MCID the tree never reaches), artifact, or
unknown (an MCID inside a form XObject, or a property list given by name).

The crawl is title2-pdf-census 0.2.2's (public pages only, robots.txt honoured,
1 s between requests to a site), imported from its published code. Stores no
document text, only counts. Machine checks only: never a WCAG judgment.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import concurrent.futures
import hashlib
import io
import json
import os
import random
import statistics
import subprocess
import sys
import tempfile
import time

__version__ = "0.1.0"

UA = ("MV2-tagtree-reach/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)
SEED = "tagtree-v1"
LEAK_THRESHOLD = 0.05   # a PDF is "leaky" if 5%+ of its page text is unreachable
MIN_CONTENT = 50        # non-space characters needed on the analysed pages
MIN_ORDER = 5           # ordered MCIDs a page needs before its order is compared
NODE_CAP = 300_000


# ---------------------------------------------------------------- PDF analysis

def lit(x):
    """The name of a PDF name object (PSLiteral), or None."""
    from pdfminer.psparser import PSLiteral
    if isinstance(x, PSLiteral):
        n = x.name
        return n.decode("latin-1") if isinstance(n, bytes) else n
    return None


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def walk_tree(root, page_ids, node_cap=NODE_CAP):
    """Depth-first walk of the structure tree from its root, kids in order.
    Returns (order, wildcard, stats): order maps a page index to its MCIDs in tag order
    (first visit kept); wildcard holds MCIDs whose page is unknown (no Pg on the element
    or its ancestors), which count as reachable on every page."""
    from pdfminer.pdftypes import PDFObjRef, resolve1
    order = collections.defaultdict(list)
    seen = collections.defaultdict(set)
    wildcard = set()
    stats = {"elements": 0, "stm_refs": 0, "capped": False}
    visited = set()

    def record(mcid, pg):
        if not is_int(mcid):
            return
        pid = pg.objid if isinstance(pg, PDFObjRef) else None
        if pid is None:
            wildcard.add(mcid)
        elif pid in page_ids:
            i = page_ids[pid]
            if mcid not in seen[i]:
                seen[i].add(mcid)
                order[i].append(mcid)

    stack = [(root.get("K"), None)]
    while stack:
        obj, pg = stack.pop()
        if isinstance(obj, PDFObjRef):
            if obj.objid in visited:
                continue
            visited.add(obj.objid)
            obj = resolve1(obj)
        if isinstance(obj, list):
            stack.extend((kid, pg) for kid in reversed(obj))
        elif is_int(obj):
            record(obj, pg)
        elif isinstance(obj, dict):
            if "S" in obj:
                stats["elements"] += 1
                if stats["elements"] > node_cap:
                    stats["capped"] = True
                    break
                stack.append((obj.get("K"), obj.get("Pg", pg)))
            elif "MCID" in obj:
                if "Stm" in obj:
                    stats["stm_refs"] += 1
                else:
                    record(resolve1(obj["MCID"]), obj.get("Pg", pg))
    return order, wildcard, stats


def make_device(rsrcmgr):
    """A pdfminer device that records, for each visible character, its marked-content
    context. Unlike a single "current tag", it keeps a stack, so content after a nested
    span still belongs to the outer MCID."""
    from pdfminer.converter import PDFPageAggregator
    from pdfminer.layout import LTChar
    from pdfminer.pdftypes import resolve1

    class MarkedContentDevice(PDFPageAggregator):
        def __init__(self, rsrcmgr):
            super().__init__(rsrcmgr, laparams=None)
            self.reset()

        def reset(self):
            self.stack, self.chars, self.form_depth = [], [], 0

        def begin_tag(self, tag, props=None):
            mcid, named = None, False
            if isinstance(props, dict):
                m = resolve1(props.get("MCID"))
                mcid = m if is_int(m) else None
            elif props is not None:
                named = True
            self.stack.append((lit(tag), mcid, named, self.form_depth))

        def end_tag(self):
            if self.stack:
                self.stack.pop()

        def begin_figure(self, name, bbox, matrix):
            self.form_depth += 1
            super().begin_figure(name, bbox, matrix)

        def end_figure(self, name):
            self.form_depth = max(0, self.form_depth - 1)
            super().end_figure(name)

        def render_char(self, *args, **kwargs):
            adv = super().render_char(*args, **kwargs)
            objs = getattr(self.cur_item, "_objs", None)
            if objs and isinstance(objs[-1], LTChar) and objs[-1].get_text().strip():
                ch = objs[-1]
                kind, mcid = classify(self.stack)
                self.chars.append((kind, mcid, ch.x0, ch.x1, ch.y1, ch.height))
            return adv

    return MarkedContentDevice(rsrcmgr)


def classify(stack):
    """(kind, mcid) for a character inside the given marked-content stack."""
    if any(frame[0] == "Artifact" for frame in stack):
        return "artifact", None
    with_mcid = [frame for frame in stack if frame[1] is not None]
    if with_mcid:
        frame = with_mcid[-1]
        return ("xobject", None) if frame[3] > 0 else ("mcid", frame[1])
    if any(frame[2] for frame in stack):
        return "named", None
    return "none", None


def discordance(ranks):
    """Share of pairs out of order (normalized Kendall distance) in a list of ranks."""
    n = len(ranks)
    if n < 2:
        return 0.0

    def sort(xs):
        if len(xs) <= 1:
            return xs, 0
        mid = len(xs) // 2
        left, a = sort(xs[:mid])
        right, b = sort(xs[mid:])
        merged, inv, i, j = [], a + b, 0, 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                inv += len(left) - i
                j += 1
        return merged + left[i:] + right[j:], inv

    return sort(list(ranks))[1] / (n * (n - 1) / 2)


def page_metrics(chars, tag_order, wildcard):
    """Character counts by class, order discordance and same-column upward jumps for one page."""
    reach = set(tag_order) | wildcard
    counts = collections.Counter()
    stream_rank, boxes, heights = {}, {}, []
    for kind, mcid, x0, x1, top, h in chars:
        heights.append(h)
        if kind == "mcid":
            if mcid in reach:
                counts["reachable"] += 1
                stream_rank.setdefault(mcid, len(stream_rank))
                b = boxes.get(mcid)
                boxes[mcid] = (min(b[0], x0), max(b[1], x1), max(b[2], top)) if b else (x0, x1, top)
            else:
                counts["dangling"] += 1
        elif kind == "none":
            counts["untagged"] += 1
        else:
            counts[kind] += 1
    seq = [m for m in tag_order if m in stream_rank]
    row = {k: counts.get(k, 0) for k in
           ("reachable", "untagged", "dangling", "artifact", "xobject", "named")}
    row["ordered"] = len(seq)
    row["discordance"] = (round(discordance([stream_rank[m] for m in seq]), 4)
                          if len(seq) >= MIN_ORDER else None)
    line = max(statistics.median(heights), 1.0) if heights else 1.0
    jumps = 0
    for a, b in zip(seq, seq[1:]):
        (ax0, ax1, atop), (bx0, bx1, btop) = boxes[a], boxes[b]
        overlap = min(ax1, bx1) - max(ax0, bx0)
        narrow = max(min(ax1 - ax0, bx1 - bx0), 1.0)
        if btop > atop + 3 * line and overlap >= 0.5 * narrow:
            jumps += 1
    row["upward_jumps"] = jumps
    return row


def analyze_tags(data, max_pages=3):
    """Reachability facts for the first max_pages pages of one PDF (bytes)."""
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdftypes import resolve1

    doc = PDFDocument(PDFParser(io.BytesIO(data)))
    root = resolve1(doc.catalog.get("StructTreeRoot"))
    if not isinstance(root, dict):
        return {"result": "no_struct_tree"}
    pages = []
    for page in PDFPage.create_pages(doc):
        pages.append(page)
        if len(pages) >= max_pages:
            break
    order, wildcard, stats = walk_tree(root, {p.pageid: i for i, p in enumerate(pages)})
    rsrc = PDFResourceManager(caching=True)
    device = make_device(rsrc)
    interp = PDFPageInterpreter(rsrc, device)
    rows = []
    for i, page in enumerate(pages):
        device.reset()
        interp.process_page(page)
        rows.append(page_metrics(device.chars, order.get(i, []), wildcard))
    return doc_row(rows, stats, len(wildcard))


def doc_row(pages, stats, wildcard):
    """One PDF's record from its page rows."""
    total = collections.Counter()
    for p in pages:
        total.update({k: p[k] for k in ("reachable", "untagged", "dangling", "artifact",
                                         "xobject", "named", "upward_jumps")})
    content = total["reachable"] + total["untagged"] + total["dangling"]
    unreachable = total["untagged"] + total["dangling"]
    disc = [p["discordance"] for p in pages if p["discordance"] is not None]
    return {
        "result": "ok", "pages_analyzed": len(pages),
        "elements": stats["elements"], "capped": stats["capped"], "stm_refs": stats["stm_refs"],
        "wildcard_mcids": wildcard,
        **{k: total[k] for k in ("reachable", "untagged", "dangling", "artifact", "xobject", "named")},
        "content_chars": content,
        "leak_share": round(unreachable / content, 4) if content else None,
        "shell": any(p["reachable"] == 0 and p["reachable"] + p["untagged"] + p["dangling"] >= MIN_CONTENT
                     for p in pages),
        "page_discordance": disc,
        "upward_jumps": total["upward_jumps"],
    }


def analyze_file(path, timeout=90):
    """analyze_tags in a child process, so a hang or crash costs one PDF, not the run."""
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


# ---------------------------------------------------------------- crawl

def run_site(census, row, pages, pdfs, per_site, delay, deadline):
    """Crawl one site with the census code, keeping PDF bodies, then analyse up to
    per_site of its tagged, text-bearing PDFs (chosen by hash, not by page order)."""
    bodies = {}

    def get(url, max_bytes, timeout=20):
        resp = census.http_get(url, max_bytes, timeout=timeout)
        if resp.status == 200 and not resp.truncated and b"%PDF" in resp.body[:1024]:
            bodies[url] = resp.body
        return resp

    site, found = census.crawl_site(row, get=get, pages=pages, pdfs=pdfs, delay=delay,
                                    deadline=deadline)
    eligible = {r["url"]: r for r in found if r.get("result") == "ok" and r.get("tagged")
                and not r.get("image_only") and r["url"] in bodies}
    docs = []
    for url in census.sample(list(eligible), per_site, SEED + "|" + row["website"]):
        rec = eligible[url]
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(bodies[url])
        try:
            res = analyze_file(f.name)
        finally:
            os.unlink(f.name)
        docs.append({"qid": rec["qid"], "kind": rec["kind"], "url": url,
                     "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
                     "producer_family": rec.get("producer_family"), "created": rec.get("created"),
                     **res})
    site["pdfs_tagged_eligible"] = len(eligible)
    site["pdfs_analyzed"] = len(docs)
    return site, docs


def crawl(census, cohort, n_sites, out_dir, workers, pages, pdfs, per_site, delay, minutes):
    deadline = time.time() + 60 * minutes if minutes else None
    by_site = {r["website"]: r for r in cohort}
    chosen = census.sample(list(by_site), n_sites, SEED)
    with open(os.path.join(out_dir, "sites-private.jsonl"), "w", encoding="utf-8") as fs, \
            open(os.path.join(out_dir, "docs-private.jsonl"), "w", encoding="utf-8") as fd, \
            concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(run_site, census, by_site[w], pages, pdfs, per_site, delay, deadline)
                for w in chosen]
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            try:
                site, docs = fut.result()
            except Exception as e:
                site, docs = {"status": "crash", "error": str(e)[:200]}, []
            fs.write(json.dumps(site) + "\n")
            for d in docs:
                fd.write(json.dumps(d) + "\n")
            fs.flush()
            fd.flush()
            if i % 50 == 0:
                print("%d/%d sites" % (i, len(futs)), flush=True)


# ---------------------------------------------------------------- summary

def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def share(docs, pred):
    k = sum(1 for d in docs if pred(d))
    return {"n": len(docs), "k": k, "share": round(k / len(docs), 4) if docs else None,
            "ci95": wilson(k, len(docs))}


def cluster_ci(docs, pred, reps=2000, seed=20261017):
    """95% interval for a share, resampling sites (PDFs of one site are not independent)."""
    by_site = collections.defaultdict(list)
    for d in docs:
        by_site[d["qid"]].append(1 if pred(d) else 0)
    groups = list(by_site.values())
    if not groups:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        pick = [groups[rng.randrange(len(groups))] for _ in groups]
        n = sum(len(g) for g in pick)
        vals.append(sum(sum(g) for g in pick) / n)
    vals.sort()
    return [round(vals[int(0.025 * reps)], 4), round(vals[int(0.975 * reps) - 1], 4)]


def leaky(d):
    return d["leak_share"] >= LEAK_THRESHOLD


def summarize(docs, sites=()):
    ok = [d for d in docs if d.get("result") == "ok"]
    el = [d for d in ok if not d.get("capped") and d.get("content_chars", 0) >= MIN_CONTENT]
    word = [d for d in el if d.get("producer_family") == "word"]
    other = [d for d in el if d.get("producer_family") != "word"]
    pages = sorted(x for d in el for x in d["page_discordance"])
    totals = {k: sum(d[k] for d in el) for k in
              ("reachable", "untagged", "dangling", "artifact", "xobject", "named")}
    p1 = share(el, leaky)
    p1["cluster_ci95"] = cluster_ci(el, leaky)
    w, o = share(word, leaky), share(other, leaky)
    p3 = share(el, lambda d: d["shell"])
    med = round(statistics.median(pages), 4) if pages else None
    s = {
        "version": __version__,
        "sites": len(sites), "site_status": dict(collections.Counter(x.get("status") for x in sites)),
        "pdfs_attempted": len(docs),
        "results": dict(collections.Counter(d.get("result") for d in docs)),
        "eligible": len(el), "eligible_sites": len({d["qid"] for d in el}),
        "excluded_capped": sum(1 for d in ok if d.get("capped")),
        "excluded_little_text": sum(1 for d in ok if not d.get("capped")
                                    and d.get("content_chars", 0) < MIN_CONTENT),
        "char_totals": totals,
        "P1_leaky": p1,
        "P2_word": w, "P2_other": o,
        "P2_difference": (round(o["share"] - w["share"], 4)
                          if word and other else None),
        "P3_shell": p3,
        "P4_pages_ordered": len(pages), "P4_median_discordance": med,
        "mean_leak_share": round(statistics.mean(d["leak_share"] for d in el), 4) if el else None,
        "explore_any_dangling": share(el, lambda d: d["dangling"] > 0),
        "explore_any_untagged": share(el, lambda d: d["untagged"] > 0),
        "explore_upward_jump": share(el, lambda d: d["upward_jumps"] > 0),
        "explore_pages_discordance_over_0.2": (sum(1 for x in pages if x > 0.2), len(pages)),
        "by_producer": {},
    }
    fams = collections.defaultdict(list)
    for d in el:
        fams[d.get("producer_family") or "unknown"].append(d)
    for fam, ds in sorted(fams.items()):
        s["by_producer"][fam] = {"leaky": share(ds, leaky),
                                 "median_leak_share": round(statistics.median(d["leak_share"] for d in ds), 4)}
    s["predictions"] = {
        "P1 leaky share >= 0.10": None if p1["share"] is None else p1["share"] >= 0.10,
        "P2 other minus word >= 0.10": None if s["P2_difference"] is None else s["P2_difference"] >= 0.10,
        "P3 shell share >= 0.02": None if p3["share"] is None else p3["share"] >= 0.02,
        "P4 median discordance <= 0.05": None if med is None else med <= 0.05,
    }
    return s


def pct(c):
    if not c or c["share"] is None:
        return "n/a"
    lo, hi = c["ci95"]
    return "%.1f%% (%.1f-%.1f), n=%d" % (100 * c["share"], 100 * lo, 100 * hi, c["n"])


def report(s):
    out = ["# tagtree-reach results (v%s)" % s["version"], "",
           "Tagged PDFs linked from US local-government websites (cities and counties of 50,000+): "
           "how much of the text on their first 3 pages is reachable from the structure tree that "
           "screen readers follow. Machine checks only; not a WCAG conformance judgment.", "",
           "- Sites crawled: %d; PDFs analysed: %d; eligible: %d from %d sites" % (
               s["sites"], s["pdfs_attempted"], s["eligible"], s["eligible_sites"]),
           "- Results: %s" % json.dumps(s["results"]),
           "- Characters (eligible PDFs): %s" % json.dumps(s["char_totals"]), "",
           "## Pre-registered predictions", "",
           "| Prediction | Measured | Met |", "|---|---|---|",
           "| P1: 10%%+ of tagged PDFs leave 5%%+ of page text unreachable | %s; site-clustered CI %s | %s |" % (
               pct(s["P1_leaky"]), s["P1_leaky"].get("cluster_ci95"), s["predictions"]["P1 leaky share >= 0.10"]),
           "| P2: Word-made PDFs are leaky 10+ points less often | Word %s; others %s; difference %s | %s |" % (
               pct(s["P2_word"]), pct(s["P2_other"]), s["P2_difference"], s["predictions"]["P2 other minus word >= 0.10"]),
           "| P3: 2%%+ have a text page with nothing reachable | %s | %s |" % (
               pct(s["P3_shell"]), s["predictions"]["P3 shell share >= 0.02"]),
           "| P4: median page discordance (tag vs stream order) is 0.05 or less | %s over %d pages | %s |" % (
               s["P4_median_discordance"], s["P4_pages_ordered"], s["predictions"]["P4 median discordance <= 0.05"]),
           "", "## Exploratory (no prediction)", "",
           "- Mean leak share: %s" % s["mean_leak_share"],
           "- Any dangling MCID text: %s" % pct(s["explore_any_dangling"]),
           "- Any untagged text: %s" % pct(s["explore_any_untagged"]),
           "- Same-column upward jump in tag order: %s" % pct(s["explore_upward_jump"]),
           "- Pages with discordance over 0.2: %d of %d" % tuple(s["explore_pages_discordance_over_0.2"]),
           "", "## By the software that made the PDF", "",
           "| Producer | Leaky | Median leak share |", "|---|---|---|"]
    for fam, v in s["by_producer"].items():
        out.append("| %s | %s | %s |" % (fam, pct(v["leaky"]), v["median_leak_share"]))
    return "\n".join(out) + "\n"


PUBLIC_FIELDS = ("url_sha256", "kind", "producer_family", "created", "result", "pages_analyzed",
                 "elements", "capped", "stm_refs", "wildcard_mcids", "reachable", "untagged",
                 "dangling", "artifact", "xobject", "named", "content_chars", "leak_share", "shell",
                 "page_discordance", "upward_jumps")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="print one PDF's reachability record as JSON")
    a.add_argument("path")
    a.add_argument("--pages", type=int, default=3)
    r = sub.add_parser("run", help="crawl a sample of the census cohort and analyse tagged PDFs")
    r.add_argument("--census", required=True, help="path of census.py (title2-pdf-census 0.2.2)")
    r.add_argument("--out-dir", required=True)
    r.add_argument("--sites", type=int, default=600)
    r.add_argument("--workers", type=int, default=8)
    r.add_argument("--pages", type=int, default=8)
    r.add_argument("--pdfs", type=int, default=8)
    r.add_argument("--per-site", type=int, default=3)
    r.add_argument("--delay", type=float, default=1.0)
    r.add_argument("--max-minutes", type=float, default=120)
    s = sub.add_parser("summarize", help="summary.json, results.md and docs-public.jsonl")
    s.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "analyze":
        import logging
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        with open(args.path, "rb") as f:
            data = f.read()
        print(json.dumps(analyze_tags(data, args.pages)))
    elif args.cmd == "run":
        import importlib.util
        spec = importlib.util.spec_from_file_location("census", args.census)
        census = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(census)
        if census.__version__ != "0.2.2":
            print("census is %s, not 0.2.2" % census.__version__, file=sys.stderr)
            return 1
        census.UA = UA  # the crawl names this study; robots.txt is checked for this agent
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
        crawl(census, cohort, args.sites, args.out_dir, args.workers, args.pages, args.pdfs,
              args.per_site, args.delay, args.max_minutes)
    else:
        docs = read_jsonl(os.path.join(args.out_dir, "docs-private.jsonl"))
        sites = read_jsonl(os.path.join(args.out_dir, "sites-private.jsonl"))
        s = summarize(docs, sites)
        with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(s, f, indent=1)
        with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8") as f:
            f.write(report(s))
        with open(os.path.join(args.out_dir, "docs-public.jsonl"), "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps({k: d.get(k) for k in PUBLIC_FIELDS}) + "\n")
        print(report(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
