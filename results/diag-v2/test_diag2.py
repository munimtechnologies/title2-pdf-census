"""Tests for diag2.py: finding an object-stream member by header number, and the index report.
No network. Apache-2.0 licensed."""

import unittest

import diag2


class FakeDoc:
    """Just what PDFDocument._getobj_objstm uses."""
    caching = True

    def __init__(self):
        from pdfminer.pdfdocument import PDFDocument
        self._parsed_objs = {}
        self._get_objects = PDFDocument._get_objects.__get__(self)


def objstm():
    from pdfminer.pdftypes import PDFStream
    head = b"4 0 5 9 "
    s = PDFStream({"N": 2, "First": len(head)}, head + b"<</S/A>> <</S/B>>")
    s.objid = 3
    return s


class ByNumber(unittest.TestCase):
    def test_found_by_header_number(self):
        doc, s = FakeDoc(), objstm()
        self.assertEqual(diag2.lit(diag2.getobj_objstm_by_number(doc, s, 1, 4)["S"]), "A")
        self.assertEqual(diag2.lit(diag2.getobj_objstm_by_number(doc, s, 0, 5)["S"]), "B")
        self.assertIn(3, doc._parsed_objs)

    def test_index_used_when_number_absent(self):
        doc, s = FakeDoc(), objstm()
        self.assertEqual(diag2.lit(diag2.getobj_objstm_by_number(doc, s, 1, 9)["S"]), "B")

    def test_patch_is_undone(self):
        from pdfminer.pdfdocument import PDFDocument
        before = PDFDocument._getobj_objstm
        with diag2.by_number():
            self.assertIs(PDFDocument._getobj_objstm, diag2.getobj_objstm_by_number)
        self.assertIs(PDFDocument._getobj_objstm, before)

    def test_header_slots(self):
        self.assertEqual(diag2.header_slots([4, 0, 5, 9, 4, 20, "x"], 3), {4: 0, 5: 1})


class IndexReport(unittest.TestCase):
    def test_counts(self):
        # header order 7, 3, 5; the cross-reference stream numbers them in sorted order instead
        counts, ex = diag2.index_report([(3, 0), (5, 1), (7, 2), (8, 0)], [7, 3, 5], found={3, 8})
        self.assertEqual(counts["index_wrong"], 3)
        self.assertEqual(counts["wrong_index_is_sorted_rank"], 3)
        self.assertEqual(counts["elements_index_wrong"], 1)
        self.assertEqual(counts["absent"], 1)
        self.assertEqual((counts["header_ascending"], counts["duplicate_numbers"]), (0, 0))
        self.assertEqual(ex[0], {"objid": 3, "xref_index": 0, "header_slot": 1})

    def test_all_right(self):
        counts, ex = diag2.index_report([(3, 0), (5, 1)], [3, 5])
        self.assertEqual((counts["index_ok"], counts.get("index_wrong", 0), ex), (2, 0, []))


class Synthetic(unittest.TestCase):
    def test_swapped_layout(self):
        data = diag2.swapped_pdf()
        self.assertTrue(data.startswith(b"%PDF-1.7"))
        self.assertTrue(data.endswith(b"startxref\n%d\n%%%%EOF\n" % data.index(b"6 0 obj")))
        self.assertIn(b"/N 2/First 8/Length 25>>", data)


if __name__ == "__main__":
    unittest.main()
