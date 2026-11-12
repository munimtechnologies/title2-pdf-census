# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for hc_pages.py (no network: the HRSA file, the repository and every website are
fakes).

python -m unittest discover -p test_hc_pages.py
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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hc_pages as hc  # noqa: E402

sp = hc.sp
PREREG = os.path.join(HERE, *hc.PREREG_PATH.split("/"))
WORD = "s" + "aybr" + "ook"
PAD = " Patients and visitors can ask for help with any page or form on this site." * 5
STATEMENT = ("<html><head><title>Accessibility</title></head><body><h1>Accessibility</h1>"
             "<p>Alpha Health follows WCAG 2.1 Level AA. As a recipient of HHS funding under "
             "Section 504, we will meet it by May 11, 2026. Email access@alpha.org to report a "
             "barrier." + PAD + "</p></body></html>").encode("utf-8")
HOME = (b'<html><head><script src="https://cdn.userway.org/widget.js"></script></head><body>'
        b'<a href="/accessibility">Accessibility</a><a href="/patients">Patients</a></body></html>')
KAPPA = "Kappa Clinic, Montréal Wing"
HEADER = ("Health Center Type,Health Center Number,Site Name,Site Address,Site Telephone Number,"
          "Site Web Address,Site Status Description,Health Center Name,"
          "Health Center Organization City,Health Center Organization State\n")
SITES = (HEADER
         + "FQHC,H80CS00001,Main Clinic,1 Elm St,555-123-4567,www.alpha.org,Active,Alpha Health,"
           "Columbus,oh\n"
         + "FQHC,H80CS00001,School Clinic,2 Oak St,555-123-4568,https://www.westschools.org/clinic,"
           "Active,Alpha Health,Columbus,oh\n"
         + "FQHC,H80CS00001,Dental,3 Pine St,555-123-4569,alpha.org/dental,Active,Alpha Health,"
           "Columbus,oh\n"
         + "FQHC,H80CS00002,Beta Main,4 Ash St,555-123-4570,https://beta.org,Active,Beta Care,"
           "Akron,OH\n"
         + "FQHC,H80CS00002,Beta Old,5 Fir St,555-123-4571,https://www.oldbeta.org,Inactive,"
           "Beta Care,Akron,OH\n"
         + "FQHC,H80CS00003,Gamma A,6 Elm St,555-123-4572,zeta.org,Active,Gamma Clinics,Dayton,OH\n"
         + "FQHC,H80CS00003,Gamma B,7 Elm St,555-123-4573,gamma.org,Active,Gamma Clinics,Dayton,OH\n"
         + "Look-Alike,LALCS00004,Delta,8 Elm St,555-123-4574,https://www.facebook.com/delta,Active,"
           "Delta Center,Erie,PA\n"
         + "Look-Alike,LALCS00004,Delta 2,9 Elm St,555-123-4575,,Active,Delta Center,Erie,PA\n"
         + "FQHC,H80CS00005,Eps,10 Elm St,555-123-4576,beta.org,Active,Epsilon Health,Akron,OH\n"
         + "FQHC,H80CS00006,Guard,11 Elm St,555-123-4577,www.guard.org,Active," + WORD + " Health,"
           "Xville,TX\n"
         + 'Look-Alike,LALCS00007,Kappa,12 Elm St,555-123-4578,kappa.org,ACTIVE,"' + KAPPA + '",'
           "Erie,PA\n"
         + "\n"
         + "FQHC,,Omega,13 Elm St,555-123-4579,omega.org,Active,Omega Health,Erie,PA\n"
         ).encode("cp1252")
