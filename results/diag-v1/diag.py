"""tagtree-diag: why do pdfminer.six and pypdf read two tagged PDFs differently?

tagtree-xcheck-v1 found two PDFs (both saved from Word) where tagtree's walk on pdfminer's parse
reaches 0 and 4 structure elements and the pypdf reader's walk reaches 809 and 3,690. The walks
are the same algorithm, so the difference is in how the two libraries read the file. This job
fetches the two files again (public pages only, robots.txt honoured) and, for each:

1. counts the structure elements reached from the root with a third parser (qpdf, via pikepdf);
2. resolves every structure element the pypdf walk reaches with pdfminer as well, and records
   where each library says the object lives and whether pdfminer returns the same element;
3. for each compressed object stream holding a mismatch, compares pdfminer's in-sequence reading
   (objs[2n + index], offsets not used) with a reading that starts at each object's listed offset;
4. runs tagtree 0.1.0 as is, and again with pdfminer reading object streams by offset.

It also compares tagtree-reach-v1's published per-PDF rows with tagtree-xcheck-v1's (by URL
hash): how many of the first run's PDFs were read again, and whether the pypdf reader agrees
on the first run's leaky, shell and small-tree PDFs.

Stores no document text and no URL: only counts, object types, structure type names and hashes.
Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import collections
import hashlib
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import urllib.robotparser

__version__ = "0.1.0"

UA = ("MV2-tagtree-diag/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)
LEAK, MIN_CONTENT, NODE_CAP = 0.05, 50, 300_000
MAX_BYTES = 60_000_000


# ---------------------------------------------------------------- fetch

def allowed(url):
    parts = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url("%s://%s/robots.txt" % (parts.scheme, parts.netloc))
    try:
        req = urllib.request.Request(rp.url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            rp.parse(r.read(500_000).decode("utf-8", "replace").splitlines())
    except Exception:
        return True  # no readable robots.txt: crawling is not disallowed
    return rp.can_fetch(UA, url)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(MAX_BYTES + 1)


# ---------------------------------------------------------------- file facts

def file_facts(data):
    return {
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "header": data[:8].decode("latin-1", "replace"),
        **{key: data.count(token) for key, token in (
            ("startxref", b"startxref"), ("eof_markers", b"%%EOF"), ("xrefstm_keys", b"/XRefStm"),
            ("prev_keys", b"/Prev"), ("objstm_keys", b"/ObjStm"), ("linearized_keys", b"/Linearized"))},
    }


# ---------------------------------------------------------------- pypdf side

def pypdf_elements(data):
    """{idnum: structure type} for every indirect structure element the walk reaches, the
    element count (as xcheck counts it), and pypdf's object-stream map {idnum: (stream, index)}."""
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt("")
    catalog = reader.trailer["/Root"].get_object()
    root = catalog.get("/StructTreeRoot")
    root = root.get_object() if root is not None else None
    found, count, visited = {}, 0, set()
    stack = [(root.raw_get("/K") if "/K" in root else None, None)]
    while stack:
        obj, _ = stack.pop()
        ref = None
        if isinstance(obj, IndirectObject):
            if obj.idnum in visited:
                continue
            visited.add(obj.idnum)
            ref = obj.idnum
            obj = obj.get_object()
        if isinstance(obj, list):
            stack.extend((kid, None) for kid in reversed(obj))
        elif isinstance(obj, dict) and "/S" in obj:
            count += 1
            if count > NODE_CAP:
                break
            if ref is not None:
                found[ref] = str(obj["/S"]).lstrip("/")
            stack.append((obj.raw_get("/K") if "/K" in obj else None, None))
    objstm = {k: tuple(v) for k, v in getattr(reader, "xref_objStm", {}).items()}
    raw_k = root.raw_get("/K") if "/K" in root else None
    return found, count, objstm, type_name(raw_k), reader


