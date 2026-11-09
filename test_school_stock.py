# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for school_stock.py (no network). Made by MV2 of Munim, Inc. with AI agents."""

import csv
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import school_stock as ss  # noqa: E402
import statement_template_check as stc  # noqa: E402

SHORT_TEMPLATE = (
    "Accessibility Statement. This website is run by [School Name] and this statement applies to "
    "[Website Link and Date]. We want as many people as possible to be able to use this website. "
    "This website is partially compliant with the Web Content Accessibility Guidelines version 2.2 "
    "AA standard. Email: [Accessibility Email Address] Phone: [School Phone Number] Mailing "
    "Address: [School Mailing Address] [School Name] values diversity and inclusion and is "
    "committed to providing an accessible online experience for all. This statement was first "
    "prepared on [Date].")
SAMPLE_VARIANT = (
    "Accessibility Statement. [This is a sample accessibility statement that you may want to use. "
    "We have sections throughout that you can edit to curate your own accessibility statement "
    "that is tailored to your website. Prior to publication, please remove this text and any "
    "other instructions which are in bold. Plus, fill out the information highlighted in bold and "
    "in square brackets.] [Delete as appropriate] [The above are examples only. Please use the "
    "checklist provided.] [Please add other items that you are choosing to not be compliant.]")
FILLED = (
    "Accessibility Statement. This website is run by Example Primary School and this statement "
    "applies to example.sch.uk as of 16/06/2025. We want as many people as possible to be able to "
    "use this website. This website is partially compliant with the Web Content Accessibility "
    "Guidelines version 2.1 AA standard. Example Primary School values diversity and inclusion "
    "and is committed to providing an accessible online experience for all.")
CREDIT = b"<footer>School Website by <a href='https://example.invalid/'>Juniper Websites</a></footer>"


def page(text, footer=CREDIT):
    return (b"<!doctype html><html><head><title>Accessibility Statement</title>"
            b"<script>var x = '[School Name]';</script></head><body><main><p>"
            + text.encode("utf-8") + b"</p></main>" + footer + b"</body></html>")


def make_get(responses):
    calls = []

    def get(url):
        calls.append(url)
        r = responses.get(url)
        if isinstance(r, list):
            r = r.pop(0)
        return r if r is not None else (404, url, "", b"")
    get.calls = calls
    return get


def no_sleep(_):
    pass


ROW = {"host": "example.sch.uk", "urn": "100", "name": "Example Primary School",
       "type_group": "Academies", "phase": "Primary", "la_name": "Example", "region": "London",
       "establishments": 1, "base": "http://www.example.sch.uk"}
URL = "http://www.example.sch.uk/accessibility-statement/"
ROBOTS = "http://www.example.sch.uk/robots.txt"
HTML = "text/html; charset=utf-8"


class FrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.checks = ss.read_parts(os.path.join(HERE, *ss.FRAME_DIR.split("/")))
        cls.hosts, cls.dropped = ss.build_frame(cls.rows)

    def test_parts_are_the_ones_uk_frame_wrote(self):
        self.assertEqual(sorted(self.checks), ["frame-part1.csv", "frame-part2.csv",
                                               "frame-part3.csv"])
        self.assertTrue(all(self.checks.values()), self.checks)
        self.assertEqual(len(self.rows), ss.FRAME_ROWS)

    def test_one_row_per_host(self):
        self.assertEqual(self.dropped, 0)
        self.assertEqual(len(self.hosts), ss.FRAME_HOSTS)
        self.assertEqual(len(set(h["host"] for h in self.hosts)), ss.FRAME_HOSTS)
        self.assertEqual(sum(h["establishments"] for h in self.hosts), ss.FRAME_ROWS)
        self.assertLessEqual(sum(1 for h in self.hosts if not h["base"]), 10)

    def test_frame_json_agrees(self):
        with open(os.path.join(HERE, "results", "uk-schools", "frame.json"), encoding="utf-8") as f:
            fj = json.load(f)
        self.assertEqual(fj["open_with_website"], ss.FRAME_ROWS)
        self.assertEqual(fj["distinct_hosts"], ss.FRAME_HOSTS)
        self.assertEqual([(p["file"], p["rows"], p["sha256"]) for p in fj["parts"]],
                         [tuple(p) for p in ss.FRAME_PARTS])
        self.assertEqual(fj["source_date"], "20261109")

    def test_crawl_order_is_fixed_and_complete(self):
        a = ss.crawl_order(self.hosts[:500])
        b = ss.crawl_order(list(reversed(self.hosts[:500])))
        self.assertEqual([r["host"] for r in a], [r["host"] for r in b])
        self.assertEqual(sorted(r["host"] for r in a), sorted(r["host"] for r in self.hosts[:500]))

    def test_base_of(self):
        self.assertEqual(ss.base_of("www.Example.sch.uk/"), "http://www.example.sch.uk")
        self.assertEqual(ss.base_of("https://example.org.uk/home"), "https://example.org.uk")
        self.assertEqual(ss.base_of(""), "")
        self.assertEqual(ss.base_of("not a site"), "")


