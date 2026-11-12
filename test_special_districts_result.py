# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered special-districts result from its saved tables.

Reads results/special-districts/ (rows.csv, frame.csv, result.json and result.txt: the output of
sealed job special-districts-v1, unchanged). It checks that the four scripts here are the ones
that ran, rebuilds the cohort from frame.csv with the pinned special_districts.py 0.1.0,
re-grades every measure, gate, prediction and described count from rows.csv, and checks every
figure in results/special-districts/SPECIAL-DISTRICTS-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_special_districts_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import json
import os
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import special_districts as sd  # noqa: E402

sp = sd.sp
RES = os.path.join(ROOT, "results", "special-districts")
NOTE = os.path.join(RES, "SPECIAL-DISTRICTS-RESULT.md")
ROWS = os.path.join(RES, "rows.csv")
FRAME = os.path.join(RES, "frame.csv")
RESULT = os.path.join(RES, "result.json")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED = {"SD1": False, "SD2": True, "SD3": True, "SD4": True, "SD5": None}
SFW_URL = "https://sfwbor.gov/accessibility_statement/index.php"
BAY_URL = "https://www.cityofbayvillage.gov/153/Accessibility"
LAST_UPDATED = "Last updated: April 24, 2026"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def shas(data):
    return (sha(data), sha(data.replace(b"\r\n", b"\n")))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def norm(x):
    """The value as it reads back from result.json."""
    return json.loads(json.dumps(x))


def n(k):
    return format(k, ",")