def type_name(x):
    try:
        from pypdf.generic import IndirectObject
        if isinstance(x, IndirectObject):
            return "ref"
    except ImportError:
        pass
    try:
        from pdfminer.pdftypes import PDFObjRef, PDFStream
        if isinstance(x, PDFObjRef):
            return "ref"
        if isinstance(x, PDFStream):
            return "stream"
    except ImportError:
        pass
    if x is None:
        return "null"
    if isinstance(x, bool):
        return "bool"
    if isinstance(x, int):
        return "int"
    if isinstance(x, float):
        return "float"
    if isinstance(x, dict):
        return "dict"
    if isinstance(x, list):
        return "array"
    if isinstance(x, (str, bytes)):
        return "string"
    return type(x).__name__


# ---------------------------------------------------------------- pdfminer side

def lit(x):
    from pdfminer.psparser import PSLiteral
    if isinstance(x, PSLiteral):
        n = x.name
        return n.decode("latin-1") if isinstance(n, bytes) else n
    return None


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def miner_pos(doc, objid):
    """(stream objid or None, index or offset) from the first xref section that lists objid."""
    for i, xref in enumerate(doc.xrefs):
        try:
            strmid, index, _ = xref.get_pos(objid)
            return {"section": i, "kind": type(xref).__name__, "stream": strmid, "index": index}
        except KeyError:
            continue
    return None


def parse_one(doc, buf):
    """One object parsed from the start of buf, with a top-level 'n g R' read as a reference."""
    from pdfminer.pdfparser import PDFStreamParser
    from pdfminer.pdftypes import PDFObjRef
    from pdfminer.psparser import KWD, PSEOF
    p = PDFStreamParser(buf + b"\n")  # a last token needs a delimiter after it to be emitted
    p.set_document(doc)
    try:
        _, obj = p.nextobject()
    except PSEOF:
        return None
    if is_int(obj):
        try:
            _, g = p.nexttoken()
            _, r = p.nexttoken()
            if is_int(g) and r is KWD(b"R"):
                try:
                    return PDFObjRef(doc, obj, g)
                except TypeError:
                    return PDFObjRef(doc, obj)
        except PSEOF:
            pass
    return obj


def objects_by_offset(doc, stream):
    """An object stream read the way the PDF spec lays it out: the header's (objid, offset)
    pairs, then each object parsed from /First + offset. Same list layout as pdfminer's
    _get_objects (2n header numbers, then the n objects), so it can stand in for it."""
    from pdfminer.pdftypes import resolve1
    n, first = int(resolve1(stream["N"])), int(resolve1(stream["First"]))
    data = stream.get_data()
    head = data[:first].split()
    pairs = [(int(head[2 * i]), int(head[2 * i + 1])) for i in range(n)]
    objs = [x for pair in pairs for x in pair]
    for _, off in pairs:
        objs.append(parse_one(doc, data[first + off:]))
    return objs, n


def stream_report(doc, strmid):
    """How pdfminer's in-sequence reading of one object stream differs from reading by offset."""
    from pdfminer.pdftypes import resolve1
    stream = doc.getobj(strmid)
    n, first = int(resolve1(stream["N"])), int(resolve1(stream["First"]))
    data = stream.get_data()
    seq, _ = doc._get_objects(stream)
    off, _ = objects_by_offset(doc, stream)
    head_tokens = len(data[:first].split())
    seq_objs, off_objs = seq[2 * n:], off[2 * n:]
    first_diff = next((i for i in range(n) if i >= len(seq_objs)
                       or type_name(seq_objs[i]) != type_name(off_objs[i])
                       or (isinstance(off_objs[i], dict) and isinstance(seq_objs[i], dict)
                           and lit(off_objs[i].get("S")) != lit(seq_objs[i].get("S")))), None)
    window = (lambda xs, i: [type_name(x) for x in xs[max(0, i - 2):i + 3]])
    return {
        "n": n, "first": first, "data_bytes": len(data), "header_tokens": head_tokens,
        "header_tokens_expected": 2 * n,
        "sequential_tokens": len(seq), "sequential_tokens_expected": 3 * n,
        "offset_types": dict(collections.Counter(type_name(x) for x in off_objs)),
        "top_level_refs": sum(1 for x in off_objs if type_name(x) == "ref"),
        "first_difference_index": first_diff,
        "sequential_types_there": None if first_diff is None else window(seq_objs, first_diff),
        "offset_types_there": None if first_diff is None else window(off_objs, first_diff),
        "endobj_tokens": data.count(b"endobj"),
        "obj_headers": len(re.findall(rb"\d+\s+\d+\s+obj\b", data)),
    }


