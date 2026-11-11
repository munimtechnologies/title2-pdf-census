# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for state_pages.py (no network: the registry list, the repository and every
website are fakes).

python -m unittest discover -p test_state_pages.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_pages as sp  # noqa: E402

PREREG = os.path.join(HERE, *sp.PREREG_PATH.split("/"))
WORD = "s" + "aybr" + "ook"
PAD = " Residents can ask for help with any page or document on this site." * 5
STATEMENT_21 = ("<html><head><title>Accessibility</title></head><body><h1>Accessibility</h1>"
                "<p>The department follows WCAG 2.1 Level AA, as the ADA Title II rule requires by "
                "April 26, 2027. Email access@ex.gov to report a barrier." + PAD
                + "</p></body></html>").encode("utf-8")
STATEMENT_20 = ("<html><body><h1>Accessibility</h1><p>We work to comply with Section 508 as well "
                "as WCAG 2.0 A and AA. Our date under Title II was April 24, 2026." + PAD
                + "</p></body></html>").encode("utf-8")
HOME = (b'<html><body><a href="/accessibility">Accessibility</a>'
        b'<a href="/parks">Parks</a></body></html>')
HEADER = ("Domain name,Domain type,Organization name,Suborganization name,City,State,"
          "Security contact email\n")
CISA = ("﻿" + HEADER
        + "29palms.gov,City,City of Twentynine Palms,,Twentynine Palms,CA,\n"
        + "agutah.gov,State or territory,Utah Attorney General's Office,,Salt Lake City,UT,"
          "sec@agutah.gov\n"
        + "AKCOURTS.GOV,State or territory,State of Alaska Court System,,Anchorage,AK,(blank)\n"
        + "coleg.gov,State or territory,Colorado General Assembly,,Denver,CO,it@coleg.gov\n"
        + "coleg.gov,State or territory,Colorado General Assembly,,Denver,CO,it@coleg.gov\n"
        + WORD + "state.gov,State or territory,Some Office,,Austin,tx,\n"
        + "bart.gov,Special district,San Francisco Bay Area Rapid Transit District,,Oakland,CA,\n"
        + '"ex.gov",State or territory,"Example Dept, Health",Sub,Columbus,oh,a@b.gov\n'
        ).encode("utf-8")
ROW = {"domain": "ex.gov", "organization": "Example Dept", "suborganization": "",
       "city": "Columbus", "state": "OH", "kind": "executive_other"}


class FakeGet:
    """Pages by exact address; addresses under a dead prefix get no answer (0); else 404."""

    def __init__(self, pages, dead=()):
        self.pages, self.dead, self.calls = pages, dead, []

    def __call__(self, url, max_bytes=3_000_000, timeout=20):
        self.calls.append(url)
        if url in self.pages:
            return 200, url, "text/html; charset=utf-8", self.pages[url]
        if any(url.startswith(d) for d in self.dead):
            return 0, url, "", b""
        return 404, url, "", b""


def no_sleep(_s):
    return None


class FrameTests(unittest.TestCase):
    def test_parse_frame(self):
        rows, info = sp.parse_frame(CISA)
        self.assertEqual([r["domain"] for r in rows],
                         ["agutah.gov", "akcourts.gov", "coleg.gov", "ex.gov"])
        self.assertEqual([r["kind"] for r in rows],
                         ["executive_other", "court", "legislature", "executive_other"])
        self.assertEqual(info, {"source_rows": 8, "dropped": 1, "eligible": 4,
                                "types": {"City": 1, "Special district": 1,
                                          "State or territory": 6}})
        self.assertEqual(rows[3]["organization"], "Example Dept, Health")
        self.assertEqual((rows[3]["suborganization"], rows[3]["state"]), ("Sub", "OH"))
        self.assertEqual(set(rows[0]), set(sp.FRAME_COLUMNS))
        self.assertFalse(any("@" in v for r in rows for v in r.values()))

    def test_kind_of(self):
        self.assertEqual(sp.kind_of("First Judicial Circuit"), "court")
        self.assertEqual(sp.kind_of("Supreme Court of Ohio"), "court")
        self.assertEqual(sp.kind_of("Guam Legislature"), "legislature")
        self.assertEqual(sp.kind_of("Virginia House of Delegates"), "legislature")
        self.assertEqual(sp.kind_of("State of X", "Senate"), "legislature")
        self.assertEqual(sp.kind_of("Arizona Dept of Environmental Quality"), "executive_other")

    def test_sample_is_fixed_hash_order(self):
        rows = [{"domain": "d%d.gov" % i} for i in range(10)]
        want = sorted(rows, key=lambda r: hashlib.sha256(
            ("state-pages-2026-11-11" + r["domain"]).encode("utf-8")).hexdigest())[:3]
        self.assertEqual(sp.sample(rows, n=3), want)
        self.assertEqual(len(sp.sample(rows)), 10)


