"""Checks the published lang-census results (results/lang-v1): recomputes every count, share,
interval and prediction verdict in summary.json that the public rows allow from the public rows
(lang-public.jsonl as the job wrote it, split byte for byte into lang-public-1.jsonl,
lang-public-2.jsonl, ... to keep each file under 2 MB; split-report.json gives the size and
SHA-256 of each part and of the original, and the parts must join back to it; the row checks are
skipped until the parts are in the repository), checks each row against the rules that produced
it, checks that the job started after its pre-registration was public, and that no public row
carries a URL, a site id or a raw /Lang string. Public rows have no site id, so the site count
and the site-resampled interval are only checked for shape. The crawl drops a repeated PDF link
within a site but not across sites, so a link two governments both post is a row for each, as
pre-registered; the repeats are counted, kept out of the non-English PDFs, and every verdict is
recomputed with each link counted once (added 2026-10-19). Then checks that every number and
verdict on docs/lang-census-results.md is the one in summary.json, and that L1 to L3 are not
scored as findings there if check K failed. No network. Apache-2.0 licensed."""

import collections
import hashlib
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.path.join(HERE, "results", "lang-v1")
# Pre-registered thresholds and rules (docs/lang-census-prereg.md; lang.py 0.1.1, Amendment 1).
L1_MIN, L2_MIN, L3_MAX, L4_MAX, K_MIN = 0.50, 0.30, 0.02, 0.03, 0.90
MIN_DETERMINED, MAJORITY, MAX_CHUNKS, MAX_TEXT = 400, 0.8, 60, 20_000
PREREG_PUBLIC_AT = "2026-10-18T17:48:37Z"  # the commit that published the pre-registration
AMENDMENT_PUBLIC_AT = "2026-10-18T19:54:03Z"  # Amendment 1 and lang.py 0.1.1
NOTE_PUBLIC_AT = "2026-10-18T20:37:37Z"  # docs/lang-census-note-before-results.md
# Rows whose URL hash an earlier row already has: links reached from more than one site.
REPEATED_ROWS = 4
PUBLIC_FIELDS = {"url_sha256", "kind", "state", "producer_family", "created", "tagged", "result",
                 "lang_present", "lang_well_formed", "lang_primary", "lang_is_name", "text_chars",
                 "chunks", "chunks_confident", "chunks_agree", "determined_chars", "text_langs",
                 "text_lang", "element_lang", "element_langs", "struct_capped", "mc_lang",
                 "mc_langs"}
# Rows of the results page's prediction table: (summary key, label as lang.report writes it,
# depends on the text languages, so not scored if K failed).
PREDICTIONS = (
    ("L1_non_english_wrong", "L1: 50%+ of non-English PDFs have a missing, unusable or other /Lang", True),
    ("L2_local_match", "L2: 30%+ of non-English PDFs declared English name the text language locally", True),
    ("L3_english_other", "L3: under 2% of English PDFs declare another language", True),
    ("L4_malformed", "L4: under 3% of /Lang values are not BCP 47-shaped", False),
    ("K_detector_agreement", "K: 90%+ detector agreement on confident chunks", False))
NOT_SCORED = "not scored (K failed)"


