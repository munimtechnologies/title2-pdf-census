"""Checks the published objstm-census results (results/objstm-v1): recomputes every count, share,
interval and prediction verdict in summary.json from objstm-public.jsonl, checks that the job
started after its pre-registration was public, that no public row carries a URL or a Producer
string, and that every number in docs/objstm-census-results.md is the one recomputed here. No
network. Apache-2.0 licensed."""

import collections
import json
import os
import statistics
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ = os.path.join(HERE, "results", "objstm-v1")
LEAK, MIN_CONTENT = 0.05, 50  # tagtree's LEAK_THRESHOLD and MIN_CONTENT
# Pre-registered thresholds (docs/objstm-census-prereg.md).
O1_MAX_SHARE, O2_MIN_WORD, O3_MAX_CHANGED = 0.05, 0.80, 2
# The record fields objstm.py compares between tagtree 0.1.1 and --xref-index.
TAGTREE_KEYS = ("result", "elements", "wildcard_mcids", "reachable", "untagged", "dangling",
                "artifact", "content_chars", "leak_share", "shell", "page_discordance",
                "upward_jumps")
# The two files of tagtree-diag-v2: URL hash -> (bytes SHA-256, wrong indexes).
KNOWN = {
    "c8c71fae13ccf1cf19cd67e19caf9f6caccad3bb0c4dc520ad8939e3c0b425b7":
        ("58f6f62bc3de1b7c9090235cfb74ddf48bc9d68a27482dd9ab0d890d05394649", 785),
    "5b10b0e8850b95ae1ae47e646da889ea9a5cc8b2fc34ca1f9e36631a57363ac3":
        ("b2696d00fc5b69095cf2258436756f7cc388f07a22172f954014e5db9ef84bd5", 3122),
}
TAGTREE_011_SHA = "0eba945a8744f1f2cb571a46a84e3937bd229e29ab2804b704f0ed9f99cb9c1e"
DIAG2_SHA = "dc657cba2785271f5b6159157d5843cc432ce6c5dab3f27c7ce39731e7553af7"
PREREG_PUBLIC_AT = "2026-10-18T14:48:28Z"  # the commit that published the pre-registration
# Producer family keys as the results page names them.
FAMILY = {"adobe": "Adobe", "word": "Word", "office-other": "other Office", "other": "other",
          "unknown": "unknown", "generator": "generator", "scanner": "scanner",
          "print-to-pdf": "print-to-PDF", "libreoffice": "LibreOffice"}