PRIVATE = ("Elm St", "555-123", "Main Clinic", "School Clinic")


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
        self.assertEqual(hc.domain_of("www.alpha.org"), "alpha.org")
        self.assertEqual(hc.domain_of("https://www.westschools.org/clinic"), "westschools.org")
        self.assertEqual(hc.domain_of("WWW.ALPHA.ORG/"), "alpha.org")
        self.assertEqual(hc.domain_of("http://www.x.org:8080/"), "x.org")
        for bad in ("", "see website", "localhost", "www.foo_bar.org", None):
            self.assertEqual(hc.domain_of(bad), "")

    def test_other_hosts_and_kinds(self):
        self.assertTrue(hc.other_host("facebook.com"))
        self.assertTrue(hc.other_host("m.facebook.com"))
        self.assertTrue(hc.other_host("sites.google.com"))
        self.assertFalse(hc.other_host("notfacebook.com"))
        self.assertFalse(hc.other_host("alpha.org"))
        self.assertEqual([hc.kind_of(n) for n in ("H80CS00001", "lalcs00004", "X1", "")],
                         ["awardee", "look_alike", "other", "other"])

    def test_parse_frame(self):
        rows, info = hc.parse_frame(SITES)
        self.assertEqual([r["domain"] for r in rows],
                         ["alpha.org", "beta.org", "gamma.org", "kappa.org"])
        self.assertEqual([r["number"] for r in rows],
                         ["H80CS00001", "H80CS00002", "H80CS00003", "LALCS00007"])
        self.assertEqual([r["kind"] for r in rows],
                         ["awardee", "awardee", "awardee", "look_alike"])
        self.assertEqual([r["sites"] for r in rows], ["3", "1", "2", "1"])
        self.assertEqual(rows[3]["organization"], KAPPA)
        self.assertEqual((rows[0]["organization"], rows[0]["city"], rows[0]["state"]),
                         ("Alpha Health", "Columbus", "OH"))
        self.assertEqual(set(rows[0]), set(hc.FRAME_COLUMNS))
        self.assertEqual(info, {"source_rows": 13,
                                "statuses": {"Active": 11, "ACTIVE": 1, "Inactive": 1},
                                "centres": 7, "active_sites": 11, "centres_active": 7,
                                "active_no_site": 1, "active_other_host": 1,
                                "centres_with_host": 6, "shared_host": 1, "dropped": 1,
                                "eligible": 4})
        joined = " ".join(v for r in rows for v in r.values())
        for private in PRIVATE + (WORD,):
            self.assertNotIn(private, joined)

    def test_short_column_names_and_missing_columns(self):
        rows, info = hc.parse_frame(("﻿HCP_MERGED_GRANT_LAL_KEY,SITE_URL,HCC_STATUS_DESC\n"
                                     "H80CS1,www.a.org,Active\n").encode("utf-8"))
        self.assertEqual([(r["domain"], r["number"], r["organization"], r["state"]) for r in rows],
                         [("a.org", "H80CS1", "", "")])
        self.assertEqual(info["eligible"], 1)
        with self.assertRaises(KeyError) as ctx:
            hc.parse_frame(b"Health Center Number,Site Status Description\nH80CS1,Active\n")
        self.assertIn("Site Web Address", str(ctx.exception))

    def test_sample_is_fixed_hash_order(self):
        rows = [{"domain": "d%d.org" % i} for i in range(10)]
        want = sorted(rows, key=lambda r: hashlib.sha256(
            ("hc-pages-2026-11-12" + r["domain"]).encode("utf-8")).hexdigest())[:3]
        self.assertEqual(hc.sample(rows, n=3), want)
        self.assertEqual(len(hc.sample(rows)), 10)


class Read504Tests(unittest.TestCase):
    def test_old_date_named(self):
        r = hc.read_504("We follow Section 504 of the Rehabilitation Act. Our website will meet "
                        "WCAG 2.1 AA by May 11, 2026.")
        self.assertTrue(r["s504"])
        self.assertTrue(r["d504_2026_05_11"])
        self.assertFalse(r["d504_2027_05_10"] or r["d504_2027_05_11"] or r["d504_2028_05_10"])
        self.assertTrue(r["old_504"])
        self.assertFalse(r["s1557"])
        self.assertIn("May 11, 2026", r["s504_snippet"])
        self.assertEqual(hc.dates_504(r), "2026-05-11")
        self.assertTrue(hc.dated_504(r))

    def test_new_dates(self):
        r = hc.read_504("Under HHS rules (45 CFR 84.84) we meet WCAG 2.1 AA by May 11, 2027; "
                        "smaller recipients by 05/10/2028.")
        self.assertTrue(r["s504"])
        self.assertEqual(hc.dates_504(r), "2027-05-11+2028-05-10")
        self.assertFalse(r["old_504"])

    def test_a_date_without_section_504_is_not_dated(self):
        r = hc.read_504("Updated May 11, 2026. Section 1557 notice of nondiscrimination.")
        self.assertFalse(r["s504"])
        self.assertTrue(r["d504_2026_05_11"])
        self.assertTrue(r["s1557"])
        self.assertFalse(r["old_504"])
        self.assertFalse(hc.dated_504(r))

    def test_may_11_2028_is_counted_apart(self):
        r = hc.read_504("Under HHS's Section 504 rule, small recipients have until May 11, 2028.")
        self.assertTrue(r["s504"])
        self.assertTrue(r["may11_2028"])
        self.assertEqual(hc.dates_504(r), "none")
        self.assertFalse(hc.dated_504(r))
        self.assertFalse(hc.read_504("By May 10, 2028 (Section 504).")["may11_2028"])

    def test_dates_504_labels(self):
        self.assertEqual(hc.dates_504({}), "none")
        self.assertEqual(hc.dates_504({"d504_2026_05_11": True, "d504_2027_05_11": True}),
                         "2026-05-11+2027-05-11")


