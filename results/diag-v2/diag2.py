"""tagtree-diag v2: does pdfminer.six misread two tagged Word PDFs because it trusts the
cross-reference index of objects in object streams?

tagtree-diag-v1 found that, in the two PDFs on which tagtree-xcheck-v1's readers disagreed,
pdfminer.six returns a different object than pypdf for 505 of 809 and 2,648 of 3,690 structure
elements; qpdf reaches the same elements as pypdf; both libraries say each object sits at the
same (stream, index); and reading the stream by offset instead of in sequence changes nothing.

pdfminer takes slot `index` of the object stream (the index the cross-reference stream gives).
pypdf looks the object number up in the stream's own header and ignores the index. So the
hypothesis is that in these files the two disagree. This job checks it directly, for each file:

1. for every compressed object, whether the header slot holding its number equals the
   cross-reference index (and, where not, whether the index is the number's rank in sorted order);
2. resolves every structure element pypdf reaches with pdfminer as is and with pdfminer finding
   objects by header number (getobj_objstm_by_number below), against pypdf;
3. runs tagtree 0.1.0 as is and with that change.

It also builds two tiny synthetic PDFs and records what pdfminer (as is and changed), pypdf and
qpdf return: one with two swapped indexes (a reproducer for this case) and one whose object
stream holds a bare reference `7 0 R` (an unconfirmed side lead from an earlier source reading).

Stores no document text and no URL: only counts, object numbers, structure type names, the
Producer string and hashes. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import collections
import contextlib
import hashlib
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.robotparser

__version__ = "0.2.0"

UA = ("MV2-tagtree-diag/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)"
      % __version__)
NODE_CAP = 300_000
MAX_BYTES = 60_000_000
TAGTREE_KEYS = ("result", "elements", "wildcard_mcids", "reachable", "untagged", "dangling",
                "artifact", "content_chars", "leak_share", "shell")


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


# ---------------------------------------------------------------- small helpers

def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def lit(x):
    from pdfminer.psparser import PSLiteral
    if isinstance(x, PSLiteral):
        n = x.name
        return n.decode("latin-1") if isinstance(n, bytes) else n
    return None


def err(e):
    return "%s: %s" % (type(e).__name__, str(e)[:160])


# ---------------------------------------------------------------- the change under test

def getobj_objstm_by_number(self, stream, index, objid):
    """pdfminer.six's PDFDocument._getobj_objstm (20260107), except that the object is found by
    its number in the object stream's header, as pypdf and qpdf do. The cross-reference index
    is used only when the header does not list the number."""
    if stream.objid in self._parsed_objs:
        objs, n = self._parsed_objs[stream.objid]
    else:
        objs, n = self._get_objects(stream)
        if self.caching:
            self._parsed_objs[stream.objid] = (objs, n)
    slots = header_slots(objs, n)
    i = 2 * n + slots.get(objid, index)
    if i >= len(objs):
        return ORIGINAL[0](self, stream, index, objid)  # let pdfminer raise its own error
    return objs[i]


def header_slots(objs, n):
    """{object number: first header slot listing it} from the 2n header numbers."""
    slots = {}
    for j in range(min(n, len(objs) // 2)):
        if is_int(objs[2 * j]):
            slots.setdefault(objs[2 * j], j)
    return slots


ORIGINAL = []


@contextlib.contextmanager
def by_number():
    from pdfminer.pdfdocument import PDFDocument
    if not ORIGINAL:
        ORIGINAL.append(PDFDocument._getobj_objstm)
    PDFDocument._getobj_objstm = getobj_objstm_by_number
    try:
        yield
    finally:
        PDFDocument._getobj_objstm = ORIGINAL[0]


# ---------------------------------------------------------------- index against header

def index_report(members, nums, found=()):
    """members: [(object number, cross-reference index)] for one object stream; nums: the object
    numbers its header lists, in order. Counts how many indexes point at the header slot that
    holds the number."""
    slot = {}
    for j, num in enumerate(nums):
        slot.setdefault(num, j)
    rank = {num: r for r, num in enumerate(sorted(set(nums)))}
    out = collections.Counter()
    examples = []
    for num, idx in sorted(members):
        j = slot.get(num)
        if j is None:
            out["absent"] += 1
        elif j == idx:
            out["index_ok"] += 1
        else:
            out["index_wrong"] += 1
            if rank[num] == idx:
                out["wrong_index_is_sorted_rank"] += 1
            if num in found:
                out["elements_index_wrong"] += 1
            if len(examples) < 4:
                examples.append({"objid": num, "xref_index": idx, "header_slot": j})
    out["duplicate_numbers"] = len(nums) - len(set(nums))
    out["header_ascending"] = int(nums == sorted(nums))
    return dict(out), examples


def pypdf_side(data):
    """pypdf's structure elements {idnum: type} reached from the root, its object-stream map
    {idnum: (stream, index)}, the headers of those streams, and the Producer string."""
    from pypdf import PdfReader
    from pypdf.generic import IndirectObject
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt("")
    root = reader.trailer["/Root"].get_object().get("/StructTreeRoot")
    root = root.get_object() if root is not None else None
    found, visited = {}, set()
    stack = [root.raw_get("/K") if root is not None and "/K" in root else None]
    while stack and len(found) <= NODE_CAP:
        obj = stack.pop()
        ref = None
        if isinstance(obj, IndirectObject):
            if obj.idnum in visited:
                continue
            visited.add(obj.idnum)
            ref, obj = obj.idnum, obj.get_object()
        if isinstance(obj, list):
            stack.extend(reversed(obj))
        elif isinstance(obj, dict) and "/S" in obj:
            if ref is not None:
                found[ref] = str(obj["/S"]).lstrip("/")
            stack.append(obj.raw_get("/K") if "/K" in obj else None)
    objstm = {k: tuple(v) for k, v in getattr(reader, "xref_objStm", {}).items()}
    headers = {}
    for stm in sorted({s for s, _ in objstm.values()}):
        s = reader.get_object(stm)
        n, first = int(s["/N"]), int(s["/First"])
        head = s.get_data()[:first].split()
        headers[stm] = [int(head[2 * j]) for j in range(min(n, len(head) // 2))]
    try:
        producer = str((reader.metadata or {}).get("/Producer", ""))[:80]
    except Exception:
        producer = ""
    return found, objstm, headers, producer


def header_check(found, objstm, headers):
    by_stream = collections.defaultdict(list)
    for num, (stm, idx) in objstm.items():
        by_stream[stm].append((num, idx))
    total, streams, examples = collections.Counter(), {}, []
    for stm, members in sorted(by_stream.items()):
        counts, ex = index_report(members, headers.get(stm, []), found)
        streams[str(stm)] = dict(counts, members=len(members))
        total.update({k: v for k, v in counts.items() if k != "header_ascending"})
        total["streams_header_ascending"] += counts["header_ascending"]
        if counts.get("index_wrong"):
            total["streams_with_wrong_index"] += 1
        examples.extend(dict(e, stream=stm) for e in ex[:2])
    return {"compressed_objects": len(objstm), "streams": len(by_stream), **dict(total),
            "examples": examples[:8], "per_stream": streams}


def miner_against_pypdf(data, found):
    """How many of pypdf's structure elements pdfminer returns as the same element type."""
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfparser import PDFParser
    doc = PDFDocument(PDFParser(io.BytesIO(data)))
    same, wrong = 0, collections.Counter()
    for num, s in found.items():
        try:
            obj = doc.getobj(num)
        except Exception as e:
            wrong[type(e).__name__] += 1
            continue
        if isinstance(obj, dict) and lit(obj.get("S")) == s:
            same += 1
        else:
            wrong[lit(obj.get("S")) if isinstance(obj, dict) else type(obj).__name__] += 1
    return {"checked": len(found), "same_element": same, "wrong": dict(wrong.most_common(6))}


