# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered district-stock result from its saved tables.

Reads results/district-stock/result.json, result.txt and the hosts tables (the run's output,
unchanged). The table of districts of 50,000 or more people (hosts-50k.csv) is re-graded band by
band with the pinned district_stock.py (unchanged; it imports district_pages.py,
district_check.py, a11y_pages.py, statement_check.py and template_check.py), and every other
figure is checked for consistency with result.json. The under-50,000 table is over the publishing
tool's 2,000,000-byte limit per file, so it is kept in two parts (hosts-under50k-part1.csv and
hosts-under50k-part2.csv); when both are present, every measure, gate, prediction and described
count is re-graded from the tables. NoteTests checks every figure in DISTRICT-STOCK-RESULT.md.

Standard library only: python -m unittest discover -p test_district_stock_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import re
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import a11y_pages as ap  # noqa: E402
import district_stock as ds  # noqa: E402

RES = os.path.join(ROOT, "results", "district-stock")
NOTE = os.path.join(RES, "DISTRICT-STOCK-RESULT.md")
BIG_TABLE = os.path.join(RES, "hosts-50k.csv")
PARTS = [os.path.join(RES, "hosts-under50k-part%d.csv" % i) for i in (1, 2)]
HAVE_PARTS = all(os.path.exists(p) for p in PARTS)
LIMIT = 2000000                  # the publishing tool's limit per file
CENSUS_PLACEHOLDER_PAGES = 129   # district-pages result: placeholder pages found through links
CITY_TEMPLATES = 235             # stock-153 (222) and stock-revize (13) unfinished templates
CITY_HOSTS = 5243
EXPECTED_PREDICTIONS = {"K1": True, "K2": True, "K3": True, "K4": True}
TOP_STATES = {"OH": "Ohio", "TX": "Texas", "NJ": "New Jersey", "CA": "California",
              "NY": "New York", "PA": "Pennsylvania"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ALL_THREE = "your_school+your_domain+fake_phone"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def norm(x):
    """The value as it reads back from result.json (tuples become lists)."""
    return json.loads(json.dumps(x))


def n(k):
    return format(k, ",")


def pct(x):
    """0.1576 -> '15.76', 1.0 -> '100' (decimal arithmetic, so no float rounding surprises)."""
    s = str((Decimal(repr(x)) * 100).quantize(Decimal("0.01")))
    return s[:-3] if s.endswith(".00") else s


def share(m):
    """[k, n, p, [lo, hi]] -> 'k of n (p%, 95% CI lo-hi%)'."""
    k, total, p, (lo, hi) = m
    return "%s of %s (%s%%, 95%% CI %s-%s%%)" % (n(k), n(total), pct(p), pct(lo), pct(hi))


def check_flags(test, rows):
    for r in rows:
        with test.subTest(leaid=r["leaid"]):
            if r["status"] == "ok":
                test.assertEqual(r["placeholder"], bool(r["placeholder_kinds"]))
                test.assertEqual(r["uncounted"], r["placeholder"] and r["census"] != "not_sampled"
                                 and not r["census_placeholder"])
                test.assertTrue(HEX64.match(r["text_sha256"]), r["text_sha256"])
            else:
                for k in ("placeholder", "uncounted", "finalsite_markup", "t2017", "t2026",
                          "generator", "title2", "same_text"):
                    test.assertFalse(r[k], k)
                test.assertEqual(r["placeholder_kinds"], "")


class ResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        cls.header, cls.raw = load_csv(BIG_TABLE)
        cls.rows = ds.typed(cls.raw)

    def test_version_status_gates(self):
        self.assertEqual(self.result["version"], ds.__version__)
        self.assertEqual(self.result["status"], "graded")
        self.assertEqual(set(self.result["gates"]),
                         {"P0_prereg_public", "G0_census", "G0_federal", "F1_frame", "G1_answered"})
        self.assertTrue(all(self.result["gates"].values()))
        self.assertEqual(self.result["census_rows"], ds.CENSUS_ROWS)
        self.assertEqual(self.result["predictions"], EXPECTED_PREDICTIONS)

    def test_table_columns_hold_no_page_text(self):
        self.assertEqual(self.header, ds.COLUMNS)
        for r in self.raw:
            self.assertTrue(r["text_sha256"] == "" or HEX64.match(r["text_sha256"]))
            int(r["text_chars"])

    def test_big_band_rows(self):
        f = self.result["frame"]
        self.assertEqual(len(self.raw), f["hosts_50k+"])
        self.assertEqual(len({r["host"] for r in self.raw}), len(self.raw))
        leaids = [r["leaid"] for r in self.raw]
        self.assertEqual(leaids, sorted(leaids))
        self.assertEqual(len(set(leaids)), len(leaids))
        for drop in ds.DROP_LEAIDS:
            self.assertNotIn(drop, leaids)
        for r in self.raw:
            self.assertEqual(r["band"], "50k+")
            self.assertGreaterEqual(int(float(r["population"])), 50000)

    def test_big_band_regrade(self):
        rs = self.rows
        self.assertEqual(norm(ap._tally(rs, "status")), self.d["status"]["50k+"])
        self.assertEqual(norm(ap._tally(rs, "census")), self.d["census"]["50k+"])
        got = ap.share(sum(1 for r in rs if ds.flagged(r)), sum(1 for r in rs if ds.answered(r)))
        self.assertEqual(norm(got), self.d["placeholder_of_answered"]["50k+"])

    def test_big_band_flags_follow_the_rules(self):
        check_flags(self, self.rows)

    def test_predictions_follow_from_measures(self):
        m = self.m
        k1 = m["K1_placeholder_hosts"]
        k2, n2 = m["K2_uncounted_of_sampled"][:2]
        k3, n3 = m["K3_kept_of_census_here"][:2]
        k4, n4 = m["K4_markup_of_placeholder"][:2]
        ga, gn = m["G1_answered"][:2]
        for key, (k, total) in (("K2_uncounted_of_sampled", (k2, n2)),
                                ("K3_kept_of_census_here", (k3, n3)),
                                ("K4_markup_of_placeholder", (k4, n4)),
                                ("G1_answered", (ga, gn))):
            self.assertEqual(norm(ap.share(k, total)), m[key], key)
        self.assertEqual(gn, m["F1_hosts"])
        self.assertEqual(n4, k1)
        self.assertTrue(ds.F1_MIN <= m["F1_hosts"] <= ds.F1_MAX)
        self.assertTrue(ds.F1_BIG_MIN <= m["F1_hosts_50k+"] <= ds.F1_BIG_MAX)
        self.assertGreaterEqual(ga / gn, ds.G1_MIN_ANSWERED)
        preds = {"K1": k1 >= ds.K1_MIN_HOSTS,
                 "K2": n2 >= ds.K2_MIN_PAGES and k2 / n2 >= ds.K2_MIN_UNCOUNTED,
                 "K3": n3 >= ds.K3_MIN_PAGES and k3 / n3 >= ds.K3_MIN_KEPT,
                 "K4": n4 >= ds.K4_MIN_PAGES and k4 / n4 >= ds.K4_MIN_MARKUP}
        self.assertEqual(preds, self.result["predictions"])

    def test_counts_are_consistent(self):
        m, d, f = self.m, self.d, self.result["frame"]
        k1 = m["K1_placeholder_hosts"]
        for key in ("placeholder_by_census", "placeholder_kinds", "placeholder_highest",
                    "placeholder_by_state"):
            self.assertEqual(sum(d[key].values()), k1, key)
        poa = d["placeholder_of_answered"]
        self.assertEqual(sum(v[0] for v in poa.values()), k1)
        self.assertEqual(sum(v[1] for v in poa.values()), m["G1_answered"][0])
        sizes = {"50k+": f["hosts_50k+"], "under50k": f["hosts"] - f["hosts_50k+"]}
        for b, size in sizes.items():
            self.assertEqual(sum(d["status"][b].values()), size, b)
            self.assertEqual(sum(d["census"][b].values()), size, b)
            ans = sum(v for k, v in d["status"][b].items() if k not in ds.NOT_ANSWERED)
            self.assertEqual(ans, poa[b][1], b)
        self.assertEqual(f["hosts"], m["F1_hosts"])
        self.assertEqual(sum(d["status"][b].get("ok", 0) for b in sizes), d["ok_pages"])
        sampled = sum(v for b in sizes for k, v in d["census"][b].items() if k != "not_sampled")
        self.assertEqual(sampled, f["census_sampled"])
        self.assertEqual(sampled, ds.CENSUS_ROWS)
        self.assertEqual(m["K2_uncounted_of_sampled"][1],
                         k1 - d["placeholder_by_census"]["not_sampled"])
        chs = d["census_here_status"]
        self.assertEqual(sum(chs.values()), d["census_here_placeholder"])
        self.assertEqual(m["K3_kept_of_census_here"][1],
                         sum(v for k, v in chs.items() if k not in ds.NOT_REACHED))
        self.assertEqual(d["placeholder_t2017"] + d["t2017_without_placeholder"], d["t2017_pages"])
        self.assertLessEqual(m["K4_markup_of_placeholder"][0], d["markup_pages"])
        self.assertEqual(d["retried"], 0)
        for b in sizes:
            for s in ("http_429", "http_503"):
                self.assertNotIn(s, d["status"][b])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), ds.result_text(self.result) + "\n")

    def test_table_sizes(self):
        tb = self.result["table_bytes"]
        self.assertEqual(os.path.getsize(BIG_TABLE), tb["hosts-50k.csv"])
        self.assertLess(tb["hosts-50k.csv"], LIMIT)
        self.assertGreater(tb["hosts-under50k.csv"], LIMIT)


