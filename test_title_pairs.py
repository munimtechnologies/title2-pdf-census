# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
import contextlib
import io
import json
import math
import os
import tempfile
import unittest

import title_pairs as tp


def row(qid, created, title, result="ok"):
    return {"qid": qid, "result": result, "created": created, "title": title}


# Site A: PRE 3/4 (two of them also in R3, 2/2), POST 1/3 (two of them also in A3, 1/2),
# PRE0 1/1, POST0 1/2 (the 2025-05-01 rows sit in both PRE and POST0).
# Site B: PRE 0/1, POST 1/1 (also A3), PRE0 0/1, POST0 0/1. Site C: PRE only 1/1 (also POST0).
# Site D: POST only, 0/1, with no title key. Plus rows that must be ignored.
ROWS = [
    row("A", "2025-05-01", False), row("A", "2025-05-01", True),
    row("A", "2026-02-01", True), row("A", "2026-02-01", True),
    row("A", "2026-05-01", True), row("A", "2026-05-01", False), row("A", "2026-08-01", False),
    row("B", "2025-06-01", False), row("B", "2026-06-01", True),
    row("C", "2025-07-01", True),
    {"qid": "D", "result": "ok", "created": "2026-09-01"},
    row("A", "2024-06-01", True), row("B", "2024-06-01", False),
    row("A", "2026-05-01", True, result="http_error"),
    row("A", None, True),
    row("A", "2026-10-17", True),
    row("B", "2023-01-01", True),
]


class WindowTests(unittest.TestCase):
    def test_windows_meet_at_the_extension(self):
        self.assertEqual(tp.WINDOWS["PRE"][1], "2026-04-19")
        self.assertEqual(tp.WINDOWS["POST"][0], "2026-04-20")
        self.assertEqual(tp.WINDOWS["R3"][1], "2026-04-19")
        self.assertEqual(tp.WINDOWS["A3"][0], "2026-04-20")
        self.assertTrue(tp.in_window("2026-10-16", tp.WINDOWS["POST"]))
        self.assertFalse(tp.in_window("2026-10-17", tp.WINDOWS["POST"]))
        self.assertFalse(tp.in_window(None, tp.WINDOWS["PRE"]))

    def test_placebo_is_the_same_split_a_year_earlier(self):
        for now, then in (("PRE", "PRE0"), ("POST", "POST0")):
            for a, b in zip(tp.WINDOWS[now], tp.WINDOWS[then]):
                self.assertEqual(a[4:], b[4:])
                self.assertEqual(int(a[:4]) - int(b[:4]), 1)

    def test_site_counts(self):
        self.assertEqual(tp.site_counts(ROWS, tp.WINDOWS["PRE"]),
                         {"A": [3, 4], "B": [0, 1], "C": [1, 1]})
        self.assertEqual(tp.site_counts(ROWS, tp.WINDOWS["POST"]),
                         {"A": [1, 3], "B": [1, 1], "D": [0, 1]})


class StatsTests(unittest.TestCase):
    def test_sign_test(self):
        self.assertEqual(tp.sign_test(0, 0), 1.0)
        self.assertEqual(tp.sign_test(3, 3), 1.0)
        self.assertAlmostEqual(tp.sign_test(10, 0), 2 / 1024, places=12)
        self.assertAlmostEqual(tp.sign_test(5, 1), 14 / 64, places=12)

    def test_mean_ci_small(self):
        self.assertTrue(math.isnan(tp.mean_ci([])[0]))
        m, low, high = tp.mean_ci([0.25])
        self.assertEqual(m, 0.25)
        self.assertTrue(math.isnan(low) and math.isnan(high))

    def test_unpaired_needs_two_sites_each(self):
        self.assertTrue(math.isnan(tp.unpaired_diff([0.5], [0.0, 1.0])[0]))
        d, low, high = tp.unpaired_diff([1.0, 0.0], [1.0, 0.0, 1.0])
        self.assertAlmostEqual(d, 1 / 6, places=12)
        self.assertLess(low, d)
        self.assertGreater(high, d)

    def test_paired_min_files(self):
        before = {"A": [3, 4], "B": [0, 1]}
        after = {"A": [1, 3], "B": [1, 1]}
        p = tp.paired(before, after, 3)
        self.assertEqual((p["sites"], p["up"], p["down"], p["same"]), (1, 0, 1, 0))
        self.assertAlmostEqual(p["mean"], -5 / 12, places=12)
        empty = tp.paired(before, {})
        self.assertEqual(empty["sites"], 0)
        self.assertTrue(math.isnan(empty["mean"]))


