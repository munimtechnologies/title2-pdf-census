# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
import contextlib
import io
import json
import math
import os
import tempfile
import unittest

import panel_retest as pr


def row(qid, h, result="ok", basic4=False, title=False, size=100, status=200, space=False):
    r = {"qid": qid, "url_sha256": h, "result": result, "status": status, "url_has_space": space,
         "bytes": size}
    if result == "ok":
        r.update(tagged=True, lang=True, title=title, image_only=False, basic4=basic4,
                 created="2026-01-01")
    return r


# Site S1: a1 read twice and unchanged; a2 read twice but re-saved (title and basic4 flip, one byte
# more); a3 not read again; a4 a 404 on a link with a space (marks S1 as a <base href> site).
# Site S2: b1 read twice; b2 tried again but an HTTP error the second time.
# Site S3: read the first time only (the second crawl got only an error there). S4: second only.
FIRST = [
    row("S1", "a1"), row("S1", "a2", basic4=True, title=True, size=200), row("S1", "a3", size=300),
    row("S1", "a4", result="http_error", status=404, space=True),
    row("S2", "b1", basic4=True, size=10), row("S2", "b2", size=20),
    row("S3", "c1"),
]
SECOND = [
    row("S1", "a1"), row("S1", "a2", size=201), row("S1", "x1"),
    row("S2", "b1", basic4=True, size=10), row("S2", "b2", result="http_error", status=500),
    row("S3", "c9", result="http_error", status=503),
    row("S4", "d1"),
]
SAME = [row("P", "p1", basic4=True), row("P", "p2"), row("P", "p3"),
        row("Q", "q1", basic4=True), row("Q", "q2")]


class MatchTests(unittest.TestCase):
    def test_match_needs_the_same_site(self):
        r = pr.analyse([row("X", "h")], [row("Y", "h")])
        self.assertEqual(r["seen"]["files"], 0)
        self.assertEqual(r["sites_in_both"], 0)
        self.assertTrue(math.isnan(r["seen_on_sites_in_both"]["share"]))

    def test_base_href_sites(self):
        self.assertEqual(pr.base_href_sites(FIRST), {"S1"})


class StatsTests(unittest.TestCase):
    def test_sign_test(self):
        self.assertEqual(pr.sign_test(0, 0), 1.0)
        self.assertAlmostEqual(pr.sign_test(0, 2), 0.5, places=12)
        self.assertAlmostEqual(pr.sign_test(10, 0), 2 / 1024, places=12)

    def test_mean_ci_small(self):
        self.assertTrue(math.isnan(pr.mean_ci([])[0]))
        m, low, high = pr.mean_ci([0.25])
        self.assertEqual(m, 0.25)
        self.assertTrue(math.isnan(low) and math.isnan(high))


class AnalysisTests(unittest.TestCase):
    def test_analyse(self):
        r = pr.analyse(FIRST, SECOND)
        self.assertEqual(r["first"], {"ok": 6, "sites": 3})
        self.assertEqual(r["second"], {"ok": 5, "sites": 3})
        self.assertEqual(r["sites_in_both"], 2)
        self.assertEqual((r["seen"]["files"], r["seen"]["of"]), (3, 6))
        self.assertEqual((r["seen_on_sites_in_both"]["files"], r["seen_on_sites_in_both"]["of"]),
                         (3, 5))
        self.assertEqual(r["seen_any_result"], {"files": 4, "of": 6})
        a = r["agree"]
        self.assertEqual((a["pairs"], a["checks_same"], a["bytes_same"], a["created_same"]),
                         (3, 2, 2, 3))
        self.assertEqual(a["disagreements"],
                         {"tagged": 0, "lang": 0, "title": 1, "image_only": 0, "basic4": 1})
        b = r["basic4"]
        self.assertEqual((b["fail"], b["pass"]),
                         ({"seen": 1, "files": 4}, {"seen": 2, "files": 2}))
        self.assertAlmostEqual(b["diff"], -0.75, places=12)
        q = r["paired_basic4"]
        self.assertEqual((q["sites"], q["up"], q["down"], q["same"]), (2, 0, 2, 0))
        self.assertAlmostEqual(q["sign_p"], 0.5, places=12)
        self.assertAlmostEqual(q["mean"], -0.75, places=12)
        self.assertEqual(r["base_href_split"],
                         {"base_href": {"sites": 1, "seen": 2, "files": 3},
                          "other": {"sites": 1, "seen": 1, "files": 2}})
        self.assertEqual(sum(r["predictions"].values()), 0)

    def test_identical_crawls_hold_every_prediction(self):
        r = pr.analyse(SAME, SAME)
        self.assertEqual(r["seen"]["share"], 1.0)
        self.assertEqual(r["paired_basic4"]["sites"], 2)
        self.assertEqual(r["paired_basic4"]["same"], 2)
        self.assertEqual(r["predictions"],
                         {"R1": True, "R2": True, "R3": True, "R4": True, "R5": True, "R6": True})

    def test_no_passing_files_never_holds_r5_r6(self):
        rows = [row("P", "p2"), row("P", "p3")]
        r = pr.analyse(rows, rows)
        self.assertTrue(math.isnan(r["basic4"]["diff"]))
        self.assertEqual(r["paired_basic4"]["sites"], 0)
        self.assertFalse(r["predictions"]["R5"])
        self.assertFalse(r["predictions"]["R6"])
        self.assertTrue(r["predictions"]["R1"])

    def test_main_prints_eight_lines_and_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for name, rows in (("first.jsonl", FIRST), ("second.jsonl", SECOND)):
                paths.append(os.path.join(d, name))
                with open(paths[-1], "w", encoding="utf-8") as f:
                    f.write("\n".join(json.dumps(r) for r in rows) + "\n")
            out = os.path.join(d, "out.json")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(pr.main(["panel_retest.py", paths[0], paths[1], out]), 0)
            lines = buf.getvalue().splitlines()
            self.assertEqual(len(lines), 8)
            self.assertEqual(lines[0], "ROWS first ok=6 sites=3 second ok=5 sites=3 sites_in_both=2")
            self.assertEqual(lines[1],
                             "SEEN all=3/6 (0.5000) sites_in_both=3/5 (0.6000) any_result=4/6")
            self.assertEqual(lines[2], "AGREE pairs=3 checks=2 bytes=2 created=3")
            self.assertEqual(lines[3], "DISAGREE tagged=0 lang=0 title=1 image_only=0 basic4=1")
            self.assertEqual(lines[4], "BASIC4 fail=1/4 pass=2/2 diff=-0.7500")
            self.assertTrue(lines[5].startswith(
                "PAIRED sites=2 up=0 down=2 same=0 sign_p=0.5000 mean=-0.7500 "))
            self.assertEqual(lines[6], "SPLIT base_href sites=1 seen=2/3 other sites=1 seen=1/2")
            self.assertEqual(lines[7], "predictions held: 0 of 6")
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["seen"]["files"], 3)


if __name__ == "__main__":
    unittest.main()
