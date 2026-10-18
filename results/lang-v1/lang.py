"""lang-census: does a PDF's declared document language match the language of its text?

Screen readers choose a voice and pronunciation rules from a PDF's document language (the
catalog's /Lang), unless a structure element or a marked-content sequence says otherwise. A
Spanish notice declared en-US is read aloud with English rules. Checkers and earlier censuses
(including title2-pdf-census) only ask whether /Lang is set; this measures whether it is right.

It runs title2-pdf-census 0.2.2's seeded crawl (public pages only, robots.txt honoured, 1 s
between requests to a site; sites chosen with tagtree-reach's seed, so the first 600 are the
same sites) and, for every readable PDF with text, reads the catalog /Lang, the /Lang entries
of structure elements and of marked content on the first pages, and the language of the text of
the first pages. The text is split into chunks of about 200 characters and each chunk is read by
two independent detectors (py3langid and langdetect); a chunk counts only where both name the
same language with probability 0.9 or more.

Pre-registered in docs/lang-census-prereg.md. Stores no document text: counts and language
codes, and, in the private file only, URLs and the raw /Lang strings.

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
import re
import subprocess
import sys
import tempfile
import time

__version__ = "0.1.0"

UA = ("MV2-lang-census/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)
SITE_SEED = "tagtree-v1"  # tagtree-reach's site order: the first 600 sites are the same
TEXT_PAGES = 5            # pages whose text, element and marked-content languages are read
MAX_TEXT = 20_000         # characters of text kept per PDF
CHUNK = 200               # characters per chunk given to the detectors
MAX_CHUNKS = 60
MIN_PROB = 0.9            # both detectors must reach this on a chunk
MIN_DETERMINED = 400      # characters of agreed chunks a PDF needs for a text language
MAJORITY = 0.8            # share of agreed characters the top language needs, else "mixed"
NODE_CAP = 20_000
# Deprecated or alternative codes, so declared and detected languages compare like for like.
ALIASES = {"iw": "he", "in": "id", "ji": "yi", "nb": "no", "nn": "no", "fil": "tl",
           "eng": "en", "spa": "es", "zho": "zh", "chi": "zh", "vie": "vi", "kor": "ko"}
# BCP 47 shape: a 2-3 letter primary subtag (or private use x-...) and optional subtags.
WELL_FORMED = re.compile(r"(?:[A-Za-z]{2,3}(?:-[A-Za-z0-9]{1,8})*|[xX](?:-[A-Za-z0-9]{1,8})+)")
MC_LANG = re.compile(rb"/Lang\s*\(([^)]{0,35})\)")
# Pre-registered thresholds (docs/lang-census-prereg.md).
L1_MIN = 0.50   # non-English PDFs whose /Lang is missing, unusable or another language
L2_MIN = 0.30   # of non-English PDFs declared English, share with an element/marked-content match
L3_MAX = 0.02   # English PDFs whose /Lang names another language
L4_MAX = 0.03   # PDFs with a /Lang whose value is not BCP 47-shaped
K_MIN = 0.90    # chunks py3langid is sure of on which langdetect agrees
PUBLIC_FIELDS = ("url_sha256", "kind", "state", "producer_family", "created", "tagged", "result",
                 "lang_present", "lang_well_formed", "lang_primary", "lang_is_name", "text_chars",
                 "chunks", "chunks_confident", "chunks_agree", "determined_chars", "text_langs",
                 "text_lang", "element_lang", "element_langs", "struct_capped", "mc_lang",
                 "mc_langs")


def err(e):
    return "%s: %s" % (type(e).__name__, str(e)[:160])


# ---------------------------------------------------------------- one PDF

def norm(code):
    """'en-US' -> 'en', 'zh-cn' -> 'zh'; None if there is no 2-3 letter primary subtag."""
    if not code:
        return None
    first = re.split(r"[-_\s]", str(code).strip().lower(), maxsplit=1)[0]
    if not re.fullmatch(r"[a-z]{2,3}", first):
        return None
    return ALIASES.get(first, first)


def resolve(obj):
    return obj.get_object() if hasattr(obj, "get_object") else obj


def text_of(v):
    if isinstance(v, bytes):
        return v.decode("latin-1").strip()
    return str(v).strip()


def chunks_of(text, size=CHUNK):
    """Whole lines joined into chunks of at least size characters; a short tail is kept only
    if it has half that."""
    out, cur, n = [], [], 0
    for line in text.splitlines():
        line = " ".join(line.split())
        if not line:
            continue
        cur.append(line)
        n += len(line)
        if n >= size:
            out.append(" ".join(cur))
            cur, n = [], 0
    if cur and n >= size // 2:
        out.append(" ".join(cur))
    return out


class Detectors:
    """py3langid (normalized probabilities) and langdetect (seeded), loaded once per process."""

    def __init__(self):
        from py3langid.langid import LanguageIdentifier, MODEL_FILE
        from langdetect import DetectorFactory
        make = (getattr(LanguageIdentifier, "from_modelpath", None)
                or getattr(LanguageIdentifier, "from_model_file", None)
                or LanguageIdentifier.from_pickled_model)
        self.langid = make(MODEL_FILE, norm_probs=True)
        DetectorFactory.seed = 0

    def detect(self, text):
        """(py3langid language, probability, langdetect language, probability)"""
        from langdetect import detect_langs
        from langdetect.lang_detect_exception import LangDetectException
        a, pa = self.langid.classify(text)
        try:
            top = detect_langs(text)[0]
            b, pb = top.lang, top.prob
        except LangDetectException:
            b, pb = None, 0.0
        return norm(a), float(pa), norm(b), float(pb)


def detect_doc(chunks, det):
    """The text language of one PDF from its chunks: a language, "mixed" or "undetermined"."""
    by, total, confident, agree = collections.Counter(), 0, 0, 0
    for c in chunks:
        a, pa, b, pb = det.detect(c)
        total += len(c)
        if pa >= MIN_PROB:
            confident += 1
            agree += int(a == b)
        if a and a == b and pa >= MIN_PROB and pb >= MIN_PROB:
            by[a] += len(c)
    determined = sum(by.values())
    if determined < MIN_DETERMINED or determined < 0.5 * total:
        text_lang = "undetermined"
    else:
        top, n = by.most_common(1)[0]
        text_lang = top if n >= MAJORITY * determined else "mixed"
    return {"chunks": len(chunks), "chunks_confident": confident, "chunks_agree": agree,
            "determined_chars": determined, "text_langs": dict(by), "text_lang": text_lang}


def element_langs(root, cap=NODE_CAP):
    """(structure elements with /Lang, {language: count}, stopped at cap)"""
    tree = resolve(root.get("/StructTreeRoot"))
    if not isinstance(tree, dict):
        return 0, {}, False
    stack, seen, n, langs = [tree.get("/K")], 0, 0, collections.Counter()
    while stack and seen < cap:
        node = resolve(stack.pop())
        seen += 1
        if isinstance(node, list):
            stack.extend(node)
            continue
        if not isinstance(node, dict):
            continue
        if "/Lang" in node:
            n += 1
            langs[norm(text_of(resolve(node["/Lang"]))) or "none"] += 1
        kids = node.get("/K")
        if kids is not None:
            stack.append(kids)
    return n, dict(langs), seen >= cap


def raw_contents(page):
    c = resolve(page.get("/Contents"))
    parts = c if isinstance(c, list) else [c]
    out = b""
    for p in parts:
        p = resolve(p)
        if hasattr(p, "get_data"):
            out += p.get_data() + b"\n"
    return out


def content_langs(pages):
    """(marked-content /Lang entries written inline in the pages' content, {language: count})"""
    n, langs = 0, collections.Counter()
    for page in pages:
        try:
            data = raw_contents(page)
        except Exception:
            continue
        for m in MC_LANG.finditer(data):
            n += 1
            langs[norm(m.group(1).decode("latin-1")) or "none"] += 1
    return n, dict(langs)


def check_bytes(data, det=None):
    """Declared, element, marked-content and text languages of one PDF (bytes), on pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    root = resolve(reader.trailer["/Root"])
    value = resolve(root.get("/Lang"))
    raw = "" if value is None else text_of(value)
    is_name = raw.startswith("/")
    pages = [reader.pages[i] for i in range(min(TEXT_PAGES, len(reader.pages)))]
    parts, size = [], 0
    for page in pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        parts.append(t)
        size += len(t)
        if size >= MAX_TEXT:
            break
    text = "\n".join(parts)[:MAX_TEXT]
    row = {"result": "ok", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "lang_raw": raw[:40], "lang_present": bool(raw),
           "lang_well_formed": bool(WELL_FORMED.fullmatch(raw)) if raw else None,
           "lang_primary": norm(raw), "lang_is_name": is_name, "text_chars": len(text)}
    row.update(detect_doc(chunks_of(text)[:MAX_CHUNKS], det or Detectors()))
    row["element_lang"], row["element_langs"], row["struct_capped"] = element_langs(root)
    row["mc_lang"], row["mc_langs"] = content_langs(pages)
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


# ---------------------------------------------------------------- crawl

def run_site(census, row, pages, pdfs, delay, deadline):
    """Crawl one site with the census code, keeping PDF bodies, then check every readable
    PDF with text that the census read."""
    bodies = {}

    def get(url, max_bytes, timeout=20):
        resp = census.http_get(url, max_bytes, timeout=timeout)
        if resp.status == 200 and not resp.truncated and b"%PDF" in resp.body[:1024]:
            bodies[url] = resp.body
        return resp

    site, found = census.crawl_site(row, get=get, pages=pages, pdfs=pdfs, delay=delay,
                                    deadline=deadline)
    docs = []
    for rec in found:
        url = rec["url"]
        if rec.get("result") != "ok" or rec.get("image_only") or url not in bodies:
            continue
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(bodies[url])
        try:
            res = check_file(f.name)
        finally:
            os.unlink(f.name)
        docs.append({"qid": rec["qid"], "kind": rec["kind"], "state": rec.get("state"), "url": url,
                     "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
                     "producer_family": rec.get("producer_family"), "created": rec.get("created"),
                     "tagged": rec.get("tagged"), "census_lang": rec.get("lang"), **res})
    site["pdfs_checked"] = len(docs)
    return site, docs


def crawl(census, cohort, n_sites, out_dir, workers, minutes):
    deadline = time.time() + 60 * minutes if minutes else None
    by_site = {r["website"]: r for r in cohort}
    chosen = census.sample(list(by_site), n_sites, SITE_SEED)
    with open(os.path.join(out_dir, "sites-private.jsonl"), "w", encoding="utf-8") as fs, \
            open(os.path.join(out_dir, "docs-private.jsonl"), "w", encoding="utf-8") as fd, \
            concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(run_site, census, by_site[w], 8, 8, 1.0, deadline) for w in chosen]
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


def run(census_path, out_dir, sites, workers, minutes):
    import importlib.util
    spec = importlib.util.spec_from_file_location("census", census_path)
    census = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(census)
    if census.__version__ != "0.2.2":
        print("need census 0.2.2", file=sys.stderr)
        return 1
    census.UA = UA  # robots.txt is checked for this agent
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
    crawl(census, cohort, sites, out_dir, workers, minutes)
    return 0


# ---------------------------------------------------------------- summary

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


def cluster_ci(docs, pred, reps=2000, seed=20261018):
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


def is_language(t):
    return t not in (None, "undetermined", "mixed")


def declared(d):
    """How the catalog /Lang relates to the text language: none, unusable, match or other."""
    if not d.get("lang_present"):
        return "none"
    if not d.get("lang_primary"):
        return "unusable"
    return "match" if d["lang_primary"] == d["text_lang"] else "other"


def wrong(d):
    return declared(d) != "match"


def local_match(d):
    """A structure element or marked-content sequence names the text language."""
    t = d["text_lang"]
    return t in (d.get("element_langs") or {}) or t in (d.get("mc_langs") or {})


def met(c, ok):
    return dict(c, met=None if c["share"] is None else ok(c["share"]))


def counts(rows):
    """{key: [PDFs, of which /Lang is not the text language]}"""
    out = collections.defaultdict(lambda: [0, 0])
    for key, d in rows:
        out[key][0] += 1
        out[key][1] += int(wrong(d))
    return {k: v for k, v in sorted(out.items(), key=lambda kv: str(kv[0]))}


def summarize(docs):
    ok = [d for d in docs if d.get("result") == "ok"]
    det = [d for d in ok if is_language(d.get("text_lang"))]
    english = [d for d in det if d["text_lang"] == "en"]
    other = [d for d in det if d["text_lang"] != "en"]
    as_english = [d for d in other if d.get("lang_primary") == "en"]
    present = [d for d in ok if d.get("lang_present")]
    confident = sum(d.get("chunks_confident", 0) for d in ok)
    agree = sum(d.get("chunks_agree", 0) for d in ok)
    malformed = collections.Counter(d.get("lang_raw") for d in present if not d.get("lang_well_formed"))
    return {
        "version": __version__,
        "pdfs": len(docs),
        "check_results": dict(collections.Counter(d.get("result") for d in docs)),
        "ok": len(ok),
        "text_lang_counts": dict(collections.Counter(d.get("text_lang") for d in ok).most_common()),
        "determined": len(det),
        "english": len(english),
        "non_english": len(other),
        "non_english_sites": len({d["qid"] for d in other}),
        "L1_non_english_wrong": dict(met(share(sum(1 for d in other if wrong(d)), len(other)),
                                         lambda s: s >= L1_MIN),
                                     cluster_ci95=cluster_ci(other, wrong)),
        "L2_local_match": met(share(sum(1 for d in as_english if local_match(d)), len(as_english)),
                              lambda s: s >= L2_MIN),
        "L3_english_other": met(share(sum(1 for d in english if declared(d) == "other"), len(english)),
                                lambda s: s < L3_MAX),
        "L4_malformed": met(share(sum(1 for d in present if not d.get("lang_well_formed")), len(present)),
                            lambda s: s < L4_MAX),
        "K_detector_agreement": met(share(agree, confident), lambda s: s >= K_MIN),
        "explore_non_english_declared": dict(sorted(collections.Counter(
            "%s:%s" % (d["text_lang"], declared(d)) for d in other).items())),
        "explore_non_english_declared_as": dict(sorted(collections.Counter(
            str(d.get("lang_primary")) for d in other if declared(d) == "other").items())),
        "explore_english_declared": dict(sorted(collections.Counter(declared(d) for d in english).items())),
        "explore_non_english_by_family": counts((d.get("producer_family"), d) for d in other),
        "explore_non_english_by_tagged": counts(("tagged" if d.get("tagged") else "untagged", d)
                                                for d in other),
        "explore_mixed_declared": dict(sorted(collections.Counter(
            str(d.get("lang_primary")) for d in ok if d.get("text_lang") == "mixed").items())),
        "explore_malformed_values": dict(malformed.most_common(20)),
        "explore_lang_is_name": sum(1 for d in present if d.get("lang_is_name")),
        "explore_lang_present_all": share(len(present), len(ok)),
    }


def public(d):
    return {k: d[k] for k in PUBLIC_FIELDS if k in d}


def pct(c):
    if not c or c.get("share") is None:
        return "n/a"
    return "%d of %d, %.1f%% (%.1f-%.1f)" % (c["k"], c["n"], 100 * c["share"],
                                             100 * c["ci95"][0], 100 * c["ci95"][1])


def report(s):
    yes = {True: "yes", False: "**no**", None: "not testable"}
    lines = ["# lang-census results (machine summary)", "",
             "PDFs checked %d; ok %d; text language determined %d (English %d, other %d on %d sites)." % (
                 s["pdfs"], s["ok"], s["determined"], s["english"], s["non_english"],
                 s["non_english_sites"]), "",
             "## Pre-registered predictions", "",
             "| Prediction | Measured | Held? |", "|---|---|---|",
             "| L1: 50%%+ of non-English PDFs have a missing, unusable or other /Lang | %s | %s |" % (
                 pct(s["L1_non_english_wrong"]), yes[s["L1_non_english_wrong"]["met"]]),
             "| L2: 30%%+ of non-English PDFs declared English name the text language locally | %s | %s |" % (
                 pct(s["L2_local_match"]), yes[s["L2_local_match"]["met"]]),
             "| L3: under 2%% of English PDFs declare another language | %s | %s |" % (
                 pct(s["L3_english_other"]), yes[s["L3_english_other"]["met"]]),
             "| L4: under 3%% of /Lang values are not BCP 47-shaped | %s | %s |" % (
                 pct(s["L4_malformed"]), yes[s["L4_malformed"]["met"]]),
             "| K: 90%%+ detector agreement on confident chunks | %s | %s |" % (
                 pct(s["K_detector_agreement"]), yes[s["K_detector_agreement"]["met"]]), "",
             "L1 site-resampled 95%% interval: %s" % json.dumps(s["L1_non_english_wrong"]["cluster_ci95"]), "",
             "## Exploratory (no prediction)", "",
             "- Text languages: %s" % json.dumps(s["text_lang_counts"]),
             "- Non-English, text language:declared: %s" % json.dumps(s["explore_non_english_declared"]),
             "- Non-English declared as: %s" % json.dumps(s["explore_non_english_declared_as"]),
             "- English, declared: %s" % json.dumps(s["explore_english_declared"]),
             "- Non-English by producer family [PDFs, wrong]: %s" % json.dumps(s["explore_non_english_by_family"]),
             "- Non-English tagged or not [PDFs, wrong]: %s" % json.dumps(s["explore_non_english_by_tagged"]),
             "- Mixed-language PDFs, declared: %s" % json.dumps(s["explore_mixed_declared"]),
             "- Malformed /Lang values: %s" % json.dumps(s["explore_malformed_values"]),
             "- /Lang given as a name: %d" % s["explore_lang_is_name"],
             "- /Lang set, all checked PDFs: %s" % pct(s["explore_lang_present_all"]), ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="print the language check of one PDF as JSON")
    c.add_argument("path")
    r = sub.add_parser("run", help="run the census crawl and check every readable PDF with text")
    r.add_argument("--census", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--sites", type=int, default=1500)
    r.add_argument("--workers", type=int, default=6)
    r.add_argument("--max-minutes", type=float, default=150)
    s = sub.add_parser("summarize")
    s.add_argument("--out-dir", required=True)
    args = ap.parse_args(argv)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import logging
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
    with open(os.path.join(args.out_dir, "lang-public.jsonl"), "w", encoding="utf-8") as f:
        for d in docs:
            if d.get("result") == "ok":
                f.write(json.dumps(public(d)) + "\n")
    text = report(summary)
    with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
