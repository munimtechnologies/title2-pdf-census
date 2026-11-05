"""Tests for results/small-pages/SMALL-PAGES-RESULT.md (no network). Apache-2.0.

Rebuilds the printed result from the saved result.json with small_pages 0.1.0, re-grades every
prediction from the saved per-site table (rows.csv) with the pinned grading code, and checks every
figure the note quotes. The run and the note were made by AI agents working for MV2; no person has
checked them yet.
"""

import csv
import hashlib
import io
import json
import os
import re
import unittest

import small_pages as sp

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "small-pages")

# The sha256 printed in the sealed run (small-pages-v1).
RUN_SHA256 = {
    "small_pages.py": "420f785b6136e945f918395eea4b8c8722f28a5cf5da1bb34d82af3bc0a8f37e",
    "a11y_pages.py": "b0b27c819b2d31b9d6e17fb207129b23aebe767e40e157678e37ad6851e200e0",
    "statement_check.py": "dc12261151610d914149e34a40c2619f458c2dc271c811265d86733cbdde4a23",
}
BOOLS = ("wcag_any", "section508", "title2", "old_date", "new_date", "date_2028", "stock",
         "contact")
STOCK = "We work to comply with Section 508 as well as"
TITLE_RE = re.compile(r"[A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+, (?:Director|Coordinator|Manager|"
                      r"Clerk|Chief|Officer|Administrator|Specialist|Supervisor|Deputy|Assistant)")
OVERLAY_NAMES = (("audioeye", "AudioEye"), ("userway", "UserWay"), ("accessibe", "accessiBe"),
                 ("recite", "Recite Me"), ("equalweb", "EqualWeb"))
# One row's name and links are withheld in the three tables (see the note's Files section).
WITHHELD = "[withheld]"
WITHHELD_QID = "Q1020609"
WITHHELD_FIELDS = {"rows.csv": ("name", "website", "page_url"),
                   "eligible.csv": ("name", "website"),
                   "cohort.csv": ("name", "website")}


