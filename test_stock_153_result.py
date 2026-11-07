# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered stock-153 result from its saved table.

Reads results/stock-153/hosts.csv, result.json and result.txt (the run's output, unchanged) and
recomputes every measure, gate, prediction and described count with the pinned stock153.py
(unchanged; it imports template_check.py and a11y_pages.py). It also checks that hosts.csv holds
no page text (only the pre-registered columns) and that every figure in
results/stock-153/STOCK-153-RESULT.md matches the data.

Standard library only: python -m unittest discover -p test_stock_153_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import sys
import unittest
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import stock153 as s153  # noqa: E402

RES = os.path.join(ROOT, "results", "stock-153")
NOTE = os.path.join(RES, "STOCK-153-RESULT.md")


def load_json(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return json.load(f)


def load_hosts():
    with open(os.path.join(RES, "hosts.csv"), encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


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


class Stock153ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.header, cls.raw = load_hosts()
        cls.rows = s153.typed(cls.raw)

    def test_columns_hold_no_page_text(self):
        self.assertEqual(self.header, s153.COLUMNS)
        texts = {r["bracket_text"] for r in self.raw if r["bracket_text"]}
        self.assertEqual(texts, {"[YOUR COMPANY NAME]"})

    def test_pinned_version_gates_and_tables(self):
        self.assertEqual(self.result["version"], s153.__version__)
        self.assertEqual(self.result["status"], "graded")
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual({k: t["rows"] for k, t in self.result["tables"].items()}, s153.EXPECTED)

    def test_one_row_per_host(self):
        self.assertEqual(len(self.raw), self.result["frame"]["hosts"])
        self.assertEqual(len({r["host"] for r in self.raw}), len(self.raw))
        self.assertNotIn("Q1020609", {r["qid"] for r in self.raw})

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = s153.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertTrue(all(preds.values()))

    def test_described_counts(self):
        got = norm(s153.described(self.rows))
        want = self.result["described"]
        self.assertEqual(sorted(got["flagged"]), sorted(want["flagged"]))
        got.pop("flagged")
        self.assertEqual(got, {k: v for k, v in want.items() if k != "flagged"})

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), s153.result_text(self.result) + "\n")

    def test_flags_follow_the_rules(self):
        for r in self.rows:
            with self.subTest(qid=r["qid"]):
                if r["status"] == "ok":
                    self.assertEqual(r["placeholder"], any(r[k] for k in s153.tc.FLAGS))
                else:
                    self.assertFalse(r["placeholder"])
                    self.assertFalse(r["hidden"])


class NoteTests(unittest.TestCase):
    """Every figure in STOCK-153-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.raw = load_hosts()
        cls.rows = s153.typed(cls.raw)
        cls.flag = [r for r in cls.rows if s153.flagged(r)]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = f.read()

    def has(self, phrase):
        self.assertIn(phrase, self.note)

    def test_headline(self):
        self.has("**%d of the %s website hosts serve a flagged page at `/153/Accessibility`**"
                 % (self.m["S1_flagged_hosts"], format(self.m["F1_hosts"], ",")))
        self.has("%d of them are hidden" % self.m["S2_hidden_flagged_hosts"])
        self.assertTrue(all(self.result["predictions"].values()))
        self.has("All four predictions held.")

    def test_prediction_table(self):
        m = self.m
        self.has("| S1 | At least 40 hosts serve a flagged page | %d | yes |" % m["S1_flagged_hosts"])
        self.has("| S2 | At least 5 flagged hosts are hidden | %d | yes |"
                 % m["S2_hidden_flagged_hosts"])
        self.has("| S3 | At least 20%% of stock pages are flagged | %s | yes |"
                 % share(m["S3_flagged_of_stock_pages"]))
        self.has("| %s against %s | yes |" % (share(m["S4_flagged_of_probed_small"]),
                                              share(m["S4_flagged_of_probed_large"])))

    def test_gates(self):
        k, n, p, _ = self.m["G1_answered"]
        self.has("%s of %s hosts (%s%%) answered" % (format(k, ","), format(n, ","), pct(p)))
        # The note continues this parenthesis ("dropped; one is ..."), so no closing bracket here.
        self.has("%s website hosts (%d rows without a usable host were dropped"
                 % (format(self.result["frame"]["hosts"], ","), self.result["frame"]["dropped"]))

    def test_cohorts_and_census_groups(self):
        hosts = {c: sum(1 for r in self.raw if r["cohort"] == c) for c in ("large", "small")}
        fc = self.d["flagged_by_cohort"]
        self.has("%d of the %s large-cohort hosts and %d of the %s small-cohort hosts"
                 % (fc["large"], format(hosts["large"], ","), fc["small"],
                    format(hosts["small"], ",")))
        g = self.d["flagged_by_census_group"]
        self.has("%d hidden, %d at the `/153/` address the census had found, %d of governments "
                 "outside the census sample and %d whose home page the census could not read"
                 % (g["hidden"], g["found_153"], g["not_sampled"], g["home_failed"]))
        self.assertEqual(sum(g.values()), self.m["S1_flagged_hosts"])

    def test_kinds_states_and_flags(self):
        k = self.d["flagged_by_kind"]
        self.has("%d cities, %d counties and %d towns" % (k["city"], k["county"], k["town"]))
        top = list(self.d["flagged_by_state"].items())[:5]
        self.has(", ".join("%s (%d)" % kv for kv in top[:4]) + " and %s (%d)" % top[4])
        self.has("across %d states" % len(self.d["flagged_by_state"]))
        f = self.d["flags"]
        self.has('"YOURMUNICIPALITY" on %d, "only meant as a template" on %d and the NAME / TITLE '
                 '/ EMAIL / PHONE block on %d' % (f["muni"], f["template_note"],
                                                  f["contact_block"]))

    def test_not_civicplus(self):
        others = [r for r in self.flag if not r["civicplus"]]
        self.assertEqual(len(others), self.d["flagged_not_civicplus"])
        self.has("%d flagged pages are not CivicPlus pages" % len(others))
        for r in others:
            self.assertEqual(r["bracket_text"], "[YOUR COMPANY NAME]")
            path = urllib.parse.urlsplit(r["final_url"]).path
            self.assertFalse(path.lower().startswith("/153/"))
            self.has("%s, %s (%s)" % (r["name"], r["state"], r["qid"]))

    def test_stock_pages(self):
        sp = self.d["stock_pages"]
        self.has("%d stock pages (%d large-cohort, %d small-cohort)"
                 % (sp["large"] + sp["small"], sp["large"], sp["small"]))
        self.has("%d of the stock pages carry the stock sentence" %
                 self.d["stock_sentence_on_stock_pages"])
        self.has("%d carry it with the word WCAG missing" % self.d["no_wcag_on_stock_pages"])
        self.has("%d `/153/` pages that the census had found are no longer a stock page"
                 % self.d["census_153_not_stock_now"])

    def test_seen_before(self):
        groups = {r[1]: r[6] for r in self.d["flagged"]}
        self.assertEqual(groups.get("Q752681"), "hidden")
        self.assertEqual(groups.get("Q1816735"), "not_sampled")
        self.has("Alhambra, California (Q752681)")
        self.has("Lincoln, Rhode Island (Q1816735)")

    def test_every_flagged_government_is_listed(self):
        for row in self.d["flagged"]:
            self.has("| " + " | ".join(row) + " |")
        self.assertEqual(len(self.d["flagged"]), self.m["S1_flagged_hosts"])


if __name__ == "__main__":
    unittest.main()