class CrawlTests(unittest.TestCase):
    def test_crawl_reads_section_504_and_restores_the_state_reader(self):
        row = {"domain": "alpha.org", "number": "H80CS00001", "organization": "Alpha Health",
               "city": "Columbus", "state": "OH", "kind": "awardee", "sites": "3"}
        get = FakeGet({"http://alpha.org/": HOME, "http://alpha.org/accessibility": STATEMENT})
        rows = hc.crawl([row], workers=1, get=get, delay=0, sleep=no_sleep)
        self.assertIs(sp.read_page, hc._STATE_READ_PAGE)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["home"], r["page_status"], r["highest"], r["overlay"]),
                         ("ok", "ok", "2.1", "userway"))
        self.assertTrue(r["s504"])
        self.assertTrue(r["d504_2026_05_11"])
        self.assertTrue(r["old_504"])
        self.assertFalse(r["may11_2028"])
        self.assertFalse(r["title2"])
        self.assertNotIn("@", r["s504_snippet"])
        self.assertEqual(r["kind"], "awardee")


def base_row(domain, **kw):
    r = {c: "" for c in hc.COLUMNS}
    r.update({k: False for k in hc.BOOLS})
    r.update(domain=domain, candidates=0, state="OH", kind="other")
    r.update(kw)
    return r


def synthetic():
    rows = []
    for i in range(300):
        rows.append(base_row(
            "d%03d.org" % i, home="ok", home_host="h%d.org" % i, candidates=1, page_status="ok",
            page_url="https://h%d.org/accessibility" % i,
            highest="2.0" if i < 40 else "2.1" if i < 200 else "2.2" if i < 230 else "",
            title2=i % 4 == 0, s504=i % 3 == 0, d504_2026_05_11=i < 12,
            d504_2027_05_11=6 <= i < 18, old_504=i < 6 and i % 3 == 0,
            overlay="userway" if i < 60 else "",
            kind="awardee" if i < 200 else "look_alike"))
    for i in range(50):  # lead to d000's site and page (www and a trailing slash)
        rows.append(base_row("e%03d.org" % i, home="ok", home_host="h0.org", candidates=1,
                             page_status="ok", page_url="https://www.h0.org/accessibility/",
                             highest="2.0", s504=True, overlay="audioeye"))
    for i in range(250):
        rows.append(base_row("f%03d.org" % i, home="ok", home_host="g%d.org" % i,
                             page_status="no_link", overlay="accessibe" if i < 100 else ""))
    for i in range(30):
        rows.append(base_row("z%03d.org" % i, home="http_0"))
    return rows


class GradeTests(unittest.TestCase):
    def test_grade_on_distinct_pages_and_homes(self):
        m, p = hc.grade(synthetic())
        self.assertEqual(m["HC1_linked_of_homes"][:3], [300, 550, 0.5455])
        self.assertEqual(m["HC2_s504_of_pages"][:3], [100, 300, 0.3333])
        self.assertEqual(m["HC3_504_dated_of_pages"][:3], [6, 300, 0.02])
        self.assertEqual(m["HC4_highest_counts"], {"2.0": 40, "2.1": 160, "2.2": 30})
        self.assertEqual(m["HC5_overlay_of_homes"][:3], [160, 550, 0.2909])
        self.assertEqual(p, {"HC1": False, "HC2": True, "HC3": True, "HC4": True, "HC5": True})

    def test_small_sets_are_not_graded(self):
        _, p = hc.grade(synthetic()[:150])  # 150 versioned pages: only HC4 is graded
        self.assertEqual(p, {"HC1": None, "HC2": None, "HC3": None, "HC4": True, "HC5": None})
        _, p = hc.grade(synthetic()[:99])  # 99 versioned pages: one short of MIN_VERSIONED
        self.assertEqual(set(p.values()), {None})
        m, p = hc.grade([])
        self.assertEqual(set(p.values()), {None})
        self.assertEqual(m["HC1_linked_of_homes"], [0, 0, None, None])

    def test_described(self):
        d = hc.described(synthetic())
        self.assertEqual((d["domains"], d["distinct_pages"], d["distinct_home_hosts"],
                          d["domain_pages_ok"]), (630, 300, 550, 350))
        self.assertEqual(d["home"], {"ok": 600, "http_0": 30})
        self.assertEqual((d["s504"], d["old_504"], d["title2"], d["may_11_2028"]),
                         (100, 2, 75, 0))
        self.assertEqual(d["dates_504"], {"none": 94, "2026-05-11": 2,
                                          "2026-05-11+2027-05-11": 2, "2027-05-11": 2})
        self.assertEqual(d["title2_dates"], {"none": 300})
        self.assertEqual(d["by_kind"]["awardee"],
                         {"pages": 200, "versioned": 200, "only_2.0": 40, "2.1": 160, "2.2": 0,
                          "s504": 67, "dated_504": 6, "old_504": 2, "title2": 50})
        self.assertEqual(d["by_kind"]["look_alike"],
                         {"pages": 100, "versioned": 30, "only_2.0": 0, "2.1": 0, "2.2": 30,
                          "s504": 33, "dated_504": 0, "old_504": 0, "title2": 25})
        self.assertEqual(set(d["by_kind"]), {"awardee", "look_alike"})
        self.assertEqual(d["by_state"]["OH"]["pages"], 300)

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rows.csv")
            sp.write_csv(path, rows, hc.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, hc.COLUMNS)
                back = hc.typed(list(reader))
        self.assertEqual(len(back), 630)
        self.assertEqual(hc.grade(back), hc.grade(rows))
        self.assertEqual(hc.described(back), hc.described(rows))


class PreregWaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.files = {}
        for name in hc.PINNED:
            data = ("# %s\nprint('x')\n" % name).encode("utf-8")
            with open(os.path.join(self.tmp.name, name), "wb") as f:
                f.write(data)
            self.files[name] = data

    def tearDown(self):
        self.tmp.cleanup()

    def fetch_for(self, remote):
        def fetch(url, **kw):
            path = url.split("?n=")[0][len(hc.REPO_RAW):]
            if path in remote:
                return remote[path]
            raise OSError("404")
        return fetch

    def test_waits_until_all_pinned_files_match(self):
        remote = dict(self.files)
        remote[hc.PREREG_PATH] = b"# prereg\nHC1 HC2 HC3 HC4 HC5\n"
        remote["state_pages.py"] = remote["state_pages.py"].replace(b"\n", b"\r\n")
        self.assertEqual(hc.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=3, pause=0), (True, 1))

    def test_refuses_a_changed_file_or_missing_prereg(self):
        remote = dict(self.files)
        remote[hc.PREREG_PATH] = b"HC5"
        remote["hc_pages.py"] = b"changed"
        self.assertEqual(hc.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))
        self.assertEqual(hc.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(dict(self.files)),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))


class MainTests(unittest.TestCase):
    def make_fetch(self, frame=SITES):
        remote = {hc.PREREG_PATH: b"# prereg HC1-HC5"}
        for name in hc.PINNED:
            with open(os.path.join(HERE, name), "rb") as f:
                remote[name] = f.read()

        def fetch(url, **kw):
            if url == hc.FRAME_URL:
                return frame
            path = url.split("?n=")[0][len(hc.REPO_RAW):]
            if url.startswith(hc.REPO_RAW) and path in remote:
                return remote[path]
            raise OSError("404 " + url)
        return fetch

    def run_main(self, fetch, get):
        with tempfile.TemporaryDirectory() as out:
            code = hc.main(["--out-dir", out, "--delay", "0", "--workers", "2"],
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
        self.assertEqual((res["eligible"], res["frame"]["shared_host"]), (4, 1))
        self.assertEqual(res["frame"]["sha256"], hashlib.sha256(SITES).hexdigest())
        self.assertEqual(get.calls, [])
        for private in PRIVATE + (WORD,):
            self.assertNotIn(private, got["frame.csv"])

    def test_stops_when_a_needed_column_is_missing(self):
        get = FakeGet({})
        frame = b"Health Center Number,Site Status Description\nH80CS1,Active\n"
        code, got = self.run_main(self.make_fetch(frame), get)
        res = json.loads(got["result.json"])
        self.assertEqual(code, 1)
        self.assertEqual(res["status"], "stopped: frame not read")
        self.assertIn("Site Web Address", res["error"])
        self.assertNotIn("frame.csv", got)
        self.assertEqual(get.calls, [])

    def test_graded_run_end_to_end(self):
        saved = hc.MIN_COHORT
        hc.MIN_COHORT = 1
        try:
            get = FakeGet({"http://alpha.org/": HOME, "http://alpha.org/accessibility": STATEMENT})
            code, got = self.run_main(self.make_fetch(), get)
        finally:
            hc.MIN_COHORT = saved
        res = json.loads(got["result.json"])
        rows = list(csv.DictReader(io.StringIO(got["rows.csv"])))
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["sampled"], res["homes_ok"], res["pages_ok"]), (4, 1, 1))
        self.assertEqual(set(res["predictions"].values()), {None})
        self.assertEqual(list(rows[0]), hc.COLUMNS)
        self.assertEqual([r["domain"] for r in rows],
                         ["alpha.org", "beta.org", "gamma.org", "kappa.org"])
        self.assertEqual([r["number"] for r in rows],
                         ["H80CS00001", "H80CS00002", "H80CS00003", "LALCS00007"])
        self.assertEqual((rows[0]["page_status"], rows[0]["s504"], rows[0]["old_504"],
                          rows[0]["d504_2026_05_11"], rows[0]["kind"], rows[0]["sites"]),
                         ("ok", "True", "True", "True", "awardee", "3"))
        self.assertEqual(rows[1]["home"], "http_404")
        self.assertEqual(rows[3]["organization"], KAPPA)
        self.assertEqual(res["described"]["dates_504"], {"2026-05-11": 1})
        self.assertEqual(res["described"]["old_504"], 1)
        for private in PRIVATE + (WORD,):
            self.assertNotIn(private, got["frame.csv"])
            self.assertNotIn(private, got["rows.csv"])
        self.assertIn("predictions: HC1=None, HC2=None, HC3=None, HC4=None, HC5=None",
                      got["result.txt"])
        hosts = ("alpha.org", "beta.org", "gamma.org", "kappa.org")
        self.assertTrue(all(any("//" + h + "/" in u or "//www." + h + "/" in u for h in hosts)
                            for u in get.calls))


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("HC1 (at most 50% of distinct home sites link to an accessibility page on "
                       "the same site)",
                       "HC2 (at least 25% of distinct pages name Section 504, 45 CFR part 84 or "
                       "HHS)",
                       "HC3 (at most 5% of distinct pages give one of the four Section 504 web "
                       "dates)",
                       "HC4 (WCAG 2.1 is the most common highest version)",
                       "HC5 (at most 30% of distinct home sites load one of the six overlay "
                       "marks)",
                       "700 to 2,500 eligible hosts", "at most 2,500 are read",
                       "at least 100 versioned pages", "at least 200 distinct pages",
                       "at least 500 distinct home sites", "`hc-pages-2026-11-12`",
                       "`Health_Center_Service_Delivery_and_LookAlike_Sites.csv`",
                       "within 150 minutes", "24 sites at a time",
                       "815 of 1,195", "179 of 808", "494 of 1,195", "(68.20%)", "(22.15%)",
                       "(41.34%)", "91 FR 25507", "89 FR 40193"):
            self.assertIn(" ".join(phrase.split()), text)
        self.assertEqual((hc.HC1_MAX_LINKED, hc.HC2_MIN_S504, hc.HC3_MAX_DATED,
                          hc.HC5_MAX_OVERLAY), (0.50, 0.25, 0.05, 0.30))
        self.assertEqual((hc.MIN_VERSIONED, hc.MIN_PAGES, hc.MIN_HOMES), (100, 200, 500))
        self.assertEqual((hc.MIN_COHORT, hc.MAX_COHORT, hc.SAMPLE_N, hc.SEED),
                         (700, 2500, 2500, "hc-pages-2026-11-12"))
        self.assertTrue(hc.FRAME_URL.endswith("/Health_Center_Service_Delivery_and_LookAlike_"
                                              "Sites.csv"))
        self.assertIsNone(hc.GUARD_RE.search(text))
        for host in hc.OTHER_HOSTS:
            self.assertIn("`%s`" % host, text)
        # The context figures quoted in the plan, recomputed.
        for k, n, pct in ((815, 1195, "68.20"), (179, 808, "22.15"), (494, 1195, "41.34")):
            self.assertEqual("%.2f" % (100.0 * k / n), pct)

    def test_pinned_versions(self):
        self.assertEqual((hc.__version__, sp.__version__, hc.ap.__version__, hc.sc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0", "0.1.0"))
        self.assertEqual(hc.ap.MAX_TRIES, 3)
        self.assertEqual(hc.ap.MIN_TEXT, 200)
        self.assertEqual(len(hc.ap.OVERLAYS), 6)


if __name__ == "__main__":
    unittest.main()
