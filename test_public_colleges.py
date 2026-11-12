# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for public_colleges.py (no network: the IPEDS file, the repository and every
website are fakes).

python -m unittest discover -p test_public_colleges.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import public_colleges as pc  # noqa: E402

sp = pc.sp
PREREG = os.path.join(HERE, *pc.PREREG_PATH.split("/"))
WORD = "s" + "aybr" + "ook"
PAD = " Students and visitors can ask for help with any page or document on this site." * 5
STATEMENT_STALE = ("<html><head><title>Accessibility</title></head><body><h1>Accessibility</h1>"
                   "<p>The college follows WCAG 2.1 Level AA. Under the ADA Title II rule, public "
                   "colleges had to meet it by April 24, 2026. Email access@ex.edu to report a "
                   "barrier." + PAD + "</p></body></html>").encode("utf-8")
HOME = (b'<html><body><a href="/accessibility">Accessibility</a>'
        b'<a href="/admissions">Admissions</a></body></html>')
MONTREAL = "Ex Community College, Montréal Campus"
HEADER = "UNITID,INSTNM,ADDR,CITY,STABBR,CHFNM,GENTELE,WEBADDR,SECTOR,CYACTIVE\n"
ROW_AAMU = ("100654,Alabama A & M University,4900 Meridian Street,Normal,AL,Dr. Jane Doe,"
            "2563725000,www.aamu.edu/,1,1\n")
IPEDS = (HEADER
         + ROW_AAMU
         + "100663,University of Alabama at Birmingham,Admin Bldg,Birmingham,AL,Some Person,"
           "2059344011,https://www.uab.edu/home,1,1\n"
         + "100700,Private College,,Xville,AL,P Q,2050000000,www.private.edu,4,1\n"
         + "100800,Closed Community College,,Yville,al,R S,2050000001,www.closed.edu,2,2\n"
         + "100900,No Site Community College,,Zville,AL,T U,2050000002,,2,1\n"
         + "101000,Branch Campus,,Wville,AL,V W,2050000003,WWW.UAB.EDU,1,1\n"
         + "101100,Guard Community College,," + WORD + " City,TX,X Y,2050000004,www.gcc.edu,2,1\n"
         + '99999,"' + MONTREAL + '",,Columbus,oh,Z A,2050000005,ex.edu,2,1\n'
         + "102000,Sector Three Center,,Vville,AL,B C,2050000006,www.tech.edu,3,1\n"
         + "\n"
         + "102100,Bad Site Community College,,Uville,AL,D E,2050000007,see catalog,2,1\n"
         ).encode("cp1252")


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


