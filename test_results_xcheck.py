"""Checks the published tagtree-xcheck results (results/xcheck-v1): recomputes X1-X5, the re-crawl
counts and the disagreement list from pairs-public.jsonl and compares them with summary.json; then
checks every number docs/tagtree-xcheck-results.md quotes, including what the two disagreements
would change in the first run (results/tagtree-v1), the third-parser diagnosis of the two
disagreements and the first run matched with the re-crawl (results/diag-v1). No network.
Apache-2.0 licensed."""

import collections
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
XC = os.path.join(HERE, "results", "xcheck-v1")
REACH = os.path.join(HERE, "results", "tagtree-v1")
DIAG = os.path.join(HERE, "results", "diag-v1")
LEAK, MIN_CONTENT = 0.05, 50  # tagtree 0.1.0's LEAK_THRESHOLD and MIN_CONTENT
# Pre-registered thresholds (docs/tagtree-xcheck-prereg.md).
THRESHOLDS = {"X1_elements_equal": 0.95, "X2_walks_equal": 0.95, "X3_any_dangling_agree": 0.95,
              "X4_shell_agree": 0.90, "X5_leaky_agree": 0.90}
LABELS = {"X1_elements_equal": "X1: same number of structure elements reached from the root",
          "X2_walks_equal": "X2: both walks reach exactly the same marked-content IDs",
          "X3_any_dangling_agree": 'X3: "has dangling text" agrees',
          "X4_shell_agree": 'X4: "has a shell page" agrees',
          "X5_leaky_agree": 'X5: "leaky" (5% or more unreachable) agrees'}
