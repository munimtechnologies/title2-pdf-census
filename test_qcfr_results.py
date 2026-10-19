"""Checks the qcfr results (pre-registered in docs/qcfr-prereg.md): runs the site-level
permutation test again on results/qcfr-v1/sites-public.json with qcfr.score_sites and checks it
gives summary.json's Q1; counts the PDF-level numbers again from the public wordsig rows; checks
that results.md, docs/qcfr-results.md and the README bullet are exactly what qcfr.py and
qcfr_page.py write from those files. The site-resampled intervals need the private site ids and
are not rechecked. No network. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents."""

import collections
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qcfr  # noqa: E402
import qcfr_page as qp  # noqa: E402

RES = os.path.join(HERE, "results", "qcfr-v1")
WORDSIG = os.path.join(HERE, "results", "wordsig-v1")
LANG = os.path.join(HERE, "results", "lang-v1", "lang.py")
PART = re.compile(r"wordsig-public-(\d+)\.jsonl")
HEX = re.compile(r"[0-9a-f]{64}")
SITE_ID = re.compile(r"Q\d{3,}")


def text(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def public_rows():
    names = sorted((n for n in os.listdir(WORDSIG) if PART.fullmatch(n)),
                   key=lambda n: int(PART.fullmatch(n).group(1)))
    rows = []
    for name in names:
        rows += [json.loads(line) for line in text("results", "wordsig-v1", name).splitlines()
                 if line.strip()]
    return rows


class ResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lang = qcfr.load_lang(LANG)
        cls.s = json.loads(text("results", "qcfr-v1", "summary.json"))
        cls.f = json.loads(text("results", "qcfr-v1", "run-facts.json"))
        cls.sites = json.loads(text("results", "qcfr-v1", "sites-public.json"))
        cls.q1 = cls.s["Q1_rest_wrong_more_than_quebec"]
        cls.rows = public_rows()

    def test_site_table(self):
        self.assertEqual(self.sites, sorted(self.sites))
        for row in self.sites:
            self.assertEqual(len(row), 3)
            self.assertIn(row[0], ("quebec", "rest"))
            self.assertTrue(isinstance(row[1], int) and isinstance(row[2], int))
            self.assertTrue(0 <= row[2] <= row[1] and row[1] >= 1)

    def test_q1_rescored(self):
        # the full 20,000 permutations with the pre-registered seed
        self.assertEqual(self.q1["permutations"], qcfr.PERMUTATIONS)
        self.assertEqual(self.q1["seed"], qcfr.SEED)
        self.assertEqual(qcfr.score_sites(self.sites), self.q1)

    def test_pdf_counts_from_public_rows(self):
        L = self.lang
        ok = [d for d in self.rows if d.get("result") == "ok"]
        self.assertEqual(len(ok), self.s["ok"])
        fr = [d for d in ok if d.get("text_lang") == "fr"]
        self.assertEqual(len(fr), self.s["french_text"])
        self.assertEqual(sum(1 for d in fr if not qcfr.group_of(d.get("state"))),
                         self.s["french_text_no_province"])
        e = self.s["explore_by_group"]
        for g in ("quebec", "rest"):
            docs = [d for d in fr if qcfr.group_of(d.get("state")) == g]
            self.assertEqual(dict(collections.Counter(L.declared(d) for d in docs)), e[g]["declared"])
            self.assertEqual(dict(collections.Counter(d["lang_primary"] for d in docs
                                                      if L.declared(d) == "other")),
                             e[g]["declared_other_primary"])
            n, k = len(docs), sum(1 for d in docs if L.wrong(d))
            if self.s["sites_with_two_groups"] == 0:
                self.assertEqual((n, k), (self.q1[g]["n"], self.q1[g]["k"]), g)
            else:
                self.assertGreaterEqual(n, self.q1[g]["n"], g)

    def test_fisher(self):
        q, r = self.q1["quebec"], self.q1["rest"]
        if q["n"] and r["n"]:
            p = qcfr.fisher_greater(r["k"], r["n"] - r["k"], q["k"], q["n"] - q["k"])
            self.assertEqual(round(p, 6), self.s["explore_pdf_level_fisher_p"])
        else:
            self.assertIsNone(self.s["explore_pdf_level_fisher_p"])

    def test_versions_and_hashes(self):
        self.assertEqual(self.s["version"], qcfr.__version__)
        self.assertEqual(self.s["lang_version"], qcfr.LANG_VERSION)
        self.assertEqual(self.f["qcfr_sha256"], qp.lf_sha256(os.path.join(HERE, "qcfr.py")))
        self.assertEqual(self.f["lang_sha256"], qp.lf_sha256(LANG))
        self.assertTrue(HEX.fullmatch(self.f["docs_rows_sha256"]))
        self.assertTrue(re.fullmatch(r"20\d\d-\d\d-\d\d", self.f["scored_on"]))

    def test_results_md(self):
        self.assertEqual(text("results", "qcfr-v1", "results.md"), qcfr.report(self.s))

    def test_page(self):
        self.assertEqual(text("docs", "qcfr-results.md"), qp.page(self.s, self.f))

    def test_readme(self):
        lines = text("README.md").splitlines()
        line = qp.readme_bullet(self.s, self.f)
        self.assertEqual(lines.count(line), 1)
        self.assertTrue(lines[lines.index(line) - 1].startswith(qp.README_ANCHOR))

    def test_wording(self):
        page = text("docs", "qcfr-results.md")
        for doc in (page, qp.readme_bullet(self.s, self.f), text("results", "qcfr-v1", "results.md"),
                    json.dumps(self.f)):
            low = doc.lower()
            for bad in qp.BANNED:
                self.assertNotIn(bad, low)
        for doc in (page, text("results", "qcfr-v1", "sites-public.json"),
                    text("results", "qcfr-v1", "summary.json")):
            self.assertIsNone(SITE_ID.search(doc))
        self.assertIn(qp.SIGN, page)
        self.assertIn("(qcfr-prereg.md)", page)
        self.assertIn("no government is named", page)


if __name__ == "__main__":
    unittest.main()
