"""Checks the published tagtree results (results/tagtree-v1, results/verapdf-v1, results/orphans-v1)
and every number README.md and docs/tagtree-*-results.md quote from them.
No network. Apache-2.0 licensed."""

import collections
import json
import os
import statistics
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REACH = os.path.join(HERE, "results", "tagtree-v1")
VERA = os.path.join(HERE, "results", "verapdf-v1")
ORPH = os.path.join(HERE, "results", "orphans-v1")
LEAK, MIN_CONTENT = 0.05, 50  # tagtree 0.1.0's LEAK_THRESHOLD and MIN_CONTENT
TAGTREE_SHA = "d49fbe0b7eb62dbdac182fe972ea5e27489fbacf22f8732bd5f0cda0e3c94fab"


def text(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(s):
    return " ".join(s.split())


def load(folder, name):
    with open(os.path.join(folder, name), encoding="utf-8") as f:
        if name.endswith(".jsonl"):
            return [json.loads(line) for line in f if line.strip()]
        return json.load(f)


def pct(k, n):
    return "%.1f%%" % (100.0 * k / n)


def wilson(k, n, z=1.96):
    """tagtree.wilson."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def cell(c):
    """'6.5% (5.0-8.5)': tagtree.pct without the n."""
    return "%.1f%% (%.1f-%.1f)" % (100 * c["share"], 100 * c["ci95"][0], 100 * c["ci95"][1])


def readme_section():
    md = flat(text("README.md"))
    return md.split("## Test: how much of a")[1].split("## Test: does reading")[0]


class ReachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load(REACH, "summary.json")
        cls.docs = load(REACH, "docs-public.jsonl")
        cls.el = [d for d in cls.docs if d["result"] == "ok" and not d["capped"]
                  and d["content_chars"] >= MIN_CONTENT]
        cls.leaky = [d for d in cls.el if d["leak_share"] >= LEAK]
        cls.doc = flat(text("docs", "tagtree-reach-results.md"))
        cls.readme = readme_section()

    def test_public_rows_add_up(self):
        s, el = self.s, self.el
        self.assertEqual(len(self.docs), s["pdfs_attempted"])
        self.assertEqual(dict(collections.Counter(d["result"] for d in self.docs)), s["results"])
        self.assertEqual(len(el), s["eligible"])
        self.assertEqual(sum(1 for d in self.docs if d["capped"]), s["excluded_capped"])
        self.assertEqual(sum(1 for d in self.docs if not d["capped"] and d["content_chars"] < MIN_CONTENT),
                         s["excluded_little_text"])
        for k in ("reachable", "untagged", "dangling", "artifact", "xobject", "named"):
            self.assertEqual(sum(d[k] for d in el), s["char_totals"][k], k)
        for d in el:
            self.assertEqual(d["content_chars"], d["reachable"] + d["untagged"] + d["dangling"])
        # Public rows carry a URL hash, never the URL or a government's name.
        self.assertTrue(all("url" not in d and "qid" not in d for d in self.docs))

    def test_predictions(self):
        s, el = self.s, self.el
        n = len(el)
        shells = [d for d in el if d["shell"]]
        for got, c in ((self.leaky, s["P1_leaky"]), (shells, s["P3_shell"])):
            self.assertEqual((len(got), n), (c["k"], c["n"]))
            self.assertEqual(wilson(len(got), n), c["ci95"])
        word = [d for d in el if d["producer_family"] == "word"]
        other = [d for d in el if d["producer_family"] != "word"]
        for group, c in ((word, s["P2_word"]), (other, s["P2_other"])):
            self.assertEqual((sum(1 for d in group if d["leak_share"] >= LEAK), len(group)), (c["k"], c["n"]))
        self.assertAlmostEqual(s["P2_other"]["share"] - s["P2_word"]["share"], s["P2_difference"], places=4)
        pages = sorted(x for d in el for x in d["page_discordance"])
        self.assertEqual(len(pages), s["P4_pages_ordered"])
        self.assertEqual(round(statistics.median(pages), 4), s["P4_median_discordance"])
        self.assertEqual(s["predictions"], {"P1 leaky share >= 0.10": False, "P2 other minus word >= 0.10": False,
                                            "P3 shell share >= 0.02": True, "P4 median discordance <= 0.05": True})

    def test_doc_sample(self):
        s, st, doc = self.s, self.s["site_status"], self.doc
        self.assertEqual(s["sites"], 600)
        self.assertIn("600 sites chosen by hash", doc)
        self.assertIn("%d home pages were read; %d sites disallow crawlers in robots.txt and %d could not be read" % (
            st["ok"], st["robots_disallow"], s["sites"] - st["ok"] - st["robots_disallow"]), doc)
        self.assertEqual(s["results"], {"ok": s["pdfs_attempted"]})
        self.assertIn("%d tagged PDFs were analysed, all without error or timeout" % s["pdfs_attempted"], doc)
        self.assertEqual(s["excluded_capped"], 0)
        self.assertIn("%d PDFs from %d sites are eligible; %d had fewer than 50 characters" % (
            s["eligible"], s["eligible_sites"], s["excluded_little_text"]), doc)
        t = s["char_totals"]
        content = t["reachable"] + t["untagged"] + t["dangling"]
        aside = t["xobject"] + t["named"]
        self.assertIn("{:,} characters of text in the eligible PDFs. {:,} more ({:.2f}%)".format(
            content, aside, 100.0 * aside / (content + aside)), doc)
        lost = t["untagged"] + t["dangling"]
        self.assertIn("{:,} of {:,} characters ({}) are unreachable: {:,} untagged and {:,} dangling".format(
            lost, content, pct(lost, content), t["untagged"], t["dangling"]), doc)

    def test_doc_predictions(self):
        s, doc = self.s, self.doc
        p1, w, o, p3 = s["P1_leaky"], s["P2_word"], s["P2_other"], s["P3_shell"]
        lo, hi = p1["cluster_ci95"]
        self.assertIn("| %d of %d, %s; site-clustered interval %.1f-%.1f%% | **No** |" % (
            p1["k"], p1["n"], cell(p1), 100 * lo, 100 * hi), doc)
        self.assertIn("| Word %s (%d of %d), others %s (%d of %d): %.1f points | **No** |" % (
            pct(w["k"], w["n"]), w["k"], w["n"], pct(o["k"], o["n"]), o["k"], o["n"],
            100 * s["P2_difference"]), doc)
        self.assertIn("| %d of %d, %s | Yes |" % (p3["k"], p3["n"], cell(p3)), doc)
        self.assertIn("| {} over {:,} pages | Yes |".format(s["P4_median_discordance"], s["P4_pages_ordered"]), doc)
        over, pages = s["explore_pages_discordance_over_0.2"]
        self.assertIn("{} of the {:,} pages ({})".format(over, pages, pct(over, pages)), doc)

    def test_doc_exploratory(self):
        el, doc, n = self.el, self.doc, len(self.el)
        shells = [d for d in el if d["shell"]]
        untagged_only = [d for d in shells if d["dangling"] == 0]
        self.assertTrue(all(d["untagged"] > 0 for d in untagged_only))
        self.assertIn("%d PDFs have at least one page where" % len(shells), doc)
        self.assertIn("In %d of them all the unreachable text is untagged; %d also have dangling text" % (
            len(untagged_only), len(shells) - len(untagged_only)), doc)
        tiny = [d for d in el if d["elements"] <= 1]
        self.assertTrue(all(d["leak_share"] >= LEAK for d in tiny))
        self.assertIn("%d of the %d PDFs (%s) have a structure tree with at most one element. All %d are leaky" % (
            len(tiny), n, pct(len(tiny), n), len(tiny)), doc)
        dangling = sum(1 for d in el if d["dangling"] > 0)
        self.assertEqual(dangling, self.s["explore_any_dangling"]["k"])
        self.assertIn("%d of %d PDFs have dangling text" % (dangling, n), doc)
        jumps = sum(1 for d in el if d["upward_jumps"] > 0)
        self.assertEqual(jumps, self.s["explore_upward_jump"]["k"])
        self.assertIn("%d of %d PDFs (%s) have at least one place" % (jumps, n, pct(jumps, n)), doc)

    def test_readme(self):
        s, md, n = self.s, self.readme, len(self.el)
        held = sum(1 for v in s["predictions"].values() if v)
        self.assertEqual(held, 2)
        self.assertIn("Two of the four predictions held", md)
        self.assertIn("On %d tagged PDFs from %d local-government sites, %d (%s) leave 5%% or more" % (
            n, s["eligible_sites"], len(self.leaky), pct(len(self.leaky), n)), md)
        w, o = s["P2_word"], s["P2_other"]
        self.assertIn("(%s against %s), but by %.1f points" % (
            pct(w["k"], w["n"]), pct(o["k"], o["n"]), 100 * s["P2_difference"]), md)
        p3 = s["P3_shell"]
        self.assertIn("%d PDFs (%s) have a page of text" % (p3["k"], pct(p3["k"], p3["n"])), md)
        tiny = [d for d in self.el if d["elements"] <= 1]
        self.assertIn("%d of the %d have a structure tree with at most one element, and all %d are leaky" % (
            len(tiny), n, len(tiny)), md)
        self.assertIn("%d PDFs have dangling text" % s["explore_any_dangling"]["k"], md)

    def test_files(self):
        self.assertEqual(self.s["version"], "0.1.0")
        self.assertIn(TAGTREE_SHA + "  tagtree.py", text("results", "tagtree-v1", "code-sha256.txt"))
        self.assertIn("P1: 10%+ of tagged PDFs", text("results", "tagtree-v1", "results.md"))
        for f in ("docs-private", "sites-private"):
            self.assertFalse(os.path.exists(os.path.join(REACH, f + ".jsonl")), f)


class VeraPDFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load(VERA, "summary.json")
        cls.rows = {r["file"]: r for r in load(VERA, "results.jsonl")}
        cls.doc = flat(text("docs", "tagtree-verapdf-results.md"))

    @staticmethod
    def unreachable(r):
        return r["untagged"] + r["dangling"] if r["result"] == "ok" else None

    def test_rows_add_up(self):
        s, rows = self.s, list(self.rows.values())
        self.assertEqual(len(rows), s["files"])
        self.assertEqual(dict(collections.Counter(r["result"] for r in rows)), s["results"])
        self.assertEqual(s["commit"][:7], "bb75f4f")
        self.assertIn("%d PDF/UA-1 files, listed by the git tree API" % s["files"], self.doc)
        self.assertEqual(s["list_source"], "git tree API")
        self.assertIn("%d were analysed; %d has no structure tree (7.1-t11-fail-a" % (
            s["results"]["ok"], s["results"]["no_struct_tree"]), self.doc)
        self.assertEqual(self.rows["7.1-t11-fail-a.pdf"]["result"], "no_struct_tree")

    def test_verdicts(self):
        v, rows = self.s["verdicts"], list(self.rows.values())
        t03 = [r for r in rows if r["clause"] == "7.1" and r["test"] == 3]
        fail = [r for r in t03 if r["verdict"] == "fail"]
        hit = [r for r in fail if self.unreachable(r)]
        self.assertEqual((len(hit), len(fail)), (v["V1_t03_fail"]["with_unreachable"], v["V1_t03_fail"]["files"]))
        self.assertFalse(v["V1_t03_fail"]["met"])
        self.assertIn("| V1: every 7.1-t03 fail file has unreachable text | %d of %d | **No** |" % (
            len(hit), len(fail)), self.doc)
        self.assertTrue(v["V2_t03_pass"]["met"])
        self.assertIn("| 0 of %d | Yes |" % v["V2_t03_pass"]["files"], self.doc)
        passes = [r for r in rows if r["verdict"] == "pass" and r["result"] == "ok" and r["content_chars"] > 0]
        self.assertEqual(len(passes), v["V3_pass_specificity"]["analysed_with_text"])
        self.assertTrue(all(self.unreachable(r) == 0 for r in passes))
        self.assertIn("| %d of %d | Yes |" % (len(passes), len(passes)), self.doc)
        self.assertIn("any of the %d pass files with text" % len(passes), readme_section())

    def test_the_miss_and_the_hit(self):
        miss, twin, hit = (self.rows[f] for f in ("7.1-t03-fail-a.pdf", "7.1-t03-pass-a.pdf", "7.1-t03-fail-b.pdf"))
        self.assertEqual(self.unreachable(miss), 0)
        self.assertIn("Image is not marked as Artifact or real content", miss["outline"])
        for k in ("reachable", "untagged", "dangling", "artifact"):
            self.assertEqual(miss[k], twin[k], k)
        self.assertIn("(%d reachable, %d artifact)" % (miss["reachable"], miss["artifact"]), self.doc)
        self.assertGreater(hit["untagged"], 0)
        self.assertIn("with %d untagged characters" % hit["untagged"], self.doc)

    def test_no_dangling_anywhere(self):
        ok = [r for r in self.rows.values() if r["result"] == "ok"]
        self.assertEqual(sum(r["dangling"] for r in ok), 0)
        self.assertEqual([r["file"] for r in ok if self.unreachable(r)], ["7.1-t03-fail-b.pdf"])
        blind = self.rows["7.1-t02-fail-a.pdf"]
        self.assertEqual(self.unreachable(blind), 0)
        self.assertIn("(%d artifact characters)" % blind["artifact"], self.doc)

    def test_files(self):
        self.assertIn(TAGTREE_SHA + "  tagtree.py", text("results", "verapdf-v1", "code-sha256.txt"))
        self.assertIn("V1: every 7.1-t03 fail file", text("results", "verapdf-v1", "results.md"))


class OrphansTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = load(ORPH, "summary.json")["cases"][0]
        cls.doc = flat(text("docs", "tagtree-orphans-results.md"))

    def test_checks(self):
        c, rec, page = self.case, self.case["record"], self.case["pages"]["1"]
        self.assertEqual(c["id"], "verapdf-1629")
        self.assertEqual(c["orphan_mcids"], [15, 16, 19])
        self.assertTrue(all(c["verdicts"][k] for k in ("O1_dangling_text", "O2_exact_mcids", "O3_counts_agree")))
        self.assertEqual(sorted(int(m) for m in page["dangling"]), c["orphan_mcids"])
        self.assertEqual(sum(page["dangling"].values()), rec["dangling"])
        self.assertIn("| O1: at least 1 dangling character | %d | Yes |" % rec["dangling"], self.doc)
        self.assertIn("%s = %d" % (" + ".join(str(page["dangling"][str(m)]) for m in c["orphan_mcids"]),
                                   rec["dangling"]), self.doc)
        self.assertEqual(sum(page["text"].values()), rec["content_chars"])
        self.assertIn("Page 1 has %d characters of text: %d are reachable (MCID 0) and %d are not, so %s" % (
            rec["content_chars"], rec["reachable"], rec["dangling"], pct(rec["dangling"], rec["content_chars"])),
            self.doc)
        self.assertEqual(page["text"]["0"], rec["reachable"])

    def test_wording(self):
        self.assertIn("not reachable from StructTreeRoot via K arrays", self.doc)
        self.assertIn("we do not call it non-conformant", self.doc)
        self.assertIn(self.case["sha256"], text("results", "orphans-v1", "summary.json"))
        self.assertIn(TAGTREE_SHA + "  tagtree.py", text("results", "orphans-v1", "code-sha256.txt"))


class WordingTests(unittest.TestCase):
    def test_no_hand_or_eye_claims(self):
        for name in ("tagtree-reach-results.md", "tagtree-verapdf-results.md", "tagtree-orphans-results.md"):
            doc = text("docs", name).lower()
            for phrase in ("by hand", "by eye", "hand check", "hand-check", "an ai"):
                self.assertNotIn(phrase, doc, (name, phrase))
            self.assertIn("ai agents working for mv2 of munim, inc.", flat(doc))
        self.assertNotIn("A hand check", text("README.md"))


if __name__ == "__main__":
    unittest.main()