class CrawlTests(unittest.TestCase):
    def test_www_fallback_and_updated_page(self):
        get = FakeGet({"http://www.ex.gov/": HOME, "http://www.ex.gov/accessibility": STATEMENT_21},
                      dead=("http://ex.gov",))
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["home_via"], r["home_host"]), ("ok", "www", "ex.gov"))
        self.assertEqual((r["candidates"], r["page_status"], r["page_rank"]), (1, "ok", 0))
        self.assertEqual(r["page_url"], "http://www.ex.gov/accessibility")
        self.assertEqual(r["highest"], "2.1")
        self.assertTrue(r["title2"])
        self.assertTrue(r["new_date"])
        self.assertFalse(r["old_date"])
        self.assertFalse(r["date_2028"])
        self.assertFalse(r["stock"])
        self.assertTrue(r["contact"])
        self.assertEqual(r["findings"], "")
        self.assertIn("[email]", r["date_snippet"])
        self.assertNotIn("@", r["date_snippet"])
        self.assertEqual(get.calls, ["http://ex.gov/robots.txt", "http://ex.gov/",
                                     "http://www.ex.gov/robots.txt", "http://www.ex.gov/",
                                     "http://www.ex.gov/accessibility"])

    def test_old_page(self):
        get = FakeGet({"http://ex.gov/": HOME, "http://ex.gov/accessibility": STATEMENT_20})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["home_via"]), ("ok", "bare"))
        self.assertEqual(r["highest"], "2.0")
        self.assertTrue(r["stock"])
        self.assertTrue(r["old_date"])
        self.assertTrue(r["section508"])
        self.assertEqual(r["findings"], "wcag-2.0+stock-sentence+old-date")
        self.assertEqual(get.calls, ["http://ex.gov/robots.txt", "http://ex.gov/",
                                     "http://ex.gov/accessibility"])

    def test_dead_home_no_link_and_robots(self):
        r = sp.crawl_site(ROW, get=FakeGet({}, dead=("http://ex.gov", "http://www.ex.gov")),
                          delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["home_via"]), ("http_0", "www"))
        r = sp.crawl_site(ROW, get=FakeGet({}), delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["home_via"]), ("http_404", "bare"))
        get = FakeGet({"http://ex.gov/": b"<html><body><a href='/parks'>Parks</a></body></html>"})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["page_status"], r["candidates"]), ("ok", "no_link", 0))
        get = FakeGet({"http://ex.gov/robots.txt": b"User-agent: *\nDisallow: /\n",
                       "http://ex.gov/": HOME})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["home_via"]), ("robots", "bare"))
        self.assertEqual(get.calls, ["http://ex.gov/robots.txt"])


def base_row(domain, **kw):
    r = {c: "" for c in sp.COLUMNS}
    r.update({k: False for k in sp.BOOLS})
    r.update(domain=domain, candidates=0, state="OH", kind="executive_other")
    r.update(kw)
    return r


def synthetic():
    rows = []
    for i in range(300):
        rows.append(base_row(
            "d%03d.gov" % i, home="ok", home_host="h%d.gov" % i, candidates=1, page_status="ok",
            page_url="https://h%d.gov/accessibility" % i,
            highest="2.0" if i < 90 else "2.1" if i < 220 else "2.2" if i < 240 else "",
            title2=i % 4 == 0, stock=i < 10, old_date=i < 3, new_date=3 <= i < 8))
    for i in range(50):  # lead to d000's site and page (www and a trailing slash)
        rows.append(base_row("e%03d.gov" % i, home="ok", home_host="h0.gov", candidates=1,
                             page_status="ok", page_url="https://www.h0.gov/accessibility/",
                             highest="2.0"))
    for i in range(200):
        rows.append(base_row("f%03d.gov" % i, home="ok", home_host="g%d.gov" % i,
                             page_status="no_link"))
    for i in range(30):
        rows.append(base_row("z%03d.gov" % i, home="http_0"))
    return rows


