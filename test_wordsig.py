"""Tests for wordsig.py: the cohort query in census.py's shape, the exact Fisher tests and power,
and the scoring of W1-W4 on made-up rows, including the lang-census Word note's 11 of 13 against
2 of 14. Loads census 0.2.2 (fixtures/census_0_2_2.py) and results/lang-v1/lang.py (0.1.1). No
network. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents."""

import json
import os
import sys
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wordsig as ws  # noqa: E402

CENSUS = os.path.join(HERE, "fixtures", "census_0_2_2.py")  # wordsig ran with census 0.2.2
LANG = os.path.join(HERE, "results", "lang-v1", "lang.py")


def doc(qid, family, text="fr", primary="en", local=False, result="ok"):
    """A lang.py row: text language, catalog /Lang and, if local, the text language on elements."""
    return {"qid": qid, "producer_family": family, "result": result, "text_lang": text,
            "lang_present": primary is not None, "lang_primary": primary,
            "element_langs": {text: 3} if local else {}, "mc_langs": {}}


def group(family, k, n, sites, text="fr", primary="en"):
    """n mismatched rows of one family, the first k marked inside, spread over sites."""
    return [doc("Q%d" % (i % sites), family, text, primary, i < k) for i in range(n)]


class StatsTests(unittest.TestCase):
    def test_fisher_known_tables(self):
        # [[3, 1], [1, 3]]: one-sided 17/70, two-sided 34/70
        self.assertAlmostEqual(ws.fisher_greater(3, 1, 1, 3), 17 / 70)
        self.assertAlmostEqual(ws.fisher_two_sided(3, 1, 1, 3), 34 / 70)
        self.assertAlmostEqual(ws.fisher_greater(0, 4, 4, 0), 1.0)

    def test_word_note_table(self):
        # the lang-census Word note: 11 of 13 Word against 2 of 14 Adobe
        self.assertEqual(round(ws.fisher_two_sided(11, 2, 2, 12), 4), 0.0004)
        self.assertAlmostEqual(ws.fisher_greater(11, 2, 2, 12), 7281 / 20058300)
        self.assertAlmostEqual(ws.fisher_two_sided(11, 2, 2, 12), 8478 / 20058300)

    def test_power_edges(self):
        # all-or-nothing shares: 4 of 4 against 0 of 4 gives p = 1/70; 3 against 3 gives 1/20
        self.assertEqual(ws.power(4, 4, 1.0, 0.0), 1.0)
        self.assertEqual(ws.power(3, 3, 1.0, 0.0), 0.0)
        self.assertEqual(ws.power(1, 1, 0.9, 0.1), 0.0)
        # with no real difference W1 holds less often than alpha (Fisher's test is conservative)
        self.assertLess(ws.power(8, 8, 0.5, 0.5), 0.05)

    def test_power_table(self):
        table = ws.power_table()
        self.assertEqual(len(table), len(ws.POWER_NS) * len(ws.POWER_SHARES))
        for row in table:
            self.assertTrue(0.0 <= row["power"] <= 1.0)
        # bigger samples and bigger gaps give more power
        by = {(r["n_word"], r["word_share"]): r["power"] for r in table}
        self.assertLess(by[(8, 0.8)], by[(15, 0.8)])
        self.assertLess(by[(10, 0.7)], by[(10, 0.8)])


class QueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.census, cls.lang = ws.setup(CENSUS, LANG)

    def test_setup_swaps_query_seed_and_agent(self):
        self.assertEqual(self.census.COHORT_QUERY, ws.cohort_query())
        self.assertEqual(self.lang.SITE_SEED, "wordsig-v1")
        self.assertEqual(self.census.UA, ws.UA)
        self.assertIn("mv2@munimtech.com", ws.UA)

    def test_query_shape(self):
        for cls in ws.CLASSES:
            q = ws.cohort_query(cls, 10000)
            self.assertIn("wdt:P17 wd:Q16", q)
            self.assertIn("FILTER(?pop >= 10000)", q)
            self.assertEqual(sum(1 for line in q.splitlines() if "OPTIONAL" in line), 1)
            self.assertEqual(q.count("{"), q.count("}"))
            self.assertEqual(q.count(" ?stateLabel"), 2)

    def test_fallback_without_provinces(self):
        seen = []
        body = {"results": {"bindings": [
            {"item": {"value": "http://www.wikidata.org/entity/Q172"}, "itemLabel": {"value": "Toronto"},
             "typeLabel": {"value": "city"}, "population": {"value": "2794356"},
             "website": {"value": "https://www.toronto.ca/"}},
            {"item": {"value": "http://www.wikidata.org/entity/Q340"}, "itemLabel": {"value": "Montreal"},
             "typeLabel": {"value": "city"}, "population": {"value": "1762949"},
             "website": {"value": "https://montreal.ca/"}}]}}

        def get(url, max_bytes, timeout=20):
            seen.append(url)
            if len(seen) == 1:
                return types.SimpleNamespace(status=504, body=b"", error="timeout")
            return types.SimpleNamespace(status=200, body=json.dumps(body).encode(), error=None)

        with mock.patch.object(self.census.time, "sleep"):
            rows = self.census.fetch_cohort(get=get)
        self.assertEqual(len(seen), 2)
        self.assertIn("OPTIONAL", self.census.urllib.parse.unquote_plus(seen[0]))
        second = self.census.urllib.parse.unquote_plus(seen[1])
        self.assertNotIn("OPTIONAL", second)
        self.assertNotIn("stateLabel", second)
        self.assertIn("wd:Q16", second)
        self.assertEqual([r["qid"] for r in rows], ["Q172", "Q340"])

    def test_versions_checked(self):
        with mock.patch.object(ws, "LANG_VERSION", "9.9.9"):
            with self.assertRaises(RuntimeError):
                ws.setup(CENSUS, LANG)


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang = ws.load(LANG, "lang")

    def noise(self):
        """Rows that are not mismatched: right /Lang, no /Lang, undetermined, failed, other family."""
        return [doc("Q1", "word", "fr", "fr", True), doc("Q2", "adobe", "en", "en"),
                doc("Q3", "word", "fr", None), doc("Q4", "adobe", "undetermined", "en"),
                doc("Q5", "word", "mixed", "en"), doc("Q6", "word", result="error"),
                doc("Q7", "libreoffice", local=True)]

    def test_word_note_held(self):
        docs = group("word", 11, 13, 11) + group("adobe", 2, 14, 9) + self.noise()
        s = ws.score(docs, self.lang)
        w1 = s["W1_word_marks_inside_more_than_adobe"]
        self.assertEqual((w1["word"]["k"], w1["word"]["n"], w1["adobe"]["k"], w1["adobe"]["n"]), (11, 13, 2, 14))
        self.assertEqual(w1["status"], "scored")
        self.assertIs(w1["met"], True)
        self.assertEqual(w1["p_one_sided"], round(7281 / 20058300, 6))
        self.assertIs(s["W2_word_60_adobe_40"]["met"], True)
        self.assertEqual(s["W4_word_sites"], {"sites": 11, "met": True})
        self.assertEqual(s["mismatched"], 28)
        self.assertEqual(s["ok"], len(docs) - 1)
        # only one direction has rows, so W3 cannot be judged
        self.assertIsNone(s["W3_same_sign_each_direction"]["met"])
        self.assertEqual(s["explore_mismatched_by_family_direction"]["word|fr-as-en"], [13, 11])
        self.assertEqual(s["explore_mismatched_by_family_direction"]["libreoffice|fr-as-en"], [1, 1])

    def test_too_few(self):
        s = ws.score(group("word", 7, 7, 7) + group("adobe", 0, 20, 5), self.lang)
        w1 = s["W1_word_marks_inside_more_than_adobe"]
        self.assertEqual(w1["status"], "inconclusive: too few")
        self.assertIsNone(w1["met"])
        self.assertIsNone(s["W2_word_60_adobe_40"]["met"])
        self.assertIsNotNone(w1["p_one_sided"])

    def test_not_held_and_one_site(self):
        s = ws.score(group("word", 5, 10, 1) + group("adobe", 5, 10, 5), self.lang)
        self.assertIs(s["W1_word_marks_inside_more_than_adobe"]["met"], False)
        self.assertIs(s["W2_word_60_adobe_40"]["met"], False)
        self.assertEqual(s["W4_word_sites"], {"sites": 1, "met": False})

    def test_both_directions(self):
        docs = (group("word", 8, 10, 6) + group("adobe", 1, 10, 6)
                + group("word", 3, 4, 3, "en", "fr") + group("adobe", 0, 4, 3, "en", "fr"))
        s = ws.score(docs, self.lang)
        w3 = s["W3_same_sign_each_direction"]
        self.assertEqual(w3["directions"]["en-as-fr"]["word"], {"k": 3, "n": 4, "share": 0.75})
        self.assertTrue(w3["directions"]["fr-as-en"]["testable"])
        self.assertIs(w3["met"], True)
        flipped = docs[:20] + group("word", 0, 4, 3, "en", "fr") + group("adobe", 3, 4, 3, "en", "fr")
        self.assertIs(ws.score(flipped, self.lang)["W3_same_sign_each_direction"]["met"], False)

    def test_french_and_report(self):
        docs = group("word", 11, 13, 11) + group("adobe", 2, 14, 9) + self.noise()
        s = ws.score(docs, self.lang)
        fr = s["explore_french_wrong"]
        # French text: 28 declared English (one of them LibreOffice's), 1 with no /Lang, 1 right
        self.assertEqual((fr["k"], fr["n"]), (29, 30))
        text = ws.report(s)
        self.assertIn("Word 11 of 13, Adobe 2 of 14", text)
        self.assertIn("| held |", text)
        low = text.lower()
        for bad in ("an ai", "by hand", "http"):
            self.assertNotIn(bad, low)


if __name__ == "__main__":
    unittest.main()
