"""Tests for tagtree-xcheck, on the same small hand-built tagged PDFs as tagtree's own tests.
With a one-byte font, bytes and characters are the same, so the pypdf reader must match tagtree
exactly here. Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import io
import os
import tempfile
import unittest

import tagtree
import xcheck

FORM = b"/Type /XObject /Subtype /Form /BBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> "
BASE = (b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 700 Td (Hello world) Tj ET EMC\n"
        b"/Artifact BMC BT /F1 12 Tf 72 40 Td (Page 1) Tj ET EMC\n"
        b"/P <</MCID 1>> BDC BT /F1 12 Tf 72 680 Td (Second line) Tj ET EMC\n"
        b"BT /F1 12 Tf 72 660 Td (Orphan text) Tj ET\n")


def stream(data, extra=b""):
    return b"<< /Length %d %s>>\nstream\n" % (len(data), extra) + data + b"\nendstream"


def build(objs):
    """A PDF from (number, body) pairs numbered 1..n, with a correct xref table."""
    out = io.BytesIO()
    out.write(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for num, body in objs:
        offsets[num] = out.tell()
        out.write(b"%d 0 obj\n" % num + body + b"\nendobj\n")
    xref = out.tell()
    n = max(offsets) + 1
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % n)
    for i in range(1, n):
        out.write(b"%010d 00000 n \n" % offsets[i])
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref))
    return out.getvalue()


def tagged_pdf(content=BASE, doc_kids=b"[8 0 R 9 0 R]", first_pg=True, struct=True):
    catalog = b"<< /Type /Catalog /Pages 2 0 R /MarkInfo << /Marked true >>"
    catalog += b" /StructTreeRoot 5 0 R >>" if struct else b" >>"
    return build([
        (1, catalog),
        (2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >>"
            b" /XObject << /Fm1 10 0 R /Fm2 11 0 R >> >> /Contents 6 0 R /StructParents 0 >>"),
        (4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        (5, b"<< /Type /StructTreeRoot /K [7 0 R] >>"),
        (6, stream(content)),
        (7, b"<< /Type /StructElem /S /Document /P 5 0 R /K " + doc_kids + b" >>"),
        (8, b"<< /Type /StructElem /S /P /P 7 0 R" + (b" /Pg 3 0 R" if first_pg else b"") + b" /K 0 >>"),
        (9, b"<< /Type /StructElem /S /P /P 7 0 R /Pg 3 0 R /K 1 >>"),
        (10, stream(b"BT /F1 12 Tf 72 600 Td (Inform) Tj ET", FORM)),
        (11, stream(b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 500 Td (Xobj) Tj ET EMC", FORM)),
    ])


NESTED = (b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 700 Td (Hello) Tj ET "
          b"/Span <</Lang (en-US)>> BDC BT /F1 12 Tf 72 690 Td (inner) Tj ET EMC "
          b"BT /F1 12 Tf 72 680 Td (after) Tj ET EMC")
SHELL = b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 700 Td (" + b"a" * 60 + b") Tj ET EMC"
VARIANTS = {
    "base": tagged_pdf(),
    "dangling": tagged_pdf(doc_kids=b"[8 0 R]"),
    "nested": tagged_pdf(NESTED),
    "forms": tagged_pdf(b"/Figure <</MCID 0>> BDC /Fm1 Do EMC /Fm2 Do"),
    "shell": tagged_pdf(SHELL, doc_kids=b"[]"),
    "wildcard": tagged_pdf(doc_kids=b"[8 0 R]", first_pg=False),
    "tj": tagged_pdf(b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 700 Td [(He) -20 (llo) 5 ( )] TJ ET EMC"),
}


class Reader(unittest.TestCase):
    def test_base_counts_each_class(self):
        r = xcheck.analyze_x(VARIANTS["base"])
        self.assertEqual(r["result"], "ok")
        self.assertEqual((r["reachable"], r["untagged"], r["dangling"], r["artifact"]), (20, 10, 0, 5))
        self.assertEqual((r["content_units"], r["elements"], r["shell"]), (30, 3, False))
        self.assertTrue(r["walks_equal"])

    def test_dangling_forms_shell_wildcard(self):
        r = xcheck.analyze_x(VARIANTS["dangling"])
        self.assertEqual((r["reachable"], r["dangling"], r["untagged"]), (10, 10, 10))
        r = xcheck.analyze_x(VARIANTS["forms"])
        self.assertEqual((r["reachable"], r["xobject"], r["untagged"]), (6, 4, 0))
        r = xcheck.analyze_x(VARIANTS["shell"])
        self.assertEqual((r["reachable"], r["dangling"], r["shell"]), (0, 60, True))
        r = xcheck.analyze_x(VARIANTS["wildcard"])
        self.assertEqual((r["reachable"], r["dangling"], r["wildcard_mcids"]), (10, 10, 1))

    def test_tj_arrays_skip_numbers_and_spaces(self):
        self.assertEqual(xcheck.analyze_x(VARIANTS["tj"])["reachable"], 5)

    def test_no_structure_tree(self):
        self.assertEqual(xcheck.analyze_x(tagged_pdf(struct=False))["result"], "no_struct_tree")

    def test_matches_tagtree_on_every_variant(self):
        for name, data in VARIANTS.items():
            x, t = xcheck.analyze_x(data), tagtree.analyze_tags(data)
            for k in xcheck.CLASSES + ("elements", "shell", "wildcard_mcids"):
                self.assertEqual(x[k], t[k], (name, k))
            self.assertEqual(x["content_units"], t["content_chars"], name)
            self.assertTrue(x["walks_equal"], name)

    def test_child_process(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(VARIANTS["base"])
        try:
            r = xcheck.analyze_x_file(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual((r["result"], r["reachable"]), ("ok", 20))

    def test_classify(self):
        self.assertEqual(xcheck.classify([("/P", 0, False, 0), ("/Artifact", None, False, 0)]), ("artifact", None))
        self.assertEqual(xcheck.classify([("/P", 3, False, 0), ("/Span", None, False, 0)]), ("mcid", 3))
        self.assertEqual(xcheck.classify([("/P", 3, False, 1)]), ("xobject", None))
        self.assertEqual(xcheck.classify([("/Span", None, True, 0)]), ("named", None))
        self.assertEqual(xcheck.classify([]), ("none", None))


class Compare(unittest.TestCase):
    def doc(self, leak=0.0, shell=False, dangling=0, x=None, content=100):
        d = {"url_sha256": "h", "result": "ok", "capped": False, "content_chars": content, "leak_share": leak,
             "shell": shell, "elements": 5, "reachable": 100, "untagged": 0, "dangling": dangling,
             "artifact": 0, "xobject": 0, "named": 0}
        d["x"] = x if x is not None else {"result": "ok", "elements": 5, "walks_equal": True,
                                          "dangling": dangling, "shell": shell, "leak_share": leak}
        return d

    def test_checks(self):
        docs = [self.doc() for _ in range(18)]
        docs.append(self.doc(leak=0.5, shell=True, dangling=10))
        docs.append(self.doc(x={"result": "ok", "elements": 4, "walks_equal": False, "dangling": 3,
                                "shell": True, "leak_share": 0.2}))
        docs.append(self.doc(content=10))            # not eligible
        docs.append(self.doc(x={"result": "timeout"}))  # eligible, not read by pypdf
        s = xcheck.compare(docs)
        self.assertEqual((s["eligible"], s["pairs"]), (21, 20))
        for name in ("X1_elements_equal", "X2_walks_equal", "X3_any_dangling_agree",
                     "X4_shell_agree", "X5_leaky_agree"):
            self.assertEqual((s["checks"][name]["k"], s["checks"][name]["n"]), (19, 20), name)
        self.assertTrue(s["checks"]["X1_elements_equal"]["met"])
        self.assertTrue(s["checks"]["X4_shell_agree"]["met"])
        self.assertEqual(len(s["disagreements"]), 1)
        self.assertNotIn("url", s["disagreements"][0])
        self.assertIn("X1_elements_equal", xcheck.report(s))


if __name__ == "__main__":
    unittest.main()