XCHECK_SHA = "8655e9e9ca34488bf6691fd1944507b905490d316a13347518a4ab8ad9e131d2"
TAGTREE_SHA = "d49fbe0b7eb62dbdac182fe972ea5e27489fbacf22f8732bd5f0cda0e3c94fab"
DIAG_SHA = "8a90cd6c618a3b7314cb6f20f7f7eaa1c0094fc6afe58f7cd994effd081d9067"


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
    """xcheck.wilson."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def agree(rows, test):
    k = sum(1 for d in rows if test(d))
    return {"n": len(rows), "k": k, "share": round(k / len(rows), 4) if rows else None,
            "ci95": wilson(k, len(rows))}


def cell(c):
    return "%.1f%% (%.1f-%.1f)" % (100 * c["share"], 100 * c["ci95"][0], 100 * c["ci95"][1])


def leaky(d):
    return d["leak_share"] >= LEAK


TESTS = {
    "X1_elements_equal": lambda d: d["x"]["elements"] == d["elements"],
    "X2_walks_equal": lambda d: d["x"]["walks_equal"],
    "X3_any_dangling_agree": lambda d: (d["x"]["dangling"] > 0) == (d["dangling"] > 0),
    "X4_shell_agree": lambda d: d["x"]["shell"] == d["shell"],
    "X5_leaky_agree": lambda d: d["x"]["leak_share"] is not None
    and (d["x"]["leak_share"] >= LEAK) == (d["leak_share"] >= LEAK),
}


class XcheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load(XC, "summary.json")
        cls.el = load(XC, "pairs-public.jsonl")  # only rows tagtree-reach would count
        cls.pairs = [d for d in cls.el if d["x"].get("result") == "ok"]
        cls.walked = [d for d in cls.pairs if d["x"].get("walks_equal") is not None]

    def test_rows_add_up(self):
        s = self.s
        self.assertEqual(len(self.el), s["eligible"])
        self.assertEqual(len(self.pairs), s["pairs"])
        self.assertEqual(len(self.pairs) - len(self.walked), s["walk_errors"])
        self.assertEqual(dict(collections.Counter(d["x"].get("result") for d in self.el)), s["x_results"])
        # Public rows carry a URL hash, never the URL or a government's name.
        self.assertTrue(all("url" not in d and "qid" not in d for d in self.el))

    def test_checks(self):
        for name, test in TESTS.items():
            rows = self.walked if name == "X2_walks_equal" else self.pairs
            want = agree(rows, test)
            want["met"] = None if want["share"] is None else want["share"] >= THRESHOLDS[name]
            self.assertEqual(want, self.s["checks"][name], name)

    def test_recrawl(self):
        r = self.s["recrawl_tagtree"]
        self.assertEqual(agree(self.el, leaky), r["leaky"])
        self.assertEqual(agree(self.el, lambda d: d["shell"]), r["shell"])
        self.assertEqual(r["v1"], {"leaky": [49, 753], "shell": [32, 753]})

    def test_disagreements(self):
        listed = sorted(d["url_sha256"] for d in self.s["disagreements"])
        found = sorted(d["url_sha256"] for d in self.pairs if not all(
            TESTS[n](d) is not False if n == "X2_walks_equal" else TESTS[n](d)
            for n in ("X1_elements_equal", "X2_walks_equal", "X3_any_dangling_agree", "X4_shell_agree")))
        self.assertEqual(found, listed)

    def test_files(self):
        self.assertEqual(self.s["version"], "0.1.0")
        sha = text("results", "xcheck-v1", "code-sha256.txt")
        self.assertIn(XCHECK_SHA + "  xcheck.py", sha)
        self.assertIn(TAGTREE_SHA + "  tagtree.py", sha)
        self.assertIn("## Pre-registered checks", text("results", "xcheck-v1", "results.md"))
        for f in ("docs-private", "sites-private"):
            self.assertFalse(os.path.exists(os.path.join(XC, f + ".jsonl")), f)


class DocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load(XC, "summary.json")
        cls.doc = flat(text("docs", "tagtree-xcheck-results.md"))
        cls.dis = cls.s["disagreements"]
        v1 = load(REACH, "docs-public.jsonl")
        cls.v1 = [d for d in v1 if d["result"] == "ok" and not d["capped"]
                  and d["content_chars"] >= MIN_CONTENT]

    def test_sample_and_checks(self):
        s, doc = self.s, self.doc
        self.assertEqual(s["tagtree_results"], {"ok": s["pdfs"]})
        self.assertEqual(s["x_results"], {"ok": s["eligible"]})
        self.assertEqual((s["pairs"], s["walk_errors"]), (s["eligible"], 0))
        self.assertIn("%d tagged PDFs were analysed by tagtree, all without error; %d are eligible" % (
            s["pdfs"], s["eligible"]), doc)
        self.assertIn("the pypdf reader read all %d without error" % s["eligible"], doc)
        for name, label in LABELS.items():
            c = s["checks"][name]
            self.assertIn("| %s | %d of %d (%.1f%%) | %d%% | %s |" % (
                label, c["k"], c["n"], 100 * c["share"], round(100 * THRESHOLDS[name]),
                "Yes" if c["met"] else "**No**"), doc)
        self.assertTrue(all(c["met"] for c in s["checks"].values()))
        self.assertIn("**All five held.**", doc)
        self.assertIn("on the other %d PDFs they reach exactly the same marked-content IDs" %
                      s["checks"]["X2_walks_equal"]["k"], doc)

    def test_disagreements(self):
        doc, (a, b) = self.doc, self.dis
        self.assertEqual([d["producer_family"] for d in self.dis], ["word", "word"])
        for d in self.dis:
            self.assertIn("`%s`" % d["url_sha256"][:8], doc)
            self.assertEqual((d["x"]["dangling"], d["x"]["untagged"], d["untagged"]), (0, 0, 0))
        self.assertIn("tagtree reaches {} and {} structure elements from the root; the pypdf reader "
                      "reaches {:,} and {:,}".format(a["elements"], b["elements"], a["x"]["elements"],
                                                     b["x"]["elements"]), doc)
        self.assertIn("tagtree counts {:,} and {:,} characters of dangling text".format(
            a["dangling"], b["dangling"]), doc)
        self.assertEqual((a["shell"], b["shell"], a["x"]["shell"], b["x"]["shell"]), (False, True, False, False))

    def test_first_run(self):
        doc, v1, n = self.doc, self.v1, len(self.v1)
        dis = {d["url_sha256"]: d for d in self.dis}
        hit = [d for d in v1 if d["url_sha256"] in dis]
        self.assertEqual(len(hit), 2)
        for d in hit:  # the same tagtree record in both runs
            for k in ("elements", "reachable", "untagged", "dangling", "content_chars", "leak_share", "shell"):
                self.assertEqual(d[k], dis[d["url_sha256"]][k], k)
        total_dangling = sum(d["dangling"] for d in v1)
        theirs = sum(d["dangling"] for d in hit)
        self.assertIn("they hold {:,} of the first run's {:,} dangling characters ({})".format(
            theirs, total_dangling, pct(theirs, total_dangling)), doc)

        alt = []  # the first run if the pypdf reader is right about the two files
        for d in v1:
            x = dis.get(d["url_sha256"], {}).get("x")
            if x:
                d = dict(d, elements=x["elements"], dangling=0, untagged=0, reachable=d["content_chars"],
                         leak_share=0.0, shell=x["shell"])
            alt.append(d)
        before, after = [d for d in v1 if leaky(d)], [d for d in alt if leaky(d)]
        self.assertIn("leaky: %d of %d (%s), not %d (%s)" % (
            len(after), n, pct(len(after), n), len(before), pct(len(before), n)), doc)
        self.assertLess(len(after) / n, 0.10)
        word = [d for d in alt if d["producer_family"] == "word"]
        other = [d for d in alt if d["producer_family"] != "word"]
        wk, ok = sum(1 for d in word if leaky(d)), sum(1 for d in other if leaky(d))
        diff = 100.0 * (ok / len(other) - wk / len(word))
        self.assertIn("Word %s (%d of %d) against %s (%d of %d): %.1f points" % (
            pct(wk, len(word)), wk, len(word), pct(ok, len(other)), ok, len(other), diff), doc)
        self.assertLess(diff, 10)
        sb, sa = sum(1 for d in v1 if d["shell"]), sum(1 for d in alt if d["shell"])
        self.assertIn("shell page: %d of %d (%s), not %d (%s)" % (sa, n, pct(sa, n), sb, pct(sb, n)), doc)
        self.assertGreaterEqual(sa / n, 0.02)
        content = sum(d["content_chars"] for d in v1)
        self.assertEqual(content, sum(d["content_chars"] for d in alt))
        lost_b = sum(d["untagged"] + d["dangling"] for d in v1)
        lost_a = sum(d["untagged"] + d["dangling"] for d in alt)
        self.assertIn("dangling text in {} PDFs, not {}; {:,} dangling characters, not {:,}; {:,} of {:,} "
                      "characters ({}) unreachable, not {:,} ({})".format(
                          sum(1 for d in alt if d["dangling"] > 0), sum(1 for d in v1 if d["dangling"] > 0),
                          sum(d["dangling"] for d in alt), total_dangling, lost_a, content,
                          pct(lost_a, content), lost_b, pct(lost_b, content)), doc)
        self.assertIn("structure tree with at most one element: %d PDFs, not %d" % (
            sum(1 for d in alt if d["elements"] <= 1), sum(1 for d in v1 if d["elements"] <= 1)), doc)

    def test_recrawl(self):
        r, doc = self.s["recrawl_tagtree"], self.doc
        self.assertIn("tagtree finds %d of %d PDFs leaky, %s, and %d with a shell page, %s, against %d and %d "
                      "of %d in the first run" % (r["leaky"]["k"], r["leaky"]["n"], cell(r["leaky"]),
                                                  r["shell"]["k"], cell(r["shell"]), r["v1"]["leaky"][0],
                                                  r["v1"]["shell"][0], r["v1"]["leaky"][1]), doc)
        a, b = self.dis
        self.assertTrue(leaky(a) and leaky(b) and b["shell"] and not a["shell"])

    def test_wording(self):
        low = self.doc.lower()
        for phrase in ("by hand", "by eye", "hand check", "hand-check", "an ai"):
            self.assertNotIn(phrase, low, phrase)
        self.assertIn("ai agents working for mv2 of munim, inc.", low)
        self.assertIn("no government is named", low)
        for d in load(XC, "pairs-public.jsonl")[:5]:
            self.assertNotIn("http", json.dumps(d))


class DiagTests(unittest.TestCase):
    """results/diag-v1: the two disagreements read again with qpdf and compared object by object,
    and the first run's rows matched with the re-crawl's."""

    @classmethod
    def setUpClass(cls):
        cls.d = load(DIAG, "diag.json")
        cls.files = cls.d["files"]
        cls.doc = flat(text("docs", "tagtree-xcheck-results.md"))
        cls.dis = {d["url_sha256"]: d for d in load(XC, "summary.json")["disagreements"]}
        cls.v1 = load(REACH, "docs-public.jsonl")
        cls.pairs = load(XC, "pairs-public.jsonl")

    def test_files(self):
        d = self.d
        self.assertEqual((d["version"], d["pdfminer"], d["pypdf"], d["pikepdf"]),
                         ("0.1.0", "20260107", "6.21.1", "10.17.0"))
        sha = text("results", "diag-v1", "code-sha256.txt")
        self.assertIn(DIAG_SHA + "  diag.py", sha)
        self.assertIn(TAGTREE_SHA + "  tagtree.py", sha)
        self.assertNotIn("http", json.dumps(d))  # URL hashes only
        self.assertEqual(sorted(f["url_sha256"] for f in self.files), sorted(self.dis))
        self.assertTrue(self.files[0]["url_sha256"].startswith("c8c71fae"))

    def test_each_file(self):
        for f in self.files:
            rec = self.dis[f["url_sha256"]]
            m = f["pdfminer"]
            self.assertEqual(f["fetch"], "ok")
            self.assertEqual((f["pypdf"]["elements"], f["qpdf_elements"], m["elements_checked"]),
                             (rec["x"]["elements"],) * 3)
            self.assertEqual(m["missing"], 0)
            self.assertEqual(m["elements_checked"] - m["same_element"], sum(m["wrong_by_type"].values()))
            self.assertEqual((m["position_agree"], m["position_differ"]), (m["elements_checked"], 0))
            for s in m["streams"].values():
                self.assertEqual(s["header_tokens"], s["header_tokens_expected"])
                self.assertEqual(s["sequential_tokens"], s["sequential_tokens_expected"])
                self.assertIsNone(s["first_difference_index"])
            self.assertEqual(f["tagtree_by_offset"], f["tagtree_as_is"])
            self.assertEqual((f["tagtree_as_is"]["elements"], f["tagtree_as_is"]["dangling"]),
                             (rec["elements"], rec["dangling"]))

    def test_doc(self):
        d, doc = self.d, self.doc
        a, b = self.files
        ma, mb = a["pdfminer"], b["pdfminer"]
        self.assertIn("qpdf (through pikepdf {}) reaches {:,} and {:,} structure elements from the root, "
                      "the same as the pypdf reader".format(d["pikepdf"], a["qpdf_elements"], b["qpdf_elements"]),
                      doc)
        self.assertIn("For {:,} of the {:,} elements and {:,} of the {:,}, pdfminer.six {} returns a different "
                      "object from the one pypdf returns".format(
                          ma["elements_checked"] - ma["same_element"], ma["elements_checked"],
                          mb["elements_checked"] - mb["same_element"], mb["elements_checked"], d["pdfminer"]), doc)
        pairs = {(e["pdfminer_S"], e["pypdf_S"]) for f in self.files for e in f["pdfminer"]["examples"]}
        self.assertIn(("P", "Textbox"), pairs)
        self.assertIn(("Figure", "Document"), pairs)
        self.assertIn("same index ({:,} of {:,} and {:,} of {:,})".format(
            ma["position_agree"], ma["elements_checked"], mb["position_agree"], mb["elements_checked"]), doc)
        self.assertIn("In the object streams checked ({} in the first file, {} in the second)".format(
            len(ma["streams"]), len(mb["streams"])), doc)
        self.assertIn("gives exactly the results it gave before ({} and {} elements)".format(
            a["tagtree_by_offset"]["elements"], b["tagtree_by_offset"]["elements"]), doc)
        self.assertIn("pypdf %s looks the object's number up" % d["pypdf"], doc)
        self.assertIn("That is a hypothesis, not yet a finding", doc)

    def test_overlap(self):
        o, doc = self.d["overlap"], self.doc
        el = [d for d in self.v1 if d["result"] == "ok" and not d["capped"] and d["content_chars"] >= MIN_CONTENT]
        again = {d["url_sha256"]: d for d in self.pairs}
        both = [d for d in el if d["url_sha256"] in again]
        same = sum(1 for d in both if all(d[k] == again[d["url_sha256"]][k]
                                          for k in ("elements", "dangling", "untagged", "reachable")))
        self.assertEqual((o["v1_eligible"], o["recrawl_pairs"], o["read_again"], o["same_tagtree_record"]),
                         (len(el), len(self.pairs), len(both), same))
        self.assertIn("Of the first run's %d eligible PDFs, %d were read again, and %d of those got exactly "
                      "the same tagtree counts" % (len(el), len(both), same), doc)
        groups = (("leaky", "leaky", leaky, lambda x: x["leak_share"] is not None and x["leak_share"] >= LEAK),
                  ("shell", "shell page", lambda d: d["shell"], lambda x: x["shell"]),
                  ("elements_le_1", "at most one structure element", lambda d: d["elements"] <= 1,
                   lambda x: x["elements"] <= 1),
                  ("any_dangling", "some dangling text", lambda d: d["dangling"] > 0, lambda x: x["dangling"] > 0))
        for key, label, test, xtest in groups:
            v1 = [d for d in el if test(d)]
            seen = [d for d in v1 if d["url_sha256"] in again]
            agreed = [d for d in seen if xtest(again[d["url_sha256"]]["x"])]
            self.assertEqual(o[key], {"v1": len(v1), "read_again": len(seen), "pypdf_agrees": len(agreed)}, key)
            self.assertIn("| %s | %d | %d | %d |" % (label, len(v1), len(seen), len(agreed)), doc)
            # every PDF the pypdf reader disagrees on is one of the two files
            off = {d["url_sha256"] for d in seen} - {d["url_sha256"] for d in agreed}
            self.assertTrue(off and off <= set(self.dis), key)


if __name__ == "__main__":
    unittest.main()
