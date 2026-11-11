# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for planned_dates.py (no network). Made by MV2 of Munim, Inc. with AI agents."""

import csv
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import council_stock as cs  # noqa: E402
import planned_dates as pd  # noqa: E402

HEAD = ("<html><head><title>Accessibility statement</title></head><body>"
        "<h1>Accessibility statement for Example Council</h1>"
        "<p>This accessibility statement applies to the Example Council website. This website is "
        "partially compliant with the Web Content Accessibility Guidelines version 2.2 AA "
        "standard, due to the non-compliances listed below.</p>")
PLANNED_PAGE = (HEAD + "<p>This statement was prepared on 1 May 2023. It was last reviewed on "
                "2 June 2024. It will be reviewed in March 2027.</p></body></html>")
PLAIN_PAGE = HEAD + "<p>This statement was last updated on 3 March 2026.</p></body></html>"
OTHER_PAGE = ("<html><body><h1>Contact us</h1><p>" + "Our offices are open on weekdays. " * 10
              + "</p></body></html>")


class Readings(unittest.TestCase):
    def test_planned_review_left_out(self):
        text = pd.stc.visible_text(PLANNED_PAGE.encode("utf-8"), "text/html")
        self.assertTrue(cs.is_statement(text))
        self.assertEqual(cs.statement_dates(text),
                         ("2027-03-31", "2023-05-01", "2027-03-31", "reviewed"))
        self.assertEqual(pd.new_dates(text),
                         ("2024-06-02", "2023-05-01", "2024-06-02", "reviewed"))
        pm = pd.planned_matches(text)
        self.assertEqual(len(pm), 1)
        self.assertEqual(pm[0][0], "2027-03-31")
        self.assertIn("will be reviewed in March 2027", pm[0][1])
        self.assertLessEqual(len(pm[0][1]), pd.SNIPPET_CHARS)

    def test_plain_statement_unchanged(self):
        text = pd.stc.visible_text(PLAIN_PAGE.encode("utf-8"), "text/html")
        a = pd.analyse(text)
        self.assertEqual(a["old_date"], "2026-03-03")
        self.assertEqual(a["new_date"], "2026-03-03")
        self.assertEqual(a["planned_n"], 0)
        self.assertEqual(a["future_phrases"], 0)

    def test_other_planned_wordings(self):
        for s, iso in (("This statement will next be reviewed in January 2027.", "2027-01-31"),
                       ("This page is due to be updated on 5 December 2026.", "2026-12-05"),
                       ("It shall be revised in June 2026.", "2026-06-30")):
            pm = pd.planned_matches(s)
            self.assertEqual([d for d, _ in pm], [iso], s)
            self.assertEqual(pd.new_dates(s)[2], "", s)
            self.assertEqual(cs.statement_dates(s)[2], iso, s)

    def test_past_reviews_kept(self):
        for s in ("We checked it. Reviewed on 4 April 2025 by our web team.",
                  "This statement was last revised in October 2025.",
                  "It was published on 2 February 2024."):
            self.assertEqual(pd.planned_matches(s), [], s)
            self.assertEqual(pd.new_dates(s), cs.statement_dates(s), s)

    def test_future_phrase_count(self):
        a = pd.analyse("It will be reviewed in March 2027. Our next review is due soon.")
        self.assertEqual(a["future_phrases"], 2)


class Frame(unittest.TestCase):
    def test_dedup_and_sources(self):
        council = [{"status": "ok", "statement_url": "https://a.example/s", "statement_date":
                    "2024-01-01", "text_sha256": "x"},
                   {"status": "not_found", "statement_url": ""},
                   {"status": "ok", "statement_url": "[withheld]"}]
        govuk = [{"status": "ok", "statement_url": "https://a.example/s"},
                 {"status": "ok", "statement_url": "https://b.example/s"}]
        items, counts = pd.build_frame([("council", council), ("govuk", govuk)])
        self.assertEqual([it["url"] for it in items], ["https://a.example/s", "https://b.example/s"])
        self.assertEqual(items[0]["sources"], "council;govuk")
        self.assertEqual(items[0]["census_date"], "2024-01-01")
        self.assertEqual(items[1]["sources"], "govuk")
        self.assertEqual(counts, {"ok_rows": {"council": 2, "govuk": 2}, "withheld": 1})
        self.assertFalse(pd.frame_ok(items, counts))


def fake_get(url):
    if url.endswith("/robots.txt"):
        if "blocked." in url:
            return 200, url, "text/plain", b"User-agent: *\nDisallow: /\n"
        return 404, url, "", b""
    if "c283." in url:
        return 404, url, "", b""
    if "other." in url:
        return 200, url, "text/html", OTHER_PAGE.encode("utf-8")
    for i in range(10):
        if "//c%d.example/" % i in url:
            return 200, url, "text/html; charset=utf-8", PLANNED_PAGE.encode("utf-8")
    return 200, url, "text/html; charset=utf-8", PLAIN_PAGE.encode("utf-8")


class ReadOne(unittest.TestCase):
    def test_statuses(self):
        nop = lambda s: None  # noqa: E731
        r = pd.read_one({"url": "https://blocked.example/a", "census_sha256": ""}, get=fake_get,
                        sleep=nop)
        self.assertEqual(r["status"], "robots")
        r = pd.read_one({"url": "https://c283.example/a"}, get=fake_get, sleep=nop)
        self.assertEqual(r["status"], "http_404")
        r = pd.read_one({"url": "https://other.example/a"}, get=fake_get, sleep=nop)
        self.assertEqual(r["status"], "not_statement")
        r = pd.read_one({"url": "https://c1.example/a", "census_sha256": "nope"}, get=fake_get,
                        sleep=nop)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["planned_n"], 1)
        self.assertEqual(r["text_same"], 0)


