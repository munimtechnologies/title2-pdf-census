# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered template-pages result from its saved table.

Reads results/template-pages/pages.csv, result.json and result.txt (the run's output, unchanged)
and recomputes every measure, gate, prediction and described count with the pinned
template_check.py (unchanged, which imports a11y_pages.py). It also checks that pages.csv holds
no page text (only the pre-registered columns), that the one row whose name and links were
withheld in the census table is the only withheld row, and that every figure in
results/template-pages/TEMPLATE-PAGES-RESULT.md matches the data.

Standard library only: python -m unittest discover -p test_template_pages_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import template_check as tc  # noqa: E402

RES = os.path.join(ROOT, "results", "template-pages")
NOTE = os.path.join(RES, "TEMPLATE-PAGES-RESULT.md")
WITHHELD = "[withheld]"


def load_json(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return json.load(f)


def norm(x):
    """The value as it reads back from result.json (tuples become lists)."""
    return json.loads(json.dumps(x))


def pct(x):
    """0.0241 -> '2.41', 1.0 -> '100'."""
    s = "%.2f" % (x * 100)
    return s[:-3] if s.endswith(".00") else s


def share(m):
    """[k, n, p, [lo, hi]] -> 'k of n (p%, 95% CI lo-hi%)'."""
    k, n, p, (lo, hi) = m
    return "%s of %s (%s%%, 95%% CI %s-%s%%)" % (format(k, ","), format(n, ","), pct(p),
                                                 pct(lo), pct(hi))


class TemplatePagesResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        with open(os.path.join(RES, "pages.csv"), encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            cls.header = list(reader.fieldnames)
            cls.raw = list(reader)
        cls.rows = tc.typed(cls.raw)
        cls.n_table = {c: t["pages"] for c, t in cls.result["tables"].items()}

    def test_columns_hold_no_page_text(self):
        self.assertEqual(self.header, tc.COLUMNS)

    def test_pinned_version_gates_and_tables(self):
        self.assertEqual(self.result["version"], tc.__version__)
        self.assertTrue(self.result["gates"]["P0_prereg_public"])
        self.assertTrue(self.result["gates"]["G0_tables"])
        self.assertEqual(self.n_table, tc.EXPECTED_PAGES)

    def test_one_row_per_page(self):
        for cohort, n in tc.EXPECTED_PAGES.items():
            qids = [r["qid"] for r in self.raw if r["cohort"] == cohort]
            self.assertEqual(len(qids), n, cohort)
            self.assertEqual(len(set(qids)), n, cohort)

    def test_regrade_measures_gate_and_predictions(self):
        measures, gate, preds = tc.grade(self.rows, self.n_table)
        self.assertEqual(norm(measures), self.result["measures"])
        self.assertEqual(gate, self.result["gates"]["G1_reread"])
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(self.result["status"], "graded" if gate else "ungraded")

    def test_described_counts(self):
        got = norm(tc.described(self.rows))
        want = self.result["described"]
        self.assertEqual(sorted(got["flagged"]), sorted(want["flagged"]))
        got.pop("flagged")
        self.assertEqual(got, {k: v for k, v in want.items() if k != "flagged"})

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), tc.result_text(self.result) + "\n")

    def test_flags_follow_the_rules(self):
        for r in self.rows:
            with self.subTest(qid=r["qid"]):
                if r["status"] == "ok":
                    self.assertEqual(r["placeholder"], any(r[k] for k in tc.FLAGS))
                    self.assertEqual(bool(r["bracket_text"]), r["bracket"])
                else:
                    self.assertFalse(r["placeholder"])

    def test_only_the_withheld_census_row_is_withheld(self):
        held = [(r["cohort"], r["qid"], r["page_url"], r["status"] == "ok")
                for r in self.raw if WITHHELD in (r["name"], r["page_url"])]
        self.assertEqual(held, [("small", "Q1020609", WITHHELD, False)])


class NoteTests(unittest.TestCase):
    """Every figure in TEMPLATE-PAGES-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        with open(os.path.join(RES, "pages.csv"), encoding="utf-8", newline="") as f:
            cls.raw = list(csv.DictReader(f))
        with open(NOTE, encoding="utf-8") as f:
            cls.note = f.read()

    def has(self, phrase):
        self.assertIn(phrase, self.note)

    def test_headline(self):
        flagged = self.d["flagged"]
        large, small = self.m["G1_reread_large"], self.m["G1_reread_small"]
        self.has("Of the %s accessibility pages read again (%d of governments of 50,000 or more, "
                 "%s of 10,000 to 49,999)" % (format(large[0] + small[0], ","), large[0],
                                               format(small[0], ",")))
        self.has("**%d are still a vendor's statement template" % len(flagged))
        new = (self.d["large"]["placeholder_not_seen_before"]
               + self.d["small"]["placeholder_not_seen_before"])
        self.has("%d of the %d had not been seen before this test" % (new, len(flagged)))
        self.assertTrue(all(self.result["predictions"].values()))
        self.has("All five predictions held.")

    def test_prediction_table(self):
        m = self.m
        # A literal percent sign in a %-format string must be written %%.
        self.has("| T1 | Small cohort: at least 1.0%% of pages read again are flagged | %s | yes |"
                 % share(m["T1_placeholder_of_small"]))
        self.has("| %s against %s%% | yes |" % (share(m["T2_placeholder_of_large"]),
                                               pct(m["T1_placeholder_of_small"][2])))
        self.has("| %s | yes |" % share(m["T3_civicplus_of_flagged"]))
        k, n, p, _ = m["T4_no_wcag_of_small"]
        self.has("| %d of %s (%s%%) | yes |" % (k, format(n, ","), pct(p)))
        self.has("| %s | yes |" % share(m["T5_in_group_of_flagged_small"]))

    def test_gates(self):
        for cohort, word in (("large", "large-cohort"), ("small", "small-cohort")):
            k, n, p, _ = self.m["G1_reread_" + cohort]
            self.has("%s of %s %s pages (%s%%)" % (format(k, ","), format(n, ","), word, pct(p)))
        self.assertTrue(all(self.result["gates"].values()))

    def test_flag_counts(self):
        lg, sm = self.d["large"], self.d["small"]
        self.has('Large cohort: %d pages with "YOURMUNICIPALITY", %d with "only meant as a '
                 'template", %d with the NAME / TITLE / EMAIL / PHONE block.'
                 % (lg["muni"], lg["template_note"], lg["contact_block"]))
        self.has("Small cohort: %d, %d and %d." % (sm["muni"], sm["template_note"],
                                                    sm["contact_block"]))
        self.assertEqual(lg["bracket"] + sm["bracket"], 0)
        self.has("No page had a bracketed capital placeholder")

    def test_civicplus(self):
        k, n = self.m["T3_civicplus_of_flagged"][:2]
        self.has("%d of the %d flagged pages are on CivicPlus" % (k, n))
        others = [r for r in self.raw if r["placeholder"] == "True" and r["civicplus"] != "True"]
        self.assertEqual(len(others), n - k)
        for r in others:
            self.has("%s, %s, carries the same template text" % (r["name"], r["state"]))

    def test_stock_without_version_group(self):
        group = [r for r in self.raw if r["cohort"] == "small" and r["status"] == "ok"
                 and r["old_stock"] == "True" and r["old_highest"] == ""]
        flagged = [r for r in group if r["placeholder"] == "True"]
        all_small = [r for r in self.raw if r["cohort"] == "small" and r["placeholder"] == "True"]
        self.assertEqual(len(flagged), len(all_small))
        self.has("All %d flagged small-cohort pages come from the %d small-cohort pages"
                 % (len(flagged), len(group)))
        self.assertEqual(len(group), 3 * len(flagged))
        self.has("one in three of those %d pages" % len(group))

    def test_missing_word_and_unchanged(self):
        lg, sm = self.d["large"], self.d["small"]
        self.has("%d small-cohort pages and %d large-cohort pages read" % (sm["no_wcag"],
                                                                         lg["no_wcag"]))
        self.has("%s of %s small-cohort pages and %d of %d large-cohort pages had exactly the "
                 "same text" % (format(sm["same_text"], ","), format(sm["pages"], ","),
                                lg["same_text"], lg["pages"]))

    def test_by_kind_and_not_seen(self):
        lg, sm = self.d["large"], self.d["small"]
        self.assertEqual(lg["placeholder_by_kind"], {"city": 3, "county": 1})
        self.has("Large cohort: 3 cities, 1 county. Small cohort: 16 cities, 7 counties, 2 towns.")
        self.assertEqual(sm["placeholder_by_kind"], {"city": 16, "county": 7, "town": 2})
        self.has("%d large-cohort and %d small-cohort pages are flagged"
                 % (lg["placeholder_not_seen_before"], sm["placeholder_not_seen_before"]))

    def test_every_flagged_government_is_listed(self):
        for cohort, name, state, kind, flags in self.d["flagged"]:
            self.has("%s, %s" % (name, state))
        contact_only = sorted("%s, %s" % (f[1], f[2]) for f in self.d["flagged"]
                              if f[4] == "contact_block")
        self.assertEqual(len(contact_only), 3)
        self.has("The three pages flagged by the contact block alone")

    def test_withheld_row_is_disclosed(self):
        statuses = {r["qid"]: r["status"] for r in self.raw}
        self.assertEqual(statuses["Q1020609"], "crash")
        self.has("One of the four is the Connecticut town (Q1020609)")
        small = self.d["status"]["small"]
        large = self.d["status"]["large"]
        self.assertEqual(sum(v for k, v in small.items() if k != "ok"), 4)
        self.assertEqual(sum(v for k, v in large.items() if k != "ok"), 3)
        self.has("Four small-cohort pages and three large-cohort pages could not be read again.")


if __name__ == "__main__":
    unittest.main()