def pct(k, total):
    """k of total as a percentage with two decimals, e.g. 345, 873 -> '39.52'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def load_all():
    result = load_json(RESULT)
    header, raw = load_csv(ROWS)
    return result, header, sp.typed(raw)


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.header, cls.rows = load_all()
        cls.frame_header, cls.frame = load_csv(FRAME)

    def test_version_status_gates_predictions(self):
        r = self.result
        self.assertEqual((r["version"], sd.__version__), ("0.1.0", "0.1.0"))
        self.assertEqual(r["status"], "graded")
        self.assertEqual(r["gates"], {"P0_prereg_public": True, "C1_frame": True})
        self.assertEqual(r["prereg_attempts"], 1)
        self.assertEqual(r["predictions"], EXPECTED)

    def test_pinned_files_are_the_ones_that_ran(self):
        files = self.result["files"]
        self.assertEqual(set(files), set(sd.PINNED))
        for name, want in files.items():
            with open(os.path.join(ROOT, name), "rb") as fh:
                self.assertIn(want, shas(fh.read()), name)

    def test_file_sizes(self):
        for path in (ROWS, FRAME, RESULT, NOTE):
            with open(path, "rb") as fh:
                self.assertLess(len(fh.read()), LIMIT, path)

    def test_frame_rebuilds_the_cohort(self):
        r, f = self.result, self.result["frame"]
        self.assertEqual(self.frame_header, sd.FRAME_COLUMNS)
        self.assertEqual(self.header, sd.COLUMNS)
        domains = [row["domain"] for row in self.frame]
        self.assertEqual(domains, sorted(set(domains)))
        self.assertEqual((len(self.frame), f["eligible"], r["eligible"]), (1161, 1161, 1161))
        self.assertEqual(f["types"][sd.FRAME_TYPE], f["eligible"])
        self.assertEqual(f["dropped"], 0)
        self.assertTrue(sd.MIN_COHORT <= len(self.frame) <= sd.MAX_COHORT)
        for row in self.frame:
            self.assertEqual(row["kind"], sd.kind_of(row["organization"], row["suborganization"]),
                             row["domain"])
        cohort = sd.sample(self.frame)
        self.assertEqual(len(cohort), r["sampled"])
        by_domain = {row["domain"]: row for row in self.rows}
        self.assertEqual(len(by_domain), len(self.rows))
        self.assertEqual(set(by_domain), {row["domain"] for row in cohort})
        for row in self.frame:
            for c in sd.FRAME_COLUMNS:
                self.assertEqual(by_domain[row["domain"]][c], row[c], (row["domain"], c))

    def test_regrade_measures_and_predictions(self):
        measures, preds = sd.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED)
        self.assertEqual((sd.SD1_MIN_ONLY_20, sd.SD2_MAX_TITLE2, sd.SD3_MAX_2028,
                          sd.SD4_MAX_LINKED, sd.SD5_MAX_2028_OF_DATED),
                         (0.50, 0.15, 0.05, 0.60, 0.50))
        self.assertEqual((sd.MIN_VERSIONED, sd.MIN_PAGES, sd.MIN_HOMES, sd.MIN_DATED),
                         (100, 200, 400, 10))

    def test_described_counts(self):
        self.assertEqual(norm(sd.described(self.rows)), self.result["described"])
        self.assertEqual(self.result["homes_ok"],
                         sum(1 for row in self.rows if row["home"] == "ok"))
        self.assertEqual(self.result["pages_ok"],
                         sum(1 for row in self.rows if row["page_status"] == "ok"))

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), sd.result_text(self.result) + "\n")

    def test_no_blocked_word(self):
        for path in (ROWS, FRAME, RESULT, NOTE):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(sd.GUARD_RE.search(fh.read()), path)


class NoteTests(unittest.TestCase):
    """Every figure in SPECIAL-DISTRICTS-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result, _, cls.rows = load_all()
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        cls.pages = sp.distinct_pages(cls.rows)
        cls.dated = [p for p in cls.pages if sd.date_set(p) != "none"]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def share(self, key):
        s = self.m[key]
        return s[0], s[1], pct(s[0], s[1])

    def test_headline(self):
        c = self.result["crawl"]
        self.has("the %s domains were read from %s to %s UTC on %s."
                 % (n(len(self.rows)), c["started_utc"][11:19], c["finished_utc"][11:19],
                    c["started_utc"][:10]))
        self.has("**Three of the five predictions held (SD2, SD3, SD4); SD1 failed, and SD5 could "
                 "not be graded: only %d pages gave any of the three dates, and the plan needed "
                 "%d.**" % (len(self.dated), sd.MIN_DATED))
        self.has("**None of the %d accessibility pages read is a special district stating its own "
                 "compliance date.**" % len(self.pages))
        k, total, p = self.share("SD4_linked_of_homes")
        self.assertEqual(pct(815, 1195), "68.20")
        self.has("Only %d of the %d home sites (%s%%) link to an accessibility page on the same "
                 "site, fewer than for cities and counties of 50,000 or more (815 of 1,195, "
                 "68.20%%)" % (k, total, p))
        k, total, p = self.share("SD1_only_2.0_of_versioned")
        hi = self.m["highest_counts"]
        self.has("%d of the %d pages that name a WCAG version (%s%%) name WCAG 2.0 as the highest, "
                 "short of the predicted 50%%; %d name 2.1 and %d name 2.2."
                 % (k, total, p, hi["2.1"], hi["2.2"]))

    def test_the_two_dated_pages(self):
        self.assertEqual(sorted(p["page_url"] for p in self.dated), [SFW_URL, BAY_URL])
        sfw = [p for p in self.dated if p["page_url"] == SFW_URL][0]
        bay = [p for p in self.dated if p["page_url"] == BAY_URL][0]
        self.assertEqual((sfw["old_date"], sfw["new_date"], sfw["date_2028"]), (True, False, False))
        self.assertIn(LAST_UPDATED, sfw["date_snippet"])
        self.assertEqual((bay["old_date"], bay["new_date"], bay["date_2028"]), (False, False, True))
        self.assertNotEqual(bay["home_host"], bay["domain"])
        self.has("%s's statement (%s) says \"%s\"" % (sfw["organization"], sfw["domain"],
                                                       LAST_UPDATED))
        self.has("the one page with April 26, 2028 is the City of Bay Village's accessibility page "
                 "(%s), where the %s's domain leads." % (bay["home_host"], bay["organization"]))
        last = sum(1 for p in self.dated if LAST_UPDATED in p["date_snippet"])
        self.has("Here that is %d of the %d dated pages." % (last, len(self.dated)))

    def test_frame_and_gates(self):
        f = self.result["frame"]
        self.has("CISA's .gov registry list (`current-full.csv`, %s bytes, SHA-256 `%s`, read %s) "
                 "has %s rows; %s of them are special district domains, and %d rows were dropped "
                 "by the publishing tool's blocked word."
                 % (n(f["bytes"]), f["sha256"][:12], f["retrieved_utc"][:10],
                    n(f["source_rows"]), n(f["eligible"]), f["dropped"]))
        self.has("P0 held (the plan and the four pinned scripts were on main at the first try); "
                 "C1 held (%s eligible domains, within %s to %s)."
                 % (n(f["eligible"]), n(sd.MIN_COHORT), n(sd.MAX_COHORT)))
        versioned = self.m["SD1_only_2.0_of_versioned"][1]
        pages = self.m["SD2_title2_of_pages"][1]
        homes = self.m["SD4_linked_of_homes"][1]
        self.has("There was enough data for SD1 (%d versioned pages, at least %d), SD2 and SD3 (%d "
                 "pages, at least %d) and SD4 (%d home sites, at least %d), but not for SD5 (%d "
                 "dated pages, at least %d)."
                 % (versioned, sd.MIN_VERSIONED, pages, sd.MIN_PAGES, homes, sd.MIN_HOMES,
                    len(self.dated), sd.MIN_DATED))

    def test_prediction_table(self):
        for key, held in (("SD1_only_2.0_of_versioned", "no"), ("SD2_title2_of_pages", "yes"),
                          ("SD3_2028_of_pages", "yes"), ("SD4_linked_of_homes", "yes")):
            k, total, p = self.share(key)
            self.has("| %s of %s (%s%%) | %s |" % (n(k), n(total), p, held))
        s5 = self.m["SD5_2028_of_dated"]
        self.has("| %d of %d (fewer than %d dated pages) | not graded |"
                 % (s5[0], s5[1], sd.MIN_DATED))

    def test_reach(self):
        d, h = self.d, self.d["home"]
        ok = self.result["homes_ok"]
        rest = len(self.rows) - ok - h["http_0"] - h["robots"] - h["http_403"] - h["http_404"]
        self.has("%d of the %s domains served a home page (%d distinct home sites). %d gave no "
                 "answer at all, %d refused the reader through robots.txt, %d answered 403 and %d "
                 "answered 404; the other %d answered with another status or with something "
                 "other than HTML."
                 % (ok, n(len(self.rows)), d["distinct_home_hosts"], h["http_0"], h["robots"],
                    h["http_403"], h["http_404"], rest))
        self.has("On %d of the %d home pages the reader found no link to an accessibility page by "
                 "the census's link rules. %d domains led to a page that was read: %d distinct "
                 "pages holding %d distinct texts."
                 % (d["page_status"]["no_link"], ok, d["domain_pages_ok"], d["distinct_pages"],
                    d["distinct_texts"]))

    def test_what_the_pages_say(self):
        d = self.d
        self.has("%d of the %d pages name WCAG at all, %d name Section 508 and %d give an email "
                 "address or phone number."
                 % (d["wcag_any"], d["distinct_pages"], d["section508"], d["contact"]))
        self.has("%d pages (%s%%) carry the vendor stock sentence"
                 % (d["stock"], pct(d["stock"], d["distinct_pages"])))
        t2 = sorted(p["domain"] for p in self.pages if p["title2"])
        self.assertEqual(len(t2), self.m["SD2_title2_of_pages"][0])
        self.has("The %d pages that name Title II are on %s and %s."
                 % (len(t2), ", ".join(t2[:-1]), t2[-1]))

    def test_overlays(self):
        ov = self.d["overlay_on_home"]
        self.assertEqual({k for k in ov if k},
                         {"accessibe", "accessibe+userway", "audioeye", "equalweb", "recite",
                          "userway"})
        total = sum(v for k, v in ov.items() if k)
        homes = self.d["distinct_home_hosts"]

        def on(vendor):
            return sum(v for k, v in ov.items() if vendor in k.split("+"))
        self.has("%d of the %d home sites (%s%%) load an overlay script: UserWay on %d, AudioEye on "
                 "%d, accessiBe on %d, EqualWeb on %d and Recite on %d (%d load both accessiBe "
                 "and UserWay)."
                 % (total, homes, pct(total, homes), on("userway"), on("audioeye"),
                    on("accessibe"), on("equalweb"), on("recite"), ov["accessibe+userway"]))

    def test_by_kind(self):
        kinds, frame_kinds = self.d["by_kind"], self.d["frame_kinds"]
        self.assertEqual(set(kinds), set(frame_kinds))
        for k in sorted(kinds):
            v = kinds[k]
            self.has("| %s | %d | %d | %d | %d | %d |"
                     % (k, frame_kinds[k], v["pages"], v["versioned"], v["only_2.0"], v["title2"]))
        self.assertEqual(sum(frame_kinds.values()), len(self.rows))

    def test_comparison(self):
        for key in ("SD4_linked_of_homes", "SD1_only_2.0_of_versioned", "SD2_title2_of_pages"):
            k, total, p = self.share(key)
            self.has("| %s of %s (%s%%) |" % (n(k), n(total), p))
        d = self.d
        self.has("| %d of %d (%s%%) |" % (d["stock"], d["distinct_pages"],
                                          pct(d["stock"], d["distinct_pages"])))
        for k, total, p in ((815, 1195, "68.20"), (1053, 1942, "54.22"), (283, 508, "55.71"),
                            (638, 809, "78.86"), (179, 808, "22.15"), (94, 1042, "9.02"),
                            (280, 808, "34.65"), (698, 1042, "66.99")):
            self.assertEqual(pct(k, total), p)
            self.has("| %s of %s (%s%%) |" % (n(k), n(total), p))


if __name__ == "__main__":
    unittest.main()