def write_csv(path, rows, cols):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.out = os.path.join(self.root, "out")
        cols = ["host", "status", "statement_url", "statement_date", "text_sha256"]
        council = [{"host": "c%d.example" % i, "status": "ok",
                    "statement_url": "https://c%d.example/accessibility-statement" % i,
                    "statement_date": "2026-03-03", "text_sha256": ""} for i in range(284)]
        council.append({"host": "x.example", "status": "not_found", "statement_url": "",
                        "statement_date": "", "text_sha256": ""})
        govuk = [{"host": "g%d.example" % i, "status": "ok",
                  "statement_url": ("https://shared.example/accessibility" if i < 6 else
                                    "https://g%d.example/accessibility-statement" % i),
                  "statement_date": "", "text_sha256": ""} for i in range(202)]
        write_csv(os.path.join(self.root, "results", "uk-councils", "hosts.csv"), council, cols)
        write_csv(os.path.join(self.root, "results", "govuk-orgs", "hosts.csv"), govuk, cols)
        plan = os.path.join(self.root, "results", "uk-planned")
        os.makedirs(plan)
        shutil.copy(os.path.join(HERE, "results", "uk-planned", "PREREG.md"), plan)
        with open(os.path.join(HERE, "statement_template_check.py"), "rb") as f:
            self.checker = f.read()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def fetch(self, url):
        if url == cs.CHECKER_RELEASE_URL:
            return self.checker
        if url == pd.RELEASE_070_URL:
            return (b"x = 1\n" + ('PLANNED_RE = re.compile(r"%s", re.I)' % pd.PLANNED_PATTERN)
                    .encode("utf-8") + b"\nPLANNED_WINDOW = 25\n")
        raise OSError("unexpected fetch %s" % url)

    def run_main(self, fetch):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            pd.main(["--out-dir", self.out, "--root", self.root, "--workers", "4", "--delay", "0"],
                    fetch=fetch, get=fake_get, sleep=lambda s: None)
        finally:
            sys.stdout = old
        with open(os.path.join(self.out, "result.json"), encoding="utf-8") as f:
            return json.load(f), buf.getvalue()

    def test_graded_run(self):
        res, printed = self.run_main(self.fetch)
        self.assertIn("planned_dates: graded", printed)
        self.assertEqual(res["status"], "graded")
        self.assertEqual(res["frame"]["urls"], 481)
        self.assertEqual(res["frame"]["both"], 0)
        m = res["measures"]
        self.assertEqual(m["F1_urls"], 481)
        self.assertEqual(m["G1_read"]["k"], 480)
        self.assertEqual(m["Q1_planned_of_read"], {"k": 10, "n": 480, "pct": 2.08})
        self.assertEqual(m["Q2_flipped_of_dated"], {"k": 10, "n": 480, "pct": 2.08})
        c = m["Q3_by_census"]["council"]
        self.assertEqual((c["read"], c["old_stale"], c["new_stale"], c["new_dated"]),
                         (283, 0, 10, 283))
        self.assertEqual(c["diff_pp"], 3.53)
        self.assertEqual(m["Q3_by_census"]["govuk"]["diff_pp"], 0.0)
        self.assertEqual(res["predictions"], {"Q1": True, "Q2": False, "Q3": False, "Q4": None})
        self.assertEqual(res["tables"]["planned.csv"]["rows"], 10)
        self.assertEqual(res["described"]["planned_year"], {"2027": 10})
        with open(os.path.join(self.out, "rows.csv"), encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 481)
        self.assertEqual(pd.grade(rows)[0], m)
        self.assertEqual(pd.described(rows), res["described"])

    def test_not_run_without_planned_rule(self):
        def fetch(url):
            if url == pd.RELEASE_070_URL:
                return b"nothing here"
            return self.fetch(url)
        res, printed = self.run_main(fetch)
        self.assertEqual(res["status"], "not_run")
        self.assertFalse(res["gates"]["P0_planned_rule"])
        self.assertFalse(os.path.exists(os.path.join(self.out, "rows.csv")))


class Plan(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(os.path.join(HERE, "results", "uk-planned", "PREREG.md"), encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("at least 80%", "at most 5%", "at most 1%", "at most 1.5 percentage points",
                       "at most 1 snippet", "284", "202", "between 400 and 486",
                       "2025-11-01", "Q1", "Q2", "Q3", "Q4", "G1", "F1", "P0"):
            self.assertIn(phrase, text)
        self.assertEqual((pd.G1_MIN_READ, pd.Q1_MAX_PLANNED, pd.Q2_MAX_FLIPPED, pd.Q3_MAX_PP,
                          pd.Q4_MAX_NOT_PLANNED), (0.80, 0.05, 0.01, 1.5, 1))
        self.assertEqual((pd.F1_MIN_URLS, pd.F1_MAX_URLS), (400, 486))
        self.assertEqual(pd.TABLE_OK_ROWS, {"council": 284, "govuk": 202})
        self.assertEqual(pd.STALE_BEFORE, "2025-11-01")


if __name__ == "__main__":
    unittest.main()