def compare_elements(data, found, objstm):
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdftypes import resolve1
    doc = PDFDocument(PDFParser(io.BytesIO(data)))
    out = {"xref_sections": [type(x).__name__ for x in doc.xrefs]}
    root = resolve1(doc.catalog.get("StructTreeRoot"))
    out["miner_root_k"] = type_name(root.get("K")) if isinstance(root, dict) else None
    k = resolve1(root.get("K")) if isinstance(root, dict) else None
    out["miner_root_k_resolved"] = type_name(k)
    same, wrong, missing = 0, collections.Counter(), 0
    pos_agree, pos_differ, bad_streams = 0, 0, collections.Counter()
    examples = []
    for idnum, s in sorted(found.items()):
        pos = miner_pos(doc, idnum)
        theirs = objstm.get(idnum)
        if pos is not None and theirs is not None and pos["stream"] == theirs[0] and pos["index"] == theirs[1]:
            pos_agree += 1
        elif theirs is not None:
            pos_differ += 1
        try:
            obj = doc.getobj(idnum)
        except Exception:
            obj = None
        if obj is None:
            missing += 1
            ok = False
        else:
            ok = isinstance(obj, dict) and lit(obj.get("S")) == s
            if ok:
                same += 1
            else:
                wrong[type_name(obj)] += 1
        if not ok:
            if theirs is not None:
                bad_streams[theirs[0]] += 1
            if len(examples) < 8:
                examples.append({"objid": idnum, "pypdf_S": s, "pdfminer": type_name(obj),
                                 "pdfminer_S": lit(obj.get("S")) if isinstance(obj, dict) else None,
                                 "pypdf_where": list(theirs) if theirs else None, "pdfminer_where": pos})
    out.update({"elements_checked": len(found), "same_element": same, "missing": missing,
                "wrong_by_type": dict(wrong), "position_agree": pos_agree, "position_differ": pos_differ,
                "mismatch_streams": {str(k): v for k, v in bad_streams.most_common()},
                "examples": examples, "streams": {}})
    for strmid, _ in bad_streams.most_common(4):
        try:
            out["streams"][str(strmid)] = stream_report(doc, strmid)
        except Exception as e:
            out["streams"][str(strmid)] = {"error": "%s: %s" % (type(e).__name__, str(e)[:160])}
    return out


# ---------------------------------------------------------------- qpdf side

def pike_elements(data):
    """Structure elements reached from the root, read by qpdf (pikepdf), counted as xcheck does."""
    import pikepdf
    pdf = pikepdf.open(io.BytesIO(data))
    root = pdf.Root.get("/StructTreeRoot")
    if root is None:
        return None
    count, seen, stack = 0, set(), [root.get("/K")]
    while stack:
        o = stack.pop()
        if o is None:
            continue
        if isinstance(o, pikepdf.Object) and o.is_indirect:
            if o.objgen in seen:
                continue
            seen.add(o.objgen)
        if isinstance(o, pikepdf.Array):
            stack.extend(reversed(list(o)))
        elif isinstance(o, pikepdf.Dictionary) and "/S" in o:
            count += 1
            if count > NODE_CAP:
                break
            stack.append(o.get("/K"))
    return count


# ---------------------------------------------------------------- tagtree, as is and patched

TAGTREE_KEYS = ("result", "elements", "wildcard_mcids", "reachable", "untagged", "dangling",
                "artifact", "content_chars", "leak_share", "shell")


def tagtree_both(data):
    import tagtree
    from pdfminer.pdfdocument import PDFDocument
    as_is = tagtree.analyze_tags(data)
    original = PDFDocument._get_objects
    PDFDocument._get_objects = objects_by_offset
    try:
        patched = tagtree.analyze_tags(data)
    finally:
        PDFDocument._get_objects = original
    return ({k: as_is.get(k) for k in TAGTREE_KEYS}, {k: patched.get(k) for k in TAGTREE_KEYS})