class RuleTests(unittest.TestCase):
    def test_checker_is_the_pinned_release(self):
        self.assertEqual(stc.__version__, "0.3.0")
        self.assertEqual(ss.CHECKER_VERSION, stc.__version__)
        self.assertIn("/v0.3.0/", ss.CHECKER_RELEASE_URL)

    def test_short_template(self):
        d = ss.check_text(SHORT_TEMPLATE, page(SHORT_TEMPLATE))
        self.assertTrue(d["placeholder"])
        self.assertEqual(d["placeholder_ids"], "revize/date;school/school_bracket")
        self.assertEqual(d["juniper_field_ids"],
                         "website_link_and_date;accessibility_email;school_phone;school_address")
        self.assertTrue(d["juniper_template"])
        self.assertFalse(d["juniper_sample"])
        self.assertTrue(d["juniper_credit"])
        self.assertTrue(d["gov_uk_sample"])
        self.assertEqual(d["highest"], "2.2")

    def test_sample_variant_is_described_not_counted(self):
        d = ss.check_text(SAMPLE_VARIANT)
        self.assertFalse(d["placeholder"])
        self.assertTrue(d["juniper_sample"])
        self.assertEqual(d["juniper_field_ids"],
                         "sample_notice;prior_to_publication;delete_as_appropriate;examples_only;"
                         "please_instruction")

    def test_filled_statement_is_clean(self):
        d = ss.check_text(FILLED, page(FILLED, footer=b"<footer>Juniper Green</footer>"))
        self.assertFalse(d["placeholder"])
        self.assertFalse(d["juniper_field"])
        self.assertTrue(d["juniper_template"])
        self.assertFalse(d["juniper_credit"])
        self.assertEqual(d["highest"], "2.1")

    def test_credit_marker(self):
        yes = (b"School Website by Juniper&nbsp;Websites", b"<span>Juniper</span> <span>Websites</span>",
               b"href='https://websites.junipereducation.org/'", b"x.web11.juniperwebsites.co.uk")
        for body in yes:
            with self.subTest(body=body):
                self.assertIsNotNone(ss.JUNIPER_CREDIT_RE.search(body))
        for body in (b"Juniper Green Primary School", b"juniper class websites list"):
            with self.subTest(body=body):
                self.assertIsNone(ss.JUNIPER_CREDIT_RE.search(body))

    def test_staging_domain(self):
        d = ss.check_text(FILLED + " It applies to https://exampleprimary.web11.juniperwebsites.co.uk")
        self.assertTrue(d["staging_domain"])
        self.assertFalse(ss.check_text(FILLED)["staging_domain"])

    def test_round_bracket_name(self):
        self.assertIn("school_name_round",
                      ss.check_text(FILLED + " This website is run by (School Name).")["juniper_field_ids"])


