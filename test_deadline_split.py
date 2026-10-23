# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
import unittest

import deadline_split as ds


def row(created, tagged=True, lang=True, title=False, image_only=False, basic4=False,
        figures=0, figures_alt=0, result="ok"):
    return {"result": result, "created": created, "tagged": tagged, "lang": lang, "title": title,
            "image_only": image_only, "basic4": basic4, "figures": figures,
            "figures_alt": figures_alt}


# Counts taken from the v0.2.2 row file (crawl started 2026-10-16T23:55:01Z), as published in
# docs/deadline-split-results.md.
PUBLISHED = {
    "PRE": {"n": 1081, "tagged": 728, "lang": 692, "title": 488, "image_only": 132, "basic4": 303,
            "figure_files": 451, "figure_files_zero_alt": 227},
    "POST": {"n": 1143, "tagged": 768, "lang": 755, "title": 446, "image_only": 125, "basic4": 276,
             "figure_files": 456, "figure_files_zero_alt": 248},
    "R3": {"n": 390, "tagged": 290},
    "A3": {"n": 396, "tagged": 264},
    "PRE0": {"n": 554, "tagged": 344},
    "POST0": {"n": 379, "tagged": 247},
}

# (first share, second share, diff, diff low, diff high) in percentage points, one decimal,
# exactly as printed in docs/deadline-split-results.md.
PRINTED = {
    "P1": (67.3, 67.2, -0.2, -4.0, 3.7),
    "P2": (64.0, 66.1, 2.0, -1.9, 6.0),
    "P3": (45.1, 39.0, -6.1, -10.2, -2.0),
    "P4": (74.4, 66.7, -7.7, -14.0, -1.3),
    "P5": (62.1, 65.2, 3.1, -3.2, 9.3),
    "P6": (50.3, 54.4, 4.1, -2.4, 10.5),
}
HELD = {"P1": False, "P2": True, "P3": False, "P4": False, "P5": True, "P6": False}


class IntervalTests(unittest.TestCase):
    def test_wilson_matches_newcombe_1998(self):
        low, high = ds.wilson(81, 263)
        self.assertAlmostEqual(low, 0.2553, delta=5e-4)
        self.assertAlmostEqual(high, 0.3662, delta=5e-4)

    def test_newcombe_hybrid_matches_newcombe_1998(self):
        d, low, high = ds.newcombe(48, 80, 56, 70)
        self.assertAlmostEqual(d, 0.2, places=9)
        self.assertAlmostEqual(low, 0.0524, delta=5e-4)
        self.assertAlmostEqual(high, 0.3339, delta=5e-4)


class WindowTests(unittest.TestCase):
    def test_boundaries_are_inclusive_and_split_at_the_extension(self):
        self.assertTrue(ds.in_window("2026-04-19", ds.WINDOWS["PRE"]))
        self.assertFalse(ds.in_window("2026-04-20", ds.WINDOWS["PRE"]))
        self.assertTrue(ds.in_window("2026-04-20", ds.WINDOWS["POST"]))
        self.assertTrue(ds.in_window("2026-10-16", ds.WINDOWS["POST"]))
        self.assertFalse(ds.in_window("2026-10-17", ds.WINDOWS["POST"]))
        self.assertFalse(ds.in_window(None, ds.WINDOWS["POST"]))
        self.assertFalse(ds.in_window("", ds.WINDOWS["POST"]))

    def test_pre_and_post_do_not_overlap(self):
        self.assertLess(ds.WINDOWS["PRE"][1], ds.WINDOWS["POST"][0])
        self.assertLess(ds.WINDOWS["PRE0"][1], ds.WINDOWS["POST0"][0])
        self.assertEqual(ds.WINDOWS["POST0"][0], ds.WINDOWS["PRE"][0])


class CountTests(unittest.TestCase):
    def test_counts(self):
        rows = [
            row("2026-04-19", tagged=True, figures=2, figures_alt=0),
            row("2026-04-20", tagged=False, figures=3, figures_alt=1),
            row("2026-10-17", tagged=True),
            row(None, tagged=True),
            row("2026-05-01", result="http_error"),
            row("2025-04-20", tagged=True, title=True),
        ]
        c = ds.count(rows)
        self.assertEqual(c["_readable"], 5)
        self.assertEqual(c["_dated"], 4)
        self.assertEqual(c["_excluded_after_crawl_day"], 1)
        self.assertEqual((c["PRE"]["n"], c["PRE"]["tagged"]), (2, 2))
        self.assertEqual((c["R3"]["n"], c["R3"]["tagged"]), (1, 1))
        self.assertEqual((c["POST"]["n"], c["POST"]["tagged"]), (1, 0))
        self.assertEqual((c["A3"]["n"], c["A3"]["tagged"]), (1, 0))
        self.assertEqual((c["POST0"]["n"], c["POST0"]["title"]), (1, 1))
        self.assertEqual(c["PRE0"]["n"], 0)
        self.assertEqual((c["PRE"]["figure_files"], c["PRE"]["figure_files_zero_alt"]), (1, 1))
        self.assertEqual((c["POST"]["figure_files"], c["POST"]["figure_files_zero_alt"]), (1, 0))


class PublishedNumbersTests(unittest.TestCase):
    def test_printed_shares_and_intervals_match_the_counts(self):
        preds = ds.predictions(PUBLISHED)
        for name, printed in PRINTED.items():
            p = preds[name]
            got = (p["first_share"], p["second_share"], p["diff"], p["diff_low"], p["diff_high"])
            for value, shown in zip(got, printed):
                self.assertLessEqual(abs(100 * value - shown), 0.06, (name, value, shown))

    def test_verdicts(self):
        preds = ds.predictions(PUBLISHED)
        self.assertEqual({k: v["held"] for k, v in preds.items()}, HELD)


if __name__ == "__main__":
    unittest.main()
