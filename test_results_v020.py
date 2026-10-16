"""Checks the published first full run (results/v0.2.0) and every number README.md quotes from it.
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
RUN = os.path.join(HERE, "results", "v0.2.0")


def read(name):
    with open(os.path.join(RUN, name), encoding="utf-8", newline="") as f:
        if name.endswith(".csv"):
            return list(csv.DictReader(f))
        return json.load(f) if name.endswith(".json") else f.read()


def readme():
    with open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        return f.read()


def ci(cell):
    """'61.2% (59.8-62.5)': census.pct without the n."""
    return c.pct(cell).split(", n=")[0]


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
        self.assertEqual(self.s["version"], "0.2.0")
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

    def test_failed_links(self):
        f = read("failed-links.json")
        self.assertEqual(f["pdfs_tried"], self.s["pdfs_tried"])
        self.assertEqual(f["http_error"], self.s["pdf_results"]["http_error"])
        self.assertLessEqual(f["http_error_with_space_in_url"], f["http_error_status_0"])
        self.assertLessEqual(f["http_error_status_0"], f["http_error"])
        self.assertEqual(f["ok_with_space_in_url"], 0)


class ReadmeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = read("summary.json")
        cls.md = readme()

    def test_reach(self):
        s, f = self.s, read("failed-links.json")
        self.assertIn("{:,} governments with a website".format(s["sites"]), self.md)
        self.assertIn("{:,} home pages read; {:,} sites disallow".format(
            s["site_status"]["ok"], s["site_status"]["robots_disallow"]), self.md)
        self.assertIn("{:,} PDFs were read from {:,} sites, out of {:,} tried".format(
            s["pdf_results"]["ok"], s["sites_with_ok_pdf"], s["pdfs_tried"]), self.md)
        self.assertIn("all {:,} PDF links with a space".format(f["http_error_with_space_in_url"]), self.md)
        self.assertIn("{:,} of the {:,} fetch errors".format(f["http_error_with_space_in_url"], f["http_error"]),
                      self.md)

    def test_overall(self):
        o = self.s["overall"]
        for label, check in (("tagged", "tagged"), ("document language set", "lang"),
                             ("title in metadata", "title"), ("image only", "image_only"),
                             ("All four basics:", "basic4")):
            self.assertIn("%s %s" % (label, ci(o[check])), self.md)

    def test_before_and_after(self):
        a, b = self.s["by_era"]["after_rule"], self.s["by_era"]["before_rule"]
        self.assertEqual(self.s["rule_date"], "2024-04-24")
        for label, check in (("tagged", "tagged"), ("all four basics", "basic4")):
            self.assertIn("%s %s against %s" % (label, ci(a[check]), ci(b[check])), self.md)
        self.assertIn("%s against %s" % (ci(a["title"]), ci(b["title"])), self.md)
        # The title is the basic that is missing most often since the rule.
        self.assertEqual(min(("tagged", "lang", "title"), key=lambda k: a[k]["share"]), "title")

    def test_within_site(self):
        p = self.s["paired_era"]
        self.assertIn("{:,} sites have PDFs from both periods".format(p["sites"]), self.md)
        self.assertIn("%+.1f percentage points" % (100 * p["mean_tagged_change"]), self.md)
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

    def test_version_and_contact(self):
        self.assertEqual(c.__version__, "0.2.1")
        self.assertIn("**%s:**" % c.__version__, self.md)
        self.assertIn("mv2@munimtech.com", self.md)
        self.assertNotIn("munimversion2", self.md)


if __name__ == "__main__":
    unittest.main()
