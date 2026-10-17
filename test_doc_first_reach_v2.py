"""Offline tests for doc-first-reach v2: every number that docs/doc-first-v2-results.md and the
README quote from results/doc-first-v2/. Apache-2.0 licensed."""

import csv
import hashlib
import json
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# The job ran site_check 0.1.1 as site_check_011.py, fetched from commit 279e85e; these tests
# only use its selection, statistics and report, so a stand-in module is enough.
sys.modules.setdefault("site_check_011", types.ModuleType("site_check_011"))
import doc_first_reach_v2 as job  # noqa: E402


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(text):
    return " ".join(text.split())


def pct(k, n):
    return 100.0 * k / n


class PublishedResultTests(unittest.TestCase):
    def setUp(self):
        self.s = json.loads(read("results", "doc-first-v2", "summary.json"))
        self.lost = json.loads(read("results", "doc-first-v2", "c-lost.json"))
        self.doc = flat(read("docs", "doc-first-v2-results.md"))
        self.readme = flat(read("README.md"))

    def test_code_is_what_ran(self):
        hashes = dict(line.split()[::-1] for line in read("results", "doc-first-v2", "code-sha256.txt").splitlines()
                      if line.strip())
        with open(os.path.join(HERE, "doc_first_reach_v2.py"), "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), hashes["job.py"])
        self.assertEqual((self.s["census_version"], self.s["site_check_011_version"], self.s["site_check_version"]),
                         ("0.2.2", "0.1.1", "0.1.2"))
        self.assertEqual((self.s["pages"], self.s["pdfs"]), (job.PAGES, job.PDFS))

    def test_counts_add_up(self):
        for group in job.GROUPS:
            t = self.s[group]
            for key in ("links", "readable"):
                x = t[key]
                for a, b in job.PAIRS:
                    d = x["%s_vs_%s" % (a, b)]
                    self.assertEqual(x[a] - x[b], d["only_" + a] - d["only_" + b])
                    self.assertAlmostEqual(job.mcnemar_p(d["only_" + a], d["only_" + b]), d["mcnemar_p"])

    def test_summary_md_and_results_page(self):
        text = job.report(self.s, self.s["smoke_sites"])
        self.assertEqual(read("results", "doc-first-v2", "summary.md").strip(), text.strip())
        for line in text.splitlines():
            if line.startswith("- "):
                self.assertIn(line, self.doc)
        for group, name in (("zero", "Zero set"), ("control2", "Control 2")):
            self.assertIn("%s (%d sites, %d with all three home pages read)" % (
                name, self.s[group]["sites"], self.s[group]["all_home_ok"]), self.doc)
        hosts = sorted(job.c.bare_host(r["website"]) for r in self.s["smoke_sites"])
        self.assertEqual(hosts, ["ada.gov", "section508.gov"])

    def test_predictions(self):
        z, ctl = self.s["zero"], self.s["control2"]
        n, m = z["all_home_ok"], ctl["all_home_ok"]
        ra, rb, rc = (ctl["readable"][a] for a in job.ARMS)
        gap1 = pct(ra - rc, m)
        self.assertLessEqual(gap1, 2)
        self.assertIn("1. **Held.** Control 2: C reached at least one readable PDF at %.1f%% of sites against "
                      "%.1f%% for A, %.1f points lower" % (pct(rc, m), pct(ra, m), gap1), self.doc)
        self.assertGreaterEqual(rc, rb)
        d = ctl["readable"]["C_vs_B"]
        self.assertIn("2. **Held.** Control 2: C reached a readable PDF at %d sites against %d for B (%d against "
                      "%d on the discordant pairs, p = %.2g)" % (rc, rb, d["only_C"], d["only_B"], d["mcnemar_p"]),
                      self.doc)
        zc, zb = z["links"]["C"], z["links"]["B"]
        self.assertGreaterEqual(pct(zc, n), 30)
        self.assertIn("3. **Held.** Zero set: C found at least one PDF link at %.1f%% of the analysed sites "
                      "(%d of %d)" % (pct(zc, n), zc, n), self.doc)
        d = z["links"]["C_vs_A"]
        self.assertLess(d["mcnemar_p"], 0.01)
        self.assertIn("4. **Held.** Zero set: C beat A on the discordant pairs, %d to %d, exact McNemar p = %.2g" % (
            d["only_C"], d["only_A"], d["mcnemar_p"]), self.doc)
        gap5 = pct(zb - zc, n)
        self.assertGreater(gap5, 5)
        d = z["links"]["C_vs_B"]
        self.assertIn("5. **Failed.** Zero set: C found at least one PDF link at %.1f%% against %.1f%% for B, "
                      "%.1f points lower" % (pct(zc, n), pct(zb, n), gap5), self.doc)
        self.assertIn("C lost %d sites to B and won %d (exact McNemar p = %.2g)" % (
            d["only_B"], d["only_C"], d["mcnemar_p"]), self.doc)
        self.assertLess(ctl["pages_read_C"], ctl["pages_read_A"])
        self.assertIn("6. **Held.** Control 2: C read %d inner pages against %d for A" % (
            ctl["pages_read_C"], ctl["pages_read_A"]), self.doc)
        self.assertIn("five of the six predictions held, and one failed", self.doc)

    def test_in_short_and_readme(self):
        z, ctl = self.s["zero"], self.s["control2"]
        n, m = z["all_home_ok"], ctl["all_home_ok"]
        r = ctl["readable"]
        control = "on %d of %d sites, against %d for random pages and %d for 0.1.1" % (r["C"], m, r["A"], r["B"])
        zero = "one on %d of %d sites, against %d for 0.1.1 and %d for random pages" % (
            z["links"]["C"], n, z["links"]["B"], z["links"]["A"])
        gap = "%.1f points below 0.1.1" % pct(z["links"]["B"] - z["links"]["C"], n)
        for text in (control, zero, gap):
            self.assertIn(text, self.doc)
            self.assertIn(text, self.readme)

    def test_c_lost(self):
        lost, z = self.lost, self.s["zero"]
        self.assertEqual(lost["sites"], z["links"]["C_vs_B"]["only_B"])
        self.assertEqual(lost["c_fell_back"], lost["sites"])
        self.assertEqual(sum(lost["c_document_like_pages_before_falling_back"].values()), lost["sites"])
        self.assertGreaterEqual(lost["b_read_5_or_more_document_like_pages"],
                                lost["b_read_all_8_pages_document_like"]
                                + lost["b_stopped_early_after_5_document_like_pages"])
        self.assertLessEqual(lost["b_readable_pdf_at_these_sites"], z["readable"]["C_vs_B"]["only_B"])
        self.assertIn("C found no PDF link at %d zero-set sites where B found some. At all %d, C had fallen back "
                      "to other pages, after 4 document-like pages at %d of them" % (
                          lost["sites"], lost["c_fell_back"], lost["c_document_like_pages_before_falling_back"]["4"]),
                      self.doc)
        self.assertIn("B read 5 or more document-like pages at %d of the %d: all 8 at %d sites, and 5 at %d sites" % (
                          lost["b_read_5_or_more_document_like_pages"], lost["sites"],
                          lost["b_read_all_8_pages_document_like"],
                          lost["b_stopped_early_after_5_document_like_pages"]), self.doc)
        self.assertIn("B reached a readable PDF at %d of the %d" % (lost["b_readable_pdf_at_these_sites"],
                                                                     lost["sites"]), self.doc)

    def test_weighted_share(self):
        st = self.lost["strata_v021"]
        sites_csv = os.path.join(HERE, "results", "v0.2.1", "sites.csv")
        if os.path.exists(sites_csv):
            with open(sites_csv, encoding="utf-8", newline="") as f:
                rows = [r for r in csv.DictReader(f) if r["status"] == "ok" and int(r["pages_read"] or 0) > 0]
            self.assertEqual(st["zero"], sum(1 for r in rows if int(r["pdf_links"] or 0) == 0))
            self.assertEqual(st["with_links"], sum(1 for r in rows if int(r["pdf_links"] or 0) > 0))
        self.assertEqual(st["zero"], self.s["zero"]["sites"])
        z, ctl, total = self.s["zero"], self.s["control2"], st["zero"] + st["with_links"]
        w = {a: 100.0 * (st["zero"] * z["readable"][a] / z["all_home_ok"]
                         + st["with_links"] * ctl["readable"][a] / ctl["all_home_ok"]) / total for a in job.ARMS}
        self.assertIn("129 with no PDF link and {:,} with one".format(st["with_links"]), self.doc)
        self.assertIn("A %.1f%%, B %.1f%%, C %.1f%%" % (w["A"], w["B"], w["C"]), self.doc)


if __name__ == "__main__":
    unittest.main()