def text(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(s):
    return " ".join(s.split())


def load(name):
    with open(os.path.join(OBJ, name), encoding="utf-8") as f:
        if name.endswith(".jsonl"):
            return [json.loads(line) for line in f if line.strip()]
        return json.load(f)


def wilson(k, n, z=1.96):
    """objstm.wilson."""
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def share(k, n):
    return {"k": k, "n": n, "share": round(k / n, 4) if n else None, "ci95": wilson(k, n)}


def pct(c):
    """objstm.pct."""
    return "%d of %d, %.1f%% (%.1f-%.1f)" % (c["k"], c["n"], 100 * c["share"],
                                             100 * c["ci95"][0], 100 * c["ci95"][1])


def key(x):
    """A dict key as json.dump writes it (None -> "null")."""
    return "null" if x is None else str(x)


def counts(pairs):
    """objstm.counts, with keys as they read back from summary.json."""
    out = {}
    for k, d in pairs:
        n, w = out.get(key(k), [0, 0])
        out[key(k)] = [n + 1, w + int(d["o"]["index_wrong"] > 0)]
    return out


def differs(a, b):
    return any(a.get(k) != b.get(k) for k in TAGTREE_KEYS)


class ObjstmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load("summary.json")
        cls.el = load("objstm-public.jsonl")  # eligible PDFs only
        cls.checked = [d for d in cls.el if d.get("o", {}).get("result") == "ok"]
        cls.objstm = [d for d in cls.checked if d["o"]["compressed_objects"] > 0]
        cls.wrong = [d for d in cls.objstm if d["o"]["index_wrong"] > 0]
        cls.changed = [d for d in cls.wrong if "xref_index" in d and differs(d, d["xref_index"])]

    def test_rows_add_up(self):
        s, el = self.s, self.el
        self.assertEqual(s["version"], "0.1.0")
        self.assertEqual(sum(s["tagtree_results"].values()), s["pdfs"])
        self.assertEqual(len(el), s["eligible"])
        self.assertTrue(all(d["result"] == "ok" and not d.get("capped") and d["content_chars"] >= MIN_CONTENT
                            for d in el))
        self.assertEqual({key(k): v for k, v in collections.Counter(
            d.get("o", {}).get("result") for d in el).items()}, s["check_results"])
        self.assertEqual((len(self.checked), len(self.objstm), len(self.wrong), len(self.changed)),
                         (s["checked"], s["with_object_streams"], s["with_wrong_index"],
                          s["changed_by_xref_index"]))
        for d in self.checked:
            o = d["o"]
            self.assertEqual(o["index_ok"] + o["index_wrong"] + o["absent"], o["compressed_objects"])
            self.assertLessEqual(o["streams_with_wrong_index"], o["streams"])
        # --xref-index was read exactly where some index was wrong
        self.assertEqual(sorted(d["url_sha256"] for d in self.el if "xref_index" in d),
                         sorted(d["url_sha256"] for d in self.wrong))

    def test_predictions(self):
        s = self.s
        o1 = share(len(self.wrong), len(self.objstm))
        o1["met"] = None if o1["share"] is None else o1["share"] < O1_MAX_SHARE
        self.assertEqual(o1, s["O1_wrong_share"])
        o2 = share(sum(1 for d in self.wrong if d.get("producer_family") == "word"), len(self.wrong))
        o2["met"] = None if o2["share"] is None else o2["share"] >= O2_MIN_WORD
        self.assertEqual(o2, s["O2_word_share"])
        self.assertEqual({"k": len(self.changed), "max": O3_MAX_CHANGED,
                          "met": len(self.changed) <= O3_MAX_CHANGED}, s["O3_changed"])

    def test_known_files(self):
        rows = {d["url_sha256"]: d for d in self.el}
        changed = {d["url_sha256"] for d in self.changed}
        for h, k in self.s["known_files"].items():
            full = [u for u in KNOWN if u.startswith(h)]
            self.assertEqual(len(full), 1, h)
            sha, expected = KNOWN[full[0]]
            self.assertEqual(k["expected"], expected)
            if not k["eligible"]:  # only eligible rows are public
                self.assertNotIn(full[0], rows)
                continue
            o = rows[full[0]].get("o", {})
            self.assertEqual((k["same_bytes"], k["index_wrong"], k["changed"]),
                             (o.get("sha256") == sha, o.get("index_wrong"), full[0] in changed), h)

    def test_exploratory(self):
        s, wrong = self.s, self.wrong
        self.assertEqual(counts((d.get("producer_family"), d) for d in self.objstm), s["explore_by_family"])
        self.assertEqual(counts(("hybrid" if d["o"].get("hybrid") else "not_hybrid", d) for d in self.objstm),
                         s["explore_hybrid"])
        self.assertEqual(counts(("word365" if d["o"].get("word365") else "other_word", d)
                                for d in self.objstm if d.get("producer_family") == "word"),
                         s["explore_word365"])
        self.assertEqual(dict(collections.Counter((d.get("created") or "")[:4] or "none" for d in wrong)),
                         s["explore_wrong_created_year"])
        fr = [d["o"]["index_wrong"] / d["o"]["compressed_objects"] for d in wrong]
        self.assertEqual(round(statistics.median(fr), 4) if fr else None, s["explore_wrong_fraction_median"])
        self.assertEqual(sum(d["o"].get("elements_index_wrong", 0) for d in wrong),
                         s["explore_elements_index_wrong"])
        el = self.el
        self.assertEqual(share(sum(1 for d in el if (d.get("leak_share") or 0) >= LEAK), len(el)),
                         s["explore_leaky_0_1_1"])
        self.assertEqual(share(sum(1 for d in el if d.get("shell")), len(el)), s["explore_shell_0_1_1"])

    def test_files(self):
        sha = text("results", "objstm-v1", "code-sha256.txt")
        self.assertIn(TAGTREE_011_SHA + "  tagtree.py", sha)
        self.assertIn(DIAG2_SHA + "  diag2.py", sha)
        for name in ("census.py", "objstm.py", "objstm-census-prereg.md"):
            self.assertIn("  " + name, sha)
        self.assertIn("pdfminer.six 20260107 pypdf 6.21.1", sha)
        started = text("results", "objstm-v1", "started-at.txt").strip()
        self.assertGreater(started, PREREG_PUBLIC_AT)  # no PDF read before the predictions were public
        self.assertIn("## Pre-registered predictions", text("results", "objstm-v1", "results.md"))
        for f in ("docs-private", "sites-private"):
            self.assertFalse(os.path.exists(os.path.join(OBJ, f + ".jsonl")), f)

    def test_private_fields(self):
        for d in self.el:
            self.assertFalse({"url", "qid", "producer"} & set(d), d.get("url_sha256"))
            self.assertNotIn("producer", d.get("o", {}))
            self.assertNotIn("http", json.dumps(d))


class ResultsPageTests(unittest.TestCase):
    """Every number on docs/objstm-census-results.md, recomputed from results/objstm-v1."""

    @classmethod
    def setUpClass(cls):
        cls.s = load("summary.json")
        cls.el = load("objstm-public.jsonl")
        cls.objstm = [d for d in cls.el if d["o"]["result"] == "ok" and d["o"]["compressed_objects"] > 0]
        cls.wrong = [d for d in cls.objstm if d["o"]["index_wrong"] > 0]
        cls.doc = flat(text("docs", "objstm-census-results.md"))
        cls.readme = flat(text("README.md"))

    def test_in_short(self):
        s, o1 = self.s, self.s["O1_wrong_share"]
        self.assertIn("%d of %d eligible tagged PDFs store objects in compressed object streams" % (
            s["with_object_streams"], s["eligible"]), self.doc)
        self.assertIn("Only %d of the %d (%.1f%%, 95%% interval %.1f-%.1f%%)" % (
            o1["k"], o1["n"], 100 * o1["share"], 100 * o1["ci95"][0], 100 * o1["ci95"][1]), self.doc)
        self.assertTrue(all(k["same_bytes"] for k in s["known_files"].values()))
        self.assertEqual(sorted(d["url_sha256"] for d in self.wrong), sorted(KNOWN))  # "the same two"
        self.assertTrue(all(s[p]["met"] for p in ("O1_wrong_share", "O2_word_share", "O3_changed")))
        self.assertIn("**All three predictions held and the known-answer check passed.**", self.doc)

    def test_run(self):
        s = self.s
        started = text("results", "objstm-v1", "started-at.txt").strip()
        self.assertIn("starting at %s UTC" % started[11:19], self.doc)
        self.assertIn("(%s UTC)" % PREREG_PUBLIC_AT[11:19], self.doc)
        self.assertIn("pypdf 6.21.1, pdfminer.six 20260107", self.doc)
        self.assertIn("It read %d PDFs from the same 600 cohort sites (tagtree 0.1.1: %d ok, %d timeout). "
                      "%d are eligible" % (s["pdfs"], s["tagtree_results"]["ok"], s["tagtree_results"]["timeout"],
                                           s["eligible"]), self.doc)
        self.assertEqual(s["checked"], s["eligible"])
        self.assertIn("the index check ran on all %d" % s["checked"], self.doc)

    def test_prediction_table(self):
        s = self.s
        self.assertIn("| %s | yes |" % pct(s["O1_wrong_share"]), self.doc)
        self.assertIn("| %s | yes |" % pct(s["O2_word_share"]), self.doc)
        self.assertIn("`--xref-index` | %d | yes |" % s["O3_changed"]["k"], self.doc)
        self.assertIn("O2 rests on two files", self.doc)
        self.assertEqual(s["O2_word_share"]["n"], 2)

    def test_known_files(self):
        rows = {d["url_sha256"][:8]: d for d in self.el}
        for h, extra in (("c8c71fae", "(as 0.1.0 read it) {} elements and {:,} of {:,} characters dangling."),
                         ("5b10b0e8", "{} elements, all {:,} characters dangling, and a shell page.")):
            d, k = rows[h], self.s["known_files"][h]
            o, x = d["o"], d["xref_index"]
            self.assertEqual(k["index_wrong"], k["expected"])
            self.assertIn("`{}`: {:,} wrong indexes, as expected, of {:,} compressed objects in {} object "
                          "streams.".format(h, o["index_wrong"], o["compressed_objects"], o["streams"]), self.doc)
            self.assertEqual((d["dangling"], d["untagged"], d["shell"]), (0, 0, False))
            self.assertIn("tagtree 0.1.1 reads {:,} structure elements with no dangling text; with "
                          "`--xref-index` ".format(d["elements"]) + (
                              extra.format(x["elements"], x["dangling"], x["content_chars"]) if h == "c8c71fae"
                              else extra.format(x["elements"], x["dangling"])), self.doc)
        x = rows["5b10b0e8"]["xref_index"]
        self.assertEqual((x["dangling"], x["shell"]), (x["content_chars"], True))  # "all", "a shell page"

    def test_exploratory(self):
        s, doc = self.s, self.doc
        fam = sorted(s["explore_by_family"].items(), key=lambda kv: (-kv[1][0], kv[0]))
        self.assertEqual(set(FAMILY), set(s["explore_by_family"]))
        self.assertIn("(PDFs with object streams, of which with a wrong index): " + "; ".join(
            "%s %d, %d" % (FAMILY[k], n, w) for k, (n, w) in fam) + ".", doc)
        w365, other = s["explore_word365"]["word365"], s["explore_word365"]["other_word"]
        word = s["explore_by_family"]["word"]
        self.assertEqual(w365[0] + other[0], word[0])
        self.assertEqual(other[1], 0)
        self.assertIn("%d of the %d Word files with object streams name it, and %d of them have wrong indexes; "
                      "none of the other %d Word files do. %d Word for Microsoft 365 files have no wrong index "
                      "at all." % (w365[0], word[0], w365[1], other[0], w365[0] - w365[1]), doc)
        hy, nh = s["explore_hybrid"]["hybrid"], s["explore_hybrid"]["not_hybrid"]
        self.assertEqual((hy[1], nh[1]), (len(self.wrong), 0))
        self.assertIn("%d of the %d, including both files with wrong indexes; none of the %d others has one" % (
            hy[0], hy[0] + nh[0], nh[0]), doc)
        self.assertIn("Both are hybrid files, but so are %d files without wrong indexes." % (hy[0] - hy[1]), doc)
        self.assertEqual(s["explore_wrong_created_year"], {"2025": 2})
        self.assertIn("Creation year** of the two files: 2025 for both.", doc)
        streams = [d["o"]["streams"] for d in self.wrong]
        self.assertEqual(streams, [d["o"]["streams_with_wrong_index"] for d in self.wrong])
        self.assertIn("over the two files, is %s; in every one of their %d object streams some index is wrong" % (
            s["explore_wrong_fraction_median"], sum(streams)), doc)
        ew = [d["o"]["elements_index_wrong"] for d in self.wrong]
        self.assertIn("Of pypdf's structure elements, {:,} have a wrong index ({:,} and {:,}).".format(
            s["explore_elements_index_wrong"], *ew), doc)
        self.assertIn("%s leaky, %s, and %d with a shell page, %s" % (
            pct(s["explore_leaky_0_1_1"]).split(", ")[0], pct(s["explore_leaky_0_1_1"]).split(", ", 1)[1],
            s["explore_shell_0_1_1"]["k"], pct(s["explore_shell_0_1_1"]).split(", ", 1)[1]), doc)

    def test_settles(self):
        self.assertIn("of %d eligible PDFs, only these two get a different tagtree record" % self.s["eligible"],
                      self.doc)
        self.assertEqual(sum(d["o"]["absent"] for d in self.el if d["o"]["result"] == "ok"), 0)  # "there were none"
        self.assertIn("no government is named", self.doc)
        self.assertNotIn("http", self.doc.replace("](../results/objstm-v1/)", ""))

    def test_readme(self):
        s, readme = self.s, self.readme
        self.assertIn("found object streams in %d of %d eligible tagged PDFs, and indexes that disagree with the "
                      "stream's header in only %d of them (%.1f%%)" % (
                          s["with_object_streams"], s["eligible"], s["with_wrong_index"],
                          100 * s["O1_wrong_share"]["share"]), readme)
        self.assertIn("**objstm-census scored:**", readme)
        self.assertIn("docs/objstm-census-results.md", readme)


if __name__ == "__main__":
    unittest.main()
