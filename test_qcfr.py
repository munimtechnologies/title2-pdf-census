"""Tests for qcfr.py: the province groups, the site table, the site-permutation test and the
scoring of Q1 on made-up rows shaped like lang.py's own (its PUBLIC_FIELDS plus qid). Loads
results/lang-v1/lang.py (0.1.1) as in the repository. No network. Apache-2.0 licensed. Made by
MV2 of Munim, Inc. with AI agents."""

import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qcfr  # noqa: E402

LANG = os.path.join(HERE, "results", "lang-v1", "lang.py")
REPS = 2000


def doc(lang, qid, state, primary="fr", text="fr", result="ok"):
    """A row with every public field of lang.py, a site id and the given text and /Lang."""
    d = dict.fromkeys(lang.PUBLIC_FIELDS)
    d.update(qid=qid, url_sha256="0" * 64, kind="city", state=state, producer_family="word",
             result=result, text_lang=text, lang_present=primary is not None,
             lang_well_formed=primary is not None, lang_primary=primary,
             element_langs={}, mc_langs={}, text_langs={text: 1000})
    return d


def sites(lang, state, n_sites, per_site, wrong_per_site, start=0):
    """n_sites sites in one province, each with per_site French PDFs, wrong_per_site declared en."""
    rows = []
    for i in range(start, start + n_sites):
        for j in range(per_site):
            rows.append(doc(lang, "Q%d" % (1000 + i), state, "en" if j < wrong_per_site else "fr"))
    return rows


