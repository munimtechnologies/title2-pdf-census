# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered stock-revize result from its saved table.

Reads results/stock-revize/hosts.csv, result.json and result.txt (the run's output, unchanged)
and recomputes every measure, gate, prediction and described count with the pinned
revize_stock.py (unchanged; it imports stock153.py, template_check.py and a11y_pages.py). It also
checks that hosts.csv holds no page text, that every figure in
results/stock-revize/STOCK-REVIZE-RESULT.md matches the data, and the note's combined count of
unfinished vendor templates across this study and stock-153 (results/stock-153/hosts.csv).

Standard library only: python -m unittest discover -p test_stock_revize_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import revize_stock as rs  # noqa: E402
import stock153 as s153  # noqa: E402

RES = os.path.join(ROOT, "results", "stock-revize")
RES153 = os.path.join(ROOT, "results", "stock-153")
NOTE = os.path.join(RES, "STOCK-REVIZE-RESULT.md")


def load_json(name, res=RES):
    with open(os.path.join(res, name), encoding="utf-8") as f:
        return json.load(f)


def load_hosts(res=RES):
    with open(os.path.join(res, "hosts.csv"), encoding="utf-8", newline="") as f:
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


class StockRevizeResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.header, cls.raw = load_hosts()
        cls.rows = rs.typed(cls.raw)

    def test_columns_hold_no_page_text(self):
        self.assertEqual(self.header, rs.COLUMNS)
        for r in self.raw:
            if r["other_text"]:
                self.assertTrue(r["other_text"].startswith("["), r["qid"])
                self.assertLessEqual(len(r["other_text"]), 60)

    def test_pinned_version_gates_and_tables(self):
        self.assertEqual(self.result["version"], rs.__version__)
        self.assertEqual(self.result["status"], "graded")
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual({k: t["rows"] for k, t in self.result["tables"].items()}, rs.EXPECTED)

    def test_one_row_per_host(self):
        self.assertEqual(len(self.raw), self.result["frame"]["hosts"])
        self.assertEqual(len({r["host"] for r in self.raw}), len(self.raw))
        self.assertNotIn("Q1020609", {r["qid"] for r in self.raw})

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = rs.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertTrue(all(preds.values()))

    def test_described_counts(self):
        got = norm(rs.described(self.rows))
        want = self.result["described"]
        self.assertEqual(sorted(got["flagged"]), sorted(want["flagged"]))
        got.pop("flagged")
        self.assertEqual(got, {k: v for k, v in want.items() if k != "flagged"})

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), rs.result_text(self.result) + "\n")

    def test_flags_follow_the_rules(self):
        for r in self.rows:
            with self.subTest(qid=r["qid"]):
                if r["status"] == "ok":
                    n = sum(1 for k in rs.PH_KEYS if r[k])
                    self.assertEqual(int(r["n_placeholders"]), n)
                    self.assertEqual(r["placeholder"], r["stock_page"] and n > 0)
                    self.assertEqual(r["unfilled"], r["stock_page"] and r["ph_name"])
                else:
                    self.assertFalse(r["placeholder"])


