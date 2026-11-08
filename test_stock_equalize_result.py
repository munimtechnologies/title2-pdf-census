# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered stock-equalize result from its saved table.

Reads results/stock-equalize/hosts.csv, result.json and result.txt (the run's output, unchanged)
and recomputes every measure, gate, prediction and described count with the pinned
equalize_stock.py (unchanged; it imports stock153.py, template_check.py and a11y_pages.py). It
also checks that hosts.csv holds no page text, that the three unfinished pages are the same pages
stock-153 flagged (results/stock-153/hosts.csv), and that every figure in
results/stock-equalize/STOCK-EQUALIZE-RESULT.md matches the data.

Standard library only: python -m unittest discover -p test_stock_equalize_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import equalize_stock as eq  # noqa: E402
import stock153 as s153  # noqa: E402

RES = os.path.join(ROOT, "results", "stock-equalize")
NOTE = os.path.join(RES, "STOCK-EQUALIZE-RESULT.md")
S153 = os.path.join(ROOT, "results", "stock-153", "hosts.csv")
REVIZE = os.path.join(ROOT, "results", "stock-revize", "result.json")
# The six template statements disclosed in PREREG.md as seen before the plan.
SEEN = {"Q1909193", "Q484745", "Q995006", "Q112069", "Q491196", "Q493054"}
EMAIL_SHIELD = "[email protected]"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
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


class StockEqualizeResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.header, cls.raw = load_csv(os.path.join(RES, "hosts.csv"))
        cls.rows = eq.typed(cls.raw)

    def test_columns_hold_no_page_text(self):
        self.assertEqual(self.header, eq.COLUMNS)
        texts = {r["other_text"] for r in self.raw if r["other_text"]}
        self.assertTrue(texts <= {"[YOUR COMPANY NAME]", "[email protected]", EMAIL_SHIELD}, texts)
        for r in self.raw:
            self.assertLessEqual(len(r["other_text"]), 60)

    def test_pinned_version_gates_and_tables(self):
        self.assertEqual(self.result["version"], eq.__version__)
        self.assertEqual(self.result["status"], "graded")
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual({k: t["rows"] for k, t in self.result["tables"].items()}, eq.EXPECTED)

    def test_one_row_per_host(self):
        self.assertEqual(len(self.raw), self.result["frame"]["hosts"])
        self.assertEqual(len({r["host"] for r in self.raw}), len(self.raw))
        self.assertNotIn("Q1020609", {r["qid"] for r in self.raw})

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = eq.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, {"W1": False, "W2": False, "W3": None})

    def test_described_counts(self):
        got = norm(eq.described(self.rows))
        want = self.result["described"]
        self.assertEqual(sorted(got["flagged"]), sorted(want["flagged"]))
        got.pop("flagged")
        self.assertEqual(got, {k: v for k, v in want.items() if k != "flagged"})

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), eq.result_text(self.result) + "\n")

    def test_flags_follow_the_rules(self):
        for r in self.rows:
            with self.subTest(qid=r["qid"]):
                if r["status"] == "ok":
                    anyph = any(r[k] for k in eq.PH_KEYS)
                    self.assertEqual(r["placeholder"], r["stock_page"] and anyph)
                    self.assertEqual(r["unfilled"], r["stock_page"] and r["ph_name"])
                    self.assertEqual(r["hidden"], r["placeholder"] and r["census"] == "home_ok"
                                     and not r["census_page_as"])
                else:
                    self.assertFalse(r["stock_page"])
                    self.assertFalse(r["placeholder"])
                    self.assertFalse(r["hidden"])

    def test_unfinished_pages_are_stock_153_pages(self):
        _, raw153 = load_csv(S153)
        by_qid = {r["qid"]: r for r in s153.typed(raw153)}
        for r in self.rows:
            if eq.stock(r) and r["placeholder"]:
                with self.subTest(qid=r["qid"]):
                    other = by_qid[r["qid"]]
                    self.assertTrue(s153.flagged(other))
                    self.assertEqual(other["text_sha256"], r["text_sha256"])


