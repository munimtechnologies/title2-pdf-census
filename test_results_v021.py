"""Checks the published second full run (results/v0.2.1) and every number README.md quotes from it.
No network. Apache-2.0 licensed."""

import collections
import csv
import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import census as c  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(HERE, "results", "v0.2.1")


def read(name, run=RUN):
    with open(os.path.join(run, name), encoding="utf-8", newline="") as f:
        if name.endswith(".csv"):
            return list(csv.DictReader(f))
        return json.load(f) if name.endswith(".json") else f.read()


def readme():
    with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        return f.read()


def ci(cell):
    """'60.3% (59.0-61.6)': census.pct without the n."""
    return c.pct(cell).split(", n=")[0]


def ci_of(k, n):
    """The same, straight from a count."""
    lo, hi = c.wilson(k, n)
    return "%.1f%% (%.1f-%.1f)" % (100.0 * k / n, 100 * lo, 100 * hi)


def share_of(k, n):
    return "%.1f%%" % (100.0 * k / n)


def sign_test(k, n):
    """Exact two-sided sign test: k of n changes in one direction."""
    tail = sum(math.comb(n, i) for i in range(max(k, n - k), n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


class RunFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = read("summary.json")
        cls.sites = read("sites.csv")

    def test_results_page_is_the_summary(self):
        self.assertEqual(self.s["version"], "0.2.1")
        self.assertEqual(c.report(self.s).replace("\r\n", "\n"), read("results.md").replace("\r\n", "\n"))

    def test_cohort(self):
        cohort = read("cohort.csv")
        self.assertEqual(len(cohort), self.s["sites"])
        self.assertEqual(len(self.sites), self.s["sites"])
        self.assertTrue(all(r["state"] == "" for r in cohort))
        self.assertTrue(all(int(r["population"]) >= 50000 for r in cohort))

    def test_sites_add_up_to_the_summary(self):
        self.assertEqual(dict(collections.Counter(r["status"] for r in self.sites)), self.s["site_status"])
        self.assertEqual(sum(int(r["pdfs_tried"]) for r in self.sites), self.s["pdfs_tried"])
        self.assertEqual(sum(int(r["pdfs_ok"]) for r in self.sites), self.s["overall"]["tagged"]["n"])
        linked = [r for r in self.sites if r["a11y_link"] in ("True", "False")]
        self.assertEqual(len(linked), self.s["home_a11y_link"]["n"])
        self.assertEqual(sum(r["a11y_link"] == "True" for r in linked), self.s["home_a11y_link"]["k"])
        # Check counts are per government (qid), so a qid listed with two websites is counted once.
        per_qid = {r["qid"]: r for r in self.sites}
        for check in ("tagged", "lang", "title", "image_only", "basic4"):
            self.assertEqual(sum(int(r[check]) for r in per_qid.values()), self.s["overall"][check]["k"], check)
        with_pdf = {r["qid"] for r in self.sites if int(r["pdfs_ok"]) > 0}
        self.assertEqual(len(with_pdf), self.s["sites_with_ok_pdf"])

    def test_link_counts(self):
        n = read("link-counts.json")
        self.assertEqual(n["pdfs_tried"], self.s["pdfs_tried"])
        for result, count in self.s["pdf_results"].items():
            self.assertEqual(n["result_" + result], count, result)

    def test_space_split_adds_up(self):
        sp, n = read("space-and-404.json"), read("link-counts.json")
        tried = sp["tried"]
        self.assertEqual(tried["with_space"] + tried["without_space"], self.s["pdfs_tried"])
        self.assertEqual(tried["with_space"], sum(v for k, v in n.items() if k.startswith("with_space_")))
        self.assertEqual(sp["http_error"]["with_space"], n["with_space_http_error"])
        self.assertEqual(sp["http_error"]["with_space"] + sp["http_error"]["without_space"],
                         self.s["pdf_results"]["http_error"])
        for side in ("with_space", "without_space"):
            self.assertLessEqual(sp["http_404"][side], sp["http_error"][side])
        r = sp["readable"]
        self.assertEqual(r["with_space"]["n"], n["with_space_ok"])
        self.assertEqual(r["with_space"]["n"] + r["without_space"]["n"], self.s["overall"]["tagged"]["n"])
        for check in ("tagged", "lang", "title", "image_only", "basic4"):
            self.assertEqual(r["with_space"][check] + r["without_space"][check], self.s["overall"][check]["k"], check)
        for family in ("scanner", "word"):
            self.assertEqual(r["with_space"][family] + r["without_space"][family],
                             self.s["by_producer"][family]["tagged"]["n"], family)


class ReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = read("summary.json")
        cls.first = read("summary.json", os.path.join(HERE, "results", "v0.2.0"))
        cls.sp = read("space-and-404.json")
        cls.md = readme()

    def test_404s(self):
        t, e = self.sp["tried"], self.sp["http_404"]
        self.assertIn("{:,} of the {:,} links with a space ({})".format(
            e["with_space"], t["with_space"], share_of(e["with_space"], t["with_space"])), self.md)
        self.assertIn("against {:,} of the {:,} without one ({})".format(
            e["without_space"], t["without_space"], share_of(e["without_space"], t["without_space"])), self.md)

    def test_reach(self):
        s, f = self.s, self.first
        self.assertEqual(s["sites"], f["sites"])
        self.assertIn("the same {:,} governments".format(s["sites"]), self.md)
        self.assertIn("{:,} home pages read; {:,} sites disallow".format(
            s["site_status"]["ok"], s["site_status"]["robots_disallow"]), self.md)
        self.assertIn("{:,} more than in the first run".format(
            s["site_status"]["robots_disallow"] - f["site_status"]["robots_disallow"]), self.md)
        self.assertIn("{:,} PDFs were read from {:,} sites, out of {:,} tried".format(
            s["pdf_results"]["ok"], s["sites_with_ok_pdf"], s["pdfs_tried"]), self.md)

    def test_overall(self):
        o = self.s["overall"]
        for label, check in (("tagged", "tagged"), ("document language set", "lang"),
                             ("title in metadata", "title"), ("image only", "image_only"),
                             ("All four basics:", "basic4")):
            self.assertIn("%s %s" % (label, ci(o[check])), self.md)
            # "Within about a point of the first run."
            self.assertLess(abs(o[check]["share"] - self.first["overall"][check]["share"]), 0.015, check)

    def test_space_split(self):
        w, wo = self.sp["readable"]["with_space"], self.sp["readable"]["without_space"]
        self.assertIn("of {:,} such PDFs, tagged {} against {} for the {:,} others".format(
            w["n"], ci_of(w["tagged"], w["n"]), ci_of(wo["tagged"], wo["n"]), wo["n"]), self.md)
        self.assertIn("all four basics {} against {}".format(
            ci_of(w["basic4"], w["n"]), ci_of(wo["basic4"], wo["n"])), self.md)
        self.assertIn("image only {} against {}".format(
            share_of(w["image_only"], w["n"]), share_of(wo["image_only"], wo["n"])), self.md)
        self.assertIn("scanner output {} against {}".format(
            share_of(w["scanner"], w["n"]), share_of(wo["scanner"], wo["n"])), self.md)
        for check in ("tagged", "basic4"):
            self.assertLess(w[check] / w["n"], wo[check] / wo["n"], check)

    def test_before_and_after(self):
        a, b = self.s["by_era"]["after_rule"], self.s["by_era"]["before_rule"]
        self.assertEqual(self.s["rule_date"], "2024-04-24")
        for label, check in (("tagged", "tagged"), ("all four basics", "basic4")):
            self.assertIn("%s %s against %s" % (label, ci(a[check]), ci(b[check])), self.md)
        self.assertIn("barely moved: %s against %s" % (ci(a["title"]), ci(b["title"])), self.md)
        self.assertEqual(min(("tagged", "lang", "title"), key=lambda k: a[k]["share"]), "title")

    def test_within_site(self):
        p = self.s["paired_era"]
        self.assertIn("{:,} sites have PDFs from both periods".format(p["sites"]), self.md)
        self.assertIn("%+.2f percentage points" % (100 * p["mean_tagged_change"]), self.md)
        self.assertIn("rose at %d sites, fell at %d and stayed the same at %d" % (
            p["improved"], p["worse"], p["same"]), self.md)
        n = p["improved"] + p["worse"]
        self.assertIn("on the %d that changed, p = %.2f)" % (n, sign_test(p["improved"], n)), self.md)

    def test_software(self):
        by = self.s["by_producer"]
        self.assertIn("Word are tagged %s" % ci(by["word"]["tagged"]), self.md)
        self.assertIn("print-to-PDF output %s" % ci(by["print-to-pdf"]["tagged"]), self.md)
        self.assertIn("scanner output %s" % ci(by["scanner"]["tagged"]), self.md)
        self.assertIn("and %s of scanner PDFs" % ci(by["scanner"]["image_only"]), self.md)

    def test_figures_and_home_pages(self):
        f = self.s["figures"]
        self.assertIn("{:,} figures are tagged in {:,} PDFs, and {}% of them".format(
            f["total"], f["pdfs_with_figures"], round(100.0 * f["with_alt"] / f["total"], 1)), self.md)
        self.assertIn("%s link to a page about accessibility" % ci(self.s["home_a11y_link"]), self.md)

    def test_files_listed(self):
        for name in ("summary.json", "results.md", "sites.csv", "cohort.csv", "link-counts.json",
                     "space-and-404.json", "code-sha256.txt"):
            self.assertTrue(os.path.exists(os.path.join(RUN, name)), name)
            self.assertIn("`%s`" % name, self.md)


if __name__ == "__main__":
    unittest.main()
