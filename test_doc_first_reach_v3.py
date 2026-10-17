"""Offline tests for doc-first-reach v3: every number that docs/doc-first-v3-results.md and the
README quote from results/doc-first-v3/, and each prediction scored from them. Apache-2.0 licensed."""

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
import doc_first_reach_v3 as job  # noqa: E402

WORDS = ("none", "one", "two", "three", "four", "five", "six")


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(text):
    return " ".join(text.split())


def pct(k, n):
    return 100.0 * k / n


def diff(x, y):
    """'1.0 points lower' / '0.5 points higher' / 'the same' for x against y, in points."""
    d = x - y
    if abs(d) < 0.05:
        return "the same"
    return "%.1f points %s" % (abs(d), "higher" if d > 0 else "lower")


def verdict(ok):
    return "**Held.**" if ok else "**Failed.**"


class PublishedResultTests(unittest.TestCase):
    def setUp(self):
        self.s = json.loads(read("results", "doc-first-v3", "summary.json"))
        self.doc = flat(read("docs", "doc-first-v3-results.md"))
        self.readme = flat(read("README.md"))

    def outcomes(self):
        z, ctl = self.s["zero"], self.s["control3"]
        n, m = z["all_home_ok"], ctl["all_home_ok"]
        w = self.weighted()
        return [pct(ctl["readable"]["A"] - ctl["readable"]["D"], m) <= 2,
                ctl["readable"]["D"] >= ctl["readable"]["B"],
                pct(z["links"]["B"] - z["links"]["D"], n) <= 5,
                (z["links"]["D_vs_A"]["only_D"] > z["links"]["D_vs_A"]["only_A"]
                 and z["links"]["D_vs_A"]["mcnemar_p"] < 0.01),
                ctl["pages_read_D"] < ctl["pages_read_A"],
                w["D"] > w["A"]]

    def weighted(self):
        st, z, ctl = self.s["strata"], self.s["zero"], self.s["control3"]
        total = st["zero"] + st["with_links"]
        return {a: 100.0 * (st["zero"] * z["readable"][a] / z["all_home_ok"]
                            + st["with_links"] * ctl["readable"][a] / ctl["all_home_ok"]) / total
                for a in job.ARMS}

    def test_code_is_what_ran(self):
        hashes = dict(line.split()[::-1] for line in read("results", "doc-first-v3", "code-sha256.txt").splitlines()
                      if line.strip())
        with open(os.path.join(HERE, "doc_first_reach_v3.py"), "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), hashes["job.py"])
        self.assertIn("doc-first-v3-prereg.md", hashes)
        self.assertEqual((self.s["census_version"], self.s["site_check_011_version"], self.s["site_check_version"]),
                         ("0.2.2", "0.1.1", "0.1.2"))
        self.assertEqual((self.s["pages"], self.s["pdfs"]), (job.PAGES, job.PDFS))
        self.assertEqual(job.PAGES, {"A": 16, "B": 8, "D": 16})

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
        self.assertEqual(read("results", "doc-first-v3", "summary.md").strip(), text.strip())
        for line in text.splitlines():
            if line.startswith("- "):
                self.assertIn(flat(line), self.doc)
        for group, name in (("zero", "Zero set"), ("control3", "Control 3")):
            self.assertIn("%s (%d sites, %d with all three home pages read)" % (
                name, self.s[group]["sites"], self.s[group]["all_home_ok"]), self.doc)
        hosts = sorted(job.c.bare_host(r["website"]) for r in self.s["smoke_sites"])
        self.assertEqual(hosts, ["ada.gov", "section508.gov"])

    def test_weighted_share(self):
        st, w = self.s["strata"], self.weighted()
        for a in job.ARMS:
            self.assertAlmostEqual(w[a], self.s["weighted_readable"][a])
        sites_csv = os.path.join(HERE, "results", "v0.2.1", "sites.csv")
        if os.path.exists(sites_csv):
            with open(sites_csv, encoding="utf-8", newline="") as f:
                rows = [r for r in csv.DictReader(f) if r["status"] == "ok" and int(r["pages_read"] or 0) > 0]
            self.assertEqual(st["zero"], sum(1 for r in rows if int(r["pdf_links"] or 0) == 0))
            self.assertEqual(st["with_links"], sum(1 for r in rows if int(r["pdf_links"] or 0) > 0))
        self.assertEqual(st["zero"], self.s["zero"]["sites"])
        self.assertIn("A %.1f%%, B %.1f%%, D %.1f%%" % (w["A"], w["B"], w["D"]), self.doc)

    def test_predictions(self):
        z, ctl = self.s["zero"], self.s["control3"]
        n, m = z["all_home_ok"], ctl["all_home_ok"]
        ok = self.outcomes()
        rd, ra, rb = (ctl["readable"][a] for a in ("D", "A", "B"))
        self.assertIn("1. %s Control 3: D reached at least one readable PDF at %.1f%% of sites against %.1f%% "
                      "for A, %s" % (verdict(ok[0]), pct(rd, m), pct(ra, m), diff(pct(rd, m), pct(ra, m))), self.doc)
        d = ctl["readable"]["D_vs_B"]
        self.assertIn("2. %s Control 3: D reached a readable PDF at %d sites against %d for B (%d against %d on "
                      "the discordant pairs, p = %.2g)" % (verdict(ok[1]), rd, rb, d["only_D"], d["only_B"],
                                                           d["mcnemar_p"]), self.doc)
        zd, zb = z["links"]["D"], z["links"]["B"]
        self.assertIn("3. %s Zero set: D found at least one PDF link at %.1f%% of the analysed sites (%d of %d) "
                      "against %.1f%% for B (%d), %s" % (verdict(ok[2]), pct(zd, n), zd, n, pct(zb, n), zb,
                                                          diff(pct(zd, n), pct(zb, n))), self.doc)
        d = z["links"]["D_vs_A"]
        self.assertIn("4. %s Zero set: on the discordant pairs D found a PDF link where A did not at %d sites, "
                      "and A where D did not at %d; exact McNemar p = %.2g" % (
                          verdict(ok[3]), d["only_D"], d["only_A"], d["mcnemar_p"]), self.doc)
        self.assertIn("5. %s Control 3: D read %d inner pages against %d for A" % (
            verdict(ok[4]), ctl["pages_read_D"], ctl["pages_read_A"]), self.doc)
        w = self.weighted()
        self.assertIn("6. %s Weighted share of read sites reaching a readable PDF: D %.1f%% against A %.1f%%" % (
            verdict(ok[5]), w["D"], w["A"]), self.doc)
        held = sum(ok)
        self.assertIn("%s of the six predictions held" % WORDS[held], self.doc.lower())

    def test_in_short_and_readme(self):
        z, ctl = self.s["zero"], self.s["control3"]
        n, m = z["all_home_ok"], ctl["all_home_ok"]
        control = "reached a readable PDF on %d of %d control sites" % (ctl["readable"]["D"], m)
        zero = "found a PDF link on %d of %d, against %d for 0.1.1 and %d for random pages" % (
            z["links"]["D"], n, z["links"]["B"], z["links"]["A"])
        pages = "reading %d inner pages against %d" % (ctl["pages_read_D"], ctl["pages_read_A"])
        for text in (control, zero, pages):
            self.assertIn(text, self.doc)
            self.assertIn(text, self.readme)
        d = z["links"]["D_vs_A"]
        self.assertIn("%d against %d sites" % (z["links"]["D"], z["links"]["A"]), self.readme)
        self.assertIn("p = %.2g" % d["mcnemar_p"], self.readme)


if __name__ == "__main__":
    unittest.main()