class NoteTests(unittest.TestCase):
    """Every figure in STOCK-EQUALIZE-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.raw = load_csv(os.path.join(RES, "hosts.csv"))
        cls.rows = eq.typed(cls.raw)
        cls.stock = [r for r in cls.rows if eq.stock(r)]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = f.read()

    def has(self, phrase):
        self.assertIn(phrase, self.note)

    def test_status_and_crawl_times(self):
        c = self.result["crawl"]
        self.has("(%s to %s UTC)" % (c["started_utc"][11:16], c["finished_utc"][11:16]))
        self.assertEqual(self.result["predictions"], {"W1": False, "W2": False, "W3": None})
        self.has("**Predictions W1 and W2 failed, and W3 was not graded.**")

    def test_headline(self):
        m = self.m
        self.has("**%d of the %s website hosts serve the Accessibility Checker statement template "
                 "at `/accessibility-statement/`**" % (m["W1_stock_hosts"],
                                                       format(m["F1_hosts"], ",")))
        self.has("**%d of the %d still carry its placeholders**"
                 % (m["W2_placeholder_hosts"], m["W1_stock_hosts"]))

    def test_all_seen_before(self):
        self.assertEqual({r["qid"] for r in self.stock}, SEEN)
        self.has("All %d are the six named in the plan as seen before it" % len(self.stock))
        for r in self.stock:
            self.has("%s, %s (%s)" % (r["name"], r["state"], r["qid"]))

    def test_two_vendor_count_unchanged(self):
        _, raw153 = load_csv(S153)
        n153 = sum(1 for r in s153.typed(raw153) if s153.flagged(r))
        nrev = load_json(REVIZE)["measures"]["R3_placeholder_of_stock"][0]
        hosts = self.m["F1_hosts"]
        self.has("they are %d of stock-153's %d flagged hosts" % (self.m["W2_placeholder_hosts"],
                                                                 n153))
        total = n153 + nrev
        self.has("**%d of %s (%s%%)**" % (total, format(hosts, ","), pct(round(total / hosts, 4))))
        self.has("(%d hosts from [stock-153]" % n153)
        self.has("and %d from [stock-revize]" % nrev)

    def test_prediction_table(self):
        m = self.m
        self.has("| W1 | At least 10 hosts serve the template statement | %d | no |"
                 % m["W1_stock_hosts"])
        self.has("| W2 | At least 5 of them keep at least one placeholder | %d | no |"
                 % m["W2_placeholder_hosts"])
        self.has("| W3 | At least 30% of template statements keep a placeholder | "
                 + share(m["W3_placeholder_of_stock"])
                 + " | not graded (fewer than 10 template statements) |")
        _, _, _, (lo, hi) = m["W3_placeholder_of_stock"]
        self.has("from %s%% to %s%%" % (pct(lo), pct(hi)))

    def test_gates(self):
        k, n, p, _ = self.m["G1_answered"]
        self.has("%s of %s hosts (%s%%) answered" % (format(k, ","), format(n, ","), pct(p)))
        self.has("%s website hosts (%d rows without a usable host were dropped)"
                 % (format(self.result["frame"]["hosts"], ","), self.result["frame"]["dropped"]))

    def test_why_failed(self):
        st = self.d["status"]
        self.has("the %s small governments outside the census sample"
                 % format(self.d["census"]["small"]["not_sampled"], ","))
        n404 = st["large"].get("http_404", 0) + st["small"].get("http_404", 0)
        self.has("%s hosts answered 404" % format(n404, ","))
        self.assertNotIn("large", self.d["stock_by_cohort"])

    def test_described(self):
        d, m = self.d, self.m
        st = d["status"]
        self.has("%d pages could be read at the address (%d large-cohort, %d small-cohort)"
                 % (d["ok_pages"], st["large"]["ok"], st["small"]["ok"]))
        self.assertEqual(d["stock_by_cohort"], {"small": m["W1_stock_hosts"]})
        self.has("All %d template statements are on small-cohort hosts" % m["W1_stock_hosts"])
        g = d["stock_by_census_group"]
        self.assertEqual(sum(g.values()), m["W1_stock_hosts"])
        self.has("%d at the address the census had found, %d hidden and %d of a government "
                 "outside the census sample" % (g["found_as"], g["hidden"], g["not_sampled"]))
        for r in self.stock:
            if eq.census_group(r) == "found_as":
                self.assertFalse(r["placeholder"])
        self.assertEqual(d["ok_plugin_markup"], d["stock_plugin_markup"])
        self.has("%d of the %d template statements carry the plugin's markup in their HTML; "
                 "no other page read does." % (d["stock_plugin_markup"], m["W1_stock_hosts"]))

    def test_placeholders(self):
        d, w2 = self.d, self.m["W2_placeholder_hosts"]
        counts = d["placeholder_counts"]
        kept = [k for k in eq.PH_KEYS if counts[k] == w2]
        self.assertEqual(d["n_placeholders"], {str(len(kept)): w2})
        for k in eq.PH_KEYS:
            self.assertIn(counts[k], (0, w2))
        self.assertEqual(counts["ph_standard"], 0)
        self.has("The %d unfinished statements each keep the same %d of the template's %d "
                 "placeholders: %s and %s." % (w2, len(kept), len(eq.PH_KEYS),
                                               ", ".join(k[3:] for k in kept[:-1]),
                                               kept[-1][3:]))
        self.has("None keeps `[ SPECIFIC STANDARD, VERSION, LEVEL ]`.")
        self.assertEqual(d["flagged_by_template_check"], w2)
        self.has("`template_check.py` (unchanged) flags all %d." % w2)
        self.assertEqual(d["unfilled"], w2)

    def test_second_section_and_brackets(self):
        d = self.d
        ok = [r for r in self.rows if r["status"] == "ok"]
        second = [r for r in ok if r["second"] and not r["stock_page"]]
        self.assertEqual(len(second), d["second_without_first"])
        self.assertEqual(len(second), 1)
        self.has("%d page carries the template's second section" % len(second))
        for r in second:
            self.assertEqual(r["n_placeholders"], "0")
            self.has("%s, %s (%s)" % (r["name"], r["state"], r["qid"]))
        self.assertEqual(d["ok_not_stock_with_placeholder"], 0)
        self.has("No page that is not the template statement carries one of its placeholders.")
        br = [r for r in ok if r["other_bracket"]]
        self.assertEqual(len(br), d["ok_other_bracket"])
        name = sum(1 for r in br if r["other_text"] == "[YOUR COMPANY NAME]")
        shield = len(br) - name
        self.assertEqual(name, self.m["W2_placeholder_hosts"])
        self.has("%d pages read carry a bracketed text of the kinds the study records: %d are an "
                 "email address hidden by a web host's email protection" % (len(br), shield))
        self.has("and %d are the \"[YOUR COMPANY NAME]\" pages above." % name)
        self.has("%d `/accessibility-statement` pages that the census had found are not the "
                 "template statement this time" % d["census_as_not_stock_now"])

    def test_every_flagged_government_is_listed(self):
        for row in self.d["flagged"]:
            self.has("| " + " | ".join(row) + " |")
        self.assertEqual(len(self.d["flagged"]), self.m["W2_placeholder_hosts"])


if __name__ == "__main__":
    unittest.main()
