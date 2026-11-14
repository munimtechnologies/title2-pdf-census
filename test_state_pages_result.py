# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered state-pages result from its saved tables.

Reads results/state-pages/ (rows.csv, frame.csv, result.json and result.txt: the output of sealed
job state-pages-v1, unchanged). It checks that the three pinned scripts here are the ones that ran,
rebuilds the cohort from frame.csv with state_pages.py 0.1.0, re-grades every measure, gate,
prediction and described count from rows.csv, and checks the figures in
results/state-pages/STATE-PAGES-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_state_pages_result.py
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
import state_pages as st  # noqa: E402

RES = os.path.join(ROOT, "results", "state-pages")
NOTE = os.path.join(RES, "STATE-PAGES-RESULT.md")
ROWS = os.path.join(RES, "rows.csv")
FRAME = os.path.join(RES, "frame.csv")
RESULT = os.path.join(RES, "result.json")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED = {"ST1": None, "ST2": None, "ST3": None, "ST4": None, "ST5": False}
NJ_KEY = "nj.gov/nj/accessibility.shtml"
FL_KEY = "flsenate.gov/about/accessibility"


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
    """k of total as a percentage with two decimals, e.g. 165, 644 -> '25.62'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def load_all():
    result = load_json(RESULT)
    header, raw = load_csv(ROWS)
    return result, header, st.typed(raw)


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.header, cls.rows = load_all()
        cls.frame_header, cls.frame = load_csv(FRAME)

    def test_version_status_gates_predictions(self):
        r = self.result
        self.assertEqual((r["version"], st.__version__), ("0.1.0", "0.1.0"))
        self.assertEqual(r["status"], "graded")
        self.assertEqual(r["gates"], {"P0_prereg_public": True, "C1_frame": True})
        self.assertEqual(r["prereg_attempts"], 1)
        self.assertEqual(r["predictions"], EXPECTED)

    def test_pinned_files_are_the_ones_that_ran(self):
        files = self.result["files"]
        self.assertEqual(set(files), set(st.PINNED))
        for name, want in files.items():
            with open(os.path.join(ROOT, name), "rb") as fh:
                self.assertIn(want, shas(fh.read()), name)

    def test_file_sizes(self):
        for path in (ROWS, FRAME, RESULT, NOTE):
            with open(path, "rb") as fh:
                self.assertLess(len(fh.read()), LIMIT, path)

    def test_frame_rebuilds_the_cohort(self):
        r, f = self.result, self.result["frame"]
        self.assertEqual(self.frame_header, st.FRAME_COLUMNS)
        self.assertEqual(self.header, st.COLUMNS)
        domains = [row["domain"] for row in self.frame]
        self.assertEqual(domains, sorted(set(domains)))
        self.assertEqual((len(self.frame), f["eligible"], r["eligible"]), (1489, 1489, 1489))
        self.assertEqual(f["types"][st.FRAME_TYPE], f["eligible"])
        self.assertEqual(f["dropped"], 0)
        self.assertTrue(st.MIN_COHORT <= len(self.frame) <= st.MAX_COHORT)
        for row in self.frame:
            self.assertEqual(row["kind"], st.kind_of(row["organization"], row["suborganization"]),
                             row["domain"])
        cohort = st.sample(self.frame)
        self.assertEqual(len(cohort), r["sampled"])
        by_domain = {row["domain"]: row for row in self.rows}
        self.assertEqual(len(by_domain), len(self.rows))
        self.assertEqual(set(by_domain), {row["domain"] for row in cohort})
        for row in self.frame:
            for c in st.FRAME_COLUMNS:
                self.assertEqual(by_domain[row["domain"]][c], row[c], (row["domain"], c))

    def test_regrade_measures_and_predictions(self):
        measures, preds = st.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED)
        self.assertEqual((st.ST1_MAX_ONLY_20, st.ST3_MAX_TITLE2, st.ST4_MAX_STOCK,
                          st.ST5_MIN_LINKED), (0.40, 0.2215, 0.05, 0.70))
        self.assertEqual((st.MIN_VERSIONED, st.MIN_PAGES, st.MIN_HOMES), (100, 200, 500))

    def test_described_counts(self):
        self.assertEqual(norm(st.described(self.rows)), self.result["described"])
        self.assertEqual(self.result["homes_ok"],
                         sum(1 for row in self.rows if row["home"] == "ok"))
        self.assertEqual(self.result["pages_ok"],
                         sum(1 for row in self.rows if row["page_status"] == "ok"))

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), st.result_text(self.result) + "\n")

    def test_no_blocked_word(self):
        for path in (ROWS, FRAME, RESULT, NOTE):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(st.GUARD_RE.search(fh.read()), path)


class NoteTests(unittest.TestCase):
    """The figures in STATE-PAGES-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result, _, cls.rows = load_all()
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        cls.pages = st.distinct_pages(cls.rows)
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def share(self, key):
        s = self.m[key]
        return s[0], s[1], pct(s[0], s[1])

    def test_headline_st5(self):
        c = self.result["crawl"]
        self.has("the %s domains were read from %s to %s UTC on %s."
                 % (n(len(self.rows)), c["started_utc"][11:19], c["finished_utc"][11:19],
                    c["started_utc"][:10]))
        k, total, p = self.share("ST5_linked_of_homes")
        self.assertEqual(pct(815, 1195), "68.20")
        self.has("Only %d of the %d home sites (%s%%) link to an accessibility page on the same "
                 "site, far below the predicted 70%% and below cities and counties of 50,000 or "
                 "more (815 of 1,195, 68.20%%)." % (k, total, p))
        self.has("| linked | %d of %d (%s%%) | no |" % (k, total, p))

    def test_offsite(self):
        ok = [r for r in self.rows if r["home"] == "ok"]
        nolink = [r for r in ok if int(r["candidates"] or 0) == 0]
        off = [r for r in nolink if int(r["offsite_links"] or 0) > 0]
        self.assertEqual(len(nolink), self.d["page_status"]["no_link"])
        anywhere = len(ok) - len(nolink) + len(off)
        self.has("%d of the %d home pages with no same-site link do link to an accessibility page "
                 "on another site" % (len(off), len(nolink)))
        self.has("%d of the %d domains that served a home page (%s%%) link to an accessibility "
                 "page somewhere." % (anywhere, len(ok), pct(anywhere, len(ok))))
        self.has("%d domains whose home page has no same-site link point to an accessibility page "
                 "on another domain" % len(off))

    def test_no_dates(self):
        d = self.d
        self.assertEqual((d["date_2026_04_24"], d["date_2027_04_26"], d["date_2028_04_26"]),
                         (0, 0, 0))
        self.assertFalse(any(p["old_date"] or p["new_date"] or p["date_2028"] for p in self.pages))
        t2 = sum(1 for p in self.pages if p["title2"])
        self.has("**None of the %d accessibility pages read gives April 24, 2026, April 26, 2027 or "
                 "April 26, 2028.** %d of them name Title II, but none states a compliance date."
                 % (len(self.pages), t2))

    def test_new_jersey_and_florida(self):
        ok = [r for r in self.rows if r["page_status"] == "ok"]
        nj = [r for r in ok if st.page_key(r) == NJ_KEY]
        self.assertEqual(len(nj), 15)
        self.assertTrue(all(r["state"] == "NJ" and r["highest"] == "2.0"
                            and r["versions"] == "2.0" for r in nj))
        self.has("names WCAG 2.0 as its only version, and %d of the registry's New Jersey domains "
                 "lead to it." % len(nj))
        fl = [r for r in ok if st.page_key(r) == FL_KEY]
        self.assertTrue(fl)
        self.assertTrue(all(r["versions"] == "2.0" and r["kind"] == "legislature" for r in fl))
        self.has("The Florida Senate's page (`flsenate.gov/About/Accessibility`) also names only "
                 "WCAG 2.0.")
        keys = {st.page_key(p) for p in self.pages if p["highest"] == "2.0"}
        self.assertTrue({NJ_KEY, FL_KEY} <= keys)

    def test_frame_and_gates(self):
        f = self.result["frame"]
        self.has("CISA's .gov registry list (`current-full.csv`, %s bytes, SHA-256 `%s`, read %s) "
                 "has %s rows; %s of them are state or territory domains, and %d rows were dropped "
                 "by the publishing tool's blocked word."
                 % (n(f["bytes"]), f["sha256"][:12], f["retrieved_utc"][:10],
                    n(f["source_rows"]), n(f["eligible"]), f["dropped"]))
        self.has("P0 held (the plan and the three pinned scripts were on main at the first try); "
                 "C1 held (%s eligible domains, within %s to %s)."
                 % (n(f["eligible"]), n(st.MIN_COHORT), n(st.MAX_COHORT)))
        versioned = self.m["ST1_only_2.0_of_versioned"][1]
        pages = self.m["ST3_title2_of_pages"][1]
        homes = self.m["ST5_linked_of_homes"][1]
        self.assertLess(versioned, st.MIN_VERSIONED)
        self.assertLess(pages, st.MIN_PAGES)
        self.assertGreaterEqual(homes, st.MIN_HOMES)
        self.has("There was enough data for ST5 (%d home sites, at least %d), but not for ST1 and "
                 "ST2 (%d versioned pages, at least %d) or ST3 and ST4 (%d pages, at least %d)."
                 % (homes, st.MIN_HOMES, versioned, st.MIN_VERSIONED, pages, st.MIN_PAGES))

    def test_prediction_table(self):
        for key in ("ST1_only_2.0_of_versioned", "ST3_title2_of_pages", "ST4_stock_of_pages"):
            k, total, p = self.share(key)
            self.has("| %s of %s (%s%%) | not graded |" % (n(k), n(total), p))
        hi = self.m["ST2_highest_counts"]
        self.has("| 2.0: %d, 2.1: %d, 2.2: %d | not graded |" % (hi["2.0"], hi["2.1"], hi["2.2"]))

    def test_reach(self):
        d, h = self.d, self.d["home"]
        ok = self.result["homes_ok"]
        rest = len(self.rows) - ok - h["http_0"] - h["robots"] - h["http_403"] - h["http_404"]
        self.assertEqual(h["crash"], 1)
        self.has("%d of the %s domains served a home page (%d distinct home sites). %d gave no "
                 "answer at all, %d refused the reader through robots.txt, %d answered 403 and %d "
                 "answered 404; the other %d answered with another status or with something "
                 "other than HTML, or crashed the reader (one site,"
                 % (ok, n(len(self.rows)), d["distinct_home_hosts"], h["http_0"], h["robots"],
                    h["http_403"], h["http_404"], rest))
        self.has("On %d of the %d home pages the reader found no link to an accessibility page by "
                 "the census's link rules. %d domains led to a page that was read: %d distinct "
                 "pages holding %d distinct texts."
                 % (d["page_status"]["no_link"], ok, d["domain_pages_ok"], d["distinct_pages"],
                    d["distinct_texts"]))

    def test_what_the_pages_say(self):
        d = self.d
        stock = self.m["ST4_stock_of_pages"][0]
        self.has("%d of the %d pages name WCAG at all, %d name Section 508 and %d give an email "
                 "address or phone number."
                 % (d["wcag_any"], d["distinct_pages"], d["section508"], d["contact"]))
        self.has("%d pages (%s%%) carry the vendor stock sentence"
                 % (stock, pct(stock, d["distinct_pages"])))

    def test_overlays(self):
        ov = self.d["overlay_on_home"]
        self.assertEqual({k for k in ov if k},
                         {"accessibe", "audioeye", "equalweb", "recite", "userway"})
        total = sum(v for k, v in ov.items() if k)
        homes = self.d["distinct_home_hosts"]
        self.has("%d of the %d home sites (%s%%) load an overlay script: accessiBe on %d, UserWay on "
                 "%d, Recite on %d, AudioEye on %d and EqualWeb on %d."
                 % (total, homes, pct(total, homes), ov["accessibe"], ov["userway"],
                    ov["recite"], ov["audioeye"], ov["equalweb"]))

    def test_by_kind(self):
        kinds = self.d["by_kind"]
        domains = {}
        for r in self.rows:
            domains[r["kind"]] = domains.get(r["kind"], 0) + 1
        self.assertEqual(set(kinds), set(domains))
        for k in sorted(kinds):
            v = kinds[k]
            self.has("| %s | %d | %d | %d | %d | %d |"
                     % (k, domains[k], v["pages"], v["versioned"], v["only_2.0"], v["title2"]))

    def test_comparison(self):
        for key in ("ST5_linked_of_homes", "ST1_only_2.0_of_versioned", "ST3_title2_of_pages",
                    "ST4_stock_of_pages"):
            k, total, p = self.share(key)
            self.has("| %s of %s (%s%%) |" % (n(k), n(total), p))
        for k, total, p in ((815, 1195, "68.20"), (283, 508, "55.71"), (179, 808, "22.15"),
                            (280, 808, "34.65")):
            self.assertEqual(pct(k, total), p)
            self.has("| %s of %s (%s%%) |" % (n(k), n(total), p))


if __name__ == "__main__":
    unittest.main()