ZIP = make_zip({"HD2024.csv": IPEDS})


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
    def test_domain_of(self):
        self.assertEqual(pc.domain_of("www.aamu.edu/"), "aamu.edu")
        self.assertEqual(pc.domain_of("https://www.uab.edu/home"), "uab.edu")
        self.assertEqual(pc.domain_of("WWW.UAB.EDU"), "uab.edu")
        self.assertEqual(pc.domain_of("my.college.edu/path/"), "my.college.edu")
        self.assertEqual(pc.domain_of("http://www.x.edu:8080/"), "x.edu")
        self.assertEqual(pc.domain_of(" www.y.edu "), "y.edu")
        for bad in ("", "see catalog", "localhost", "www.foo_bar.edu", None):
            self.assertEqual(pc.domain_of(bad), "")

    def test_parse_frame(self):
        rows, info = pc.parse_frame(IPEDS)
        self.assertEqual([r["domain"] for r in rows], ["aamu.edu", "ex.edu", "uab.edu"])
        self.assertEqual([r["kind"] for r in rows], ["public_4yr", "public_2yr", "public_4yr"])
        self.assertEqual([r["unitid"] for r in rows], ["100654", "99999", "100663"])
        self.assertEqual(info, {"source_rows": 10, "sectors": {"1": 3, "2": 5, "3": 1, "4": 1},
                                "inactive": 1, "no_site": 2, "shared_host": 1, "dropped": 1,
                                "eligible": 3})
        self.assertEqual(rows[1]["organization"], MONTREAL)
        self.assertEqual((rows[1]["city"], rows[1]["state"]), ("Columbus", "OH"))
        self.assertEqual(rows[2]["organization"], "University of Alabama at Birmingham")
        self.assertEqual(set(rows[0]), set(pc.FRAME_COLUMNS))
        joined = " ".join(v for r in rows for v in r.values())
        for private in ("Jane", "2563725000", "Meridian", "Admin Bldg"):
            self.assertNotIn(private, joined)

    def test_utf8_with_bom_and_missing_columns(self):
        rows, info = pc.parse_frame(("﻿" + HEADER + ROW_AAMU).encode("utf-8"))
        self.assertEqual([r["domain"] for r in rows], ["aamu.edu"])
        self.assertEqual(info["source_rows"], 1)
        with self.assertRaises(KeyError):
            pc.parse_frame(b"UNITID,INSTNM,CITY,STABBR,SECTOR,CYACTIVE\n1,A,B,AL,1,1\n")

    def test_csv_from_zip(self):
        table, name = pc.csv_from_zip(ZIP)
        self.assertEqual((table, name), (IPEDS, "HD2024.csv"))
        with self.assertRaises(KeyError):
            pc.csv_from_zip(make_zip({"other.csv": b"x"}))

    def test_sample_is_fixed_hash_order(self):
        rows = [{"domain": "d%d.edu" % i} for i in range(10)]
        want = sorted(rows, key=lambda r: hashlib.sha256(
            ("public-colleges-2026-11-12" + r["domain"]).encode("utf-8")).hexdigest())[:3]
        self.assertEqual(pc.sample(rows, n=3), want)
        self.assertEqual(len(pc.sample(rows)), 10)

    def test_date_set_and_stale(self):
        self.assertEqual(pc.date_set({}), "none")
        self.assertEqual(pc.date_set({"old_date": True, "new_date": True}),
                         "2026-04-24+2027-04-26")
        self.assertTrue(pc.stale({"old_date": True}))
        self.assertFalse(pc.stale({"old_date": True, "new_date": True}))
        self.assertFalse(pc.stale({"old_date": True, "date_2028": True}))
        self.assertFalse(pc.stale({"new_date": True}))


class CrawlTests(unittest.TestCase):
    def test_a_stale_page_is_read_by_the_state_crawler(self):
        row = {"domain": "ex.edu", "unitid": "99999", "organization": MONTREAL, "city": "Columbus",
               "state": "OH", "kind": "public_2yr"}
        get = FakeGet({"http://ex.edu/": HOME, "http://ex.edu/accessibility": STATEMENT_STALE})
        r = sp.crawl_site(row, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["page_status"], r["highest"]), ("ok", "ok", "2.1"))
        self.assertTrue(r["old_date"])
        self.assertTrue(r["title2"])
        self.assertFalse(r["new_date"])
        self.assertFalse(r["date_2028"])
        self.assertTrue(pc.stale(r))
        self.assertEqual(pc.date_set(r), "2026-04-24")
        self.assertEqual(r["kind"], "public_2yr")


def base_row(domain, **kw):
    r = {c: "" for c in pc.COLUMNS}
    r.update({k: False for k in sp.BOOLS})
    r.update(domain=domain, candidates=0, state="OH", kind="other")
    r.update(kw)
    return r


