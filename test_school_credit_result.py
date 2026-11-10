# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered school-credit follow-up from its saved table.

Reads results/uk-schools/credit-followup/result.json, result.txt and hosts.csv (the output of
sealed job school-credit-v2, unchanged), re-grades every measure, prediction and described count
with the pinned school_credit.py 0.1.0 (unchanged; it imports school_stock.py 0.1.0 and
statement_template_check.py 0.3.0), and checks every figure in
results/uk-schools/CREDIT-FOLLOWUP-RESULT.md against the data. When school-stock's own tables
(results/uk-schools/hosts-part1..4.csv) are present, it also checks that the re-read covered
exactly the hosts behind school-stock's J1.

Standard library only: python -m unittest discover -p test_school_credit_result.py
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
import school_credit as sc  # noqa: E402
import school_stock as ss  # noqa: E402

UK = os.path.join(ROOT, "results", "uk-schools")
RES = os.path.join(UK, "credit-followup")
NOTE = os.path.join(UK, "CREDIT-FOLLOWUP-RESULT.md")
TABLE = os.path.join(RES, "hosts.csv")
STOCK_PARTS = [os.path.join(UK, "hosts-part%d.csv" % i) for i in (1, 2, 3, 4)]
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED_PREDICTIONS = {"K1": False, "K2": False, "K3": True, "L1": True}
J2_PCT = "43.78"                   # school-stock's J2 result (SCHOOL-STOCK-RESULT.md)


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
    """k of total as a percentage with two decimals, e.g. 272, 574 -> '47.39'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def typed(raw):
    return [dict(r, **{k: r[k] == "True" for k in sc.BOOLS}) for r in raw]


def load_rows():
    _, raw = load_csv(TABLE)
    return raw, typed(raw)


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.raw, cls.rows = load_rows()

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual(r["version"], sc.__version__)
        self.assertEqual(r["checker_version"], sc.CHECKER_VERSION)
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]), {"P0_registered", "P0_checker", "C0_published",
                                           "C1_hosts", "C2_within_21_days"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED_PREDICTIONS)

    def test_table_matches_result_json(self):
        t = self.result["table"]
        self.assertEqual(t["file"], "hosts.csv")
        with open(TABLE, "rb") as fh:
            data = fh.read()
        self.assertEqual(len(data), t["bytes"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), t["sha256"])
        self.assertLess(len(data), LIMIT)
        header, rows = load_csv(TABLE)
        self.assertEqual(header, sc.COLUMNS)
        self.assertEqual(len(rows), t["rows"])

    def test_pinned_scripts_are_the_ones_that_ran(self):
        for name in ("school_credit.py", "school_stock.py"):
            with open(os.path.join(ROOT, name), "rb") as fh:
                data = fh.read()
            self.assertIn(self.result["files"][name],
                          (hashlib.sha256(data).hexdigest(),
                           hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()), name)

    def test_one_row_per_host_in_host_order(self):
        hosts = [r["host"] for r in self.raw]
        self.assertEqual(len(hosts), self.result["frame_hosts"])
        self.assertEqual(len(set(hosts)), len(hosts))
        self.assertEqual(hosts, sorted(hosts))
        with open(TABLE, encoding="utf-8") as fh:
            self.assertIsNone(ss.GUARD_RE.search(fh.read()))

    def test_regrade_measures_and_predictions(self):
        measures, preds = sc.grade(self.rows, self.result["gates"])
        self.assertEqual(norm(measures), self.result["measures"])
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED_PREDICTIONS)

    def test_described_counts(self):
        self.assertEqual(norm(sc.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), sc.result_text(self.result) + "\n")

    def test_flags_only_on_read_pages(self):
        for r in self.rows:
            if r["status"] != "ok":
                for k in sc.CREDITS + ("family", "graded", "same_text"):
                    self.assertFalse(r[k], (r["host"], k))
                self.assertEqual(r["placeholder_ids"], "")

    @unittest.skipUnless(all(os.path.exists(p) for p in STOCK_PARTS),
                         "school-stock's tables are not in this folder")
    def test_frame_is_school_stock_j1(self):
        stock = []
        for p in STOCK_PARTS:
            stock.extend(load_csv(p)[1])
        j1 = {r["host"]: r for r in ss.typed(stock) if ss.flagged(r)}
        self.assertEqual(sorted(j1), [r["host"] for r in self.rows])
        for r in self.rows:
            s = j1[r["host"]]
            self.assertEqual(r["stock_template"], bool(s["juniper_template"]), r["host"])
            self.assertEqual(r["l1_group"], sc.l1_group(s), r["host"])
            self.assertEqual(r["stock_us_template"], sc.us_template(s), r["host"])


class NoteTests(unittest.TestCase):
    """Every figure in CREDIT-FOLLOWUP-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.rows = load_rows()
        cls.g = [r for r in cls.rows if r["graded"]]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def test_status_and_crawl_times(self):
        c = self.result["crawl"]
        self.has("(%s to %s UTC on %s)" % (c["started_utc"][11:16], c["finished_utc"][11:16],
                                            c["started_utc"][:10]))
        self.has("**Two of the four predictions held (K3, L1) and two failed (K1, K2).**")

    def test_headline(self):
        g, d = len(self.g), self.d
        fam = sum(1 for r in self.g if r["family"])
        gh = sum(1 for r in self.g if r["greenhouse"])
        fs = sum(1 for r in self.g if r["finalsite"])
        none = sum(1 for r in self.g if not any(r[k] for k in sc.CREDITS))
        one_company = [r for r in self.g if r["family"] + r["greenhouse"] + r["finalsite"] == 1]
        self.assertEqual(len(one_company) + none, g)  # no page credits two of the companies
        self.assertEqual((fam, gh, fs, none), (d["graded_family"], d["graded_greenhouse"],
                                               d["graded_finalsite"], d["graded_no_credit"]))
        self.has("**The %s unfinished school statements that could be read again credit three "
                 "website companies: Juniper Education's school-website brands on %d (%s%%), "
                 "Greenhouse School Websites on %d (%s%%) and Finalsite on %d (%s%%)**; %d (%s%%) "
                 "credit none of the five names searched."
                 % (n(g), fam, pct(fam, g), gh, pct(gh, g), fs, pct(fs, g), none, pct(none, g)))

    def test_reread(self):
        d, m = self.d, self.m
        self.assertEqual(d["not_graded_by_status"], {"http_0": m["frame_hosts"] - m["graded_hosts"]})
        self.assertEqual(d["ok_without_placeholder"], 0)
        self.has("%s of the %s hosts were read again and still carry a placeholder (the graded "
                 "set); %d did not answer at all, and no page that was read had lost its "
                 "placeholders." % (n(m["graded_hosts"]), n(m["frame_hosts"]),
                                    d["not_graded_by_status"]["http_0"]))

    def test_prediction_table(self):
        m = self.m
        self.assertEqual((sc.K1_MIN_FAMILY, sc.K2_MIN_MISSED, sc.K3_MIN_SAME, sc.L1_MIN_GREENHOUSE),
                         (0.90, 0.10, 0.90, 0.80))
        for key, held in (("K1_family", "no"), ("K2_missed_by_j2_pattern", "no"),
                          ("K3_unchanged_text", "yes"),
                          ("L1_greenhouse_of_three_field_group", "yes")):
            s = m[key]
            self.assertEqual(pct(s["k"], s["n"]), "%.2f" % s["pct"])
            self.has("| %s of %s (%s%%) | %s |" % (n(s["k"]), n(s["n"]), pct(s["k"], s["n"]), held))

    def test_k2_older_brands(self):
        d, c = self.d, self.d["credit_combinations"]
        self.assertEqual(c.get("juniper+e4education"), d["graded_e4education"])
        self.assertEqual(c.get("juniper+primarysite"), d["graded_primarysite"])
        self.has("Every page with an e4education credit (%d) or a PrimarySite credit (%d) also "
                 "carries the Juniper Websites credit" % (d["graded_e4education"],
                                                          d["graded_primarysite"]))
        self.has("school-stock's J2 (at least 80%% of placeholder hosts with the Juniper Websites "
                 "credit) failed at %s%%" % J2_PCT)

    def test_closing_sentence_split(self):
        t = [r for r in self.g if r["stock_template"]]
        fam = sum(1 for r in t if r["family"])
        gh = sum(1 for r in t if r["greenhouse"])
        self.assertEqual(fam + gh, len(t))
        self.assertFalse(any(r["family"] and r["greenhouse"] for r in t))
        self.has("Of the %d graded pages with the template's closing sentence, %d credit a Juniper "
                 "brand and %d credit Greenhouse School Websites; every one credits exactly one of "
                 "the two." % (len(t), fam, gh))
        lg = [r for r in self.g if r["l1_group"]]
        self.assertTrue(all(r["stock_template"] for r in lg))
        self.has("all %d graded pages that keep exactly GOV.UK's three sample fields" % len(lg))

    def test_without_sentence(self):
        rest = [r for r in self.g if not r["stock_template"]]
        fs = sum(1 for r in rest if r["finalsite"])
        fam = sum(1 for r in rest if r["family"])
        none = sum(1 for r in rest if not any(r[k] for k in sc.CREDITS))
        self.assertEqual(fs + fam + none, len(rest))
        us = [r for r in self.g if r["stock_us_template"]]
        self.assertTrue(all(r["finalsite"] for r in us))
        self.assertEqual(len(us), fs)
        self.has("Of the %d graded pages without the closing sentence, %d credit Finalsite, %d a "
                 "Juniper brand and %d none." % (len(rest), fs, fam, none))
        self.has("All %d graded pages that keep a placeholder of the 2017 US template credit "
                 "Finalsite" % len(us))

    def test_k3_changed(self):
        s, d = self.m["K3_unchanged_text"], self.d
        self.has("%s of the %s pages (%s%%) have the same text as in school-stock's read; %d "
                 "changed but still keep a placeholder." % (n(s["k"]), n(s["n"]),
                                                            pct(s["k"], s["n"]),
                                                            d["graded_text_changed"]))

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(ss.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
