"""Checks the wordsig results (pre-registered in docs/wordsig-prereg.md): scores the public rows
in results/wordsig-v1/ again with wordsig.score and checks that every value in summary.json that
does not need a site id comes out the same; checks run-facts.json against the summary and the
pre-registration; and checks that docs/wordsig-results.md and the dated section of
docs/lang-word-note.md are exactly what wordsig_page.py writes from those files. Public rows carry
no site id, so W4's site count and the site-resampled intervals are not rechecked. No network.
Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents."""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wordsig as ws  # noqa: E402
import wordsig_page as wp  # noqa: E402

RES = os.path.join(HERE, "results", "wordsig-v1")
LANG = os.path.join(HERE, "results", "lang-v1", "lang.py")
# values that need a site id, and the count that includes PDFs public rows leave out
SITE_KEYS = ("cluster_ci95", "W4_word_sites", "pdfs")


def text(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def without_sites(x):
    if isinstance(x, dict):
        return {k: without_sites(v) for k, v in x.items() if k not in SITE_KEYS}
    return x


class ResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang = ws.load(LANG, "lang")
        cls.rows = wp.load_public(RES)
        cls.s = json.loads(text("results", "wordsig-v1", "summary.json"))
        cls.f = json.loads(text("results", "wordsig-v1", "run-facts.json"))
        cls.page = text("docs", "wordsig-results.md")
        cls.note = text("docs", "lang-word-note.md")
        cls.prereg = text("docs", "wordsig-prereg.md")

    def test_public_rows(self):
        self.assertEqual(len(self.rows), self.s["ok"])
        for d in self.rows:
            self.assertEqual(d["result"], "ok")
            self.assertLessEqual(set(d), set(self.lang.PUBLIC_FIELDS))

    def test_rescored(self):
        # url_sha256 stands in for the site id; every value that needs the real one is left out
        rows = [dict(d, qid=d["url_sha256"]) for d in self.rows]
        again = json.loads(json.dumps(ws.score(rows, self.lang)))
        self.assertEqual(without_sites(again), without_sites(self.s))

    def test_w1(self):
        w1 = self.s["W1_word_marks_inside_more_than_adobe"]
        w, a = w1["word"], w1["adobe"]
        self.assertEqual(w1["status"] == "scored", w["n"] >= ws.MIN_GROUP and a["n"] >= ws.MIN_GROUP)
        if w["n"] and a["n"]:
            p = ws.fisher_greater(w["k"], w["n"] - w["k"], a["k"], a["n"] - a["k"])
            self.assertEqual(round(p, 6), w1["p_one_sided"])

    def test_w3_as_the_text_says(self):
        dirs = self.s["W3_same_sign_each_direction"]["directions"]
        for v in dirs.values():
            self.assertEqual(v["testable"], v["word"]["n"] >= 3 and v["adobe"]["n"] >= 3)
        if all(v["testable"] for v in dirs.values()):
            want = all(v["word"]["k"] * v["adobe"]["n"] > v["adobe"]["k"] * v["word"]["n"]
                       for v in dirs.values())
            self.assertIs(wp.w3_prereg(self.s), want)
        else:
            self.assertIsNone(wp.w3_prereg(self.s))

    def test_facts(self):
        f, s = self.f, self.s
        self.assertEqual(f["pdfs_from_sites"], s["pdfs"])
        self.assertGreaterEqual(s["pdfs"], s["ok"])
        self.assertLessEqual(f["sites_crawled"], f["cohort_sites"])
        self.assertEqual(sum(f["site_results"].values()), f["sites_crawled"])
        self.assertEqual(sum(f["cohort_provinces"].values()), f["cohort_sites"])
        self.assertTrue(f["code_matches_prereg"])
        for name in wp.STUDY_FILES:
            self.assertIn(f["code_sha256"][name], self.prereg, name)

    def test_page(self):
        self.assertEqual(self.page, wp.page(self.s, self.f))

    def test_note(self):
        self.assertEqual(self.note.count(wp.NOTE_HEAD), 1)
        self.assertIn(wp.note_section(self.s, self.f), self.note)
        self.assertTrue(self.note.rstrip().endswith(wp.SIGN))

    def test_wording(self):
        for doc in (self.page, wp.note_section(self.s, self.f), json.dumps(self.f)):
            low = doc.lower()
            for bad in wp.BANNED:
                self.assertNotIn(bad, low)
        self.assertIn(wp.SIGN, self.page)
        self.assertIn("(wordsig-prereg.md)", self.page)
        self.assertIn("no government is named", self.page)


if __name__ == "__main__":
    unittest.main()