class StatsTests(unittest.TestCase):
    def test_fisher_known_table(self):
        self.assertAlmostEqual(qcfr.fisher_greater(3, 1, 1, 3), 17 / 70)
        self.assertAlmostEqual(qcfr.fisher_greater(0, 4, 4, 0), 1.0)

    def test_groups(self):
        self.assertEqual(qcfr.group_of("Quebec"), "quebec")
        self.assertEqual(qcfr.group_of("Ontario"), "rest")
        self.assertEqual(qcfr.group_of("New Brunswick"), "rest")
        self.assertIsNone(qcfr.group_of(None))
        self.assertIsNone(qcfr.group_of(""))

    def test_gap(self):
        table = [["quebec", 4, 1], ["quebec", 6, 1], ["rest", 5, 4], ["rest", 5, 1]]
        self.assertAlmostEqual(qcfr.gap(table, [t[0] for t in table]), 5 / 10 - 2 / 10)

    def test_permutation_extremes(self):
        # 5 sites all wrong against 5 all right: only 1 of the 252 labelings is as extreme
        table = [["rest", 5, 5]] * 5 + [["quebec", 5, 0]] * 5
        p = qcfr.permutation_p(table, REPS)
        self.assertLess(p, 0.02)
        self.assertEqual(p, qcfr.permutation_p(table, REPS))  # same seed, same p
        # the reverse is as far from the prediction as it can be
        rev = [["rest", 5, 0]] * 5 + [["quebec", 5, 5]] * 5
        self.assertEqual(qcfr.permutation_p(rev, REPS), 1.0)

    def test_one_big_site_is_not_enough(self):
        # one site outside Quebec with many wrong PDFs: a PDF-level test would call it, the site
        # permutation does not, because any of the 5 'rest' labels could have landed on it
        table = [["rest", 60, 60]] + [["rest", 2, 0]] * 4 + [["quebec", 2, 0]] * 5
        self.assertLess(qcfr.fisher_greater(60, 8, 0, 10), 0.001)
        self.assertGreater(qcfr.permutation_p(table, REPS), 0.3)


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang = qcfr.load_lang(LANG)

    def noise(self):
        """Rows Q1 must not count: English text, undetermined, failed, no province."""
        L = self.lang
        return [doc(L, "Q900", "Ontario", "en", "en"), doc(L, "Q901", "Quebec", "fr", "undetermined"),
                doc(L, "Q902", "Quebec", "en", "mixed"), doc(L, "Q903", "Ontario", result="error"),
                doc(L, "Q904", None, "en"), doc(L, "Q905", "", None)]

    def test_held(self):
        docs = (sites(self.lang, "Ontario", 3, 5, 4) + sites(self.lang, "New Brunswick", 3, 5, 3, 3)
                + sites(self.lang, "Quebec", 8, 5, 1, 6) + self.noise())
        s = qcfr.score(docs, self.lang, REPS)
        q1 = s["Q1_rest_wrong_more_than_quebec"]
        self.assertEqual(q1["rest"], {"sites": 6, "k": 21, "n": 30, "share": 0.7})
        self.assertEqual(q1["quebec"], {"sites": 8, "k": 8, "n": 40, "share": 0.2})
        self.assertEqual(q1["status"], "scored")
        self.assertEqual(q1["gap"], 0.5)
        self.assertIs(q1["met"], True)
        self.assertEqual(s["french_text_no_province"], 2)
        self.assertEqual(s["french_text"], 72)
        self.assertEqual(s["ok"], len(docs) - 1)
        self.assertEqual(s["explore_by_group"]["rest"]["declared"], {"match": 9, "other": 21})
        self.assertEqual(s["explore_by_group"]["quebec"]["declared_other_primary"], {"en": 8})

    def test_not_held(self):
        docs = sites(self.lang, "Ontario", 5, 4, 1) + sites(self.lang, "Quebec", 5, 4, 2, 5)
        q1 = qcfr.score(docs, self.lang, REPS)["Q1_rest_wrong_more_than_quebec"]
        self.assertEqual(q1["status"], "scored")
        self.assertLess(q1["gap"], 0)
        self.assertIs(q1["met"], False)

    def test_equal_shares_not_held(self):
        docs = sites(self.lang, "Ontario", 5, 4, 2) + sites(self.lang, "Quebec", 5, 4, 2, 5)
        q1 = qcfr.score(docs, self.lang, REPS)["Q1_rest_wrong_more_than_quebec"]
        self.assertEqual(q1["gap"], 0.0)
        self.assertIs(q1["met"], False)

    def test_too_few(self):
        # 3 sites outside Quebec is under the minimum of 4, however many PDFs they have
        docs = sites(self.lang, "Ontario", 3, 10, 10) + sites(self.lang, "Quebec", 10, 5, 0, 3)
        q1 = qcfr.score(docs, self.lang, REPS)["Q1_rest_wrong_more_than_quebec"]
        self.assertEqual(q1["status"], "inconclusive: too few")
        self.assertIsNone(q1["met"])
        self.assertIsNone(q1["p_permutation"])
        # 4 sites but only 16 PDFs is under the minimum of 20
        docs = sites(self.lang, "Ontario", 4, 4, 4) + sites(self.lang, "Quebec", 10, 5, 0, 4)
        q1 = qcfr.score(docs, self.lang, REPS)["Q1_rest_wrong_more_than_quebec"]
        self.assertEqual(q1["status"], "inconclusive: too few")

    def test_missing_and_unusable_lang_count_as_wrong(self):
        L = self.lang
        docs = [doc(L, "Q1", "Ontario", None), doc(L, "Q1", "Ontario", ""), doc(L, "Q1", "Ontario", "fr")]
        table, split = qcfr.site_table(qcfr.french_rows(docs, L), L)
        self.assertEqual((table, split), ([["rest", 3, 2]], 0))

    def test_site_in_two_groups_left_out(self):
        L = self.lang
        docs = [doc(L, "Q1", "Quebec"), doc(L, "Q1", "Ontario", "en"), doc(L, "Q2", "Quebec")]
        table, split = qcfr.site_table(qcfr.french_rows(docs, L), L)
        self.assertEqual((table, split), ([["quebec", 1, 0]], 1))

    def test_public_table_rescores(self):
        docs = (sites(self.lang, "Ontario", 4, 6, 3) + sites(self.lang, "Manitoba", 2, 3, 3, 4)
                + sites(self.lang, "Quebec", 9, 4, 1, 6))
        s = qcfr.score(docs, self.lang, REPS)
        table, _ = qcfr.site_table(qcfr.french_rows(docs, self.lang), self.lang)
        self.assertEqual(qcfr.score_sites(table, REPS), s["Q1_rest_wrong_more_than_quebec"])
        for row in table:
            self.assertEqual(len(row), 3)
            self.assertIn(row[0], ("quebec", "rest"))

    def test_report_words(self):
        docs = sites(self.lang, "Ontario", 5, 5, 4) + sites(self.lang, "Quebec", 6, 5, 1, 5)
        text = qcfr.report(qcfr.score(docs, self.lang, REPS))
        self.assertIn("outside Quebec 20 of 25 (5 sites), Quebec 6 of 30 (6 sites)", text)
        self.assertIn("| held |", text)
        low = text.lower()
        for bad in ("an ai", "by hand", "http", "://"):
            self.assertNotIn(bad, low)
        self.assertIsNone(re.search(r"Q1\d{3}", text))  # no site id

    def test_versions_checked(self):
        with mock.patch.object(qcfr, "LANG_VERSION", "9.9.9"):
            with self.assertRaises(RuntimeError):
                qcfr.load_lang(LANG)


class MainTests(unittest.TestCase):
    def test_writes_counts_only_and_refuses_used_folder(self):
        lang = qcfr.load_lang(LANG)
        docs = sites(lang, "Ontario", 4, 5, 3) + sites(lang, "Quebec", 4, 5, 1, 4)
        for d in docs:
            d["url"] = "https://example.invalid/a.pdf"
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "docs-private.jsonl")
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(json.dumps(d) + "\n" for d in docs))
            out = os.path.join(tmp, "out")
            with mock.patch("sys.stdout"):
                self.assertEqual(qcfr.main(["--lang", LANG, "--docs", src, "--out-dir", out]), 0)
                self.assertEqual(qcfr.main(["--lang", LANG, "--docs", src, "--out-dir", out]), 2)
            self.assertEqual(sorted(os.listdir(out)), ["results.md", "sites-public.json", "summary.json"])
            for name in os.listdir(out):
                with open(os.path.join(out, name), encoding="utf-8") as f:
                    body = f.read()
                for bad in ("://", "example", "qid", "url"):
                    self.assertNotIn(bad, body, name)
                self.assertIsNone(re.search(r"Q1\d{3}", body), name)
            with open(os.path.join(out, "sites-public.json"), encoding="utf-8") as f:
                self.assertEqual(json.load(f), [["quebec", 5, 1]] * 4 + [["rest", 5, 3]] * 4)


if __name__ == "__main__":
    unittest.main()
