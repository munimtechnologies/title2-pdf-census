# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for special_districts.py (no network: the registry list, the repository and
every website are fakes).

python -m unittest discover -p test_special_districts.py
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
import special_districts as sd  # noqa: E402

sp = sd.sp
PREREG = os.path.join(HERE, *sd.PREREG_PATH.split("/"))
WORD = "s" + "aybr" + "ook"
PAD = " Customers can ask for help with any page or document on this site." * 5
STATEMENT_2028 = ("<html><head><title>Accessibility</title></head><body><h1>Accessibility</h1>"
                  "<p>The district follows WCAG 2.1 Level AA. Under the ADA Title II rule, special "
                  "district governments must meet it by April 26, 2028. Email access@ex.gov to "
                  "report a barrier." + PAD + "</p></body></html>").encode("utf-8")
HOME = (b'<html><body><a href="/accessibility">Accessibility</a>'
        b'<a href="/rates">Rates</a></body></html>')
HEADER = ("Domain name,Domain type,Organization name,Suborganization name,City,State,"
          "Security contact email\n")
CISA = ("﻿" + HEADER
        + "29palms.gov,City,City of Twentynine Palms,,Twentynine Palms,CA,\n"
        + "agutah.gov,State or territory,Utah Attorney General's Office,,Salt Lake City,UT,"
          "sec@agutah.gov\n"
        + "bart.gov,Special district,San Francisco Bay Area Rapid Transit District,,Oakland,CA,"
          "sec@bart.gov\n"
        + "TVFR.GOV,Special district,Tualatin Valley Fire & Rescue,,Aurora,or,(blank)\n"
        + "tvfr.gov,Special district,Tualatin Valley Fire & Rescue,,Aurora,or,(blank)\n"
        + WORD + "water.gov,Special district,Some Water District,,Austin,tx,\n"
        + '"ex.gov",Special district,"Example Park District, North",Sub,Columbus,oh,a@b.gov\n'
        + "zone7water.gov,Special district,Zone 7 Water Agency,,Livermore,CA,it@zone7water.gov\n"
        ).encode("utf-8")


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
        rows, info = sd.parse_frame(CISA)
        self.assertEqual([r["domain"] for r in rows],
                         ["bart.gov", "ex.gov", "tvfr.gov", "zone7water.gov"])
        self.assertEqual([r["kind"] for r in rows], ["transit", "parks", "fire", "water"])
        self.assertEqual(info, {"source_rows": 8, "dropped": 1, "eligible": 4,
                                "types": {"City": 1, "Special district": 6,
                                          "State or territory": 1}})
        self.assertEqual(rows[1]["organization"], "Example Park District, North")
        self.assertEqual((rows[1]["suborganization"], rows[1]["state"]), ("Sub", "OH"))
        self.assertEqual(rows[2]["state"], "OR")
        self.assertEqual(set(rows[0]), set(sd.FRAME_COLUMNS))
        self.assertFalse(any("@" in v for r in rows for v in r.values()))

    def test_kind_of(self):
        self.assertEqual(sd.kind_of("Lucas County 911 Regional Council"), "emergency")
        self.assertEqual(sd.kind_of("West Metro Fire-Rescue District"), "fire")
        self.assertEqual(sd.kind_of("Tridell-Lapoint Water Improvement District"), "water")
        self.assertEqual(sd.kind_of("Metropolitan Sewer District"), "water")
        self.assertEqual(sd.kind_of("Port of Seattle"), "transit")
        self.assertEqual(sd.kind_of("Columbus Metropolitan Library"), "library")
        self.assertEqual(sd.kind_of("Portland Parks Foundation"), "parks")
        self.assertEqual(sd.kind_of("Valley Hospital District"), "health")
        self.assertEqual(sd.kind_of("Housing Authority of X"), "housing")
        self.assertEqual(sd.kind_of("Los Angeles County Employees Retirement Association"),
                         "other")
        self.assertEqual(sd.kind_of("Some District", "Recreation Department"), "parks")

    def test_sample_is_fixed_hash_order(self):
        rows = [{"domain": "d%d.gov" % i} for i in range(10)]
        want = sorted(rows, key=lambda r: hashlib.sha256(
            ("special-districts-2026-11-11" + r["domain"]).encode("utf-8")).hexdigest())[:3]
        self.assertEqual(sd.sample(rows, n=3), want)
        self.assertEqual(len(sd.sample(rows)), 10)

    def test_date_set(self):
        self.assertEqual(sd.date_set({}), "none")
        self.assertEqual(sd.date_set({"old_date": True, "date_2028": True}),
                         "2026-04-24+2028-04-26")
        self.assertEqual(sd.date_set({"new_date": True, "old_date": False}), "2027-04-26")


