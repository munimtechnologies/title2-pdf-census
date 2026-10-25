# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
import contextlib
import io
import json
import math
import os
import tempfile
import unittest

import miss_reasons as mr
import panel_retest as pr


def row(qid, h, result="ok", basic4=False, size=100, status=200, space=False, same_site=True):
    r = {"qid": qid, "url_sha256": h, "result": result, "status": status, "url_has_space": space,
         "bytes": size, "same_site": same_site}
    if result == "ok":
        r.update(tagged=True, lang=True, title=True, image_only=False, basic4=basic4,
                 created="2026-01-01")
    return r


# Site S1 (a <base href> site: a5 is a 404 on a link with a space): a1 passes and is read again;
# a2 fails and gets no response the second time; a3 fails and has no second row; a4 fails, is
# hosted off the site and is read again. Site S2: b1 passes and has no second row; b2 fails and is
# read again; b3 fails and is too large the second time. S3 has only a passing file (not paired);
# S4 is readable in the first crawl only.
FIRST = [
    row("S1", "a1", basic4=True, size=100), row("S1", "a2", size=200), row("S1", "a3", size=300),
    row("S1", "a4", size=400, same_site=False),
    row("S1", "a5", result="http_error", status=404, space=True),
    row("S2", "b1", basic4=True, size=10), row("S2", "b2", size=20), row("S2", "b3", size=30),
    row("S3", "c1", basic4=True, size=50),
    row("S4", "d1"),
]
SECOND = [
    row("S1", "a1", basic4=True, size=100), row("S1", "a2", result="http_error", status=0),
    row("S1", "a4", size=400, same_site=False),
    row("S2", "b2", size=20), row("S2", "b3", result="too_large"),
    row("S3", "c1", basic4=True, size=50),
    row("S4", "d1", result="http_error", status=503),
]


class PieceTests(unittest.TestCase):
    def test_reason(self):
        self.assertEqual(mr.reason(row("X", "h", result="http_error", status=0)), "no_response")
        self.assertEqual(mr.reason(row("X", "h", result="http_error", status=None)), "no_response")
        self.assertEqual(mr.reason(row("X", "h", result="http_error", status=403)), "http_4xx")
        self.assertEqual(mr.reason(row("X", "h", result="parse_error")), "parse_error")

    def test_classify(self):
        files, both = mr.classify(FIRST, SECOND)
        self.assertEqual(both, {"S1", "S2", "S3"})
        got = {k[1]: o for k, (_, o, _) in files.items()}
        self.assertEqual(got, {"a1": "seen", "a2": "notok", "a3": "norow", "a4": "seen",
                               "b1": "norow", "b2": "seen", "b3": "notok", "c1": "seen"})
        self.assertEqual(set(mr.paired_sites(files)), {"S1", "S2"})

    def test_size_bands_empty(self):
        s = mr.size_bands([])
        self.assertTrue(math.isnan(s["adjusted"]) and math.isnan(s["unadjusted"]))