class ReadOneTests(unittest.TestCase):
    def test_template_page(self):
        get = make_get({ROBOTS: (404, ROBOTS, "", b""),
                        URL: (200, URL, HTML, page(SHORT_TEMPLATE))})
        r = ss.read_one(ROW, get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "ok")
        self.assertTrue(r["placeholder"])
        self.assertTrue(r["juniper_credit"])
        self.assertFalse(r["other_host"])
        self.assertEqual(len(r["text_sha256"]), 64)
        self.assertEqual(get.calls, [ROBOTS, URL])

    def test_no_answer_ends_the_host(self):
        get = make_get({ROBOTS: (0, ROBOTS, "", b"")})
        r = ss.read_one(ROW, get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "http_0")
        self.assertEqual(get.calls, [ROBOTS])
        self.assertFalse(ss.answered(r))

    def test_robots_disallow(self):
        get = make_get({ROBOTS: (200, ROBOTS, "text/plain", b"User-agent: *\nDisallow: /\n")})
        r = ss.read_one(ROW, get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "robots")
        self.assertEqual(get.calls, [ROBOTS])
        self.assertTrue(ss.answered(r))

    def test_not_found(self):
        r = ss.read_one(ROW, get=make_get({}), sleep=no_sleep)
        self.assertEqual(r["status"], "http_404")
        self.assertFalse(r["placeholder"])

    def test_redirect_home(self):
        home = "https://www.example.sch.uk/"
        get = make_get({URL: (200, home, HTML, page(SHORT_TEMPLATE))})
        self.assertEqual(ss.read_one(ROW, get=get, sleep=no_sleep)["status"], "redirect_home")

    def test_retry_once_on_503(self):
        get = make_get({URL: [(503, URL, "", b""), (200, URL, HTML, page(SHORT_TEMPLATE))]})
        r = ss.read_one(ROW, get=get, sleep=no_sleep)
        self.assertTrue(r["retried"])
        self.assertEqual(r["status"], "ok")
        self.assertEqual(get.calls, [ROBOTS, URL, URL])

    def test_not_a_statement(self):
        body = b"<html><body><p>" + b"Welcome to our school. " * 20 + b"</p></body></html>"
        get = make_get({URL: (200, URL, HTML, body)})
        self.assertEqual(ss.read_one(ROW, get=get, sleep=no_sleep)["status"], "not_statement")

    def test_short_page(self):
        get = make_get({URL: (200, URL, HTML, b"<html><body>Accessibility</body></html>")})
        self.assertEqual(ss.read_one(ROW, get=get, sleep=no_sleep)["status"], "short")

    def test_other_host(self):
        other = "https://www.trust.example.org/accessibility-statement/"
        get = make_get({URL: (200, other, HTML, page(FILLED))})
        r = ss.read_one(ROW, get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "ok")
        self.assertTrue(r["other_host"])

    def test_bad_url(self):
        row = dict(ROW, base="")
        get = make_get({})
        self.assertEqual(ss.read_one(row, get=get, sleep=no_sleep)["status"], "bad_url")
        self.assertEqual(get.calls, [])

    def test_deadline_skips(self):
        rows = [dict(ROW, host="h%d.sch.uk" % i) for i in range(3)]
        out = ss.crawl(rows, workers=2, deadline=1.0, get=make_get({}), sleep=no_sleep)
        self.assertEqual([r["status"] for r in out], ["not_started"] * 3)


def synthetic(n_ok_ph, n_credit, n_tmpl, n_kept, n_uk, n_22, n_dead, n_other):
    rows = []

    def add(**kw):
        r = ss.blank(dict(ROW, host="h%d.sch.uk" % len(rows)))
        r.update(kw)
        rows.append(r)
    for i in range(n_ok_ph):
        add(status="ok", placeholder=True, juniper_credit=i < n_credit)
    for i in range(n_tmpl):
        add(status="ok", juniper_template=True, placeholder=i < n_kept)
    for i in range(n_uk):
        add(status="ok", gov_uk_sample=True, highest="2.2" if i < n_22 else "2.1")
    for _ in range(n_dead):
        add(status="http_0")
    for _ in range(n_other):
        add(status="http_404")
    return rows


class GradeTests(unittest.TestCase):
    def test_predictions(self):
        rows = synthetic(500, 450, 200, 100, 300, 120, 50, 1000)
        m, gates, p = ss.grade(rows)
        self.assertEqual(m["F1_hosts"], 2050)
        self.assertTrue(gates["G1_answered"])
        # 500 placeholder pages plus the 100 template pages that keep one
        self.assertEqual(m["J1_placeholder_hosts"], 600)
        self.assertEqual(p, {"J1": True, "J2": False, "J3": True, "J4": False})
        self.assertEqual(m["J2_credit_of_placeholder"], {"k": 450, "n": 600, "pct": 75.0})
        self.assertEqual(m["J3_kept_of_juniper_template"], {"k": 100, "n": 200, "pct": 50.0})
        self.assertEqual(m["J4_wcag22_of_gov_uk_wording"], {"k": 120, "n": 300, "pct": 40.0})

    def test_too_few_is_not_graded(self):
        # 20 + 20 kept template pages = 40 placeholder pages: J2 needs 50
        rows = synthetic(20, 20, 20, 20, 100, 100, 0, 10)
        _, _, p = ss.grade(rows)
        self.assertEqual(p, {"J1": False, "J2": None, "J3": None, "J4": None})

    def test_gates(self):
        rows = synthetic(500, 450, 200, 100, 300, 120, 5000, 0)
        _, gates, p = ss.grade(rows)
        self.assertFalse(gates["G1_answered"])
        self.assertEqual(p, {"J1": None, "J2": None, "J3": None, "J4": None})
        _, gates, p = ss.grade(synthetic(500, 450, 200, 100, 300, 120, 0, 0), frame_ok=False)
        self.assertFalse(gates["F1_frame"])
        self.assertIsNone(p["J1"])

    def test_described(self):
        d = ss.described(synthetic(10, 5, 4, 2, 3, 1, 1, 1))
        self.assertEqual(d["ok_pages"], 17)
        self.assertEqual(d["status"], {"ok": 17, "http_0": 1, "http_404": 1})
        self.assertEqual(d["ok_juniper_template"], 4)


