# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered school-stock result from its saved tables.

Reads results/uk-schools/result.json, result.txt and the four hosts tables (the run's output,
unchanged), re-grades every measure, gate, prediction and described count with the pinned
school_stock.py 0.1.0 (unchanged; it imports statement_template_check.py 0.3.0), and checks every
figure in results/uk-schools/SCHOOL-STOCK-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_school_stock_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import json
import os
import re
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import school_stock as ss  # noqa: E402

RES = os.path.join(ROOT, "results", "uk-schools")
NOTE = os.path.join(RES, "SCHOOL-STOCK-RESULT.md")
PARTS = [os.path.join(RES, "hosts-part%d.csv" % i) for i in (1, 2, 3, 4)]
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED_PREDICTIONS = {"J1": True, "J2": False, "J3": False, "J4": True}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GOV_THREE = "gov-uk/email_address;gov-uk/phone;gov-uk/number_of_days"
US_TEMPLATE_IDS = {"school/your_school", "school/your_domain", "school/fake_phone"}
US_DISTRICT_HOSTS = 1067           # district-stock: US school-district hosts with the 2017 template
US_HOST_PCT = "9.21"               # district-stock: 1,067 of 11,581 hosts
US_READ_PCT = "46.72"              # district-stock: 1,067 of 2,284 readable pages


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
    """k of total as a percentage with two decimals, e.g. 667, 23802 -> '2.80'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def ids(r):
    return [i for i in (r.get("placeholder_ids") or "").split(";") if i]


def load_rows():
    raw = []
    for p in PARTS:
        _, rows = load_csv(p)
        raw.extend(rows)
    return raw, ss.typed(raw)


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.raw, cls.rows = load_rows()

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual(r["version"], ss.__version__)
        self.assertEqual(r["checker_version"], ss.CHECKER_VERSION)
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]), {"P0_prereg", "P0_checker", "F1_frame", "G1_answered"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED_PREDICTIONS)
        f = r["frame"]
        self.assertEqual((f["rows"], f["hosts"], f["dropped"]), (ss.FRAME_ROWS, ss.FRAME_HOSTS, 0))
        self.assertTrue(all(f["parts_ok"].values()))

    def test_tables_match_result_json(self):
        tables = self.result["tables"]
        self.assertEqual([t["file"] for t in tables], [os.path.basename(p) for p in PARTS])
        for t, p in zip(tables, PARTS):
            with open(p, "rb") as fh:
                data = fh.read()
            self.assertEqual(len(data), t["bytes"], p)
            self.assertEqual(hashlib.sha256(data).hexdigest(), t["sha256"], p)
            self.assertLess(len(data), LIMIT, p)
            header, rows = load_csv(p)
            self.assertEqual(header, ss.COLUMNS, p)
            self.assertEqual(len(rows), t["rows"], p)

    def test_one_row_per_host_in_host_order(self):
        hosts = [r["host"] for r in self.raw]
        self.assertEqual(len(hosts), ss.FRAME_HOSTS)
        self.assertEqual(len(set(hosts)), len(hosts))
        self.assertEqual(hosts, sorted(hosts))

    def test_no_page_text_and_no_blocked_word(self):
        for r in self.raw:
            self.assertTrue(r["text_sha256"] == "" or HEX64.match(r["text_sha256"]))
            int(r["text_chars"])
        for p in PARTS:
            with open(p, encoding="utf-8") as fh:
                self.assertIsNone(ss.GUARD_RE.search(fh.read()), p)

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = ss.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED_PREDICTIONS)

    def test_described_counts(self):
        self.assertEqual(norm(ss.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), ss.result_text(self.result) + "\n")

    def test_flags_only_on_read_pages(self):
        for r in self.rows:
            if r["status"] != "ok":
                for k in ("placeholder", "juniper_credit", "juniper_template", "juniper_field",
                          "gov_uk_sample"):
                    self.assertFalse(r[k], (r["host"], k))
                self.assertEqual(r["placeholder_ids"], "")
            else:
                self.assertEqual(r["placeholder"], bool(ids(r)), r["host"])


class NoteTests(unittest.TestCase):
    """Every figure in SCHOOL-STOCK-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.rows = load_rows()
        cls.ph = [r for r in cls.rows if ss.flagged(r)]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def test_status_and_crawl_times(self):
        c = self.result["crawl"]
        self.has("(%s to %s UTC)" % (c["started_utc"][11:16], c["finished_utc"][11:16]))
        self.has("**Two of the four predictions held (J1, J4) and two failed (J2, J3).**")

    def test_headline(self):
        k1, hosts, oks = self.m["J1_placeholder_hosts"], self.m["F1_hosts"], self.d["ok_pages"]
        self.has("**%s of the %s school website hosts in England's register (%s%%) serve an "
                 "accessibility statement that still carries template placeholders at "
                 "`/accessibility-statement/`**, or %s%% of the %s statement pages that could be "
                 "read there." % (n(k1), n(hosts), pct(k1, hosts), pct(k1, oks), n(oks)))
        primary = self.d["placeholder_by_phase"]["Primary"]
        self.has("Behind those %d hosts are %d establishments, and %d of the hosts are listed under "
                 "a primary school." % (k1, self.d["placeholder_establishments"], primary))

    def test_two_templates(self):
        ph, k1 = self.ph, len(self.ph)
        both = [r for r in ph if r["juniper_template"] and r["juniper_credit"]]
        sentence_only = [r for r in ph if r["juniper_template"] and not r["juniper_credit"]]
        credit_only = [r for r in ph if r["juniper_credit"] and not r["juniper_template"]]
        neither = [r for r in ph if not r["juniper_credit"] and not r["juniper_template"]]
        three = [r for r in sentence_only if r["placeholder_ids"] == GOV_THREE]
        bracket = [r for r in ph if "school/school_bracket" in ids(r)]
        bracket_credit = [r for r in bracket if r["juniper_credit"]]
        self.assertEqual(len(both) + len(sentence_only), self.m["J3_kept_of_juniper_template"]["k"])
        self.assertEqual(len(both) + len(credit_only), self.m["J2_credit_of_placeholder"]["k"])
        self.assertEqual(len(bracket), self.d["placeholder_ids"]["school/school_bracket"])
        self.has("%d of the %d carry that sentence and the Juniper Websites credit."
                 % (len(both), k1))
        self.has("%d of the %d keep a bracketed school name, and %d of those %d carry the Juniper "
                 "credit." % (len(bracket), k1, len(bracket_credit), len(bracket)))
        self.has("%d carry that sentence without the Juniper credit, and %d of those %d keep exactly "
                 "three fields of GOV.UK's sample statement and nothing else that the checker flags"
                 % (len(sentence_only), len(three), len(sentence_only)))
        self.has("%d carry the Juniper credit without the sentence, and %d carry neither."
                 % (len(credit_only), len(neither)))
        self.assertGreater(len(sentence_only), k1 * 0.4)  # "about half"

    def test_prediction_table(self):
        m = self.m
        self.assertEqual((ss.J1_MIN_HOSTS, ss.J2_MIN_CREDIT, ss.J3_MIN_KEPT, ss.J4_MIN_22),
                         (400, 0.80, 0.40, 0.50))
        self.has("| %s | yes |" % n(m["J1_placeholder_hosts"]))
        for key, held in (("J2_credit_of_placeholder", "no"), ("J3_kept_of_juniper_template", "no"),
                          ("J4_wcag22_of_gov_uk_wording", "yes")):
            s = m[key]
            self.assertEqual(pct(s["k"], s["n"]), "%.2f" % s["pct"])
            self.has("| %s of %s (%s%%) | %s |" % (n(s["k"]), n(s["n"]), pct(s["k"], s["n"]), held))

    def test_gates(self):
        f, g = self.result["frame"], self.m["G1_answered"]
        self.has("The frame is the %s establishments (%s hosts)" % (n(f["rows"]), n(f["hosts"])))
        self.has("%s of %s hosts (%s%%) answered, above G1's 80%%"
                 % (n(g["k"]), n(g["n"]), pct(g["k"], g["n"])))

    def test_j3_filled_in(self):
        s = self.m["J3_kept_of_juniper_template"]
        self.has("%s of them keep no placeholder." % n(s["n"] - s["k"]))

    def test_statuses(self):
        st = self.d["status"]
        self.has("%s hosts serve a readable statement page at the address. %s hosts answered 404 "
                 "(no page at the address), %s disallowed the address in robots.txt, %s did not "
                 "answer at all, %d redirected to a home page and %d served a page that does not "
                 "mention accessibility." % (n(st["ok"]), n(st["http_404"]), n(st["robots"]),
                                             n(st["http_0"]), st["redirect_home"],
                                             st["not_statement"]))

    def test_credit_share(self):
        d, k2 = self.d, self.m["J2_credit_of_placeholder"]["k"]
        c, oks = d["ok_juniper_credit"], d["ok_pages"]
        self.has("The Juniper credit is on %s of the %s readable pages (%s%%), and %d of those %s "
                 "(%s%%) keep a placeholder." % (n(c), n(oks), pct(c, oks), k2, n(c), pct(k2, c)))

    def test_juniper_fields(self):
        d = self.d
        self.has("are on %d pages, %d of which have no 0.3.0 placeholder, so %d readable pages carry "
                 "one or the other." % (d["juniper_field_pages"],
                                        d["juniper_field_without_placeholder"],
                                        d["placeholder_or_juniper_field"]))
        self.has("%d pages carry the long sample variant, and %d name the vendor's build address"
                 % (d["ok_juniper_sample"], d["staging_domain_pages"]))

    def test_us_template_and_types(self):
        us = [r for r in self.ph if US_TEMPLATE_IDS & set(ids(r))]
        indep = [r for r in us if r["type_group"] == "Independent schools"]
        self.has("%d of the %d keep a placeholder of the 2017 US template" % (len(us), len(self.ph)))
        self.has("found on %s US school-district hosts" % n(US_DISTRICT_HOSTS))
        self.has("and %d of those %d are independent schools." % (len(indep), len(us)))
        g = self.d["by_type_group"]
        parts = []
        for name, label in (("Independent schools", ""), ("Academies", " academies"),
                            ("Local authority maintained schools",
                             " local-authority maintained schools")):
            parts.append("%s of %s%s (%s%%)" % (n(g[name]["placeholder"]), n(g[name]["ok"]), label,
                                                pct(g[name]["placeholder"], g[name]["ok"])))
        # The note reads: "27 of 117 (23.08%), against 310 of 3,146 academies (9.85%) and ..."
        self.has("keep a placeholder more often: %s, against %s and %s." % tuple(parts))

    def test_wcag_regions_texts(self):
        h, d, k1 = self.d["placeholder_highest"], self.d, self.m["J1_placeholder_hosts"]
        self.assertEqual(sum(h.values()), k1)
        self.has("%d of the %d name WCAG 2.2 as the highest version, %d name 2.0, %d name 2.1 and "
                 "%d names none." % (h["2.2"], k1, h["2.0"], h["2.1"], h[""]))
        reg = d["placeholder_by_region"]
        top = sorted(reg.items(), key=lambda kv: (-kv[1], kv[0]))[:2]
        self.assertEqual([k for k, _ in top], ["South East", "East of England"])
        self.has("Most are in the South East (%d) and the East of England (%d)."
                 % (top[0][1], top[1][1]))
        self.has("The %d pages have %d distinct texts, %d were served from another host, and %d hosts "
                 "answered 429 or 503" % (k1, d["placeholder_distinct_texts"],
                                          d["placeholder_other_host"], d["retried"]))

    def test_comparison_with_district_stock(self):
        k1, hosts, oks = self.m["J1_placeholder_hosts"], self.m["F1_hosts"], self.d["ok_pages"]
        self.has("(%s%% against %s%% in district-stock)" % (pct(k1, hosts), US_HOST_PCT))
        self.has("the share is %s%% against %s%%." % (pct(k1, oks), US_READ_PCT))

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(ss.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