class GradeTests(unittest.TestCase):
    def test_grade_on_distinct_pages_and_homes(self):
        m, p = sp.grade(synthetic())
        self.assertEqual(m["ST1_only_2.0_of_versioned"][:3], [90, 240, 0.375])
        self.assertEqual(m["ST2_highest_counts"], {"2.0": 90, "2.1": 130, "2.2": 20})
        self.assertEqual(m["ST3_title2_of_pages"][:3], [75, 300, 0.25])
        self.assertEqual(m["ST4_stock_of_pages"][:3], [10, 300, 0.0333])
        self.assertEqual(m["ST5_linked_of_homes"][:3], [300, 500, 0.6])
        self.assertEqual(p, {"ST1": True, "ST2": True, "ST3": False, "ST4": True, "ST5": False})

    def test_small_sets_are_not_graded(self):
        _, p = sp.grade(synthetic()[:10])
        self.assertEqual(set(p.values()), {None})
        m, p = sp.grade([])
        self.assertEqual(m["ST5_linked_of_homes"], [0, 0, None, None])

    def test_described(self):
        d = sp.described(synthetic())
        self.assertEqual((d["domains"], d["distinct_pages"], d["distinct_home_hosts"],
                          d["domain_pages_ok"]), (580, 300, 500, 350))
        self.assertEqual((d["date_2026_04_24"], d["date_2027_04_26"], d["only_2026_04_24"]),
                         (3, 5, 3))
        self.assertEqual(d["home"], {"ok": 550, "http_0": 30})
        self.assertEqual(d["by_state"]["OH"]["only_2.0"], 90)

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rows.csv")
            sp.write_csv(path, rows, sp.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, sp.COLUMNS)
                back = sp.typed(list(reader))
        self.assertEqual(len(back), 580)
        self.assertEqual(sp.grade(back), sp.grade(rows))
        self.assertEqual(sp.described(back), sp.described(rows))

    def test_guard_word_cells_are_withheld(self):
        self.assertEqual(sp.cell("x " + WORD.upper() + " y"), "[withheld]")
        self.assertEqual(sp.cell(True), "True")
        self.assertEqual(sp.cell(None), "")


class PreregWaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.files = {}
        for name in sp.PINNED:
            data = ("# %s\nprint('x')\n" % name).encode("utf-8")
            with open(os.path.join(self.tmp.name, name), "wb") as f:
                f.write(data)
            self.files[name] = data

    def tearDown(self):
        self.tmp.cleanup()

    def fetch_for(self, remote):
        def fetch(url, **kw):
            path = url.split("?n=")[0][len(sp.REPO_RAW):]
            if path in remote:
                return remote[path]
            raise OSError("404")
        return fetch

    def test_waits_until_all_pinned_files_match(self):
        remote = dict(self.files)
        remote[sp.PREREG_PATH] = b"# prereg\nST1 ST2 ST3 ST4 ST5\n"
        remote["a11y_pages.py"] = remote["a11y_pages.py"].replace(b"\n", b"\r\n")
        self.assertEqual(sp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=3, pause=0), (True, 1))

    def test_refuses_a_changed_file_or_missing_prereg(self):
        remote = dict(self.files)
        remote[sp.PREREG_PATH] = b"ST5"
        remote["statement_check.py"] = b"changed"
        self.assertEqual(sp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))
        self.assertEqual(sp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(dict(self.files)),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))