@unittest.skipUnless(HAVE_PARTS, "the two parts of the under-50,000 table are not here yet")
class FullRegradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        _, raw50 = load_csv(BIG_TABLE)
        cls.parts = [load_csv(p) for p in PARTS]
        cls.small = [r for _, raw in cls.parts for r in raw]
        cls.rows = ds.typed(raw50 + cls.small)

    def test_parts_split_once_in_leaid_order(self):
        (h1, p1), (h2, p2) = self.parts
        self.assertEqual(h1, ds.COLUMNS)
        self.assertEqual(h2, ds.COLUMNS)
        self.assertTrue(p1 and p2)
        self.assertLess(p1[-1]["leaid"], p2[0]["leaid"])
        leaids = [r["leaid"] for r in self.small]
        self.assertEqual(leaids, sorted(leaids))
        self.assertEqual(len(set(leaids)), len(leaids))
        f = self.result["frame"]
        self.assertEqual(len(self.small), f["hosts"] - f["hosts_50k+"])
        for r in self.small:
            self.assertEqual(r["band"], "under50k")
        for p in PARTS:
            self.assertLess(os.path.getsize(p), LIMIT)
        header_bytes = len((",".join(ds.COLUMNS) + "\n").encode("utf-8"))
        self.assertEqual(sum(os.path.getsize(p) for p in PARTS) - header_bytes,
                         self.result["table_bytes"]["hosts-under50k.csv"])

    def test_one_row_per_host(self):
        self.assertEqual(len(self.rows), self.result["frame"]["hosts"])
        self.assertEqual(len({r["host"] for r in self.rows}), len(self.rows))
        for drop in ds.DROP_LEAIDS:
            self.assertNotIn(drop, {r["leaid"] for r in self.rows})

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = ds.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED_PREDICTIONS)

    def test_described_counts(self):
        self.assertEqual(norm(ds.described(self.rows)), self.result["described"])

    def test_flags_follow_the_rules(self):
        check_flags(self, self.rows)

    def test_the_unmarked_placeholder_page(self):
        ph = [r for r in self.rows if ds.flagged(r) and not r["finalsite_markup"]]
        self.assertEqual(len(ph), 1)
        self.assertEqual(ph[0]["placeholder_kinds"], "fake_phone")