def synthetic():
    rows = []
    for i in range(300):
        rows.append(base_row(
            "d%03d.edu" % i, home="ok", home_host="h%d.edu" % i, candidates=1, page_status="ok",
            page_url="https://h%d.edu/accessibility" % i,
            highest="2.0" if i < 40 else "2.1" if i < 200 else "2.2" if i < 230 else "",
            title2=i % 4 == 0, old_date=i < 20, new_date=10 <= i < 30, date_2028=30 <= i < 34,
            kind="public_4yr" if i < 100 else "public_2yr"))
    for i in range(50):  # lead to d000's site and page (www and a trailing slash)
        rows.append(base_row("e%03d.edu" % i, home="ok", home_host="h0.edu", candidates=1,
                             page_status="ok", page_url="https://www.h0.edu/accessibility/",
                             highest="2.0", old_date=True))
    for i in range(250):
        rows.append(base_row("f%03d.edu" % i, home="ok", home_host="g%d.edu" % i,
                             page_status="no_link"))
    for i in range(30):
        rows.append(base_row("z%03d.edu" % i, home="http_0"))
    return rows


class GradeTests(unittest.TestCase):
    def test_grade_on_distinct_pages_and_homes(self):
        m, p = pc.grade(synthetic())
        self.assertEqual(m["PC1_linked_of_homes"][:3], [300, 550, 0.5455])
        self.assertEqual(m["PC2_only_2.0_of_versioned"][:3], [40, 230, 0.1739])
        self.assertEqual(m["PC3_highest_counts"], {"2.0": 40, "2.1": 160, "2.2": 30})
        self.assertEqual(m["PC4_title2_of_pages"][:3], [75, 300, 0.25])
        self.assertEqual(m["PC5_stale_of_dated"][:3], [10, 34, 0.2941])
        self.assertEqual(p, {"PC1": False, "PC2": True, "PC3": True, "PC4": True, "PC5": True})

    def test_small_sets_are_not_graded(self):
        _, p = pc.grade(synthetic()[:19])  # 19 dated pages: one short of MIN_DATED
        self.assertEqual(set(p.values()), {None})
        _, p = pc.grade(synthetic()[:20])  # 20 dated pages: only PC5 is graded
        self.assertEqual(p, {"PC1": None, "PC2": None, "PC3": None, "PC4": None, "PC5": True})
        m, p = pc.grade([])
        self.assertEqual(set(p.values()), {None})
        self.assertEqual(m["PC1_linked_of_homes"], [0, 0, None, None])

    def test_described(self):
        d = pc.described(synthetic())
        self.assertEqual((d["domains"], d["distinct_pages"], d["distinct_home_hosts"],
                          d["domain_pages_ok"]), (630, 300, 550, 350))
        self.assertEqual(d["home"], {"ok": 600, "http_0": 30})
        self.assertEqual(d["dates"], {"none": 266, "2026-04-24": 10, "2026-04-24+2027-04-26": 10,
                                      "2027-04-26": 10, "2028-04-26": 4})
        self.assertEqual(d["by_kind"]["public_4yr"],
                         {"pages": 100, "versioned": 100, "only_2.0": 40, "2.1": 60, "2.2": 0,
                          "title2": 25, "dated": 34, "stale": 10})
        self.assertEqual(d["by_kind"]["public_2yr"],
                         {"pages": 200, "versioned": 130, "only_2.0": 0, "2.1": 100, "2.2": 30,
                          "title2": 50, "dated": 0, "stale": 0})
        self.assertEqual(set(d["by_kind"]), {"public_4yr", "public_2yr"})
        self.assertEqual(d["by_state"]["OH"]["pages"], 300)

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rows.csv")
            sp.write_csv(path, rows, pc.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, pc.COLUMNS)
                back = sp.typed(list(reader))
        self.assertEqual(len(back), 630)
        self.assertEqual(pc.grade(back), pc.grade(rows))
        self.assertEqual(pc.described(back), pc.described(rows))


class PreregWaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.files = {}
        for name in pc.PINNED:
            data = ("# %s\nprint('x')\n" % name).encode("utf-8")
            with open(os.path.join(self.tmp.name, name), "wb") as f:
                f.write(data)
            self.files[name] = data

    def tearDown(self):
        self.tmp.cleanup()

    def fetch_for(self, remote):
        def fetch(url, **kw):
            path = url.split("?n=")[0][len(pc.REPO_RAW):]
            if path in remote:
                return remote[path]
            raise OSError("404")
        return fetch

    def test_waits_until_all_pinned_files_match(self):
        remote = dict(self.files)
        remote[pc.PREREG_PATH] = b"# prereg\nPC1 PC2 PC3 PC4 PC5\n"
        remote["state_pages.py"] = remote["state_pages.py"].replace(b"\n", b"\r\n")
        self.assertEqual(pc.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=3, pause=0), (True, 1))

    def test_refuses_a_changed_file_or_missing_prereg(self):
        remote = dict(self.files)
        remote[pc.PREREG_PATH] = b"PC5"
        remote["public_colleges.py"] = b"changed"
        self.assertEqual(pc.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))
        self.assertEqual(pc.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(dict(self.files)),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))


class MainTests(unittest.TestCase):
    def make_fetch(self, frame=ZIP):
        remote = {pc.PREREG_PATH: b"# prereg PC1-PC5"}
        for name in pc.PINNED:
            with open(os.path.join(HERE, name), "rb") as f:
                remote[name] = f.read()

        def fetch(url, **kw):
            if url == pc.FRAME_URL:
                return frame
            path = url.split("?n=")[0][len(pc.REPO_RAW):]
            if url.startswith(pc.REPO_RAW) and path in remote:
                return remote[path]
            raise OSError("404 " + url)
        return fetch

    def run_main(self, fetch, get, extra=()):
        with tempfile.TemporaryDirectory() as out:
            code = pc.main(["--out-dir", out, "--delay", "0", "--workers", "2"] + list(extra),
                           fetch=fetch, get=get, sleep=no_sleep)
            got = {}
            for name in sorted(os.listdir(out)):
                with open(os.path.join(out, name), encoding="utf-8", newline="") as f:
                    got[name] = f.read()
        return code, got

    def test_no_website_read_when_frame_is_outside_the_range(self):
        get = FakeGet({})
        code, got = self.run_main(self.make_fetch(), get)
        res = json.loads(got["result.json"])
        self.assertIn("frame.csv", got)
        self.assertNotIn("rows.csv", got)
        self.assertEqual(code, 1)
        self.assertTrue(res["status"].startswith("stopped: frame size"))
        self.assertEqual(res["gates"], {"P0_prereg_public": True, "C1_frame": False})
        self.assertEqual((res["eligible"], res["frame"]["shared_host"]), (3, 1))
        self.assertEqual(res["frame"]["sha256"], hashlib.sha256(ZIP).hexdigest())
        self.assertEqual(res["frame"]["member_sha256"], hashlib.sha256(IPEDS).hexdigest())
        self.assertEqual(res["frame"]["member"], "HD2024.csv")
        self.assertEqual(get.calls, [])

    def test_stops_when_the_archive_has_no_directory_file(self):
        get = FakeGet({})
        code, got = self.run_main(self.make_fetch(make_zip({"other.csv": b"x"})), get)
        res = json.loads(got["result.json"])
        self.assertEqual(code, 1)
        self.assertEqual(res["status"], "stopped: frame not read")
        self.assertIn("hd2024.csv", res["error"])
        self.assertNotIn("frame.csv", got)
        self.assertEqual(get.calls, [])

    def test_graded_run_end_to_end(self):
        saved = pc.MIN_COHORT
        pc.MIN_COHORT = 1
        try:
            get = FakeGet({"http://ex.edu/": HOME, "http://ex.edu/accessibility": STATEMENT_STALE})
            code, got = self.run_main(self.make_fetch(), get)
        finally:
            pc.MIN_COHORT = saved
        res = json.loads(got["result.json"])
        rows = list(csv.DictReader(io.StringIO(got["rows.csv"])))
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["sampled"], res["homes_ok"], res["pages_ok"]), (3, 1, 1))
        self.assertEqual(set(res["predictions"].values()), {None})
        self.assertEqual(list(rows[0]), pc.COLUMNS)
        self.assertEqual([r["domain"] for r in rows], ["aamu.edu", "ex.edu", "uab.edu"])
        self.assertEqual([r["unitid"] for r in rows], ["100654", "99999", "100663"])
        self.assertEqual((rows[1]["page_status"], rows[1]["highest"], rows[1]["old_date"],
                          rows[1]["kind"], rows[1]["organization"]),
                         ("ok", "2.1", "True", "public_2yr", MONTREAL))
        self.assertEqual(rows[0]["home"], "http_404")
        self.assertEqual(res["described"]["dates"], {"2026-04-24": 1})
        for private in ("Jane", "2563725000", "Meridian", WORD):
            self.assertNotIn(private, got["frame.csv"])
            self.assertNotIn(private, got["rows.csv"])
        self.assertIn("predictions: PC1=None, PC2=None, PC3=None, PC4=None, PC5=None",
                      got["result.txt"])
        domains = ("aamu.edu", "ex.edu", "uab.edu")
        self.assertTrue(all(any("//" + d + "/" in u or "//www." + d + "/" in u for d in domains)
                            for u in get.calls))


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("PC1 (at least 75% of distinct home sites link to an accessibility page on "
                       "the same site)",
                       "PC2 (at most 30% of versioned pages name WCAG 2.0 as the highest version)",
                       "PC3 (WCAG 2.1 is the most common highest version)",
                       "PC4 (at least 20% of distinct pages name Title II)",
                       "PC5 (of dated pages, at least 25% give April 24, 2026 and neither later "
                       "date)",
                       "1,000 to 2,500 eligible hosts", "at most 2,500 are read",
                       "at least 100 versioned pages", "at least 200 distinct pages",
                       "at least 500 distinct home sites", "at least 20 dated pages",
                       "`public-colleges-2026-11-12`", "`HD2024.zip`", "`HD2024.csv`",
                       "within 150 minutes", "24 sites at a time",
                       "283 of 508", "179 of 808", "815 of 1,195", "12 of 17", "(55.71%)",
                       "(22.15%)", "(68.20%)", "(70.59%)"):
            self.assertIn(" ".join(phrase.split()), text)
        self.assertEqual((pc.PC1_MIN_LINKED, pc.PC2_MAX_ONLY_20, pc.PC4_MIN_TITLE2,
                          pc.PC5_MIN_STALE_OF_DATED), (0.75, 0.30, 0.20, 0.25))
        self.assertEqual((pc.MIN_VERSIONED, pc.MIN_PAGES, pc.MIN_HOMES, pc.MIN_DATED),
                         (100, 200, 500, 20))
        self.assertEqual((pc.MIN_COHORT, pc.MAX_COHORT, pc.SAMPLE_N, pc.SEED),
                         (1000, 2500, 2500, "public-colleges-2026-11-12"))
        self.assertEqual(pc.FRAME_URL, "https://nces.ed.gov/ipeds/datacenter/data/HD2024.zip")
        self.assertEqual(pc.SECTORS, {"1": "public_4yr", "2": "public_2yr"})
        self.assertIsNone(pc.GUARD_RE.search(text))
        # The context figures quoted in the plan, recomputed.
        for k, n, pct in ((283, 508, "55.71"), (179, 808, "22.15"), (815, 1195, "68.20"),
                          (12, 17, "70.59")):
            self.assertEqual("%.2f" % (100.0 * k / n), pct)

    def test_pinned_versions(self):
        self.assertEqual((pc.__version__, sp.__version__, pc.ap.__version__, pc.sc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0", "0.1.0"))
        self.assertEqual(pc.ap.MAX_TRIES, 3)
        self.assertEqual(pc.ap.MIN_TEXT, 200)


if __name__ == "__main__":
    unittest.main()