class AnalysisTests(unittest.TestCase):
    def test_analyse(self):
        r = mr.analyse(FIRST, SECOND)
        self.assertEqual(r["files"], {"sites_in_both": 3, "paired_sites": 2, "files": 7,
                                      "fail": 5, "pass": 2})
        self.assertEqual(r["outcomes"], {"fail": {"seen": 2, "notok": 2, "norow": 1},
                                         "pass": {"seen": 1, "notok": 0, "norow": 1}})
        g = r["gaps"]
        self.assertAlmostEqual(g["seen"]["mean"], -1 / 12, places=12)
        self.assertAlmostEqual(g["notok"]["mean"], 5 / 12, places=12)
        self.assertAlmostEqual(g["norow"]["mean"], -1 / 3, places=12)
        self.assertEqual((g["notok"]["up"], g["notok"]["down"]), (2, 0))
        self.assertEqual(r["notok_reasons"],
                         {"fail": {"no_response": 1, "too_large": 1}, "pass": {}})
        s = r["size"]
        self.assertEqual(s["cuts"], [30, 200])
        self.assertEqual((s["median_fail"], s["median_pass"]), (200, 55))
        self.assertAlmostEqual(s["unadjusted"], -0.1, places=12)
        self.assertAlmostEqual(s["adjusted"], 0.0, places=12)
        self.assertEqual(s["bands"][2], {"fail": [1, 3], "pass": [0, 0]})
        h, o = r["base_href_split"]["base_href"], r["base_href_split"]["other"]
        self.assertEqual((h["sites"], h["down"], o["sites"], o["up"]), (1, 1, 1, 1))
        self.assertAlmostEqual(o["mean"], 0.5, places=12)
        self.assertEqual(r["same_site_split"],
                         {"onsite": {"fail": [1, 4], "pass": [1, 2]},
                          "offsite": {"fail": [1, 1], "pass": [0, 0]}})
        self.assertEqual(r["predictions"], {"M1": True, "M2": True, "M3": True, "M4": False})

    def test_seen_gap_matches_panel_retest(self):
        r = mr.analyse(FIRST, SECOND)
        p = pr.analyse(FIRST, SECOND)["paired_basic4"]
        self.assertEqual(r["gaps"]["seen"]["sites"], p["sites"])
        self.assertAlmostEqual(r["gaps"]["seen"]["mean"], p["mean"], places=12)

    def test_identical_crawls(self):
        r = mr.analyse(FIRST, FIRST)
        self.assertEqual(r["gaps"]["seen"]["same"], 2)
        self.assertEqual(r["gaps"]["seen"]["mean"], 0.0)
        self.assertFalse(r["predictions"]["M1"])
        self.assertFalse(r["predictions"]["M4"])

    def test_main_prints_eleven_lines_and_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for name, rows in (("first.jsonl", FIRST), ("second.jsonl", SECOND)):
                paths.append(os.path.join(d, name))
                with open(paths[-1], "w", encoding="utf-8") as f:
                    f.write("\n".join(json.dumps(r) for r in rows) + "\n")
            out = os.path.join(d, "out.json")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(mr.main(["miss_reasons.py", paths[0], paths[1], out]), 0)
            lines = buf.getvalue().splitlines()
            self.assertEqual(len(lines), 11)
            self.assertEqual(lines[0], "FILES sites_in_both=3 paired_sites=2 files=7 fail=5 pass=2")
            self.assertEqual(lines[1],
                             "OUTCOME fail seen=2 notok=2 norow=1 pass seen=1 notok=0 norow=1")
            self.assertEqual(lines[2], "GAPS seen=-0.0833 notok=0.4167 norow=-0.3333 sites=2")
            self.assertTrue(lines[3].startswith(
                "GAP notok up=2 down=0 same=0 sign_p=0.5000 mean=0.4167 ("))
            self.assertTrue(lines[4].startswith(
                "GAP norow up=1 down=1 same=0 sign_p=1.0000 mean=-0.3333 ("))
            self.assertEqual(lines[5], "NOTOK fail no_response=1,too_large=1 pass none")
            self.assertEqual(lines[6], "SIZE median fail=200 pass=55 cuts=30,200 "
                                       "unadjusted=-0.1000 adjusted=0.0000")
            self.assertEqual(lines[7], "BANDS b0 fail=1/1 pass=0/1 b1 fail=0/1 pass=1/1 "
                                       "b2 fail=1/3 pass=0/0")
            self.assertTrue(lines[8].startswith(
                "SPLIT base_href sites=1 up=0 down=1 mean=-0.6667 other sites=1 up=1 down=0 "
                "sign_p=1.0000 mean=0.5000 ("))
            self.assertEqual(lines[9], "PLACE onsite fail=1/4 pass=1/2 offsite fail=1/1 pass=0/0")
            self.assertEqual(lines[10], "predictions held: 3 of 4")
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["files"]["paired_sites"], 2)


if __name__ == "__main__":
    unittest.main()
