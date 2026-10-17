"""Tests for tagtree-reach, on small hand-built tagged PDFs. Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import io
import os
import tempfile
import unittest

import tagtree

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


class AnalyzeTags(unittest.TestCase):
    def test_base_counts_each_class(self):
        r = tagtree.analyze_tags(tagged_pdf())
        self.assertEqual(r["result"], "ok")
        self.assertEqual((r["reachable"], r["untagged"], r["dangling"], r["artifact"]), (20, 10, 0, 5))
        self.assertEqual(r["content_chars"], 30)
        self.assertAlmostEqual(r["leak_share"], 0.3333)
        self.assertFalse(r["shell"])
        self.assertEqual(r["elements"], 3)

    def test_mcid_the_tree_never_reaches_is_dangling(self):
        r = tagtree.analyze_tags(tagged_pdf(doc_kids=b"[8 0 R]"))
        self.assertEqual((r["reachable"], r["dangling"], r["untagged"]), (10, 10, 10))

    def test_nested_span_keeps_outer_mcid(self):
        content = (b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 700 Td (Hello) Tj ET "
                   b"/Span <</Lang (en-US)>> BDC BT /F1 12 Tf 72 690 Td (inner) Tj ET EMC "
                   b"BT /F1 12 Tf 72 680 Td (after) Tj ET EMC")
        r = tagtree.analyze_tags(tagged_pdf(content))
        self.assertEqual((r["reachable"], r["untagged"]), (15, 0))

    def test_form_xobjects(self):
        # Fm1 is drawn inside the page's MCID 0 (reachable); Fm2 carries its own MCID (unknown).
        r = tagtree.analyze_tags(tagged_pdf(b"/Figure <</MCID 0>> BDC /Fm1 Do EMC /Fm2 Do"))
        self.assertEqual((r["reachable"], r["xobject"], r["untagged"]), (6, 4, 0))

    def test_shell_page(self):
        content = b"/P <</MCID 0>> BDC BT /F1 12 Tf 72 700 Td (" + b"a" * 60 + b") Tj ET EMC"
        r = tagtree.analyze_tags(tagged_pdf(content, doc_kids=b"[]"))
        self.assertEqual((r["reachable"], r["dangling"]), (0, 60))
        self.assertTrue(r["shell"])

    def test_mcid_without_page_counts_everywhere(self):
        r = tagtree.analyze_tags(tagged_pdf(doc_kids=b"[8 0 R]", first_pg=False))
        self.assertEqual((r["reachable"], r["dangling"]), (10, 10))
        self.assertEqual(r["wildcard_mcids"], 1)

    def test_no_structure_tree(self):
        self.assertEqual(tagtree.analyze_tags(tagged_pdf(struct=False))["result"], "no_struct_tree")

    def test_child_process(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(tagged_pdf())
        try:
            r = tagtree.analyze_file(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual((r["result"], r["reachable"]), ("ok", 20))


class Pieces(unittest.TestCase):
    def test_discordance(self):
        self.assertEqual(tagtree.discordance([0, 1, 2, 3, 4]), 0.0)
        self.assertEqual(tagtree.discordance([4, 3, 2, 1, 0]), 1.0)
        self.assertAlmostEqual(tagtree.discordance([1, 0, 2, 3, 4]), 0.1)

    def test_classify(self):
        self.assertEqual(tagtree.classify([("P", 0, False, 0), ("Artifact", None, False, 0)]), ("artifact", None))
        self.assertEqual(tagtree.classify([("P", 3, False, 0), ("Span", None, False, 0)]), ("mcid", 3))
        self.assertEqual(tagtree.classify([("P", 3, False, 1)]), ("xobject", None))
        self.assertEqual(tagtree.classify([("Span", None, True, 0)]), ("named", None))
        self.assertEqual(tagtree.classify([]), ("none", None))

    def test_upward_jump_and_order(self):
        chars = [("mcid", 0, 72, 200, 600, 12), ("mcid", 1, 72, 200, 700, 12)]
        self.assertEqual(tagtree.page_metrics(chars, [0, 1], set())["upward_jumps"], 1)
        self.assertEqual(tagtree.page_metrics(chars, [1, 0], set())["upward_jumps"], 0)
        side = [("mcid", 0, 72, 200, 600, 12), ("mcid", 1, 320, 500, 700, 12)]  # next column
        self.assertEqual(tagtree.page_metrics(side, [0, 1], set())["upward_jumps"], 0)
        many = [("mcid", i, 72, 200, 700 - 20 * i, 12) for i in range(5)]
        row = tagtree.page_metrics(many, [1, 0, 2, 3, 4], set())
        self.assertAlmostEqual(row["discordance"], 0.1)
        self.assertEqual(row["ordered"], 5)


class Summary(unittest.TestCase):
    def doc(self, qid, fam, leak, shell=False, disc=(0.0,)):
        return {"qid": qid, "kind": "city", "producer_family": fam, "result": "ok", "capped": False,
                "content_chars": 100, "leak_share": leak, "shell": shell, "page_discordance": list(disc),
                "reachable": 100, "untagged": 0, "dangling": 0, "artifact": 0, "xobject": 0, "named": 0,
                "upward_jumps": 0}

    def test_predictions(self):
        docs = [self.doc("Q%d" % (i // 2), "word" if i < 4 else "adobe", 0.5 if i >= 8 else 0.0)
                for i in range(10)]
        docs.append({"qid": "Q9", "result": "timeout"})
        docs.append(dict(self.doc("Q9", "word", 0.0), content_chars=10))
        s = tagtree.summarize(docs, [{"status": "ok"}])
        self.assertEqual(s["eligible"], 10)
        self.assertEqual(s["excluded_little_text"], 1)
        self.assertEqual(s["P1_leaky"]["k"], 2)
        self.assertTrue(s["predictions"]["P1 leaky share >= 0.10"])
        self.assertAlmostEqual(s["P2_difference"], 0.3333)
        self.assertTrue(s["predictions"]["P2 other minus word >= 0.10"])
        self.assertFalse(s["predictions"]["P3 shell share >= 0.02"])
        self.assertTrue(s["predictions"]["P4 median discordance <= 0.05"])
        self.assertIn("P1", tagtree.report(s))


if __name__ == "__main__":
    unittest.main()