def text(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read().decode("utf-8")


def table(name):
    return list(csv.DictReader(io.StringIO(text(name))))


def typed(rows):
    return [dict(r, **{k: r.get(k) == "True" for k in BOOLS}) for r in rows]


def pct(k, n):
    return "%.2f" % (100 * k / n)


def ci(x):
    return "%.2f%% to %.2f%%" % (100 * x[0], 100 * x[1])


class SavedRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(text("result.json"))

    def test_code_is_what_ran(self):
        for name, digest in RUN_SHA256.items():
            with open(os.path.join(HERE, name), "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), digest, name)
        self.assertEqual(self.r["files"], RUN_SHA256)
        self.assertEqual(self.r["version"], sp.__version__)

    def test_printed_result_rebuilds(self):
        self.assertEqual(sp.result_text(self.r), text("result.txt").rstrip("\n"))

    def test_status_and_gates(self):
        r = self.r
        self.assertEqual(r["status"], "graded")
        self.assertEqual(r["prereg_attempts"], 1)
        self.assertEqual(r["gates"], {"P0_prereg_public": True, "C1_cohort": True})
        self.assertTrue(sp.MIN_COHORT <= r["eligible"] <= sp.MAX_COHORT)
        self.assertEqual(r["sampled"], min(sp.SAMPLE_N, r["eligible"]))

    def test_thresholds_are_the_preregistered_ones(self):
        self.assertEqual((sp.S1_MIN_ONLY_20, sp.S2_MIN_STOCK, sp.S3_MAX_TITLE2, sp.S4_MAX_LINKED,
                          sp.S5_MIN_SMALL_2027, sp.MIN_HOMES, sp.MIN_PAGES, sp.MIN_VERSIONED,
                          sp.MIN_DATED, sp.SAMPLE_N, sp.SEED),
                         (0.5571, 0.3465, 0.2215, 0.682, 0.40, 1000, 400, 200, 15, 2500,
                          "small-pages-2026-11-02"))

    def test_predictions_follow_from_the_measures(self):
        m = self.r["measures"]
        k1, n1 = m["S1_only_2.0_of_versioned"][:2]
        k2, n2 = m["S2_stock_of_pages"][:2]
        k3, n3 = m["S3_title2_of_pages"][:2]
        k4, n4 = m["S4_linked_of_homes"][:2]
        k5, n5 = m["S5_2027_without_2028_of_dated"][:2]
        for key, value in m.items():
            self.assertEqual(sp.ap.share(*value[:2]), value, key)
        self.assertEqual((n2, n3, n4), (self.r["pages_ok"], self.r["pages_ok"],
                                        self.r["homes_ok"]))
        self.assertLess(n5, sp.MIN_DATED)
        expect = {"S1": k1 / n1 >= sp.S1_MIN_ONLY_20, "S2": k2 / n2 >= sp.S2_MIN_STOCK,
                  "S3": k3 / n3 <= sp.S3_MAX_TITLE2, "S4": k4 / n4 < sp.S4_MAX_LINKED,
                  "S5": None}
        self.assertEqual(self.r["predictions"], expect)
        self.assertEqual(expect, {"S1": True, "S2": True, "S3": True, "S4": True, "S5": None})

    def test_described_adds_up(self):
        r, d = self.r, self.r["described"]
        self.assertEqual(sum(d["home"].values()), r["sampled"])
        self.assertEqual(d["home"]["ok"], r["homes_ok"])
        self.assertEqual(sum(d["page_status"].values()), r["sampled"])
        self.assertEqual(d["page_status"][""], r["sampled"] - r["homes_ok"])
        self.assertEqual(d["page_status"]["ok"], r["pages_ok"])
        self.assertEqual(sum(d["page_rank"].values()), r["pages_ok"])
        self.assertEqual(sum(d["versions"].values()), r["pages_ok"])
        self.assertEqual(sum(d["findings"].values()), r["pages_ok"])
        self.assertEqual(sum(d["overlay_on_home"].values()), r["homes_ok"])
        self.assertEqual(sum(x["pages"] for x in d["by_kind"].values()), r["pages_ok"])
        self.assertEqual(sum(x["only_2.0"] for x in d["by_kind"].values()),
                         r["measures"]["S1_only_2.0_of_versioned"][0])
        self.assertEqual(sum(x["stock"] for x in d["by_kind"].values()),
                         r["measures"]["S2_stock_of_pages"][0])


class TableTests(unittest.TestCase):
    """The per-site table is the run's table: it gives the graded result and every figure."""

    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(text("result.json"))
        cls.rows = typed(table("rows.csv"))
        cls.pages = [x for x in cls.rows if x["page_status"] == "ok"]

    def test_columns_and_rows(self):
        self.assertEqual(list(table("rows.csv")[0]), sp.COLUMNS)
        self.assertEqual(len(self.rows), self.r["sampled"])
        self.assertEqual(len({x["qid"] for x in self.rows}), self.r["sampled"])

    def test_table_regrades_to_the_saved_result(self):
        measures, preds = sp.grade(self.rows)
        self.assertEqual(json.loads(json.dumps(measures)), self.r["measures"])
        self.assertEqual(preds, self.r["predictions"])
        self.assertEqual(json.loads(json.dumps(sp.described(self.rows))), self.r["described"])

    def test_cohort_files(self):
        eligible = table("eligible.csv")
        cohort = table("cohort.csv")
        self.assertEqual(list(eligible[0]), sp.COHORT_COLUMNS)
        self.assertEqual(len(eligible), self.r["eligible"])
        self.assertEqual(len(cohort), self.r["sampled"])
        picked = sp.sample(eligible)
        self.assertEqual(sorted(x["qid"] for x in picked), sorted(x["qid"] for x in cohort))
        self.assertEqual(sorted(x["qid"] for x in cohort), sorted(x["qid"] for x in self.rows))

    def test_no_named_officials(self):
        for x in self.rows:
            self.assertIsNone(TITLE_RE.search(x["version_snippet"]), x["qid"])
            self.assertIsNone(TITLE_RE.search(x["date_snippet"]), x["qid"])

    def test_only_one_row_withheld(self):
        for name, fields in WITHHELD_FIELDS.items():
            rows = table(name)
            hits = [(x["qid"], k) for x in rows for k, v in x.items() if WITHHELD in (v or "")]
            self.assertEqual(hits, [(WITHHELD_QID, k) for k in fields], name)
            row = [x for x in rows if x["qid"] == WITHHELD_QID]
            self.assertEqual(len(row), 1, name)
            self.assertTrue(row[0]["state"] and row[0]["population"], name)


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(text("result.json"))
        cls.md = text("SMALL-PAGES-RESULT.md")
        cls.flat = re.sub(r"\s+", " ", cls.md)
        cls.rows = typed(table("rows.csv"))
        cls.pages = [x for x in cls.rows if x["page_status"] == "ok"]

    def test_in_short(self):
        r, m, md = self.r, self.r["measures"], self.md
        k1, n1 = m["S1_only_2.0_of_versioned"][:2]
        k2, n2 = m["S2_stock_of_pages"][:2]
        k3, n3 = m["S3_title2_of_pages"][:2]
        k4, n4 = m["S4_linked_of_homes"][:2]
        n5 = m["S5_2027_without_2028_of_dated"][1]
        self.assertIn("- {:,} accessibility pages were read, from the {:,} home pages that could be "
                      "read (of {:,} sampled governments of 10,000 to 49,999 people).".format(
                          r["pages_ok"], r["homes_ok"], r["sampled"]), md)
        self.assertIn("- {} of the {:,} name a WCAG 2.x version ({}%).".format(
            n1, r["pages_ok"], pct(n1, r["pages_ok"])), md)
        self.assertIn("- Of those {}, {} name WCAG 2.0 and no later version ({}%, 95% CI {}): below "
                      "the WCAG 2.1 Level AA that the ADA Title II rule adopts. In the 50,000+ "
                      "census it was 283 of 508 (55.71%).".format(
                          n1, k1, pct(k1, n1), ci(m["S1_only_2.0_of_versioned"][3])), md)
        self.assertIn("- {} of the {:,} pages ({}%) carry the stock sentence".format(
            k2, n2, pct(k2, n2)), md)
        self.assertIn("- Only {} of the {:,} name Title II ({}%), and only {} give any of the three "
                      "compliance dates.".format(k3, n3, pct(k3, n3), n5), md)
        self.assertIn("- {:,} of the {:,} home pages ({}%) link to a same-site accessibility or ADA "
                      "page, against 815 of 1,195 (68.2%) in the 50,000+ census.".format(
                          k4, n4, pct(k4, n4)), md)
        self.assertIn("**All 4 graded predictions hold; S5 had too few dated pages to grade.**", md)
        graded = [v for v in r["predictions"].values() if v is not None]
        self.assertEqual((len(graded), sum(graded)), (4, 4))

    def test_gates(self):
        r, md = self.r, self.md
        self.assertIn("at the job's first check; the job's 18 offline tests passed before the "
                      "crawl.", md)
        self.assertIn("- C1: {:,} governments were eligible after leaving out the {:,} of the "
                      "50,000+ cohort and their websites (1,500 to 9,000 needed); the first {:,} "
                      "in the pre-registered hash order were read.".format(
                          r["eligible"], r["big_cohort_rows"], r["sampled"]), md)
        for name, digest in RUN_SHA256.items():
            self.assertIn("%s %s" % (name, digest), md)

    def test_predictions(self):
        m, md = self.r["measures"], self.md
        s1, s2, s3, s4, s5 = (m[k] for k in sorted(m))
        self.assertIn("- **S1: holds.** %d of %d versioned pages name only WCAG 2.0 (%s%%, 95%% CI "
                      "%s); at least 55.71%% was predicted." % (s1[0], s1[1], pct(*s1[:2]),
                                                               ci(s1[3])), md)
        self.assertIn("- **S2: holds.** {} of {:,} pages carry the stock sentence ({}%, 95% CI {}); "
                      "at least 34.65% was predicted.".format(s2[0], s2[1], pct(*s2[:2]),
                                                             ci(s2[3])), md)
        self.assertIn("- **S3: holds.** {} of {:,} pages name Title II ({}%, 95% CI {}); at most "
                      "22.15% was predicted.".format(s3[0], s3[1], pct(*s3[:2]), ci(s3[3])), md)
        self.assertIn("- **S4: holds.** {:,} of {:,} home pages have a same-site link the rules "
                      "pick as an accessibility page ({}%, 95% CI {}); below 68.2% was predicted."
                      .format(s4[0], s4[1], pct(*s4[:2]), ci(s4[3])), md)
        self.assertEqual(s5[0], 1)
        self.assertIn("- **S5: not graded.** Only %d pages give April 24, 2026, April 26, 2027 or "
                      "April 26, 2028 (at least %d needed); %d of the %d gives April 26, 2027 "
                      "without April 26, 2028." % (s5[1], sp.MIN_DATED, s5[0], s5[1]), md)

    def test_stock_measured_the_census_way(self):
        k = sum(1 for x in self.pages if STOCK in x["version_snippet"])
        n = len(self.pages)
        self.assertGreaterEqual(k / n, sp.S2_MIN_STOCK)
        self.assertIn("Counted the census's way, {} of the {:,} pages carry it ({}%), still well "
                      "above 34.65%, so S2 holds either way.".format(k, n, pct(k, n)), self.md)

    def test_versions(self):
        d, md, pages = self.r["described"], self.md, self.pages
        v = d["versions"]
        self.assertEqual(set(v), {"", "2.0", "2.1", "2.2", "2.0+2.1", "2.1+2.2", "2.0+2.2"})
        self.assertIn("- Every combination of versions named: none %d, only 2.0 %d, only 2.1 %d, "
                      "only 2.2 %d, 2.0 and 2.1 %d, 2.1 and 2.2 %d, 2.0 and 2.2 %d." % (
                          v[""], v["2.0"], v["2.1"], v["2.2"], v["2.0+2.1"], v["2.1+2.2"],
                          v["2.0+2.2"]), md)
        high = {h: sum(1 for x in pages if x["highest"] == h) for h in ("2.0", "2.1", "2.2")}
        self.assertIn("- Highest version named: 2.0 on %d pages, 2.1 on %d and 2.2 on %d."
                      % (high["2.0"], high["2.1"], high["2.2"]), md)
        n = len(pages)
        self.assertIn("- {} of the {:,} mention WCAG at all ({}%) and {} name Section 508 ({}%)."
                      .format(d["wcag_any"], n, pct(d["wcag_any"], n), d["section508"],
                              pct(d["section508"], n)), md)

    def test_stock_sentence(self):
        md, pages = self.md, self.pages
        only20 = [x for x in pages if x["highest"] == "2.0"]
        k = sum(1 for x in only20 if x["stock"])
        self.assertIn("- %d of the %d pages that name only WCAG 2.0 (%s%%) carry the stock "
                      "sentence." % (k, len(only20), pct(k, len(only20))), md)
        stock = [x for x in pages if x["stock"]]
        rest = [x for x in pages if x["highest"] and not x["stock"]]
        hi = {h: sum(1 for x in rest if x["highest"] == h) for h in ("2.0", "2.1", "2.2")}
        self.assertIn("- Leaving the %d stock-sentence pages out, %d of the other %d versioned "
                      "pages name only WCAG 2.0 (%s%%); %d name 2.1 as their highest version and %d "
                      "name 2.2." % (len(stock), hi["2.0"], len(rest), pct(hi["2.0"], len(rest)),
                                     hi["2.1"], hi["2.2"]), md)
        self.assertTrue(hi["2.1"] > hi["2.0"] > 0)
        bare = [x for x in stock if not x["highest"]]
        self.assertIn("- %d pages carry the stock sentence but name no WCAG version by the "
                      "census's rules." % len(bare), md)
        names = {x["name"] for x in bare}
        self.assertTrue({"Neosho", "Rahway", "Bond County"} <= names)
        self.assertIn("This was found after grading and is not pre-registered.", md)

    def test_by_kind(self):
        b = self.r["described"]["by_kind"]
        c, co, t = b["city"], b["county"], b["town"]
        self.assertIn("- By kind: cities %d of %d versioned pages name only 2.0 (%s%%), counties %d "
                      "of %d (%s%%), towns %d of %d (%s%%)." % (
                          c["only_2.0"], c["versioned"], pct(c["only_2.0"], c["versioned"]),
                          co["only_2.0"], co["versioned"], pct(co["only_2.0"], co["versioned"]),
                          t["only_2.0"], t["versioned"], pct(t["only_2.0"], t["versioned"])),
                      self.md)

    def test_dates(self):
        d, md, pages = self.r["described"], self.md, self.pages
        self.assertEqual((d["date_2026_04_24"], d["date_2027_04_26"], d["date_2028_04_26"]),
                         (0, 1, 2))
        self.assertIn("- Dates: no page gives April 24, 2026", md)
        new = [x for x in pages if x["new_date"]]
        self.assertEqual([x["name"] for x in new], ["Lebanon"])
        self.assertIn("compliance date for smaller local governments", new[0]["date_snippet"])
        self.assertIn("Small Entity Compliance Guide", new[0]["date_snippet"])
        self.assertIn("\"the April 26, 2027 compliance date for smaller local governments\"", md)
        late = sorted(x["name"] for x in pages if x["date_2028"])
        self.assertEqual(late, ["Archuleta County", "Troy"])
        self.assertTrue(all(x["title2"] for x in pages if x["date_2028"]))
        self.assertIn("Two pages (Archuleta County, Colorado and Troy, Ohio) name Title II and give "
                      "April 26, 2028.", md)

    def test_how_pages_were_found(self):
        r, d, md = self.r, self.r["described"], self.md
        h = d["home"]
        other = sum(c for k, c in h.items() if k.startswith("http_") and k not in ("http_0",
                                                                                   "http_403"))
        self.assertEqual(h["ok"] + h["robots"] + h["http_0"] + h["http_403"] + other, r["sampled"])
        self.assertIn("- Home pages: {:,} read; {} refused by robots.txt; {} gave no answer "
                      "(timeouts, DNS or TLS errors); {} answered HTTP 403; {} other HTTP errors."
                      .format(h["ok"], h["robots"], h["http_0"], h["http_403"], other), md)
        linked = r["measures"]["S4_linked_of_homes"][0]
        self.assertIn("- Of the {:,}, {} had no same-site link to an accessibility or ADA page; of "
                      "the {:,} with one, {} could not be read.".format(
                          r["homes_ok"], d["page_status"]["no_link"], linked,
                          linked - r["pages_ok"]), md)
        self.assertEqual(r["homes_ok"] - d["page_status"]["no_link"], linked)
        pr = d["page_rank"]
        self.assertEqual(set(pr), {"0", "1", "3"})
        self.assertIn("- The {:,} pages were picked by their URL path ({}), their link text ({}) or "
                      "an \"ADA\" link ({}).".format(r["pages_ok"], pr["0"], pr["1"], pr["3"]), md)
        o = d["overlay_on_home"]
        homes = r["homes_ok"]
        with_any = homes - o[""]
        each = {key: sum(c for combo, c in o.items() if key in combo.split("+"))
                for key, _ in OVERLAY_NAMES}
        self.assertEqual(set(x for combo in o if combo for x in combo.split("+")), set(each))
        self.assertEqual(max(len(combo.split("+")) for combo in o), 2)
        self.assertIn("- {} of the {:,} home pages ({}%) carry code or links of an accessibility "
                      "overlay: {} (some carry two).".format(
                          with_any, homes, pct(with_any, homes),
                          ", ".join(("%s on %d" if i < len(OVERLAY_NAMES) - 1 else
                                     "and %s on %d") % (name, each[key])
                                    for i, (key, name) in enumerate(OVERLAY_NAMES))
                          .replace(", and ", " and ")), md)

    def test_withheld_row_is_explained(self):
        row = [x for x in self.rows if x["qid"] == WITHHELD_QID][0]
        self.assertIn("- One withheld row: in all three tables, the name, website and page URL of "
                      "Wikidata item %s (a Connecticut town of %s people) read `%s`"
                      % (WITHHELD_QID, "{:,}".format(int(row["population"])), WITHHELD), self.md)
        self.assertEqual((row["state"], row["kind"]), ("Connecticut", "town"))
        self.assertIn("unchanged except for one town's name and links (see Files)", self.md)

    def test_wording(self):
        md = self.md
        self.assertIn("not yet checked by a person", self.flat)
        self.assertIn("Nothing here says any government's website is or is not accessible.", md)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", md, re.I), [])
        self.assertNotIn("MIT", md)
        self.assertNotIn("@", md)
        self.assertNotIn("will be added", md)


if __name__ == "__main__":
    unittest.main()
