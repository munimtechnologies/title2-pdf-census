# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
import unittest

import site_split as ss


def row(qid, created, tagged=True, result="ok"):
    return {"qid": qid, "result": result, "created": created, "tagged": tagged}


# Site A: R3 2/2 tagged, A3 0/1 (down). Site B: R3 0/1, A3 1/2 (up). Site C: A3 only, 1/1.
# Site D: R3 1/1, A3 1/1 (same). Plus rows that must be ignored.
ROWS = [
    row("A", "2026-01-20"), row("A", "2026-04-19"), row("A", "2026-04-20", tagged=False),
    row("B", "2026-03-01", tagged=False), row("B", "2026-05-01"), row("B", "2026-07-19", tagged=False),
    row("C", "2026-06-01"),
    row("D", "2026-02-01"), row("D", "2026-06-01"),
    row("A", "2026-05-01", result="http_error"),
    row("B", None),
    row("C", "2026-07-20"),
    row("D", "2026-01-19"),
]


class StatsTests(unittest.TestCase):
    def test_sign_test_exact(self):
        self.assertAlmostEqual(ss.sign_test(0, 5), 0.0625, places=12)
        self.assertAlmostEqual(ss.sign_test(1, 9), 22 / 1024, places=12)
        self.assertAlmostEqual(ss.sign_test(9, 1), 22 / 1024, places=12)
        self.assertEqual(ss.sign_test(3, 3), 1.0)
        self.assertEqual(ss.sign_test(0, 0), 1.0)

    def test_mean_ci(self):
        m, low, high = ss.mean_ci([0.0, 1.0])
        self.assertAlmostEqual(m, 0.5, places=12)
        self.assertAlmostEqual(low, 0.5 - 0.979982, places=6)
        self.assertAlmostEqual(high, 0.5 + 0.979982, places=6)

    def test_unpaired_diff(self):
        d, low, high = ss.unpaired_diff([0.0, 1.0], [1.0, 1.0])
        self.assertAlmostEqual(d, 0.5, places=12)
        self.assertAlmostEqual(low, 0.5 - 0.979982, places=6)
        self.assertAlmostEqual(high, 0.5 + 0.979982, places=6)


class WindowTests(unittest.TestCase):
    def test_windows_are_inclusive_and_meet_at_the_extension(self):
        self.assertEqual(ss.WINDOWS["A3"][0], "2026-04-20")
        self.assertEqual(ss.WINDOWS["R3"][1], "2026-04-19")
        self.assertTrue(ss.in_window("2026-07-19", ss.WINDOWS["A3"]))
        self.assertFalse(ss.in_window("2026-07-20", ss.WINDOWS["A3"]))
        self.assertFalse(ss.in_window("2026-01-19", ss.WINDOWS["R3"]))
        self.assertFalse(ss.in_window(None, ss.WINDOWS["R3"]))

    def test_placebo_is_the_same_months_a_year_earlier(self):
        for now, then in (("R3", "R3_2025"), ("A3", "A3_2025")):
            for a, b in zip(ss.WINDOWS[now], ss.WINDOWS[then]):
                self.assertEqual(a[4:], b[4:])
                self.assertEqual(int(a[:4]) - int(b[:4]), 1)


class AnalysisTests(unittest.TestCase):
    def test_site_counts(self):
        self.assertEqual(ss.site_counts(ROWS, ss.WINDOWS["R3"]),
                         {"A": [2, 2], "B": [0, 1], "D": [1, 1]})
        self.assertEqual(ss.site_counts(ROWS, ss.WINDOWS["A3"]),
                         {"A": [0, 1], "B": [1, 2], "C": [1, 1], "D": [1, 1]})

    def test_analyse(self):
        r = ss.analyse(ROWS)
        self.assertEqual(r["sites"]["R3"], 3)
        self.assertEqual(r["sites"]["A3"], 4)
        self.assertEqual((r["tagged"]["R3"], r["files"]["R3"]), (3, 4))
        self.assertEqual((r["tagged"]["A3"], r["files"]["A3"]), (3, 5))
        self.assertAlmostEqual(r["site_weighted"]["R3"]["mean"], 2 / 3, places=12)
        self.assertAlmostEqual(r["site_weighted"]["A3"]["mean"], 0.625, places=12)
        self.assertAlmostEqual(r["site_weighted_diff"]["diff"], 0.625 - 2 / 3, places=12)
        p = r["paired"]
        self.assertEqual((p["sites"], p["up"], p["down"], p["same"]), (3, 1, 1, 1))
        self.assertAlmostEqual(p["mean"], -0.5 / 3, places=12)
        self.assertEqual(r["placebo_paired"]["sites"], 0)
        self.assertEqual(r["predictions"],
                         {"S1": True, "S2": True, "S3": False, "S4": True, "S5": False,
                          "S6": False})

    def test_pooled_without_top_breaks_ties_by_qid(self):
        c = {name: ss.site_counts(ROWS, ss.WINDOWS[name]) for name in ("R3", "A3")}
        top = ss.pooled_without_top(c["R3"], c["A3"], drop=1)
        self.assertEqual((top["dropped_sites"], top["dropped_files"]), (1, 3))
        self.assertEqual((top["before_k"], top["before_n"]), (1, 2))
        self.assertEqual((top["after_k"], top["after_n"]), (3, 4))
        self.assertAlmostEqual(top["diff"], 0.25, places=12)


if __name__ == "__main__":
    unittest.main()
