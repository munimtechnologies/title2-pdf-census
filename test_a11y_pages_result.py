"""Tests for A11Y-PAGES-RESULT.md (no network). Apache-2.0.

Rebuilds the printed result from the saved result.json with a11y_pages 0.1.0, re-derives every
prediction from the saved measures with the pre-registered thresholds, and checks every figure
the note quotes. The run and the note were made by AI agents working for MV2; no person has
checked them yet.
"""

import hashlib
import json
import os
import re
import unittest

import a11y_pages as ap

HERE = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(HERE, "results", "a11y-pages")

# The sha256 printed in the sealed run (a11y-pages-v1).
RUN_SHA256 = {
    "a11y_pages.py": "b0b27c819b2d31b9d6e17fb207129b23aebe767e40e157678e37ad6851e200e0",
    "test_a11y_pages.py": "4d69bd9b04d88075a97f7b4639d09a4ba9cbdf9128b2ec8177609d8575f468ec",
}
OVERLAY_NAMES = (("audioeye", "AudioEye"), ("userway", "UserWay"), ("accessibe", "accessiBe"),
                 ("recite", "Recite Me"), ("equalweb", "EqualWeb"))


def text(name):
    with open(os.path.join(RESULT, name), "rb") as f:
        return f.read().decode("utf-8")


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
        self.assertEqual(self.r["script_sha256"], RUN_SHA256["a11y_pages.py"])
        self.assertEqual(self.r["version"], ap.__version__)

    def test_printed_result_rebuilds(self):
        self.assertEqual(ap.result_text(self.r), text("result.txt").rstrip("\n"))

    def test_status_and_gates(self):
        r = self.r
        self.assertEqual(r["status"], "graded")
        self.assertEqual(r["polls"], 1)
        self.assertEqual(r["gates"], {"P0_prereg_public": True, "A1_cohort": True,
                                      "A2_homes": True, "A3_pages": True})
        self.assertTrue(ap.MIN_COHORT <= r["cohort"] <= ap.MAX_COHORT)
        self.assertGreaterEqual(r["homes_ok"], ap.MIN_HOMES)
        self.assertGreaterEqual(r["pages_ok"], ap.MIN_PAGES)

    def test_measures_are_consistent(self):
        r, m, d = self.r, self.r["measures"], self.r["described"]
        k1, n1 = m["H1_only_2.0_of_versioned"][:2]
        hc = m["H2_highest_counts"]
        k3, n3 = m["H3_versioned_of_pages"][:2]
        big, small = m["H5_versioned_big"], m["H5_versioned_small"]
        self.assertEqual(n3, r["pages_ok"])
        self.assertEqual(k3, n1)
        self.assertEqual(sum(hc.values()), n1)
        self.assertEqual(hc["2.0"], k1)
        self.assertEqual(big[1] + small[1], n3)
        self.assertEqual(big[0] + small[0], k3)
        # The version combinations add up to the pages and to the highest-version counts.
        v = d["versions"]
        self.assertEqual(sum(v.values()), n3)
        self.assertEqual(n3 - v[""], k3)
        high = {"2.0": 0, "2.1": 0, "2.2": 0}
        for combo, c in v.items():
            if combo:
                high[max(combo.split("+"))] += c
        self.assertEqual(high, hc)
        self.assertEqual(v["2.0"], k1)
        for key in ("H1_only_2.0_of_versioned", "H3_versioned_of_pages", "H4_old_only_of_dated",
                    "H5_versioned_big", "H5_versioned_small"):
            self.assertEqual(ap.share(*m[key][:2]), m[key], key)
        self.assertEqual(sum(d["page_status"].values()), r["cohort"])
        self.assertEqual(sum(d["home"].values()), r["cohort"])
        self.assertEqual(d["page_status"][""], r["cohort"] - r["homes_ok"])
        self.assertEqual(sum(d["page_rank"].values()), n3)
        self.assertEqual(sum(d["overlay_on_home"].values()), r["homes_ok"])
        self.assertEqual(sum(x["pages"] for x in d["by_kind"].values()), n3)
        self.assertEqual(sum(x["versioned"] for x in d["by_kind"].values()), k3)
        self.assertEqual(sum(x["only_2.0"] for x in d["by_kind"].values()), k1)

    def test_predictions_follow_from_the_measures(self):
        m = self.r["measures"]
        k1, n1 = m["H1_only_2.0_of_versioned"][:2]
        hc = m["H2_highest_counts"]
        k3, n3 = m["H3_versioned_of_pages"][:2]
        k4, n4 = m["H4_old_only_of_dated"][:2]
        big, small = m["H5_versioned_big"], m["H5_versioned_small"]
        self.assertEqual((ap.H1_MIN_ONLY_20, ap.H3_MIN_VERSIONED, ap.H4_MIN_OLD_ONLY,
                          ap.H5_MIN_GAP, ap.MIN_VERSIONED, ap.MIN_DATED, ap.MIN_SIZE_GROUP,
                          ap.BIG), (0.15, 0.40, 0.30, 0.05, 200, 20, 80, 250000))
        self.assertGreaterEqual(n1, ap.MIN_VERSIONED)
        self.assertLess(n4, ap.MIN_DATED)
        self.assertTrue(big[1] >= ap.MIN_SIZE_GROUP and small[1] >= ap.MIN_SIZE_GROUP)
        expect = {"H1": k1 / n1 >= ap.H1_MIN_ONLY_20,
                  "H2": hc["2.1"] > hc["2.0"] and hc["2.1"] > hc["2.2"],
                  "H3": k3 / n3 >= ap.H3_MIN_VERSIONED,
                  "H4": None,
                  "H5": big[2] - small[2] >= ap.H5_MIN_GAP}
        self.assertEqual(self.r["predictions"], expect)
        self.assertEqual(expect, {"H1": True, "H2": False, "H3": True, "H4": None, "H5": False})


class NoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.loads(text("result.json"))
        cls.md = text("A11Y-PAGES-RESULT.md")
        cls.flat = re.sub(r"\s+", " ", cls.md)

    def test_in_short(self):
        r, m, md = self.r, self.r["measures"], self.md
        k1, n1 = m["H1_only_2.0_of_versioned"][:2]
        k3, n3 = m["H3_versioned_of_pages"][:2]
        hc = m["H2_highest_counts"]
        self.assertIn("- {} accessibility pages were read, from the {:,} home pages that could be "
                      "read (of {:,} sites).".format(n3, r["homes_ok"], r["cohort"]), md)
        self.assertIn("- %d of the %d name a WCAG 2.x version (%s%%)." % (k3, n3, pct(k3, n3)), md)
        self.assertIn("- Of those %d, %d name WCAG 2.0 and no later version (%s%%, 95%% CI %s): "
                      "below the 2.1 the rule adopts." % (n1, k1, pct(k1, n1),
                                                           ci(m["H1_only_2.0_of_versioned"][3])),
                      md)
        self.assertIn("- %d name 2.1 as their highest version and %d name 2.2."
                      % (hc["2.1"], hc["2.2"]), md)
        self.assertIn("**2 of the 4 graded predictions hold, including the main one (H1); H4 had "
                      "too few pages to grade.**", md)
        graded = [v for v in r["predictions"].values() if v is not None]
        self.assertEqual((len(graded), sum(graded)), (4, 2))

    def test_gates(self):
        r, md = self.r, self.md
        self.assertTrue(ap.COHORT_COMMIT.startswith("279e85e"))
        self.assertIn("A1: the cohort file (results/v0.2.2/cohort.csv at commit 279e85e) has "
                      "{:,} rows.".format(r["cohort"]), md)
        self.assertIn("A2: {:,} home pages were read (at least {} needed).".format(
            r["homes_ok"], ap.MIN_HOMES), md)
        self.assertIn("A3: %d accessibility pages were read (at least %d needed)."
                      % (r["pages_ok"], ap.MIN_PAGES), md)

    def test_predictions(self):
        m, md = self.r["measures"], self.md
        k1, n1 = m["H1_only_2.0_of_versioned"][:2]
        hc = m["H2_highest_counts"]
        k3, n3 = m["H3_versioned_of_pages"][:2]
        k4, n4 = m["H4_old_only_of_dated"][:2]
        big, small = m["H5_versioned_big"], m["H5_versioned_small"]
        self.assertIn("- **H1 (main): holds.** %d of %d versioned pages name only WCAG 2.0 (%s%%); "
                      "at least 15%% was predicted." % (k1, n1, pct(k1, n1)), md)
        self.assertIn("- **H2: fails.** The highest version named is 2.0 on %d pages, 2.1 on %d and "
                      "2.2 on %d; 2.1 was predicted to lead." % (hc["2.0"], hc["2.1"], hc["2.2"]),
                      md)
        self.assertIn("- **H3: holds.** %d of %d accessibility pages name a WCAG 2.x version (%s%%, "
                      "95%% CI %s); at least 40%% was predicted." % (
                          k3, n3, pct(k3, n3), ci(m["H3_versioned_of_pages"][3])), md)
        self.assertIn("- **H4: not graded.** Only %d pages give the old or the new compliance date "
                      "(at least %d needed); %d of the %d give the old date only." % (
                          n4, ap.MIN_DATED, k4, n4), md)
        gap = "%.1f" % (100 * (small[2] - big[2]))
        self.assertGreater(small[2], big[2])
        self.assertIn("- **H5: fails, the other way round.** %d of %d pages of governments of "
                      "250,000+ are versioned (%s%%, 95%% CI %s), against %d of %d for those of "
                      "50,000 to 249,999 (%s%%, 95%% CI %s): %s percentage points lower, where at "
                      "least 5 points higher was predicted." % (
                          big[0], big[1], pct(big[0], big[1]), ci(big[3]), small[0], small[1],
                          pct(small[0], small[1]), ci(small[3]), gap), md)

    def test_what_the_pages_say(self):
        d, md, n = self.r["described"], self.md, self.r["pages_ok"]
        v = d["versions"]
        self.assertEqual(set(v), {"", "2.0", "2.1", "2.2", "2.1+2.2", "2.0+2.1", "2.0+2.1+2.2"})
        self.assertIn("- Every combination of versions named: none %d, only 2.0 %d, only 2.1 %d, "
                      "only 2.2 %d, 2.1 and 2.2 %d, 2.0 and 2.1 %d, all three %d." % (
                          v[""], v["2.0"], v["2.1"], v["2.2"], v["2.1+2.2"], v["2.0+2.1"],
                          v["2.0+2.1+2.2"]), md)
        self.assertIn("- %d of the %d mention WCAG at all (%s%%), %d name Section 508 (%s%%) and %d "
                      "name Title II (%s%%)." % (d["wcag_any"], n, pct(d["wcag_any"], n),
                                                 d["section508"], pct(d["section508"], n),
                                                 d["title2"], pct(d["title2"], n)), md)
        self.assertIn("- %d pages name Title II but only WCAG 2.0." % d["title2_only_2.0"], md)
        self.assertEqual(d["both_dates"], 0)
        self.assertIn("- %d pages give the April 24, 2026 date that the April 2026 interim rule "
                      "replaced, %d give the new April 26, 2027 date, and none gives both."
                      % (d["old_date"], d["new_date"]), md)
        city, county = d["by_kind"]["city"], d["by_kind"]["county"]
        self.assertIn("- By kind: cities %d of %d versioned pages name only 2.0 (%s%%), counties %d "
                      "of %d (%s%%)." % (city["only_2.0"], city["versioned"],
                                         pct(city["only_2.0"], city["versioned"]),
                                         county["only_2.0"], county["versioned"],
                                         pct(county["only_2.0"], county["versioned"])), md)

    def test_how_pages_were_found(self):
        r, d, md = self.r, self.r["described"], self.md
        h = d["home"]
        other = sum(c for k, c in h.items() if k.startswith("http_") and k not in ("http_0",
                                                                                   "http_403"))
        self.assertEqual(h["ok"] + h["robots"] + h["http_0"] + h["http_403"] + other, r["cohort"])
        self.assertIn("- Home pages: {:,} read; {} refused by robots.txt; {} gave no answer "
                      "(timeouts, DNS or TLS errors); {} answered HTTP 403; {} other HTTP errors."
                      .format(h["ok"], h["robots"], h["http_0"], h["http_403"], other), md)
        self.assertIn("- Of the {:,}, {} had no same-site link to an accessibility or ADA page ({} "
                      "of them link only to other sites).".format(
                          r["homes_ok"], d["page_status"]["no_link"],
                          d["no_same_site_link_but_offsite"]), md)
        pr = d["page_rank"]
        self.assertEqual(set(pr), {"0", "1", "3"})
        self.assertIn("- The %d pages were picked by their URL path (%d), their link text (%d) or an "
                      "\"ADA\" link (%d)." % (r["pages_ok"], pr["0"], pr["1"], pr["3"]), md)
        o = d["overlay_on_home"]
        homes = r["homes_ok"]
        with_any = homes - o[""]
        each = {key: sum(c for combo, c in o.items() if key in combo.split("+"))
                for key, _ in OVERLAY_NAMES}
        self.assertEqual(set(x for combo in o if combo for x in combo.split("+")),
                         set(each))
        self.assertIn("- {} of the {:,} home pages ({}%) carry code or links of an accessibility "
                      "overlay: {} (some carry two or three).".format(
                          with_any, homes, pct(with_any, homes),
                          ", ".join(("%s on %d" if i < len(OVERLAY_NAMES) - 1 else
                                     "and %s on %d") % (name, each[key])
                                    for i, (key, name) in enumerate(OVERLAY_NAMES))
                          .replace(", and ", " and ")), md)

    def test_timing_hashes_and_wording(self):
        r, md = self.r, self.md
        self.assertIn("commit 34ea3e8", md)
        self.assertIn("at its first poll", md)
        self.assertIn("crawled from %s to %s." % (r["crawl_started_utc"], r["crawl_finished_utc"]),
                      md)
        for digest in RUN_SHA256.values():
            self.assertIn(digest, md)
        self.assertIn("their 17 tests passed", md)
        self.assertIn("not yet checked by a person", self.flat)
        self.assertEqual(re.findall(r"by\s+hand|by\s+eye|hand[- ]check", md, re.I), [])
        self.assertNotIn("MIT", md)
        self.assertNotIn("@", md)


if __name__ == "__main__":
    unittest.main()