def tagtree_row(data):
    import tagtree
    row = tagtree.analyze_tags(data)
    return {k: row.get(k) for k in TAGTREE_KEYS}


def diagnose(data):
    row = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    try:
        found, objstm, headers, row["producer"] = pypdf_side(data)
        row["pypdf_elements"] = len(found)
        row["header_check"] = header_check(found, objstm, headers)
    except Exception as e:
        row["pypdf_error"] = err(e)
        found = {}
    for name, ctx in (("as_is", contextlib.nullcontext), ("by_number", by_number)):
        with ctx():
            try:
                row["pdfminer_" + name] = miner_against_pypdf(data, found)
            except Exception as e:
                row["pdfminer_" + name] = {"error": err(e)}
            try:
                row["tagtree_" + name] = tagtree_row(data)
            except Exception as e:
                row["tagtree_" + name] = {"error": err(e)}
    return row


# ---------------------------------------------------------------- synthetic files

def build_pdf(objstm_head, objstm_body, n, xref_rows):
    """A small PDF: catalog 1, empty page tree 2, object stream 3 (n members), and a
    cross-reference stream as object 6 whose rows for objects 4 and 5 are xref_rows."""
    data = objstm_head + objstm_body
    parts, offsets = [b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"], {}

    def add(num, content):
        offsets[num] = sum(len(p) for p in parts)
        parts.append(b"%d 0 obj\n" % num + content + b"\nendobj\n")

    add(1, b"<</Type/Catalog/Pages 2 0 R>>")
    add(2, b"<</Type/Pages/Kids[]/Count 0>>")
    add(3, b"<</Type/ObjStm/N %d/First %d/Length %d>>\nstream\n" % (n, len(objstm_head), len(data))
        + data + b"\nendstream")
    xref_at = sum(len(p) for p in parts)
    rows = [(0, 0, 65535), (1, offsets[1], 0), (1, offsets[2], 0), (1, offsets[3], 0)]
    rows += list(xref_rows) + [(1, xref_at, 0)]
    table = b"".join(bytes([t]) + f2.to_bytes(4, "big") + f3.to_bytes(2, "big") for t, f2, f3 in rows)
    parts.append(b"6 0 obj\n<</Type/XRef/Size 7/W[1 4 2]/Root 1 0 R/Length %d>>\nstream\n" % len(table)
                 + table + b"\nendstream\nendobj\n")
    parts.append(b"startxref\n%d\n%%%%EOF\n" % xref_at)
    return b"".join(parts)


def swapped_pdf():
    """The header lists object 4 (/S /A) first and object 5 (/S /B) second; the
    cross-reference stream gives 4 index 1 and 5 index 0."""
    return build_pdf(b"4 0 5 9 ", b"<</S/A>> <</S/B>>", 2, [(2, 3, 1), (2, 3, 0)])


def bare_ref_pdf():
    """An object stream whose only member, object 4, is the bare reference `2 0 R`; object 5
    is free."""
    return build_pdf(b"4 0 ", b"2 0 R", 1, [(2, 3, 0), (0, 0, 0)])


def describe(x):
    if isinstance(x, dict):
        s = x.get("S", x.get("/S"))
        return "dict S=%s" % (lit(s) or str(s).lstrip("/"))
    return type(x).__name__


def read_synthetic(data):
    out = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfparser import PDFParser
    for name, ctx in (("pdfminer_as_is", contextlib.nullcontext), ("pdfminer_by_number", by_number)):
        with ctx():
            try:
                doc = PDFDocument(PDFParser(io.BytesIO(data)))
                out[name] = {str(k): _safe(lambda k=k: describe(doc.getobj(k))) for k in (4, 5)}
            except Exception as e:
                out[name] = {"error": err(e)}
    try:
        from pypdf import PdfReader
        from pypdf.generic import IndirectObject
        reader = PdfReader(io.BytesIO(data))
        out["pypdf"] = {str(k): _safe(lambda k=k: describe(IndirectObject(k, 0, reader).get_object()))
                        for k in (4, 5)}
    except Exception as e:
        out["pypdf"] = {"error": err(e)}
    try:
        import pikepdf
        pdf = pikepdf.open(io.BytesIO(data))
        out["qpdf"] = {str(k): _safe(lambda k=k: _pike(pdf.get_object((k, 0)))) for k in (4, 5)}
    except Exception as e:
        out["qpdf"] = {"error": err(e)}
    return out


def _safe(f):
    try:
        return f()
    except Exception as e:
        return "error " + err(e)


def _pike(o):
    import pikepdf
    if isinstance(o, pikepdf.Dictionary):
        return "dict S=%s" % str(o.get("/S")).lstrip("/")
    return type(o).__name__


# ---------------------------------------------------------------- main

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    urls_path, out_dir = argv[0], argv[1]
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
              "pikepdf": pike, "files": [], "synthetic": {}}
    for name, make in (("swapped_index", swapped_pdf), ("bare_reference", bare_ref_pdf)):
        try:
            result["synthetic"][name] = read_synthetic(make())
        except Exception as e:
            result["synthetic"][name] = {"error": err(e)}
        print(json.dumps({name: result["synthetic"][name]}), flush=True)
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
            row["fetch"] = "error " + err(e)
        result["files"].append(row)
        print(json.dumps({k: v for k, v in row.items() if k != "header_check"})[:3000], flush=True)
    with open(os.path.join(out_dir, "diag2.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