class MainTests(unittest.TestCase):
    def make_fetch(self):
        remote = {sp.PREREG_PATH: b"# prereg ST1-ST5"}
        for name in sp.PINNED:
            with open(os.path.join(HERE, name), "rb") as f:
                remote[name] = f.read()

        def fetch(url, **kw):
            if url == sp.FRAME_URL:
                return CISA
            path = url.split("?n=")[0][len(sp.REPO_RAW):]
            if url.startswith(sp.REPO_RAW) and path in remote:
                return remote[path]
            raise OSError("404 " + url)
        return fetch

    def test_no_website_read_when_frame_is_outside_the_range(self):
        get = FakeGet({})
        with tempfile.TemporaryDirectory() as out:
            code = sp.main(["--out-dir", out], fetch=self.make_fetch(), get=get, sleep=no_sleep)
            with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertTrue(os.path.exists(os.path.join(out, "frame.csv")))
            self.assertFalse(os.path.exists(os.path.join(out, "rows.csv")))
        self.assertEqual(code, 1)
        self.assertTrue(res["status"].startswith("stopped: frame size"))
        self.assertEqual(res["gates"], {"P0_prereg_public": True, "C1_frame": False})
        self.assertEqual((res["eligible"], res["frame"]["dropped"]), (4, 1))
        self.assertEqual(res["frame"]["sha256"], hashlib.sha256(CISA).hexdigest())
        self.assertEqual(get.calls, [])

    def test_graded_run_end_to_end(self):
        saved = sp.MIN_COHORT
        sp.MIN_COHORT = 1
        try:
            get = FakeGet({"http://ex.gov/": HOME, "http://ex.gov/accessibility": STATEMENT_21})
            with tempfile.TemporaryDirectory() as out:
                code = sp.main(["--out-dir", out, "--delay", "0", "--workers", "2"],
                               fetch=self.make_fetch(), get=get, sleep=no_sleep)
                with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                    res = json.load(f)
                with open(os.path.join(out, "rows.csv"), encoding="utf-8", newline="") as f:
                    rows = list(csv.DictReader(f))
                with open(os.path.join(out, "frame.csv"), encoding="utf-8") as f:
                    frame = f.read()
                with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
                    text = f.read()
        finally:
            sp.MIN_COHORT = saved
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["sampled"], res["homes_ok"], res["pages_ok"]), (4, 1, 1))
        self.assertEqual(set(res["predictions"].values()), {None})
        self.assertEqual([r["domain"] for r in rows],
                         ["agutah.gov", "akcourts.gov", "coleg.gov", "ex.gov"])
        self.assertEqual((rows[3]["page_status"], rows[3]["highest"], rows[3]["title2"]),
                         ("ok", "2.1", "True"))
        self.assertEqual(rows[0]["home"], "http_404")
        self.assertNotIn("@", frame)
        self.assertIn("predictions: ST1=None, ST2=None, ST3=None, ST4=None, ST5=None", text)
        domains = ("agutah.gov", "akcourts.gov", "coleg.gov", "ex.gov")
        self.assertTrue(all(any("//" + d + "/" in u or "//www." + d + "/" in u for d in domains)
                            for u in get.calls))


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("ST1 (at most 40% of versioned pages name WCAG 2.0 as the highest version)",
                       "ST2 (WCAG 2.1 is the highest version on more versioned pages than 2.0, "
                       "and on more than 2.2)",
                       "ST3 (at most 22.15% of distinct pages name Title II)",
                       "ST4 (at most 5% of distinct pages carry the stock sentence)",
                       "ST5 (at least 70% of distinct home sites link to an accessibility page on "
                       "the same site)",
                       "1,000 to 4,000 eligible domains", "at most 2,000 are read",
                       "at least 100 versioned pages", "at least 200 distinct pages",
                       "at least 500 distinct home sites", "`state-pages-2026-11-11`",
                       "`State or territory`", "within 150 minutes", "24 sites at a time",
                       "283 of 508", "179 of 808", "280 of 808", "815 of 1,195"):
            self.assertIn(" ".join(phrase.split()), text)
        self.assertEqual((sp.ST1_MAX_ONLY_20, sp.ST3_MAX_TITLE2, sp.ST4_MAX_STOCK,
                          sp.ST5_MIN_LINKED, sp.MIN_VERSIONED, sp.MIN_PAGES, sp.MIN_HOMES),
                         (0.40, 0.2215, 0.05, 0.70, 100, 200, 500))
        self.assertEqual((sp.MIN_COHORT, sp.MAX_COHORT, sp.SAMPLE_N, sp.SEED, sp.FRAME_TYPE),
                         (1000, 4000, 2000, "state-pages-2026-11-11", "State or territory"))
        self.assertEqual(sp.FRAME_URL, "https://raw.githubusercontent.com/cisagov/dotgov-data/"
                                       "main/current-full.csv")
        self.assertIsNone(sp.GUARD_RE.search(text))

    def test_pinned_versions(self):
        self.assertEqual((sp.__version__, sp.ap.__version__, sp.sc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0"))
        self.assertEqual(sp.ap.MAX_TRIES, 3)
        self.assertEqual(sp.ap.MIN_TEXT, 200)


if __name__ == "__main__":
    unittest.main()