class CrawlTests(unittest.TestCase):
    def test_a_2028_page_is_read_by_the_state_crawler(self):
        row = {"domain": "ex.gov", "organization": "Example Water District", "suborganization": "",
               "city": "Columbus", "state": "OH", "kind": "water"}
        get = FakeGet({"http://ex.gov/": HOME, "http://ex.gov/accessibility": STATEMENT_2028})
        r = sp.crawl_site(row, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["page_status"], r["highest"]), ("ok", "ok", "2.1"))
        self.assertTrue(r["date_2028"])
        self.assertTrue(r["title2"])
        self.assertFalse(r["old_date"])
        self.assertFalse(r["new_date"])
        self.assertEqual(sd.date_set(r), "2028-04-26")
        self.assertEqual(r["kind"], "water")


def base_row(domain, **kw):
    r = {c: "" for c in sd.COLUMNS}
    r.update({k: False for k in sp.BOOLS})
    r.update(domain=domain, candidates=0, state="OH", kind="other")
    r.update(kw)
    return r


def synthetic():
    rows = []
    for i in range(300):
        rows.append(base_row(
            "d%03d.gov" % i, home="ok", home_host="h%d.gov" % i, candidates=1, page_status="ok",
            page_url="https://h%d.gov/accessibility" % i,
            highest="2.0" if i < 160 else "2.1" if i < 240 else "2.2" if i < 250 else "",
            title2=i % 5 == 0, old_date=i < 6, new_date=6 <= i < 12, date_2028=12 <= i < 16,
            stock=i < 30, kind="fire" if i < 100 else "water"))
    for i in range(50):  # lead to d000's site and page (www and a trailing slash)
        rows.append(base_row("e%03d.gov" % i, home="ok", home_host="h0.gov", candidates=1,
                             page_status="ok", page_url="https://www.h0.gov/accessibility/",
                             highest="2.0", date_2028=True))
    for i in range(250):
        rows.append(base_row("f%03d.gov" % i, home="ok", home_host="g%d.gov" % i,
                             page_status="no_link"))
    for i in range(30):
        rows.append(base_row("z%03d.gov" % i, home="http_0"))
    return rows


