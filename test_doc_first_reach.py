"""Offline tests for doc-first-reach: its selection and statistics, and every number that
docs/doc-first-results.md and the README quote from results/doc-first/. Apache-2.0 licensed."""

import hashlib
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doc_first_reach as job  # noqa: E402


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(text):
    return " ".join(text.split())


def row(site, status="ok", pages="5", links="0"):
    return {"website": site, "status": status, "pages_read": pages, "pdf_links": links}


def rec(group, a_links, b_links, a_ok=0, b_ok=0, b_status="ok"):
    base = {"pages_read": 8, "pdfs_tried": 0, "doc_pages_read": None, "results": []}
    return {"group": group, "website": "x",
            "A": dict(base, status="ok", pdf_links=a_links, pdfs_ok=a_ok),
            "B": dict(base, status=b_status, pdf_links=b_links, pdfs_ok=b_ok, doc_pages_read=3)}


class JobTests(unittest.TestCase):
    def test_select(self):
        rows = [row("a"), row("b", pages="0"), row("c", status="robots_disallow"), row("d", links="4")]
        rows += [row("f%d" % i, links="1") for i in range(150)]
        zero, control = job.select(rows)
        self.assertEqual([r["website"] for r in zero], ["a"])
        self.assertEqual(len(control), job.CONTROL_N)
        self.assertEqual(control, job.select(rows)[1])
        self.assertTrue(all(int(r["pdf_links"]) > 0 for r in control))

    def test_mcnemar(self):
        self.assertEqual(job.mcnemar_p(0, 0), 1.0)
        self.assertEqual(job.mcnemar_p(3, 3), 1.0)
        self.assertAlmostEqual(job.mcnemar_p(0, 10), 2 / 1024)
        self.assertAlmostEqual(job.mcnemar_p(1, 9), 2 * 11 / 1024)

    def test_tally(self):
        recs = [rec("zero", 0, 3, b_ok=1), rec("zero", 0, 0), rec("zero", 2, 0, a_ok=2), rec("zero", 1, 1),
                rec("zero", 0, 5, b_status="home_404")]
        t = job.tally(recs)
        self.assertEqual((t["sites"], t["both_home_ok"]), (5, 4))
        self.assertEqual(t["links"], {"A": 2, "B": 2, "both": 1, "only_A": 1, "only_B": 1, "neither": 1,
                                      "mcnemar_p": 1.0})


class PublishedResultTests(unittest.TestCase):
    def setUp(self):
        self.s = json.loads(read("results", "doc-first", "summary.json"))
        self.doc = flat(read("docs", "doc-first-results.md"))
        self.readme = flat(read("README.md"))

    def test_code_is_what_ran(self):
        hashes = dict(line.split()[::-1] for line in read("results", "doc-first", "code-sha256.txt").splitlines()
                      if line.strip())
        with open(os.path.join(HERE, "doc_first_reach.py"), "rb") as f:
            self.assertEqual(hashlib.sha256(f.read()).hexdigest(), hashes["job.py"])
        self.assertEqual((self.s["census_version"], self.s["site_check_version"]), ("0.2.2", "0.1.1"))
        self.assertEqual((self.s["pages"], self.s["pdfs"]), (job.PAGES, job.PDFS))

    def test_counts_add_up(self):
        for group in ("zero", "control"):
            t = self.s[group]
            for key in ("links", "readable"):
                x = t[key]
                self.assertEqual(x["both"] + x["only_A"] + x["only_B"] + x["neither"], t["both_home_ok"])
                self.assertEqual((x["A"], x["B"]), (x["both"] + x["only_A"], x["both"] + x["only_B"]))
                self.assertAlmostEqual(job.mcnemar_p(x["only_A"], x["only_B"]), x["mcnemar_p"])

    def test_summary_md_and_results_page(self):
        self.assertEqual(read("results", "doc-first", "summary.md").strip(), job.report(self.s).strip())
        for line in job.report(self.s).splitlines():
            if line.startswith("- "):
                self.assertIn(line, self.doc)
        self.assertIn("Zero set (%d sites, %d with both home pages read)" % (
            self.s["zero"]["sites"], self.s["zero"]["both_home_ok"]), self.doc)
        self.assertIn("Control set (%d sites, %d with both home pages read)" % (
            self.s["control"]["sites"], self.s["control"]["both_home_ok"]), self.doc)

    def test_predictions(self):
        z, ctl = self.s["zero"], self.s["control"]
        n, m = z["both_home_ok"], ctl["both_home_ok"]
        b_share, a_share = 100.0 * z["links"]["B"] / n, 100.0 * z["links"]["A"] / n
        self.assertGreaterEqual(b_share, 30)
        self.assertIn("B found at least one PDF link at %.1f%% of the analysed sites (%d of %d)" % (
            b_share, z["links"]["B"], n), self.doc)
        self.assertLessEqual(a_share, 15)
        self.assertIn("A found one at %.1f%% (%d of %d)" % (a_share, z["links"]["A"], n), self.doc)
        self.assertLess(z["links"]["mcnemar_p"], 0.01)
        self.assertIn("%d to %d, exact McNemar p = %.2g" % (
            z["links"]["only_B"], z["links"]["only_A"], z["links"]["mcnemar_p"]), self.doc)
        ra, rb = ctl["readable"]["A"], ctl["readable"]["B"]
        gap = 100.0 * (ra - rb) / m
        self.assertGreater(gap, 2)
        self.assertIn("B reached at least one readable PDF at %.1f%% of sites against %.1f%% for A, "
                      "%.1f points lower" % (100.0 * rb / m, 100.0 * ra / m, gap), self.doc)
        self.assertIn("(%d against %d, p = %.2g)" % (ctl["readable"]["only_A"], ctl["readable"]["only_B"],
                                                     ctl["readable"]["mcnemar_p"]), self.doc)
        self.assertLess(ctl["pages_read_B"], ctl["pages_read_A"])
        self.assertIn("B read %d inner pages against %d for A" % (ctl["pages_read_B"], ctl["pages_read_A"]),
                      self.doc)
        self.assertIn("four of the five predictions held, and one failed", self.doc)
        self.assertIn("4. **Failed.**", self.doc)

    def test_in_short_and_readme(self):
        z, ctl = self.s["zero"], self.s["control"]
        n, m = z["both_home_ok"], ctl["both_home_ok"]
        found = "on %d of %d sites, against %d for random pages" % (z["links"]["B"], n, z["links"]["A"])
        readable = "(%d of %d against %d of %d)" % (ctl["readable"]["B"], m, ctl["readable"]["A"], m)
        gap = "%.1f points worse" % (100.0 * (ctl["readable"]["A"] - ctl["readable"]["B"]) / m)
        for text in (found, readable, gap):
            self.assertIn(text, self.doc)
            self.assertIn(text, self.readme)

    def test_b_missed(self):
        b = json.loads(read("results", "doc-first", "b-missed.json"))
        ctl = self.s["control"]
        self.assertEqual(b["sites"], ctl["links"]["only_A"])
        self.assertEqual(b["sites"], b["b_all_8_pages_document_like"] + 1)
        self.assertLessEqual(b["a_readable_pdf_at_these_sites"], ctl["readable"]["only_A"])
        self.assertIn("B found no PDF link at %d sites where A found some. At all %d, B used its full 8 pages, "
                      "and at %d of them all 8 were document-like" % (
                          b["sites"], b["b_read_all_8_pages"], b["b_all_8_pages_document_like"]), self.doc)


if __name__ == "__main__":
    unittest.main()