class AnalysisTests(unittest.TestCase):
    def test_analyse(self):
        r = tp.analyse(ROWS)
        self.assertEqual(r["titled"], {"PRE": 4, "POST": 2, "R3": 2, "A3": 2, "PRE0": 1,
                                       "POST0": 2})
        self.assertEqual(r["files"], {"PRE": 6, "POST": 5, "R3": 2, "A3": 3, "PRE0": 2,
                                      "POST0": 4})
        self.assertEqual(r["sites"], {"PRE": 3, "POST": 3, "R3": 1, "A3": 2, "PRE0": 2,
                                      "POST0": 3})
        sw = r["site_weighted"]
        self.assertAlmostEqual(sw["PRE_POST"]["diff"], -5 / 36, places=12)
        self.assertTrue(math.isnan(sw["R3_A3"]["diff"]))
        self.assertAlmostEqual(sw["PRE0_POST0"]["diff"], 0.0, places=12)
        p = r["paired"]["PRE_POST"]
        self.assertEqual((p["sites"], p["up"], p["down"], p["same"]), (2, 1, 1, 0))
        self.assertEqual(p["sign_p"], 1.0)
        self.assertAlmostEqual(p["mean"], 7 / 24, places=12)
        q = r["paired"]["R3_A3"]
        self.assertEqual((q["sites"], q["up"], q["down"], q["same"]), (1, 0, 1, 0))
        self.assertAlmostEqual(q["mean"], -0.5, places=12)
        z = r["paired"]["PRE0_POST0"]
        self.assertEqual((z["sites"], z["up"], z["down"], z["same"]), (2, 0, 1, 1))
        self.assertAlmostEqual(z["mean"], -0.25, places=12)
        d = r["paired_min_files"]
        self.assertEqual((d["sites"], d["min_files"]), (1, 3))
        self.assertAlmostEqual(d["mean"], -5 / 12, places=12)
        self.assertEqual(r["predictions"],
                         {"U1": True, "U2": True, "U3": True, "U4": False, "U5": False,
                          "U6": True})

    def test_main_prints_ten_lines_and_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            data = os.path.join(d, "rows.jsonl")
            out = os.path.join(d, "out.json")
            with open(data, "w", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(r) for r in ROWS) + "\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(tp.main(["title_pairs.py", data, out]), 0)
            lines = buf.getvalue().splitlines()
            self.assertEqual(len(lines), 10)
            self.assertEqual(lines[0],
                             "CHECK title PRE=4/6 POST=2/5 R3=2/2 A3=2/3 PRE0=1/2 POST0=2/4")
            self.assertEqual(lines[1], "SITES PRE=3 POST=3 R3=1 A3=2 PRE0=2 POST0=3")
            self.assertTrue(lines[2].startswith("SW PRE->POST diff=-0.1389 "))
            self.assertTrue(lines[5].startswith("PAIRED PRE->POST sites=2 up=1 down=1 same=0 "))
            self.assertTrue(lines[8].startswith("PAIRED3 PRE->POST sites=1 "))
            self.assertEqual(lines[-1], "predictions held: 4 of 6")
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["files"]["PRE"], 6)


if __name__ == "__main__":
    unittest.main()
