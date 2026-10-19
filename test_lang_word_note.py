"""Checks docs/lang-word-note.md, an exploratory (not pre-registered) breakdown of the
lang-census's non-English PDFs by the tool that made them: recomputes every number on the page
from the public rows in results/lang-v1/ (lang-public-1.jsonl, lang-public-2.jsonl, ...), checks
that the totals agree with summary.json, and that the page says it was not pre-registered. Public
rows have no site id, so the page's site count is not checked here. No network. Apache-2.0
licensed."""

import json
import math
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.path.join(HERE, "results", "lang-v1")
GROUPS = ("Word", "Adobe", "Everything else")
# (PDFs, right /Lang, no /Lang, declares another language, of those marked locally), as on the page
WANT = {"Word": (15, 1, 1, 13, 11), "Adobe": (34, 7, 13, 14, 2), "Everything else": (16, 0, 5, 11, 3)}


def text(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(s):
    return " ".join(s.split())


def load_rows():
    """The public rows, from the numbered parts of lang-public.jsonl."""
    rows = []
    for name in sorted(os.listdir(LANG)):
        if re.fullmatch(r"lang-public(-\d+)?\.jsonl", name):
            with open(os.path.join(LANG, name), encoding="utf-8") as f:
                rows += [json.loads(line) for line in f if line.strip()]
    return rows


def is_language(t):
    return t not in (None, "undetermined", "mixed")


def declared(d):
    """lang.declared: none, unusable, match or other."""
    if not d.get("lang_present"):
        return "none"
    if not d.get("lang_primary"):
        return "unusable"
    return "match" if d["lang_primary"] == d["text_lang"] else "other"


def local_match(d):
    t = d["text_lang"]
    return t in (d.get("element_langs") or {}) or t in (d.get("mc_langs") or {})


def group(d):
    f = d.get("producer_family")
    return "Word" if f == "word" else "Adobe" if f == "adobe" else "Everything else"


def breakdown(other):
    out = {g: {"pdfs": 0, "match": 0, "none": 0, "other": 0, "unusable": 0, "local": 0} for g in GROUPS}
    for d in other:
        g, v = out[group(d)], declared(d)
        g["pdfs"] += 1
        g[v] += 1
        if v == "other" and local_match(d):
            g["local"] += 1
    return out


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]]: the tables with these margins that are no
    more likely than this one."""
    r1, c1, n = a + b, a + c, a + b + c + d
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)

    def ways(k):
        return math.comb(r1, k) * math.comb(n - r1, c1 - k)

    obs = ways(a)
    return sum(ways(k) for k in range(lo, hi + 1) if ways(k) <= obs) / math.comb(n, c1)


class WordNoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()
        cls.s = json.loads(text("results", "lang-v1", "summary.json"))
        cls.other = [d for d in cls.rows if is_language(d["text_lang"]) and d["text_lang"] != "en"]
        cls.english = [d for d in cls.rows if d["text_lang"] == "en"]
        cls.b = breakdown(cls.other)
        cls.doc = flat(text("docs", "lang-word-note.md"))

    def test_rows_present(self):
        self.assertEqual(len(self.rows), self.s["ok"])
        self.assertEqual(len(self.other), self.s["non_english"])

    def test_breakdown(self):
        for g in GROUPS:
            c = self.b[g]
            self.assertEqual((c["pdfs"], c["match"], c["none"], c["other"], c["local"]), WANT[g], g)
            self.assertEqual(c["unusable"], 0, g)
        # every other-language declaration among them is English
        self.assertEqual({d["lang_primary"] for d in self.other if declared(d) == "other"}, {"en"})

    def test_agrees_with_summary(self):
        s, b = self.s, self.b
        fam = s["explore_non_english_by_family"]
        wrong = {g: b[g]["pdfs"] - b[g]["match"] for g in GROUPS}
        self.assertEqual(fam["word"], [b["Word"]["pdfs"], wrong["Word"]])
        self.assertEqual(fam["adobe"], [b["Adobe"]["pdfs"], wrong["Adobe"]])
        rest = [sum(v[0] for k, v in fam.items() if k not in ("word", "adobe")),
                sum(v[1] for k, v in fam.items() if k not in ("word", "adobe"))]
        self.assertEqual(rest, [b["Everything else"]["pdfs"], wrong["Everything else"]])
        self.assertEqual(s["L2_local_match"]["k"], sum(b[g]["local"] for g in GROUPS))
        self.assertEqual(s["L2_local_match"]["n"], sum(b[g]["other"] for g in GROUPS))
        self.assertEqual(s["explore_non_english_declared_as"], {"en": sum(b[g]["other"] for g in GROUPS)})

    def test_table(self):
        tot = {k: sum(self.b[g][k] for g in GROUPS) for k in ("pdfs", "match", "none", "other", "local")}
        for name, c in [(g, self.b[g]) for g in GROUPS] + [("All", tot)]:
            self.assertIn("| %s | %d | %d | %d | %d | %d |" % (
                name, c["pdfs"], c["match"], c["none"], c["other"], c["local"]), self.doc)
        self.assertIn("All %d declarations of another language name English, and none of the %d has "
                      "an unusable value." % (tot["other"], tot["pdfs"]), self.doc)
        self.assertIn("The lang-census found %d PDFs" % tot["pdfs"], self.doc)
        self.assertIn("%d of them declare English as their document language, and %d of those %d" % (
            tot["other"], tot["local"], tot["other"]), self.doc)

    def test_claims(self):
        w, a, e = self.b["Word"], self.b["Adobe"], self.b["Everything else"]
        local = w["local"] + a["local"] + e["local"]
        doc = self.doc
        self.assertIn("%d of the %d PDFs that declare English while marking the real language inside "
                      "are Word output." % (w["local"], local), doc)
        self.assertIn("In %d of Word's %d English-declared non-English PDFs" % (w["local"], w["other"]), doc)
        self.assertIn("For Adobe output it is %d of %d, for everything else %d of %d." % (
            a["local"], a["other"], e["local"], e["other"]), doc)
        p = fisher_two_sided(w["local"], w["other"] - w["local"], a["local"], a["other"] - a["local"])
        self.assertIn("(%d of %d against %d of %d)" % (w["local"], w["other"], a["local"], a["other"]), doc)
        self.assertIn("gives p = %.4f (two-sided)" % p, doc)
        self.assertIn("Of Word's %d non-English PDFs, %d have a /Lang, and %d of those say English." % (
            w["pdfs"], w["pdfs"] - w["none"], w["other"]), doc)
        self.assertIn("That covers %d of the %d English-declared non-English PDFs, %d of them Word's." % (
            local, w["other"] + a["other"] + e["other"], w["local"]), doc)
        self.assertIn("Small numbers (%d Word and %d Adobe PDFs)" % (w["pdfs"], a["pdfs"]), doc)

    def test_english_baseline(self):
        parts = []
        for fam, label in (("word", "Word"), ("adobe", "Adobe")):
            rows = [d for d in self.english if d.get("producer_family") == fam]
            k = sum(1 for d in rows if d["lang_present"])
            parts.append("%d of %d English %s PDFs (%.1f%%)" % (k, len(rows), label, 100 * k / len(rows)))
        self.assertIn("%s have a /Lang, against %s." % tuple(parts), self.doc)

    def test_fisher(self):
        # a known table: [[3, 1], [1, 3]] has two-sided p = 34/70
        self.assertAlmostEqual(fisher_two_sided(3, 1, 1, 3), 34 / 70)

    def test_wording(self):
        low = self.doc.lower()
        for bad in ("an ai", "by hand", "hand check"):
            self.assertNotIn(bad, low)
        self.assertIn("**Exploratory, not pre-registered:**", self.doc)
        self.assertIn("no government is named", self.doc)
        self.assertIn("(lang-census-results.md)", self.doc)
        self.assertIn("(../results/lang-v1/)", self.doc)
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents.", self.doc)


if __name__ == "__main__":
    unittest.main()