class TableTests(unittest.TestCase):
    def test_round_trip(self):
        rows = synthetic(3, 1, 2, 1, 1, 1, 1, 1)
        with tempfile.TemporaryDirectory() as tmp:
            parts = ss.write_tables(tmp, rows)
            self.assertEqual(len(parts), 1)
            self.assertEqual(parts[0]["rows"], len(rows))
            with open(os.path.join(tmp, parts[0]["file"]), encoding="utf-8", newline="") as f:
                back = ss.typed(list(csv.DictReader(f)))
        self.assertEqual(ss.grade(back), ss.grade(rows))
        self.assertEqual(list(back[0].keys())[:3], ["host", "urn", "name"])


class RunTests(unittest.TestCase):
    def test_not_run_without_the_release(self):
        def fetch(url):
            raise OSError("offline")
        get = make_get({})
        with tempfile.TemporaryDirectory() as tmp:
            code = ss.main(["--out-dir", tmp], fetch=fetch, get=get, sleep=no_sleep)
            with open(os.path.join(tmp, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "not_run")
        self.assertFalse(result["gates"]["P0_checker"])
        self.assertTrue(result["gates"]["P0_prereg"])
        self.assertEqual(get.calls, [])

    def test_release_match_reads_the_local_file(self):
        with open(os.path.join(HERE, "statement_template_check.py"), "rb") as f:
            data = f.read()
        self.assertTrue(ss.checker_matches_release(HERE, fetch=lambda url: data.replace(b"\n", b"\r\n")))
        self.assertFalse(ss.checker_matches_release(HERE, fetch=lambda url: data + b"#"))


class PreregTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(HERE, *ss.PREREG_PATH.split("/")), encoding="utf-8") as f:
            cls.raw = f.read()
        cls.text = " ".join(cls.raw.split())

    def test_constants_are_the_registered_ones(self):
        for phrase in ("J1 (at least 400 hosts)", "J2 (at least 80%", "at least 50 such pages",
                       "J3 (at least 40%", "at least 100 such pages", "J4 (at least 50%",
                       "at least 200 such pages", "G1 (at least 80%", "school-stock-2026-11",
                       "`/accessibility-statement/`", "statement_template_check.py 0.3.0",
                       "24,659", "23,802", "fe6568ec3ee7", "fbb89b0c61a9", "e0b1e8ddc949"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.text)
        self.assertEqual((ss.J1_MIN_HOSTS, ss.J2_MIN_CREDIT, ss.J2_MIN_PAGES, ss.J3_MIN_KEPT,
                          ss.J3_MIN_PAGES, ss.J4_MIN_22, ss.J4_MIN_PAGES, ss.G1_MIN_ANSWERED),
                         (400, 0.80, 50, 0.40, 100, 0.50, 200, 0.80))
        self.assertEqual(ss.CRAWL_SEED, "school-stock-2026-11")
        self.assertEqual(ss.PROBE_PATH, "/accessibility-statement/")

    def test_wording(self):
        lower = self.raw.lower()
        for word in ("an ai", "by hand", "by eye"):
            self.assertNotIn(word, lower)
        self.assertIn("Made by MV2 of Munim, Inc. with AI agents", self.text)
        self.assertIn("Apache-2.0", self.text)
        self.assertIn("4(1)(c)", self.text)
        self.assertNotIn(" MIT", self.raw)


if __name__ == "__main__":
    unittest.main()
