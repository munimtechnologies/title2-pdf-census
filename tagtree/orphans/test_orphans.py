"""Tests for tagtree-orphans' pure parts. Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import unittest

import orphans

CASE = {"id": "t", "page": 1, "orphan_mcids": [15, 16, 19]}


def ch(kind, mcid=None):
    return (kind, mcid, 0.0, 1.0, 10.0, 1.0)


class Split(unittest.TestCase):
    def test_counts(self):
        chars = [ch("mcid", 1), ch("mcid", 15), ch("mcid", 15), ch("none"), ch("artifact"),
                 ch("xobject"), ch("mcid", 16)]
        self.assertEqual(orphans.split(chars, {1}),
                         {"text": {"1": 1, "15": 2, "16": 1}, "dangling": {"15": 2, "16": 1}})

    def test_all_reached(self):
        self.assertEqual(orphans.split([ch("mcid", 3)], {3}), {"text": {"3": 1}, "dangling": {}})


class Judge(unittest.TestCase):
    def test_all_met(self):
        pages = {"1": {"text": {"1": 5, "15": 2, "16": 3, "19": 1},
                       "dangling": {"15": 2, "16": 3, "19": 1}}, "2": {"text": {}, "dangling": {}}}
        v = orphans.judge(CASE, pages, {"result": "ok", "dangling": 6})
        self.assertTrue(v["O1_dangling_text"])
        self.assertTrue(v["O2_exact_mcids"])
        self.assertTrue(v["O3_counts_agree"])
        self.assertEqual(v["dangling_mcids"], [15, 16, 19])

    def test_extra_or_missing_mcid_fails_o2(self):
        pages = {"1": {"text": {"15": 2, "16": 3, "19": 1, "20": 4},
                       "dangling": {"15": 2, "16": 3, "20": 4}}}
        v = orphans.judge(CASE, pages, {"result": "ok", "dangling": 9})
        self.assertTrue(v["O1_dangling_text"])
        self.assertFalse(v["O2_exact_mcids"])
        self.assertEqual(v["dangling_mcids"], [15, 16, 20])

    def test_named_mcid_without_text_is_left_out(self):
        pages = {"1": {"text": {"15": 2, "16": 3}, "dangling": {"15": 2, "16": 3}}}
        v = orphans.judge(CASE, pages, {"result": "ok", "dangling": 5})
        self.assertEqual(v["named_with_text"], [15, 16])
        self.assertTrue(v["O2_exact_mcids"])

    def test_no_named_text_is_untestable(self):
        pages = {"1": {"text": {"1": 5}, "dangling": {}}}
        v = orphans.judge(CASE, pages, {"result": "ok", "dangling": 0})
        self.assertIsNone(v["O1_dangling_text"])
        self.assertIsNone(v["O2_exact_mcids"])
        self.assertTrue(v["O3_counts_agree"])

    def test_counts_disagree(self):
        pages = {"1": {"text": {"15": 2}, "dangling": {"15": 2}}}
        self.assertFalse(orphans.judge(CASE, pages, {"result": "ok", "dangling": 7})["O3_counts_agree"])

    def test_not_analysed(self):
        v = orphans.judge(CASE, None, {"result": "timeout"})
        self.assertIsNone(v["O1_dangling_text"])
        self.assertIsNone(v["O3_counts_agree"])

    def test_report(self):
        rows = [{"id": "t", "record": {"result": "ok", "reachable": 9, "untagged": 0, "dangling": 6},
                 "verdicts": {"O1_dangling_text": True, "O2_exact_mcids": True,
                              "O3_counts_agree": True, "named_with_text": [15],
                              "dangling_mcids": [15]}},
                {"id": "u", "result": "download_error"}]
        text = orphans.report(rows)
        self.assertIn("| t | ok | 9 | 0 | 6 |", text)
        self.assertIn("| u | download_error |", text)


if __name__ == "__main__":
    unittest.main()