# ---------------------------------------------------------------- one file

def diagnose(data):
    row = {"file": file_facts(data)}
    try:
        found, count, objstm, raw_k, _ = pypdf_elements(data)
        row["pypdf"] = {"elements": count, "indirect_elements": len(found), "root_k": raw_k,
                        "objstm_entries": len(objstm)}
    except Exception as e:
        row["pypdf"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:160])}
        found, objstm = {}, {}
    try:
        row["qpdf_elements"] = pike_elements(data)
    except Exception as e:
        row["qpdf_elements"] = "error %s: %s" % (type(e).__name__, str(e)[:160])
    try:
        row["pdfminer"] = compare_elements(data, found, objstm)
    except Exception as e:
        row["pdfminer"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:160])}
    try:
        row["tagtree_as_is"], row["tagtree_by_offset"] = tagtree_both(data)
    except Exception as e:
        row["tagtree_as_is"] = {"error": "%s: %s" % (type(e).__name__, str(e)[:160])}
    return row


# ---------------------------------------------------------------- first run against the re-crawl

def eligible(d):
    return d.get("result") == "ok" and not d.get("capped") and d.get("content_chars", 0) >= MIN_CONTENT


def overlap(v1_rows, pairs):
    """The first run's eligible PDFs that the re-crawl read again, and whether the pypdf reader
    agrees with the first run's flags on them."""
    el = [d for d in v1_rows if eligible(d)]
    again = {d["url_sha256"]: d for d in pairs}
    both = [d for d in el if d["url_sha256"] in again]
    out = {"v1_eligible": len(el), "recrawl_pairs": len(pairs), "read_again": len(both),
           "same_tagtree_record": sum(1 for d in both if all(
               d[k] == again[d["url_sha256"]][k] for k in ("elements", "dangling", "untagged", "reachable")))}
    groups = {"leaky": lambda d: d["leak_share"] >= LEAK, "shell": lambda d: d["shell"],
              "elements_le_1": lambda d: d["elements"] <= 1, "any_dangling": lambda d: d["dangling"] > 0}
    for name, test in groups.items():
        v1 = [d for d in el if test(d)]
        seen = [d for d in v1 if d["url_sha256"] in again]
        x = [again[d["url_sha256"]]["x"] for d in seen]
        xtest = {"leaky": lambda r: r["leak_share"] is not None and r["leak_share"] >= LEAK,
                 "shell": lambda r: r["shell"], "elements_le_1": lambda r: r["elements"] <= 1,
                 "any_dangling": lambda r: r["dangling"] > 0}[name]
        out[name] = {"v1": len(v1), "read_again": len(seen), "pypdf_agrees": sum(1 for r in x if xtest(r))}
    return out


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    urls_path, out_dir = argv[0], argv[1]
    v1_path = argv[2] if len(argv) > 2 else ""
    pairs_path = argv[3] if len(argv) > 3 else ""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    import pdfminer
    import pypdf
    try:
        import pikepdf
        pike = pikepdf.__version__
    except Exception:
        pike = None
    result = {"version": __version__, "pdfminer": pdfminer.__version__, "pypdf": pypdf.__version__,
              "pikepdf": pike, "files": []}
    with open(urls_path, encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip()]
    for url in urls:
        row = {"url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest()}
        try:
            if not allowed(url):
                row["fetch"] = "robots_disallow"
            else:
                data = fetch(url)
                if len(data) > MAX_BYTES or b"%PDF" not in data[:1024]:
                    row["fetch"] = "not_a_pdf_or_too_big"
                else:
                    row["fetch"] = "ok"
                    row.update(diagnose(data))
        except Exception as e:
            row["fetch"] = "error %s: %s" % (type(e).__name__, str(e)[:160])
        result["files"].append(row)
        print(json.dumps(row)[:3000], flush=True)
    if v1_path and pairs_path and os.path.exists(v1_path) and os.path.exists(pairs_path):
        result["overlap"] = overlap(read_jsonl(v1_path), read_jsonl(pairs_path))
    else:
        result["overlap"] = None
    with open(os.path.join(out_dir, "diag.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result.get("overlap")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
