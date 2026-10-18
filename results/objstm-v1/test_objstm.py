"""Tests for objstm.py: the index check on small PDFs built here (via diag2.build_pdf), the child
process, and the summary's pre-registered counts on made-up records. No network.
Apache-2.0 licensed."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diag2  # noqa: E402
import objstm  # noqa: E402


def in_order_pdf():
    """swapped_pdf's file with the indexes the header implies: 4 at 0, 5 at 1."""
    return diag2.build_pdf(b"4 0 5 9 ", b"<</S/A>> <</S/B>>", 2, [(2, 3, 0), (2, 3, 1)])


class Check(unittest.TestCase):
    def test_swapped(self):
        r = objstm.check_bytes(diag2.swapped_pdf())
        self.assertEqual((r["result"], r["compressed_objects"], r["streams"], r["index_ok"], r["index_wrong"]),
                         ("ok", 2, 1, 0, 2))
        self.assertEqual((r["streams_with_wrong_index"], r["absent"], r["duplicate_numbers"]), (1, 0, 0))
        self.assertFalse(r["hybrid"])
        self.assertFalse(r["word365"])

    def test_in_order(self):
        r = objstm.check_bytes(in_order_pdf())
        self.assertEqual((r["compressed_objects"], r["index_ok"], r["index_wrong"]), (2, 2, 0))
        self.assertEqual(r["streams_with_wrong_index"], 0)

    def test_child_process(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(diag2.swapped_pdf())
        try:
            r = objstm.check_file(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual((r["result"], r["index_wrong"]), ("ok", 2))

    def test_not_a_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"not a pdf")
        try:
            r = objstm.check_file(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(r["result"], "error")

    def test_hybrid(self):
        self.assertTrue(objstm.is_hybrid(b"trailer\n<< /Size 9 /XRefStm 1234 >>"))
        self.assertFalse(objstm.is_hybrid(b"<< /Type /XRef /Size 9 >>"))


def doc(h, fam, compressed, wrong, changed=False, content=100):
    d = {"qid": "Q1", "kind": "city", "url": "https://example.org/%s.pdf" % h, "url_sha256": h,
         "producer_family": fam, "created": "2025-03-01", "result": "ok", "capped": False,
         "elements": 5, "content_chars": content, "reachable": content, "untagged": 0, "dangling": 0,
         "leak_share": 0.0, "shell": False, "page_discordance": [0.0], "upward_jumps": 0}
    d["o"] = {"result": "ok", "compressed_objects": compressed, "index_wrong": wrong,
              "elements_index_wrong": wrong, "hybrid": False, "word365": fam == "word",
              "producer": "Some Producer", "sha256": "0" * 64}
    if wrong:
        d["xref_index"] = {k: d.get(k) for k in objstm.TAGTREE_KEYS}
        if changed:
            d["xref_index"].update(elements=0, dangling=content, reachable=0, leak_share=1.0)
    return d


class Summary(unittest.TestCase):
    def setUp(self):
        self.docs = [doc("a", "word", 10, 4, changed=True), doc("b", "word", 10, 0),
                     doc("c", "adobe", 10, 0), doc("d", "adobe", 0, 0), doc("e", "word", 10, 2),
                     doc("f", "word", 10, 3, content=10)]  # f: too little text, not eligible

    def test_counts(self):
        s = objstm.summarize(self.docs)
        self.assertEqual((s["pdfs"], s["eligible"], s["checked"], s["with_object_streams"],
                          s["with_wrong_index"], s["changed_by_xref_index"]), (6, 5, 5, 4, 2, 1))
        self.assertEqual((s["O1_wrong_share"]["k"], s["O1_wrong_share"]["n"], s["O1_wrong_share"]["met"]),
                         (2, 4, False))
        self.assertEqual((s["O2_word_share"]["k"], s["O2_word_share"]["n"], s["O2_word_share"]["met"]),
                         (2, 2, True))
        self.assertEqual(s["O3_changed"], {"k": 1, "max": 2, "met": True})
        self.assertEqual(s["explore_by_family"], {"adobe": [1, 0], "word": [3, 2]})
        self.assertEqual(s["explore_word365"], {"word365": [3, 2]})
        self.assertEqual(s["explore_wrong_fraction_median"], 0.3)
        self.assertEqual(s["known_files"], {})
        self.assertIn("| O1: under 5% of PDFs with object streams have a wrong index |", objstm.report(s))

    def test_none_wrong(self):
        s = objstm.summarize([doc("b", "word", 10, 0)])
        self.assertIsNone(s["O2_word_share"]["met"])
        self.assertTrue(s["O1_wrong_share"]["met"])
        self.assertIn("not testable", objstm.report(s))

    def test_known_file(self):
        h = "c8c71fae13ccf1cf19cd67e19caf9f6caccad3bb0c4dc520ad8939e3c0b425b7"
        s = objstm.summarize([doc(h, "word", 859, 785, changed=True)])
        self.assertEqual(s["known_files"]["c8c71fae"],
                         {"eligible": True, "same_bytes": False, "index_wrong": 785, "expected": 785,
                          "changed": True})

    def test_public(self):
        row = objstm.public(self.docs[0])
        self.assertNotIn("url", row)
        self.assertNotIn("qid", row)
        self.assertNotIn("producer", row["o"])
        self.assertEqual(row["xref_index"]["elements"], 0)
        self.assertNotIn("http", str(row))


if __name__ == "__main__":
    unittest.main()
