# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered district-pages result from its saved tables.

Reads results/district-pages/rows.csv, sample.csv, result.json and result.txt (the run's output,
unchanged) and recomputes every measure, prediction and described count with the pinned
district_pages.py (unchanged; it imports district_check.py, a11y_pages.py, statement_check.py and
template_check.py). It also checks that rows.csv and sample.csv describe the same 2,500
districts, and that every figure in results/district-pages/DISTRICT-PAGES-RESULT.md matches the
data, including the counts the note marks as found after grading.

Standard library only: python -m unittest discover -p test_district_pages_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import district_pages as dp  # noqa: E402

RES = os.path.join(ROOT, "results", "district-pages")
NOTE = os.path.join(RES, "DISTRICT-PAGES-RESULT.md")
SENTENCE = "positive place for everyone"  # the 2017 template's first sentence


def load_json(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return json.load(f)


def load_csv(name):
    with open(os.path.join(RES, name), encoding="utf-8", newline="") as f:
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


def ratio(k, n):
    return "%s of %s (%s%%)" % (format(k, ","), format(n, ","), "%.2f" % (100.0 * k / n))


def ok_pages(rows, band=None):
    return [r for r in rows if r["page_status"] == "ok" and band in (None, r["band"])]


def is_ph(r):
    return dp.truthy(r["placeholder"])


def has_sentence(r):
    return SENTENCE in " ".join((r["version_snippet"], r["date_snippet"], r["threshold_snippet"]))


class DistrictPagesResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.header, cls.rows = load_csv("rows.csv")
        cls.sheader, cls.sample = load_csv("sample.csv")

    def test_columns(self):
        self.assertEqual(self.header, list(dp.COLUMNS))
        self.assertEqual(self.sheader, dp.FRAME_COLUMNS)

    def test_version_gates_and_status(self):
        self.assertEqual(self.result["version"], dp.__version__)
        self.assertFalse(self.result["dry_run"])
        self.assertEqual(self.result["status"], "graded")
        self.assertTrue(all(self.result["gates"].values()))

    def test_rows_match_the_sample(self):
        self.assertEqual(len(self.rows), self.result["sampled"])
        self.assertEqual(len(self.sample), self.result["sampled"])
        by = {r["leaid"]: r for r in self.sample}
        self.assertEqual(len(by), len(self.sample))
        for r in self.rows:
            s = by[r["leaid"]]
            self.assertEqual({k: r[k] for k in dp.FRAME_COLUMNS}, s, r["leaid"])
        self.assertEqual(dp.tally_band(self.sample), self.result["sampled_by_band"])
        for r in self.sample:
            self.assertEqual(r["band"], dp.band(int(r["population"])))

    def test_counts_read(self):
        self.assertEqual(sum(1 for r in self.rows if r["home"] == "ok"), self.result["homes_ok"])
        self.assertEqual(len(ok_pages(self.rows)), self.result["pages_ok"])

    def test_regrade_measures_and_predictions(self):
        measures, preds = dp.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        self.assertEqual(norm(preds), self.result["predictions"])

    def test_described_counts(self):
        self.assertEqual(norm(dp.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), dp.result_text(self.result) + "\n")


class NoteTests(unittest.TestCase):
    """Every figure in DISTRICT-PAGES-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json("result.json")
        cls.m = cls.result["measures"]
        cls.p = cls.result["predictions"]
        cls.b = cls.result["described"]["by_band"]
        _, cls.rows = load_csv("rows.csv")
        with open(NOTE, encoding="utf-8") as f:
            cls.note = f.read()

    def has(self, phrase):
        self.assertIn(phrase, self.note)

    def test_prediction_table(self):
        m, p = self.m, self.p
        self.assertEqual(p, {"D1": True, "D2": True, "D3": False, "D4": True, "D5": False,
                             "D6": True})
        self.has("Four of the six predictions held")
        self.has("| D1 | Under 50,000: fewer than 55.71%% of versioned pages name only WCAG 2.0 "
                 "| %s | yes |" % share(m["D1_only_2.0_of_versioned_under50k"]))
        self.has("| D2 | Under 50,000: fewer than 10%% of pages carry the stock sentence | %s | yes |"
                 % share(m["D2_stock_of_pages_under50k"]))
        self.has("| %s against %s | no |" % (share(m["D3_newer_of_versioned_50k+"]),
                                             share(m["D3_newer_of_versioned_under50k"])))
        self.has("| D4 | At least 0.5%% of all pages read carry a placeholder | %s | yes |"
                 % share(m["D4_placeholder_of_pages_all"]))
        self.has("| %s | no |" % share(m["D5_linked_of_homes_under50k"]))
        self.has("| D6 | Under 50,000: at least 22.15%% of pages name Title II | %s | yes |"
                 % share(m["D6_title2_of_pages_under50k"]))
        gap = (m["D3_newer_of_versioned_under50k"][0] / m["D3_newer_of_versioned_under50k"][1]
               - m["D3_newer_of_versioned_50k+"][0] / m["D3_newer_of_versioned_50k+"][1])
        self.has("%.2f points lower" % (100 * gap))

    def test_gates_and_reading(self):
        r = self.result
        self.has("%s website hosts (%s of 50,000 or more)" % (format(r["frame"], ","),
                                                              format(r["frame_by_band"]["50k+"], ",")))
        self.has("%s home pages and %d accessibility pages were read" % (format(r["homes_ok"], ","),
                                                                         r["pages_ok"]))
        b = self.b
        self.has("%d of them in the 50k+ band and %d under 50,000"
                 % (b["50k+"]["pages_ok"], b["under50k"]["pages_ok"]))

    def test_template_headline(self):
        pages = ok_pages(self.rows)
        ph = [r for r in pages if is_ph(r)]
        self.has("**%d of the %d district accessibility pages read (%s%%) are still a statement "
                 "template with its placeholders in**" % (len(ph), len(pages),
                                                          pct(len(ph) / len(pages))))
        b = self.b
        self.has("%d of %d pages in the 50k+ band and %d of %d under 50,000"
                 % (b["50k+"]["placeholder"], b["50k+"]["pages_ok"], b["under50k"]["placeholder"],
                    b["under50k"]["pages_ok"]))
        fs = [r for r in pages if "finalsite" in r["platform"].split("+")]
        self.assertTrue(all("finalsite" in r["platform"].split("+") for r in ph))
        self.has("all %d are on sites whose home page carries Finalsite markup" % len(ph))
        self.has("%d of the %d accessibility pages read on Finalsite sites (%s%%)"
                 % (len(ph), len(fs), "%.2f" % (100.0 * len(ph) / len(fs))))

    def test_template_kinds(self):
        kinds = {}
        for r in ok_pages(self.rows):
            if is_ph(r):
                kinds[r["placeholder_kinds"]] = kinds.get(r["placeholder_kinds"], 0) + 1
        self.assertEqual(kinds, {"your_school+your_domain+fake_phone": 91, "your_school": 35,
                                 "your_domain+fake_phone": 2, "your_school+your_domain": 1})
        self.has('91 keep all three, 35 keep only "the Your School website", 2 keep only the '
                 'address and the phone number, and 1 keeps the name and the address')

    def test_template_family(self):
        pages = ok_pages(self.rows)
        fam = [r for r in pages if has_sentence(r)]
        self.has("%s carry the template's first sentence" % ratio(len(fam), len(pages)))
        big = sum(1 for r in fam if r["band"] == "50k+")
        small = sum(1 for r in fam if r["band"] == "under50k")
        self.has("%d of %d in the 50k+ band and %d of %d under 50,000"
                 % (big, self.b["50k+"]["pages_ok"], small, self.b["under50k"]["pages_ok"]))
        ph = [r for r in pages if is_ph(r)]
        self.has("%d of the %d template pages" % (sum(1 for r in ph if has_sentence(r)), len(ph)))
        gen = [r for r in pages if dp.truthy(r["generator_line"])]
        self.has("%d pages credit the Accessibility Statement Generator, %d of them among the %d"
                 % (len(gen), sum(1 for r in gen if is_ph(r)), len(ph)))

    def test_only_20_without_templates(self):
        ver = [r for r in ok_pages(self.rows, "under50k") if r["highest"]]
        rest = [r for r in ver if not is_ph(r)]
        self.has("%s name only WCAG 2.0"
                 % ratio(sum(1 for r in rest if r["highest"] == "2.0"), len(rest)))

    def test_overlays(self):
        def audio(band):
            homes = [r for r in self.rows if r["home"] == "ok" and r["band"] == band]
            return ratio(sum(1 for r in homes if "audioeye" in r["overlay"].split("+")), len(homes))
        self.has("AudioEye's script is on %s home pages read in the 50k+ band and %s under 50,000"
                 % (audio("50k+"), audio("under50k")))

    def test_dates_threshold_and_504(self):
        b, s = self.b["50k+"], self.b["under50k"]
        self.has("%d under-50,000 pages give April 26, 2028" % s["date_2028_04_26"])
        self.has("%d pages of 50k+ districts still give April 24, 2026 and %d gives April 26, 2027"
                 % (b["date_2026_04_24"], b["date_2027_04_26"]))
        self.assertEqual(b["students_threshold"] + s["students_threshold"], 0)
        self.assertEqual(b["finalsite_line"] + s["finalsite_line"], 0)
        self.has("No page read gives the 50,000 threshold in students")
        self.has("Section 504 on %d of %d pages in the 50k+ band and %d of %d under 50,000"
                 % (b["s504"], b["pages_ok"], s["s504"], s["pages_ok"]))

    def test_frame_file_withheld_is_disclosed(self):
        self.assertFalse(os.path.exists(os.path.join(RES, "frame.csv")))
        self.has("`frame.csv` is not published")


if __name__ == "__main__":
    unittest.main()