class NoteTests(unittest.TestCase):
    """Every figure in STOCK-REVIZE-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.raw = load_hosts()
        cls.rows = rs.typed(cls.raw)
        _, raw153 = load_hosts(RES153)
        cls.rows153 = s153.typed(raw153)
        with open(NOTE, encoding="utf-8") as f:
            cls.note = f.read()

    def has(self, phrase):
        self.assertIn(phrase, self.note)

    def test_headline(self):
        self.has("**%d of the %s website hosts serve Revize's stock accessibility statement**"
                 % (self.m["R1_stock_hosts"], format(self.m["F1_hosts"], ",")))
        self.has("**%d of those %d still carry at least one placeholder, %d with all six**"
                 % (self.m["R3_placeholder_of_stock"][0], self.m["R1_stock_hosts"],
                    self.d["n_placeholders"]["6"]))
        self.assertTrue(all(self.result["predictions"].values()))
        self.has("All three predictions held.")

    def test_prediction_table(self):
        m = self.m
        self.has("| R1 | At least 30 hosts serve the stock statement | %d | yes |"
                 % m["R1_stock_hosts"])
        self.has("| R2 | At least 4 are unfilled (still say `[Your Agency/Website Name]`) | %d | yes |"
                 % m["R2_unfilled_hosts"])
        self.has("| R3 | At least 15%% of stock statements keep a placeholder | %s | yes |"
                 % share(m["R3_placeholder_of_stock"]))

    def test_gates(self):
        k, n, p, _ = self.m["G1_answered"]
        self.has("%s of %s hosts (%s%%) answered" % (format(k, ","), format(n, ","), pct(p)))

    def test_described(self):
        d = self.d
        sc = d["stock_by_cohort"]
        self.has("%d in the large cohort and %d in the small cohort" % (sc["large"], sc["small"]))
        self.assertEqual(d["stock_revize_markup"], self.m["R1_stock_hosts"])
        self.has("all %d carry Revize markup" % d["stock_revize_markup"])
        g = d["stock_by_census_group"]
        self.has("%d at the address the census had found, %d hidden and %d of governments outside "
                 "the census sample" % (g["found_rv"], g["hidden"], g["not_sampled"]))
        pc = d["placeholder_counts"]
        self.has("`[Your Agency/Website Name]` %d, `[Date]` %d, `[Contact Email]` %d, "
                 "`[Contact Phone]` %d, `[Agency Address]` %d, `[X business days]` %d"
                 % (pc["ph_name"], pc["ph_date"], pc["ph_email"], pc["ph_phone"],
                    pc["ph_address"], pc["ph_days"]))
        n = d["n_placeholders"]
        self.has("%d pages keep all six, %d keep three and %d keep one" % (n["6"], n["3"], n["1"]))
        self.assertEqual(d["flagged_by_template_check"], 0)
        self.has("`template_check.py` flags none of the %d" % self.m["R3_placeholder_of_stock"][0])
        pg = d["placeholder_by_census_group"]
        self.has("%d of the %d sit at the address the census had found" % (pg["found_rv"],
                                                                         self.m["R3_placeholder_of_stock"][0]))
        self.has("%d `/accessibility_statement` pages that the census had found are no longer the "
                 "stock statement" % d["census_rv_not_stock_now"])
        self.has("%d pages read carry another bracketed placeholder" % d["ok_other_bracket"])
        self.assertEqual(d["ok_token"], 0)

    def test_seen_before(self):
        rows = {r[1]: r for r in self.d["flagged"]}
        for qid in ("Q955130", "Q1124743"):
            self.assertEqual(rows[qid][5], "name+date+email+phone+address+days")
        self.has("Raymore, Missouri (Q955130)")
        self.has("Penobscot County, Maine (Q1124743)")

    def test_every_flagged_government_is_listed(self):
        for row in self.d["flagged"]:
            self.has("| " + " | ".join(row) + " |")

    def test_combined_with_stock_153(self):
        rv = {r["host"]: r for r in self.rows if rs.stock(r) and r["placeholder"]}
        cp = {r["host"]: r for r in self.rows153 if s153.flagged(r)}
        self.assertEqual(set(rv) & set(cp), set())
        both = list(rv.values()) + list(cp.values())
        hosts = {c: sum(1 for r in self.rows if r["cohort"] == c) for c in ("large", "small")}
        total = sum(hosts.values())
        by = {c: sum(1 for r in both if r["cohort"] == c) for c in ("large", "small")}
        self.has("**%d of the %s hosts (%s%%) serve an unfinished vendor template at one of the two "
                 "stock addresses**" % (len(both), format(total, ","),
                                        "%.2f" % (100.0 * len(both) / total)))
        self.has("%d of %s large-cohort hosts (%s%%) and %d of %s small-cohort hosts (%s%%)"
                 % (by["large"], format(hosts["large"], ","),
                    "%.2f" % (100.0 * by["large"] / hosts["large"]),
                    by["small"], format(hosts["small"], ","),
                    "%.2f" % (100.0 * by["small"] / hosts["small"])))
        self.has("(%d at the CivicPlus address, %d at the Revize address)" % (len(cp), len(rv)))
        self.assertTrue(re.search(r"counted 29", self.note))


if __name__ == "__main__":
    unittest.main()