class NoteTests(unittest.TestCase):
    """Every figure in DISTRICT-STOCK-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = f.read()

    def has(self, phrase):
        self.assertIn(phrase, self.note)

    def test_status_and_crawl_times(self):
        c = self.result["crawl"]
        self.has("(%s to %s UTC)" % (c["started_utc"][11:16], c["finished_utc"][11:16]))
        self.assertEqual(self.result["predictions"], EXPECTED_PREDICTIONS)
        self.has("**All four predictions held.**")

    def test_headline(self):
        m = self.m
        k1, hosts, ans = m["K1_placeholder_hosts"], m["F1_hosts"], m["G1_answered"][0]
        self.has("**%s of the %s US public school district website hosts (%s%%) serve an "
                 "accessibility statement that still carries template placeholders at "
                 "`/accessibility-statement`**, or %s%% of the %s hosts that answered."
                 % (n(k1), n(hosts), pct(round(k1 / hosts, 4)), pct(round(k1 / ans, 4)), n(ans)))

    def test_comparisons(self):
        k1 = self.m["K1_placeholder_hosts"]
        self.assertEqual(round(k1 / CENSUS_PLACEHOLDER_PAGES), 8)
        self.assertTrue(4 < k1 / CITY_TEMPLATES < 5)
        self.has("about 8 times the %d such pages" % CENSUS_PLACEHOLDER_PAGES)
        self.has("more than 4 times the %d unfinished vendor templates found at two stock "
                 "addresses on %s US city" % (CITY_TEMPLATES, n(CITY_HOSTS)))
        self.has("in its sample of %s districts" % n(ds.CENSUS_ROWS))

    def test_bands(self):
        poa = self.d["placeholder_of_answered"]
        k, total, p, (lo, hi) = poa["50k+"]
        self.has("%s of %s answering hosts of districts of 50,000 or more people (%s%%, 95%% CI "
                 "%s-%s%%)" % (n(k), n(total), pct(p), pct(lo), pct(hi)))
        k, total, p, (lo, hi) = poa["under50k"]
        self.has("%s of %s answering hosts of districts under 50,000 (%s%%, 95%% CI %s-%s%%)"
                 % (n(k), n(total), pct(p), pct(lo), pct(hi)))
        self.assertGreater(poa["50k+"][2], poa["under50k"][2])

    def test_prediction_table(self):
        m = self.m
        self.assertEqual((ds.K1_MIN_HOSTS, ds.K2_MIN_UNCOUNTED, ds.K3_MIN_KEPT, ds.K4_MIN_MARKUP),
                         (400, 0.15, 0.90, 0.95))
        self.has("| K1 | At least 400 hosts serve a placeholder page at `/accessibility-statement` "
                 "| %s | yes |" % n(m["K1_placeholder_hosts"]))
        self.has("| K2 | Of the census-sampled hosts that serve a placeholder page there, at least "
                 "15% are districts for which the census counted no placeholder page | "
                 + share(m["K2_uncounted_of_sampled"]) + " | yes |")
        self.has("| K3 | Of the hosts where the census read a placeholder page at this address, at "
                 "least 90% still serve one | " + share(m["K3_kept_of_census_here"]) + " | yes |")
        self.has("| K4 | At least 95% of placeholder pages carry Finalsite markup | "
                 + share(m["K4_markup_of_placeholder"]) + " | yes |")

    def test_gates(self):
        f, m = self.result["frame"], self.m
        self.has("%s website hosts, %s of them in districts of 50,000 or more people "
                 "(%d district dropped as planned)" % (n(f["hosts"]), n(f["hosts_50k+"]),
                                                       f["dropped"]))
        k, total, p, _ = m["G1_answered"]
        self.has("All %s census rows were read (G0), and %s of %s hosts (%s%%) answered"
                 % (n(self.result["census_rows"]), n(k), n(total), pct(p)))

    def test_within_sample(self):
        k2, n2 = self.m["K2_uncounted_of_sampled"][:2]
        self.has("the one address finds %d hosts serving a placeholder page, against the census's "
                 "%d found by following links; %d of the %d are districts the census did not count"
                 % (n2, CENSUS_PLACEHOLDER_PAGES, k2, n2))

    def test_pages_read(self):
        d, k1 = self.d, self.m["K1_placeholder_hosts"]
        st = d["status"]
        n404 = sum(st[b].get("http_404", 0) for b in st)
        self.has("%s pages could be read at the address (%s in districts of 50,000 or more, %s "
                 "under 50,000), and %s of them (%s%%) keep a placeholder. %s hosts answered 404 "
                 "(no page at the address)." % (n(d["ok_pages"]), n(st["50k+"]["ok"]),
                                                n(st["under50k"]["ok"]), n(k1),
                                                pct(round(k1 / d["ok_pages"], 4)), n(n404)))

    def test_census_records(self):
        c = self.d["placeholder_by_census"]
        self.has("By census record, the %s are: %d of districts outside the census sample, %d at "
                 "the address the census had read, %d where the census read a different "
                 "accessibility page, %d whose home page linked no page the census read and %d "
                 "whose home page the census could not read."
                 % (n(self.m["K1_placeholder_hosts"]), c["not_sampled"], c["found_here"],
                    c["found_elsewhere"], c["no_page"], c["home_failed"]))

    def test_census_pages_unchanged(self):
        d = self.d
        ok = d["census_here_status"]["ok"]
        self.assertEqual(d["census_here_same_text"], ok)
        self.assertEqual(self.m["K3_kept_of_census_here"][:2], [ok, ok])
        self.has("Of the %d census placeholder pages at this address, %d did not answer, and all %d "
                 "that answered serve the same visible text as when the census read them"
                 % (d["census_here_placeholder"], d["census_here_placeholder"] - ok, ok))

    def test_placeholder_kinds(self):
        kinds, k1 = self.d["placeholder_kinds"], self.m["K1_placeholder_hosts"]
        three, school = kinds[ALL_THREE], kinds["your_school"]
        self.has("%d pages keep all three kinds (\"Your School\", a yourschool.com-style address "
                 "and 555-555-5555), %d keep only \"Your School\", and %d keep another combination."
                 % (three, school, k1 - three - school))
        self.assertEqual(kinds.get("fake_phone"), 1)

    def test_template_sentence_and_credit(self):
        d, k1 = self.d, self.m["K1_placeholder_hosts"]
        self.has("%s of the %s carry the 2017 template's first sentence. %s readable pages carry "
                 "that sentence: %d districts filled the template in, and %s (%s%%) did not."
                 % (n(d["placeholder_t2017"]), n(k1), n(d["t2017_pages"]),
                    d["t2017_without_placeholder"], n(d["placeholder_t2017"]),
                    pct(round(d["placeholder_t2017"] / d["t2017_pages"], 4))))
        self.has("%d of the %s keep the template's credit to the 2017 Accessibility Statement "
                 "Generator." % (d["placeholder_generator"], n(k1)))

    def test_wcag_and_title2(self):
        h, k1 = self.d["placeholder_highest"], self.m["K1_placeholder_hosts"]
        self.has("The highest WCAG version named is 2.0 on %s of the %s (%s%%), 2.1 on %d, 2.2 on "
                 "%d, and none on %d." % (n(h["2.0"]), n(k1), pct(round(h["2.0"] / k1, 4)),
                                          h["2.1"], h["2.2"], h[""]))
        self.assertEqual(set(h), {"2.0", "2.1", "2.2", ""})
        self.has("%d of the %s mention Title II." % (self.d["placeholder_title2"], n(k1)))

    def test_2026_template_and_markup(self):
        d, m = self.d, self.m
        self.assertEqual(d["placeholder_t2026"], 0)
        self.has("is on %d pages, and neither keeps a placeholder." % d["t2026_pages"])
        self.assertEqual(d["t2026_pages"], 2)
        self.assertEqual(m["K4_markup_of_placeholder"][0], m["K1_placeholder_hosts"] - 1)
        self.has("%s of the %s readable pages carry Finalsite markup. The one placeholder page "
                 "without it keeps only the dummy phone number." % (n(d["markup_pages"]),
                                                                    n(d["ok_pages"])))

    def test_states(self):
        by_state = self.d["placeholder_by_state"]
        top = sorted(by_state.items(), key=lambda kv: (-kv[1], kv[0]))[:len(TOP_STATES)]
        self.assertEqual({k for k, _ in top}, set(TOP_STATES))
        listed = ["%s (%d)" % (TOP_STATES[k], v) for k, v in top]
        self.has("The %s are in %d states, most in %s and %s." % (
            n(self.m["K1_placeholder_hosts"]), len(by_state), ", ".join(listed[:-1]), listed[-1]))

    def test_no_retries(self):
        self.assertEqual(self.d["retried"], 0)
        self.has("No server answered 429 or 503, so no address was asked twice.")

    def test_files(self):
        tb = self.result["table_bytes"]
        self.has("(`hosts-under50k.csv`, %s bytes) is over the publishing tool's limit of %s bytes "
                 "per file" % (n(tb["hosts-under50k.csv"]), n(LIMIT)))


if __name__ == "__main__":
    unittest.main()