class GradeTests(unittest.TestCase):
    def test_grade_on_distinct_pages_and_homes(self):
        m, p = sd.grade(synthetic())
        self.assertEqual(m["SD1_only_2.0_of_versioned"][:3], [160, 250, 0.64])
        self.assertEqual(m["highest_counts"], {"2.0": 160, "2.1": 80, "2.2": 10})
        self.assertEqual(m["SD2_title2_of_pages"][:3], [60, 300, 0.2])
        self.assertEqual(m["SD3_2028_of_pages"][:3], [4, 300, 0.0133])
        self.assertEqual(m["SD4_linked_of_homes"][:3], [300, 550, 0.5455])
        self.assertEqual(m["SD5_2028_of_dated"][:3], [4, 16, 0.25])
        self.assertEqual(p, {"SD1": True, "SD2": False, "SD3": True, "SD4": True, "SD5": True})

    def test_small_sets_are_not_graded(self):
        _, p = sd.grade(synthetic()[:9])  # 9 dated pages: one short of MIN_DATED
        self.assertEqual(set(p.values()), {None})
        _, p = sd.grade(synthetic()[:10])  # 10 dated pages: only SD5 is graded
        self.assertEqual(p, {"SD1": None, "SD2": None, "SD3": None, "SD4": None, "SD5": True})
        m, p = sd.grade([])
        self.assertEqual(set(p.values()), {None})
        self.assertEqual(m["SD4_linked_of_homes"], [0, 0, None, None])

    def test_described(self):
        d = sd.described(synthetic())
        self.assertEqual((d["domains"], d["distinct_pages"], d["distinct_home_hosts"],
                          d["domain_pages_ok"]), (630, 300, 550, 350))
        self.assertEqual(d["home"], {"ok": 600, "http_0": 30})
        self.assertEqual(d["dates"], {"none": 284, "2026-04-24": 6, "2027-04-26": 6,
                                      "2028-04-26": 4})
        self.assertEqual(d["stock"], 30)
        self.assertEqual(d["by_kind"]["fire"], {"pages": 100, "versioned": 100, "only_2.0": 100,
                                                "title2": 20, "dated": 16, "date_2028": 4})
        self.assertEqual(d["by_kind"]["water"]["only_2.0"], 60)
        self.assertEqual(d["by_kind"]["water"]["versioned"], 150)
        self.assertEqual(set(d["by_kind"]), {"fire", "water"})
        self.assertEqual(d["by_state"]["OH"]["pages"], 300)

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rows.csv")
            sp.write_csv(path, rows, sd.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, sd.COLUMNS)
                back = sp.typed(list(reader))
        self.assertEqual(len(back), 630)
        self.assertEqual(sd.grade(back), sd.grade(rows))
        self.assertEqual(sd.described(back), sd.described(rows))


class PreregWaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.files = {}
        for name in sd.PINNED:
            data = ("# %s\nprint('x')\n" % name).encode("utf-8")
            with open(os.path.join(self.tmp.name, name), "wb") as f:
                f.write(data)
            self.files[name] = data

    def tearDown(self):
        self.tmp.cleanup()

    def fetch_for(self, remote):
        def fetch(url, **kw):
            path = url.split("?n=")[0][len(sd.REPO_RAW):]
            if path in remote:
                return remote[path]
            raise OSError("404")
        return fetch

    def test_waits_until_all_pinned_files_match(self):
        remote = dict(self.files)
        remote[sd.PREREG_PATH] = b"# prereg\nSD1 SD2 SD3 SD4 SD5\n"
        remote["state_pages.py"] = remote["state_pages.py"].replace(b"\n", b"\r\n")
        self.assertEqual(sd.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=3, pause=0), (True, 1))

    def test_refuses_a_changed_file_or_missing_prereg(self):
        remote = dict(self.files)
        remote[sd.PREREG_PATH] = b"SD5"
        remote["state_pages.py"] = b"changed"
        self.assertEqual(sd.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))
        self.assertEqual(sd.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(dict(self.files)),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))


