"""Offline tests for small_pages.py (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import csv
import hashlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import small_pages as sp  # noqa: E402

PAD = " Residents can ask for help with any page or document on this site." * 5
STATEMENT = ("<html><head><title>Accessibility</title></head><body><main><h1>Accessibility</h1>"
             "<p>We work to comply with Section 508 as well as WCAG 2.0 A and AA. Under Title II "
             "our site will meet the rule by April 26, 2027." + PAD + "</p></main></body></html>"
             ).encode("utf-8")
UPDATED = ("<html><body><h1>Accessibility</h1><p>Our site follows WCAG 2.1 Level AA. The date "
           "for our town is April 26, 2028 (it was April 26, 2027)." + PAD + "</p></body></html>"
           ).encode("utf-8")
HOME = (b'<html><body><a href="/accessibility">Accessibility</a>'
        b'<a href="/parks">Parks</a></body></html>')
BIG_CSV = (b"qid,name,kind,state,population,website\n"
           b"Q60,New York City,city,New York,8804190,https://www.nyc.gov/main\n"
           b"Q7,Big County,county,Ohio,60000,https://d.gov/\n"
           b"Q99,Big City,city,Ohio,70000,https://www.b.gov/\n")


def binding(qid, typ, pop, site, label="Place", state="Ohio"):
    return {"item": {"value": "http://www.wikidata.org/entity/" + qid},
            "itemLabel": {"value": label}, "typeLabel": {"value": typ},
            "stateLabel": {"value": state}, "population": {"value": str(pop)},
            "website": {"value": site}}


SPARQL = {"results": {"bindings": [
    binding("Q1", "city of the United States", 20000, "https://www.a.gov/"),
    binding("Q2", "city of the United States", 60000, "https://e.gov/"),
    binding("Q3", "city of the United States", "x", "https://f.gov/"),
    binding("Q4", "city of the United States", 30000, "https://b.gov"),
    binding("Q5", "county of Ohio", 15000, "http://a.gov/home"),
    binding("Q6", "town of the United States", 12000, "https://c.org"),
    binding("Q7", "county of Ohio", 30000, "https://g.gov/"),
    binding("Q8", "city of the United States", 9999, "https://h.gov/"),
]}}


class FakeGet:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def __call__(self, url, max_bytes=3_000_000, timeout=20):
        self.calls.append(url)
        if url in self.pages:
            return 200, url, "text/html; charset=utf-8", self.pages[url]
        return 404, url, "", b""


def no_sleep(_s):
    return None


ROW = {"qid": "Q1", "name": "Ex", "kind": "city", "state": "Ohio", "population": 20000,
       "website": "http://ex.gov"}


class CohortTests(unittest.TestCase):
    def test_queries(self):
        full, simple = sp.cohort_queries()
        self.assertIn("FILTER(?pop >= 10000)", full)
        self.assertIn("HAVING (MAX(?pop) < 50000)", full)
        self.assertIn("OPTIONAL", full)
        self.assertNotIn("OPTIONAL", simple)
        self.assertNotIn("stateLabel", simple)
        self.assertIn("HAVING (MAX(?pop) < 50000)", simple)

    def test_big_cohort(self):
        qids, hosts = sp.big_cohort(BIG_CSV)
        self.assertEqual(qids, {"Q60", "Q7", "Q99"})
        self.assertEqual(hosts, {"nyc.gov", "d.gov", "b.gov"})

    def test_parse_cohort_band_exclusions_and_hosts(self):
        qids, hosts = sp.big_cohort(BIG_CSV)
        rows = sp.parse_cohort(SPARQL, qids, hosts)
        self.assertEqual([r["qid"] for r in rows], ["Q1", "Q6"])
        self.assertEqual([r["kind"] for r in rows], ["city", "town"])
        self.assertEqual(rows[0]["population"], 20000)
        self.assertEqual(rows[0]["website"], "https://www.a.gov/")
        self.assertEqual(rows[1]["state"], "Ohio")

    def test_parse_cohort_without_exclusions(self):
        rows = sp.parse_cohort(SPARQL)
        self.assertEqual([r["qid"] for r in rows], ["Q4", "Q7", "Q1", "Q6"])
        self.assertEqual(rows[1]["kind"], "county")

    def test_sample_is_fixed_hash_order(self):
        rows = [{"qid": "Q%d" % i} for i in range(10)]
        got = sp.sample(rows, n=3)
        want = sorted(rows, key=lambda r: hashlib.sha256(
            ("small-pages-2026-11-02" + r["qid"]).encode("utf-8")).hexdigest())[:3]
        self.assertEqual(got, want)
        self.assertEqual(len(sp.sample(rows)), 10)
        self.assertEqual(sp.SAMPLE_N, 2500)

    def test_fetch_cohort_falls_back_to_simple_query(self):
        calls = []

        def fetch(url, **kw):
            calls.append(url)
            if "OPTIONAL" in url:
                raise OSError("timeout")
            return json.dumps(SPARQL).encode("utf-8")
        data = sp.fetch_cohort(fetch=fetch, sleep=no_sleep)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].startswith(sp.WIKIDATA_SPARQL + "?"))
        self.assertEqual(len(data["results"]["bindings"]), 8)

    def test_fetch_cohort_gives_up(self):
        def fetch(url, **kw):
            raise OSError("down")
        with self.assertRaises(RuntimeError):
            sp.fetch_cohort(fetch=fetch, sleep=no_sleep)


class CrawlTests(unittest.TestCase):
    def test_small_statement_with_old_small_date(self):
        get = FakeGet({"http://ex.gov/": HOME, "http://ex.gov/accessibility": STATEMENT})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual(r["home"], "ok")
        self.assertEqual(r["candidates"], 1)
        self.assertEqual(r["page_status"], "ok")
        self.assertEqual(r["page_rank"], 0)
        self.assertEqual(r["highest"], "2.0")
        self.assertTrue(r["stock"])
        self.assertTrue(r["title2"])
        self.assertTrue(r["section508"])
        self.assertTrue(r["new_date"])
        self.assertFalse(r["old_date"])
        self.assertFalse(r["date_2028"])
        self.assertFalse(r["contact"])
        self.assertEqual(r["findings"], "wcag-2.0+stock-sentence+small-2027")
        self.assertEqual(get.calls, ["http://ex.gov/robots.txt", "http://ex.gov/",
                                     "http://ex.gov/accessibility"])

    def test_updated_statement_has_no_findings(self):
        get = FakeGet({"http://ex.gov/": HOME, "http://ex.gov/accessibility": UPDATED})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual(r["page_status"], "ok")
        self.assertEqual(r["highest"], "2.1")
        self.assertTrue(r["new_date"])
        self.assertTrue(r["date_2028"])
        self.assertFalse(r["stock"])
        self.assertEqual(r["findings"], "")

    def test_no_link_and_dead_home(self):
        get = FakeGet({"http://ex.gov/": b"<html><body><a href='/parks'>Parks</a></body></html>"})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual((r["home"], r["page_status"], r["candidates"]), ("ok", "no_link", 0))
        r = sp.crawl_site(ROW, get=FakeGet({}), delay=0, sleep=no_sleep)
        self.assertEqual(r["home"], "http_404")

    def test_robots_disallow(self):
        get = FakeGet({"http://ex.gov/robots.txt": b"User-agent: *\nDisallow: /\n",
                       "http://ex.gov/": HOME})
        r = sp.crawl_site(ROW, get=get, delay=0, sleep=no_sleep)
        self.assertEqual(r["home"], "robots")
        self.assertEqual(get.calls, ["http://ex.gov/robots.txt"])


def page(highest="", stock=False, title2=False, old=False, new=False, d28=False):
    return {"home": "ok", "candidates": 1, "page_status": "ok", "highest": highest,
            "stock": stock, "title2": title2, "old_date": old, "new_date": new, "date_2028": d28}


def synthetic_rows():
    rows = []
    for i in range(500):
        rows.append(page(highest="2.0" if i < 200 else "2.1" if i < 300 else "",
                         stock=i < 150, title2=i % 5 == 0,
                         old=315 <= i < 320, new=300 <= i < 315, d28=310 <= i < 315))
    rows += [{"home": "ok", "candidates": 2, "page_status": "http_404"} for _ in range(100)]
    rows += [{"home": "ok", "candidates": 0, "page_status": "no_link"} for _ in range(400)]
    rows += [{"home": "robots"} for _ in range(50)]
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        m, p = sp.grade(synthetic_rows())
        self.assertEqual(m["S1_only_2.0_of_versioned"][:3], [200, 300, 0.6667])
        self.assertEqual(m["S2_stock_of_pages"][:3], [150, 500, 0.3])
        self.assertEqual(m["S3_title2_of_pages"][:3], [100, 500, 0.2])
        self.assertEqual(m["S4_linked_of_homes"][:3], [600, 1000, 0.6])
        self.assertEqual(m["S5_2027_without_2028_of_dated"][:3], [10, 20, 0.5])
        self.assertEqual(p, {"S1": True, "S2": False, "S3": True, "S4": True, "S5": True})

    def test_gates_leave_predictions_ungraded(self):
        m, p = sp.grade(synthetic_rows()[:10])
        self.assertEqual(p, {"S1": None, "S2": None, "S3": None, "S4": None, "S5": None})
        m, p = sp.grade([])
        self.assertEqual(m["S4_linked_of_homes"], [0, 0, None, None])

    def test_described(self):
        d = sp.described(synthetic_rows())
        self.assertEqual(d["date_2027_04_26"], 15)
        self.assertEqual(d["date_2028_04_26"], 5)
        self.assertEqual(d["only_2026_04_24"], 5)
        self.assertEqual(d["home"], {"ok": 1000, "robots": 50})


class PreregTests(unittest.TestCase):
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
        remote[sp.PREREG_PATH] = b"# prereg\nS1 S2 S3 S4 S5\n"
        remote["a11y_pages.py"] = remote["a11y_pages.py"].replace(b"\n", b"\r\n")
        ok, n = sp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote), sleep=no_sleep,
                                   tries=3, pause=0)
        self.assertEqual((ok, n), (True, 1))

    def test_refuses_a_changed_file_or_missing_prereg(self):
        remote = dict(self.files)
        remote[sp.PREREG_PATH] = b"S5"
        remote["statement_check.py"] = b"changed"
        self.assertEqual(sp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))
        remote = dict(self.files)
        self.assertEqual(sp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))


class MainTests(unittest.TestCase):
    def make_fetch(self):
        remote = {sp.PREREG_PATH: b"# prereg S1-S5"}
        for name in sp.PINNED:
            with open(os.path.join(HERE, name), "rb") as f:
                remote[name] = f.read()

        def fetch(url, **kw):
            if url == sp.BIG_COHORT_URL:
                return BIG_CSV
            if url.startswith(sp.WIKIDATA_SPARQL):
                return json.dumps(SPARQL).encode("utf-8")
            path = url.split("?n=")[0][len(sp.REPO_RAW):]
            if url.startswith(sp.REPO_RAW) and path in remote:
                return remote[path]
            raise OSError("404 " + url)
        return fetch

    def test_stops_when_cohort_is_outside_the_range(self):
        with tempfile.TemporaryDirectory() as out:
            code = sp.main(["--out-dir", out], fetch=self.make_fetch(), get=FakeGet({}),
                           sleep=no_sleep)
            self.assertEqual(code, 1)
            with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertTrue(res["status"].startswith("stopped: cohort size"))
            self.assertEqual(res["gates"], {"P0_prereg_public": True, "C1_cohort": False})
            self.assertEqual(res["eligible"], 2)
            self.assertFalse(os.path.exists(os.path.join(out, "rows.csv")))

    def test_graded_run_end_to_end(self):
        saved = sp.MIN_COHORT
        sp.MIN_COHORT = 1
        try:
            get = FakeGet({"https://www.a.gov/": HOME,
                           "https://www.a.gov/accessibility": STATEMENT})
            with tempfile.TemporaryDirectory() as out:
                code = sp.main(["--out-dir", out, "--delay", "0", "--workers", "2"],
                               fetch=self.make_fetch(), get=get, sleep=no_sleep)
                self.assertEqual(code, 0)
                with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                    res = json.load(f)
                with open(os.path.join(out, "rows.csv"), encoding="utf-8") as f:
                    rows = list(csv.DictReader(f))
                with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
                    text = f.read()
        finally:
            sp.MIN_COHORT = saved
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["sampled"], res["homes_ok"], res["pages_ok"]), (2, 1, 1))
        self.assertEqual(set(res["predictions"].values()), {None})
        self.assertEqual([r["qid"] for r in rows], ["Q1", "Q6"])
        self.assertEqual(rows[0]["findings"], "wcag-2.0+stock-sentence+small-2027")
        self.assertEqual(rows[1]["home"], "http_404")
        self.assertIn("predictions: S1=None, S2=None, S3=None, S4=None, S5=None", text)


if __name__ == "__main__":
    unittest.main()
