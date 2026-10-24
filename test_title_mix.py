# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
import contextlib
import io
import json
import math
import os
import tempfile
import unittest

import title_mix as tm


def row(qid, created, family, title, result="ok"):
    return {"qid": qid, "result": result, "created": created, "producer_family": family,
            "title": title}


# One site. PRE: office 2/2 titled, adobe 1/2, rest (libreoffice) 0/1.
# POST: office 1/2 (office-other + word), print-to-pdf 0/2. Plus rows that must be ignored.
ROWS = [
    row("A", "2025-05-01", "word", True), row("A", "2025-05-01", "word", True),
    row("A", "2025-06-01", "adobe", True), row("A", "2025-06-01", "adobe", False),
    row("A", "2025-07-01", "libreoffice", False),
    row("A", "2026-05-01", "office-other", True), row("A", "2026-05-01", "word", False),
    row("A", "2026-06-01", "print-to-pdf", False), row("A", "2026-06-01", "print-to-pdf", False),
    row("A", "2026-05-01", "word", True, result="http_error"),
    row("A", None, "word", True),
    row("A", "2026-10-17", "word", True),
]


class GroupTests(unittest.TestCase):
    def test_groups(self):
        for family, expected in (("word", "office"), ("office-other", "office"),
                                 ("adobe", "adobe"), ("print-to-pdf", "print-to-pdf"),
                                 ("scanner", "scanner"), ("unknown", "unknown"),
                                 ("libreoffice", "rest"), ("google-docs", "rest"),
                                 ("generator", "rest"), ("other", "rest")):
            self.assertEqual(tm.group({"producer_family": family}), expected)

    def test_group_counts_cover_every_group(self):
        c = tm.group_counts(tm.window_rows(ROWS, tm.WINDOWS["PRE"]))
        self.assertEqual(c, {"office": [2, 2], "adobe": [1, 2], "print-to-pdf": [0, 0],
                             "scanner": [0, 0], "unknown": [0, 0], "rest": [0, 1]})


class WindowTests(unittest.TestCase):
    def test_windows_meet_at_the_extension(self):
        self.assertEqual(tm.WINDOWS["PRE"][1], "2026-04-19")
        self.assertEqual(tm.WINDOWS["POST"][0], "2026-04-20")
        self.assertEqual(tm.WINDOWS["R3"][1], "2026-04-19")
        self.assertEqual(tm.WINDOWS["A3"][0], "2026-04-20")
        self.assertTrue(tm.in_window("2026-10-16", tm.WINDOWS["POST"]))
        self.assertFalse(tm.in_window("2026-10-17", tm.WINDOWS["POST"]))
        self.assertFalse(tm.in_window(None, tm.WINDOWS["PRE"]))

    def test_placebo_is_the_same_split_a_year_earlier(self):
        for now, then in (("PRE", "PRE0"), ("POST", "POST0")):
            for a, b in zip(tm.WINDOWS[now], tm.WINDOWS[then]):
                self.assertEqual(a[4:], b[4:])
                self.assertEqual(int(a[:4]) - int(b[:4]), 1)


class DecomposeTests(unittest.TestCase):
    def test_parts_add_up(self):
        before = {"office": [2, 2], "adobe": [1, 2], "print-to-pdf": [0, 0], "scanner": [0, 0],
                  "unknown": [0, 0], "rest": [0, 0]}
        after = {"office": [1, 2], "adobe": [0, 0], "print-to-pdf": [0, 2], "scanner": [0, 0],
                 "unknown": [0, 0], "rest": [0, 0]}
        d = tm.decompose(before, after)
        self.assertAlmostEqual(d["diff"], -0.5, places=12)
        self.assertAlmostEqual(d["within"], -0.25, places=12)
        self.assertAlmostEqual(d["mix"], -0.25, places=12)

    def test_same_mix_means_no_mix_part(self):
        before = {g: [1, 4] for g in tm.GROUP_ORDER}
        after = {g: [3, 4] for g in tm.GROUP_ORDER}
        d = tm.decompose(before, after)
        self.assertAlmostEqual(d["within"], 0.5, places=12)
        self.assertAlmostEqual(d["mix"], 0.0, places=12)

    def test_empty_window_is_nan(self):
        empty = {g: [0, 0] for g in tm.GROUP_ORDER}
        self.assertTrue(math.isnan(tm.decompose(empty, empty)["within"]))


class AnalysisTests(unittest.TestCase):
    def test_analyse(self):
        r = tm.analyse(ROWS, reps=50)
        self.assertEqual(r["titled"], {"PRE": 3, "POST": 1, "R3": 0, "A3": 1, "PRE0": 0,
                                       "POST0": 3})
        self.assertEqual(r["files"], {"PRE": 5, "POST": 4, "R3": 0, "A3": 4, "PRE0": 0,
                                      "POST0": 5})
        m = r["PRE_POST"]
        self.assertAlmostEqual(m["diff"], -0.35, places=12)
        self.assertAlmostEqual(m["within"], -0.2, places=12)
        self.assertAlmostEqual(m["mix"], -0.15, places=12)
        self.assertTrue(math.isnan(r["R3_A3"]["within"]))
        self.assertEqual(r["largest_groups"], ["office", "adobe", "rest"])
        self.assertEqual(r["largest_lower"], ["office"])
        b = r["bootstrap_within_PRE_POST"]
        self.assertEqual((b["sites"], b["reps"]), (1, 50))
        self.assertAlmostEqual(b["low"], -0.2, places=12)
        self.assertAlmostEqual(b["high"], -0.2, places=12)
        self.assertEqual(r["predictions"],
                         {"T1": False, "T2": True, "T3": False, "T4": False, "T5": False,
                          "T6": True})

    def test_bootstrap_is_reproducible(self):
        rows = ROWS + [row("B", "2025-05-01", "adobe", False), row("B", "2026-05-01", "adobe", True)]
        pre = tm.window_rows(rows, tm.WINDOWS["PRE"])
        post = tm.window_rows(rows, tm.WINDOWS["POST"])
        first = tm.bootstrap_within(pre, post, reps=200)
        self.assertEqual(first, tm.bootstrap_within(pre, post, reps=200))
        self.assertEqual(first["sites"], 2)
        self.assertLessEqual(first["low"], first["high"])

    def test_main_prints_nine_lines_and_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            data = os.path.join(d, "rows.jsonl")
            out = os.path.join(d, "out.json")
            with open(data, "w", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(r) for r in ROWS) + "\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(tm.main(["title_mix.py", data, out]), 0)
            lines = buf.getvalue().splitlines()
            self.assertEqual(len(lines), 9)
            self.assertTrue(lines[0].startswith("CHECK title PRE=3/5 POST=1/4"))
            self.assertEqual(lines[-1], "predictions held: 2 of 6")
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["files"]["PRE"], 5)


if __name__ == "__main__":
    unittest.main()