def text(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def flat(s):
    return " ".join(s.split())


def load(name):
    with open(os.path.join(LANG, name), encoding="utf-8") as f:
        if name.endswith(".jsonl"):
            return [json.loads(line) for line in f if line.strip()]
        return json.load(f)


def load_rows():
    """The public rows, from lang-public.jsonl or its numbered parts."""
    rows = []
    for name in sorted(os.listdir(LANG)):
        if re.fullmatch(r"lang-public(-\d+)?\.jsonl", name):
            rows += load(name)
    return rows


def wilson(k, n, z=1.96):
    """lang.wilson."""
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
    """lang.pct."""
    if not c or c.get("share") is None:
        return "n/a"
    return "%d of %d, %.1f%% (%.1f-%.1f)" % (c["k"], c["n"], 100 * c["share"],
                                             100 * c["ci95"][0], 100 * c["ci95"][1])


def met(c, ok):
    return dict(c, met=None if c["share"] is None else ok(c["share"]))


def key(x):
    """A dict key as json.dump writes it (None -> "null")."""
    return "null" if x is None else str(x)


def is_language(t):
    return t not in (None, "undetermined", "mixed")


def declared(d):
    """lang.declared: none, unusable, match or other."""
    if not d.get("lang_present"):
        return "none"
    if not d.get("lang_primary"):
        return "unusable"
    return "match" if d["lang_primary"] == d["text_lang"] else "other"


def wrong(d):
    return declared(d) != "match"


def local_match(d):
    t = d["text_lang"]
    return t in (d.get("element_langs") or {}) or t in (d.get("mc_langs") or {})


def counts(pairs):
    """lang.counts, with keys as they read back from summary.json."""
    out = {}
    for k, d in pairs:
        n, w = out.get(key(k), [0, 0])
        out[key(k)] = [n + 1, w + int(wrong(d))]
    return out


def tally(items):
    return {key(k): v for k, v in collections.Counter(items).items()}


def predictions(rows):
    """L1 to L4 and K (without L1's site-resampled interval) as lang.py scores them."""
    det = [d for d in rows if is_language(d["text_lang"])]
    english = [d for d in det if d["text_lang"] == "en"]
    other = [d for d in det if d["text_lang"] != "en"]
    present = [d for d in rows if d["lang_present"]]
    as_english = [d for d in other if d["lang_primary"] == "en"]
    return {
        "L1_non_english_wrong": met(share(sum(1 for d in other if wrong(d)), len(other)),
                                    lambda x: x >= L1_MIN),
        "L2_local_match": met(share(sum(1 for d in as_english if local_match(d)), len(as_english)),
                              lambda x: x >= L2_MIN),
        "L3_english_other": met(share(sum(1 for d in english if declared(d) == "other"), len(english)),
                                lambda x: x < L3_MAX),
        "L4_malformed": met(share(sum(1 for d in present if not d["lang_well_formed"]), len(present)),
                            lambda x: x < L4_MAX),
        "K_detector_agreement": met(share(sum(d["chunks_agree"] for d in rows),
                                          sum(d["chunks_confident"] for d in rows)),
                                    lambda x: x >= K_MIN)}


class LangTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load("summary.json")
        cls.ok = load_rows()  # readable PDFs only
        if not cls.ok:
            raise unittest.SkipTest("the public rows are not in results/lang-v1/ yet")
        cls.det = [d for d in cls.ok if is_language(d["text_lang"])]
        cls.english = [d for d in cls.det if d["text_lang"] == "en"]
        cls.other = [d for d in cls.det if d["text_lang"] != "en"]
        cls.present = [d for d in cls.ok if d["lang_present"]]
        first = {}
        for d in cls.ok:
            first.setdefault(d["url_sha256"], d)
        cls.once = list(first.values())  # each link counted once, at its first row

    def test_parts_join(self):
        """The parts are the job's lang-public.jsonl, byte for byte (split_rows.py's report)."""
        rep = load("split-report.json")
        self.assertEqual(rep["src"], "lang-public.jsonl")
        self.assertTrue(rep["joined_equals_src"])
        names = sorted(n for n in os.listdir(LANG) if re.fullmatch(r"lang-public(-\d+)?\.jsonl", n))
        self.assertEqual(names, [p["name"] for p in rep["parts"]])
        joined = b""
        for p in rep["parts"]:
            with open(os.path.join(LANG, p["name"]), "rb") as f:
                b = f.read()
            self.assertLessEqual(len(b), rep["max_bytes"], p["name"])
            self.assertEqual((len(b), hashlib.sha256(b).hexdigest()), (p["bytes"], p["sha256"]), p["name"])
            self.assertTrue(b.endswith(b"\n"), p["name"])  # cut at line ends only
            joined += b
        self.assertEqual((len(joined), hashlib.sha256(joined).hexdigest()),
                         (rep["src_bytes"], rep["src_sha256"]))
        self.assertEqual(sum(p["rows"] for p in rep["parts"]), rep["src_rows"])
        self.assertEqual(rep["src_rows"], len(self.ok))

    def test_rows_add_up(self):
        s = self.s
        self.assertEqual(s["version"], "0.1.1")
        self.assertEqual(sum(s["check_results"].values()), s["pdfs"])
        self.assertEqual(s["check_results"].get("ok", 0), s["ok"])
        self.assertEqual(len(self.ok), s["ok"])
        self.assertEqual(len(self.ok) - len(self.once), REPEATED_ROWS)
        self.assertEqual(tally(d["text_lang"] for d in self.ok), s["text_lang_counts"])
        self.assertEqual((len(self.det), len(self.english), len(self.other)),
                         (s["determined"], s["english"], s["non_english"]))
        # no site ids in public rows: only the shape of the site count can be checked
        self.assertLessEqual(s["non_english_sites"], s["non_english"])
        self.assertEqual(s["non_english_sites"] == 0, s["non_english"] == 0)

    def test_repeated_links(self):
        """A link posted by two governments is a row for each, as the pre-registration counts
        PDFs; counted once instead, no non-English PDF changes and no verdict changes."""
        seen = collections.Counter(d["url_sha256"] for d in self.ok)
        for d in self.other:
            self.assertEqual(seen[d["url_sha256"]], 1, d["url_sha256"])
        once = predictions(self.once)
        for name in ("L1_non_english_wrong", "L2_local_match"):
            self.assertEqual(once[name], {k: v for k, v in self.s[name].items() if k != "cluster_ci95"})
        for name, *_ in PREDICTIONS:
            self.assertEqual(once[name]["met"], self.s[name]["met"], name)
        self.assertLessEqual(once["L3_english_other"]["k"], self.s["L3_english_other"]["k"])
        self.assertLessEqual(once["L4_malformed"]["k"], self.s["L4_malformed"]["k"])
        self.assertGreaterEqual(once["K_detector_agreement"]["share"], 0.988)
        doc = flat(text("docs", "lang-census-results.md"))
        self.assertIn("%d rows hold %d distinct URL hashes" % (len(self.ok), len(self.once)), doc)
        self.assertIn("None of the %d non-English PDFs has a repeated link" % len(self.other), doc)
        self.assertIn("L3 stays at %d or fewer of at least %d English PDFs" % (
            self.s["L3_english_other"]["k"], self.s["L3_english_other"]["n"] - REPEATED_ROWS), doc)
        self.assertIn("L4 at %d or fewer of at least %d" % (
            self.s["L4_malformed"]["k"], self.s["L4_malformed"]["n"] - REPEATED_ROWS), doc)
        self.assertIn("K at 98.8% or more", doc)

    def test_each_row(self):
        for d in self.ok:
            h = d["url_sha256"]
            self.assertEqual(d["result"], "ok", h)
            self.assertLessEqual(d["chunks_agree"], d["chunks_confident"], h)
            self.assertLessEqual(d["chunks_confident"], d["chunks"], h)
            self.assertLessEqual(d["chunks"], MAX_CHUNKS, h)
            self.assertLessEqual(d["text_chars"], MAX_TEXT, h)
            det = d["determined_chars"]
            self.assertEqual(sum(d["text_langs"].values()), det, h)
            self.assertTrue(all(n > 0 for n in d["text_langs"].values()), h)
            # chunks never hold more characters than the text, so 0.5 * text_chars bounds the rule
            if is_language(d["text_lang"]):
                self.assertGreaterEqual(det, MIN_DETERMINED, h)
                self.assertGreaterEqual(d["text_langs"].get(d["text_lang"], 0), MAJORITY * det, h)
            elif d["text_lang"] == "mixed":
                self.assertGreaterEqual(det, MIN_DETERMINED, h)
                self.assertLess(max(d["text_langs"].values()), MAJORITY * det, h)
            else:
                self.assertEqual(d["text_lang"], "undetermined", h)
                self.assertTrue(det < MIN_DETERMINED or det < 0.5 * d["text_chars"], h)
            self.assertEqual(sum(d["element_langs"].values()), d["element_lang"], h)
            self.assertEqual(sum(d["mc_langs"].values()), d["mc_lang"], h)
            if not d["lang_present"]:
                self.assertEqual((d["lang_primary"], d["lang_well_formed"], d["lang_is_name"]),
                                 (None, None, False), h)
            else:
                self.assertIn(d["lang_well_formed"], (True, False), h)
            if d["lang_primary"] is not None:
                self.assertTrue(d["lang_present"], h)
                self.assertTrue(re.fullmatch(r"[a-z]{2,3}", d["lang_primary"]), h)
            if d["lang_is_name"]:  # "/en-US" is neither BCP 47-shaped nor usable
                self.assertEqual((d["lang_well_formed"], d["lang_primary"]), (False, None), h)

    def test_predictions(self):
        s, once = self.s, predictions(self.ok)
        for name, *_ in PREDICTIONS:
            want = {k: v for k, v in s[name].items() if k != "cluster_ci95"}
            self.assertEqual(once[name], want, name)
        ci = s["L1_non_english_wrong"]["cluster_ci95"]
        if self.other:
            self.assertTrue(0.0 <= ci[0] <= ci[1] <= 1.0, ci)
        else:
            self.assertIsNone(ci)

    def test_exploratory(self):
        s, other = self.s, self.other
        self.assertEqual(tally("%s:%s" % (d["text_lang"], declared(d)) for d in other),
                         s["explore_non_english_declared"])
        self.assertEqual(tally(str(d["lang_primary"]) for d in other if declared(d) == "other"),
                         s["explore_non_english_declared_as"])
        self.assertEqual(tally(declared(d) for d in self.english), s["explore_english_declared"])
        self.assertEqual(counts((d.get("producer_family"), d) for d in other), s["explore_non_english_by_family"])
        self.assertEqual(counts(("tagged" if d.get("tagged") else "untagged", d) for d in other),
                         s["explore_non_english_by_tagged"])
        # lang.py keys these by str(), so a missing /Lang reads back as "None", not "null"
        self.assertEqual(tally(str(d["lang_primary"]) for d in self.ok if d["text_lang"] == "mixed"),
                         s["explore_mixed_declared"])
        self.assertEqual(sum(1 for d in self.present if d["lang_is_name"]), s["explore_lang_is_name"])
        self.assertEqual(share(len(self.present), len(self.ok)), s["explore_lang_present_all"])
        # the raw values are private; the 20 most common are in the summary
        bad = s["explore_malformed_values"]
        k = s["L4_malformed"]["k"]
        self.assertLessEqual(len(bad), 20)
        if len(bad) < 20:
            self.assertEqual(sum(bad.values()), k)
        else:
            self.assertLessEqual(sum(bad.values()), k)

    def test_private_fields(self):
        for d in self.ok:
            self.assertLessEqual(set(d), PUBLIC_FIELDS, d.get("url_sha256"))
            self.assertEqual(len(d["url_sha256"]), 64)
            self.assertNotIn("http", json.dumps(d))


class ResultsPageTests(unittest.TestCase):
    """Every number and verdict on docs/lang-census-results.md, as summary.json has it. Written
    before the results existed, so it covers both outcomes of check K."""

    @classmethod
    def setUpClass(cls):
        cls.s = load("summary.json")
        cls.k_held = cls.s["K_detector_agreement"]["met"] is True
        cls.doc = flat(text("docs", "lang-census-results.md"))
        cls.readme = flat(text("README.md"))

    def test_files(self):
        sha = text("results", "lang-v1", "code-sha256.txt")
        for name in ("census.py", "lang.py", "test_lang.py", "lang-census-prereg.md"):
            self.assertIn("  " + name, sha)
        self.assertIn("pypdf 6.21.1 py3langid 0.4.0 langdetect 1.0.9", sha)
        started = text("results", "lang-v1", "started-at.txt").strip()
        self.assertGreater(started, PREREG_PUBLIC_AT)  # no PDF read before the predictions were public
        self.assertIn("## Pre-registered predictions", text("results", "lang-v1", "results.md"))
        for f in ("docs-private", "sites-private"):
            self.assertFalse(os.path.exists(os.path.join(LANG, f + ".jsonl")), f)

    def test_links(self):
        for link in ("(lang-census-prereg.md)", "(lang-census-note-before-results.md)", "(../results/lang-v1/)"):
            self.assertIn(link, self.doc)
        self.assertIn("Amendment 1", self.doc)
        for at in (PREREG_PUBLIC_AT, AMENDMENT_PUBLIC_AT, NOTE_PUBLIC_AT):
            self.assertIn("%s UTC" % at[11:19], self.doc)

    def test_run(self):
        s, n = self.s, self.s["text_lang_counts"]
        started = text("results", "lang-v1", "started-at.txt").strip()
        self.assertGreater(started, AMENDMENT_PUBLIC_AT)
        self.assertIn("started at %s UTC on %s" % (started[11:19], started[:10]), self.doc)
        self.assertIn("pypdf 6.21.1, py3langid 0.4.0 and langdetect 1.0.9", self.doc)
        self.assertIn("lang.py checked %d PDFs (results: %s)." % (s["pdfs"], ", ".join(
            "%s %d" % kv for kv in sorted(s["check_results"].items()))), self.doc)
        self.assertIn("Of the %d it read, %d got a text language (%d English; %d in another language, from %d "
                      "sites), %d were mixed and %d undetermined." % (
                          s["ok"], s["determined"], s["english"], s["non_english"], s["non_english_sites"],
                          n.get("mixed", 0), n.get("undetermined", 0)), self.doc)

    def test_prediction_table(self):
        for name, label, needs_k in PREDICTIONS:
            c = self.s[name]
            if needs_k and not self.k_held:
                verdict = NOT_SCORED
            else:
                verdict = {True: "yes", False: "**no**", None: "not testable"}[c["met"]]
            self.assertIn("| %s | %s | %s |" % (label, pct(c), verdict), self.doc)
        self.assertIn("L1 site-resampled 95%% interval: %s" % json.dumps(
            self.s["L1_non_english_wrong"]["cluster_ci95"]), self.doc)
        self.assertIn("/Lang set, all checked PDFs: %s" % pct(self.s["explore_lang_present_all"]), self.doc)

    def test_k_outcome(self):
        doc = self.doc
        if self.k_held:
            self.assertIn("**Check K held:**", doc)
            self.assertNotIn(NOT_SCORED, doc)
            self.assertNotIn("cannot be trusted", doc)
        else:
            self.assertIn("**Check K failed:**", doc)
            self.assertIn("so the text languages cannot be trusted and L1 to L3 are not scored as findings", doc)
            self.assertIn("untested", doc)
            for p in ("L1", "L2", "L3"):
                for claim in ("%s held" % p, "%s did not hold" % p, "%s failed" % p):
                    self.assertNotIn(claim, doc)

    def test_wording(self):
        low = self.doc.lower()
        for bad in ("an ai", "by hand", "hand check", "http"):
            self.assertNotIn(bad, low)
        self.assertIn("no government is named", self.doc)
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents.", self.doc)

    def test_readme(self):
        self.assertIn("**lang-census scored:**", self.readme)
        self.assertIn("docs/lang-census-results.md", self.readme)


if __name__ == "__main__":
    unittest.main()