class MainTests(unittest.TestCase):
    def make_fetch(self):
        remote = {sd.PREREG_PATH: b"# prereg SD1-SD5"}
        for name in sd.PINNED:
            with open(os.path.join(HERE, name), "rb") as f:
                remote[name] = f.read()

        def fetch(url, **kw):
            if url == sd.FRAME_URL:
                return CISA
            path = url.split("?n=")[0][len(sd.REPO_RAW):]
            if url.startswith(sd.REPO_RAW) and path in remote:
                return remote[path]
            raise OSError("404 " + url)
        return fetch

    def test_no_website_read_when_frame_is_outside_the_range(self):
        get = FakeGet({})
        with tempfile.TemporaryDirectory() as out:
            code = sd.main(["--out-dir", out], fetch=self.make_fetch(), get=get, sleep=no_sleep)
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
        saved = sd.MIN_COHORT
        sd.MIN_COHORT = 1
        try:
            get = FakeGet({"http://ex.gov/": HOME, "http://ex.gov/accessibility": STATEMENT_2028})
            with tempfile.TemporaryDirectory() as out:
                code = sd.main(["--out-dir", out, "--delay", "0", "--workers", "2"],
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
            sd.MIN_COHORT = saved
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["sampled"], res["homes_ok"], res["pages_ok"]), (4, 1, 1))
        self.assertEqual(set(res["predictions"].values()), {None})
        self.assertEqual([r["domain"] for r in rows],
                         ["bart.gov", "ex.gov", "tvfr.gov", "zone7water.gov"])
        self.assertEqual((rows[1]["page_status"], rows[1]["highest"], rows[1]["date_2028"],
                          rows[1]["kind"]), ("ok", "2.1", "True", "parks"))
        self.assertEqual(rows[0]["home"], "http_404")
        self.assertEqual(res["described"]["dates"], {"2028-04-26": 1})
        self.assertNotIn("@", frame)
        self.assertIn("predictions: SD1=None, SD2=None, SD3=None, SD4=None, SD5=None", text)
        domains = ("bart.gov", "ex.gov", "tvfr.gov", "zone7water.gov")
        self.assertTrue(all(any("//" + d + "/" in u or "//www." + d + "/" in u for d in domains)
                            for u in get.calls))


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("SD1 (at least 50% of versioned pages name WCAG 2.0 as the highest version)",
                       "SD2 (at most 15% of distinct pages name Title II)",
                       "SD3 (at most 5% of distinct pages give April 26, 2028)",
                       "SD4 (at most 60% of distinct home sites link to an accessibility page on "
                       "the same site)",
                       "SD5 (of dated pages, at most half give April 26, 2028)",
                       "800 to 3,000 eligible domains", "at most 3,000 are read",
                       "at least 100 versioned pages", "at least 200 distinct pages",
                       "at least 400 distinct home sites", "at least 10 dated pages",
                       "`special-districts-2026-11-11`", "`Special district`",
                       "within 150 minutes", "24 sites at a time",
                       "283 of 508", "179 of 808", "815 of 1,195", "638 of 809", "94 of 1,042",
                       "1,053 of 1,942", "280 of 808", "698 of 1,042", "(55.71%)", "(78.86%)",
                       "(22.15%)", "(9.02%)", "(54.22%)"):
            self.assertIn(" ".join(phrase.split()), text)
        self.assertEqual((sd.SD1_MIN_ONLY_20, sd.SD2_MAX_TITLE2, sd.SD3_MAX_2028,
                          sd.SD4_MAX_LINKED, sd.SD5_MAX_2028_OF_DATED),
                         (0.50, 0.15, 0.05, 0.60, 0.50))
        self.assertEqual((sd.MIN_VERSIONED, sd.MIN_PAGES, sd.MIN_HOMES, sd.MIN_DATED),
                         (100, 200, 400, 10))
        self.assertEqual((sd.MIN_COHORT, sd.MAX_COHORT, sd.SAMPLE_N, sd.SEED, sd.FRAME_TYPE),
                         (800, 3000, 3000, "special-districts-2026-11-11", "Special district"))
        self.assertEqual(sd.FRAME_URL, "https://raw.githubusercontent.com/cisagov/dotgov-data/"
                                       "main/current-full.csv")
        self.assertIsNone(sd.GUARD_RE.search(text))
        # The context figures quoted in the plan, recomputed.
        for k, n, pct in ((283, 508, "55.71"), (638, 809, "78.86"), (179, 808, "22.15"),
                          (94, 1042, "9.02"), (1053, 1942, "54.22")):
            self.assertEqual("%.2f" % (100.0 * k / n), pct)

    def test_pinned_versions(self):
        self.assertEqual((sd.__version__, sp.__version__, sd.ap.__version__, sd.sc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0", "0.1.0"))
        self.assertEqual(sd.ap.MAX_TRIES, 3)
        self.assertEqual(sd.ap.MIN_TEXT, 200)


if __name__ == "__main__":
    unittest.main()
