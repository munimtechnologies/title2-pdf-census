"""Offline tests of stock153.py (no network is used).

Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""

import csv
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stock153 as s  # noqa: E402

TEMPLATE = ("YOURMUNICIPALITY is committed to providing electronic communication that is "
            "accessible to the widest possible audience, regardless of technology or ability. "
            "This statement is only meant as a template local government accessibility statement. "
            "We work to comply with Section 508 as well as WCAG 2.0 A and AA.")
EDITED = ("The City is committed to providing electronic communication that is accessible to the "
          "widest possible audience, regardless of technology or ability. Contact the clerk with "
          "any questions about this page or about our services. We work to comply with Section "
          "508 as well as WCAG 2.0 A and AA.")


def page(text, civic=True):
    foot = "<footer>Government Websites by CivicPlus</footer>" if civic else ""
    return ("<html><body><main><p>" + text + "</p></main>" + foot + "</body></html>").encode()


def fake_get(pages, robots=None):
    robots = robots or {}

    def get(url):
        if url.endswith("/robots.txt"):
            body = robots.get(url)
            return (200, url, "text/plain", body) if body else (404, url, "", b"")
        if url in pages:
            status, final, body = pages[url]
            return status, final, "text/html; charset=utf-8", body
        return 404, url, "", b""
    return get


def frow(census="home_ok", p153=False, host="foo.gov", cohort="small", qid="Q1"):
    return {"cohort": cohort, "qid": qid, "name": "Foo", "kind": "city", "state": "Ohio",
            "population": "12000", "host": host,
            "probe_url": "https://www." + host + "/153/Accessibility", "dupes": 0,
            "census": census, "census_page_153": p153}


def no_sleep(_):
    return None


def read(row, pages, robots=None):
    return s.read_one(row, get=fake_get(pages, robots), delay=0, sleep=no_sleep)


class FrameTests(unittest.TestCase):
    def test_host_of(self):
        self.assertEqual(s.host_of("http://www.Foo.gov/"), ("foo.gov", "http://www.foo.gov"))
        self.assertEqual(s.host_of("foo.gov"), ("foo.gov", "http://foo.gov"))
        self.assertEqual(s.host_of("https://www.a.gov:8443/x"),
                         ("a.gov", "https://www.a.gov:8443"))
        self.assertEqual(s.host_of("[withheld]"), ("", ""))
        self.assertEqual(s.host_of("http://localhost/"), ("", ""))

    def test_build_frame(self):
        large = [{"qid": "Q2", "name": "Big", "kind": "city", "state": "Ohio",
                  "population": "60000", "website": "https://www.foo.gov/", "home": "ok",
                  "page_status": "ok", "page_url": "https://www.foo.gov/153/Accessibility"}]
        small = [{"qid": "Q3", "name": "Foo2", "website": "http://foo.gov"},
                 {"qid": "Q4", "name": "[withheld]", "website": "[withheld]"},
                 {"qid": "Q5", "name": "Bar", "website": "https://bar.org/"},
                 {"qid": "Q6", "name": "Baz", "website": "https://baz.us/"},
                 {"qid": "Q7", "name": "Qux", "website": "https://qux.us/"}]
        sample = [{"qid": "Q5", "home": "ok", "page_status": "ok",
                   "page_url": "https://bar.org/accessibility"},
                  {"qid": "Q7", "home": "robots", "page_status": "", "page_url": ""}]
        frame, dropped = s.build_frame(large, small, sample)
        self.assertEqual(dropped, 1)
        self.assertEqual([r["host"] for r in frame], ["foo.gov", "bar.org", "baz.us", "qux.us"])
        self.assertEqual(frame[0]["dupes"], 1)
        self.assertEqual(frame[0]["cohort"], "large")
        self.assertEqual(frame[0]["probe_url"], "https://www.foo.gov/153/Accessibility")
        self.assertEqual((frame[0]["census"], frame[0]["census_page_153"]), ("home_ok", True))
        self.assertEqual((frame[1]["census"], frame[1]["census_page_153"]), ("home_ok", False))
        self.assertEqual((frame[2]["census"], frame[2]["census_page_153"]), ("not_sampled", False))
        self.assertEqual((frame[3]["census"], frame[3]["census_page_153"]), ("home_failed", False))


class ReadTests(unittest.TestCase):
    def test_template_hidden(self):
        row = frow()
        out = read(row, {row["probe_url"]: (200, row["probe_url"], page(TEMPLATE))})
        self.assertEqual(out["status"], "ok")
        for k in ("civicplus", "a11y_text", "stock_page", "muni", "template_note", "placeholder",
                  "hidden"):
            self.assertIs(out[k], True, k)
        self.assertIs(out["contact_block"], False)

    def test_template_found_or_unsampled_is_not_hidden(self):
        for census, p153 in (("home_ok", True), ("not_sampled", False), ("home_failed", False)):
            row = frow(census=census, p153=p153)
            out = read(row, {row["probe_url"]: (200, row["probe_url"], page(TEMPLATE))})
            self.assertIs(out["placeholder"], True)
            self.assertIs(out["hidden"], False, census)

    def test_edited_page(self):
        row = frow()
        out = read(row, {row["probe_url"]: (200, row["probe_url"], page(EDITED))})
        self.assertEqual(out["status"], "ok")
        self.assertIs(out["placeholder"], False)
        self.assertIs(out["stock_page"], True)
        self.assertIs(out["stock"], True)
        self.assertIs(out["hidden"], False)

    def test_redirect_and_other_platform_are_not_stock_pages(self):
        row = frow()
        home = "https://www.foo.gov/"
        out = read(row, {row["probe_url"]: (200, home, page(EDITED))})
        self.assertIs(out["stock_page"], False)
        out = read(row, {row["probe_url"]: (200, row["probe_url"], page(EDITED, civic=False))})
        self.assertIs(out["civicplus"], False)
        self.assertIs(out["stock_page"], False)

    def test_statuses(self):
        row = frow()
        self.assertEqual(read(row, {})["status"], "http_404")
        robots = {"https://www.foo.gov/robots.txt": b"User-agent: *\nDisallow: /153/\n"}
        self.assertEqual(read(row, {}, robots)["status"], "robots")
        short = {row["probe_url"]: (200, row["probe_url"], page("Hi"))}
        self.assertEqual(read(row, short)["status"], "short")


def synthetic():
    """4,800 hosts: 70 stock pages (47 flagged, 6 of them hidden), the rest 404 or no answer."""
    rows = []

    def add(n, cohort, **kw):
        for _ in range(n):
            r = frow(cohort=cohort, qid="Q%d" % (len(rows) + 1))
            r.update(status="http_404", stock_page=False, placeholder=False, hidden=False,
                     civicplus=False)
            r.update(kw)
            rows.append(r)
    add(6, "small", status="ok", stock_page=True, placeholder=True, hidden=True, civicplus=True,
        muni=True)
    add(39, "small", status="ok", stock_page=True, placeholder=True, civicplus=True, muni=True,
        census_page_153=True)
    add(15, "small", status="ok", stock_page=True, civicplus=True)
    add(2, "large", status="ok", stock_page=True, placeholder=True, civicplus=True, muni=True,
        census_page_153=True)
    add(8, "large", status="ok", stock_page=True, civicplus=True)
    add(1000, "large")
    add(3630, "small")
    add(100, "small", status="http_0")
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        rows = synthetic()
        self.assertEqual(len(rows), 4800)
        measures, gates, preds = s.grade(rows)
        self.assertEqual(gates, {"F1_frame": True, "G1_answered": True})
        self.assertEqual(measures["S1_flagged_hosts"], 47)
        self.assertEqual(measures["S2_hidden_flagged_hosts"], 6)
        self.assertEqual(measures["S3_flagged_of_stock_pages"][:2], [47, 70])
        self.assertEqual(measures["S4_flagged_of_probed_large"][:2], [2, 1010])
        self.assertEqual(measures["S4_flagged_of_probed_small"][:2], [45, 3690])
        self.assertEqual(preds, {"S1": True, "S2": True, "S3": True, "S4": True})

    def test_gate_fails(self):
        _, gates, preds = s.grade(synthetic()[:4799])
        self.assertIs(gates["F1_frame"], False)
        self.assertEqual(preds, {"S1": None, "S2": None, "S3": None, "S4": None})

    def test_csv_round_trip_grades_the_same(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hosts.csv")
            s.write_csv(path, rows, s.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                back = s.typed(list(csv.DictReader(f)))
        self.assertEqual(s.grade(back), s.grade(rows))
        d = s.described(back)
        self.assertEqual(d["flagged_by_census_group"], {"found_153": 41, "hidden": 6})
        self.assertEqual(d["flagged_by_cohort"], {"small": 45, "large": 2})
        self.assertEqual(d["stock_pages"], {"large": 10, "small": 60})
        self.assertEqual(len(d["flagged"]), 47)
        self.assertEqual(d["flagged"][0][-1], "found_153")


class RunTests(unittest.TestCase):
    def test_not_run_without_plan(self):
        def fetch(url):
            raise OSError("404")
        with tempfile.TemporaryDirectory() as d:
            s.main(["--out-dir", d], fetch=fetch, get=fake_get({}), sleep=no_sleep)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
        self.assertEqual(result["status"], "not_run")
        self.assertIs(result["gates"]["P0_prereg_public"], False)

    def test_not_run_on_wrong_tables(self):
        def fetch(url):
            path = url[len(s.REPO_RAW):].split("?")[0]
            if path == s.PREREG_PATH:
                return b"plan S1 S2 S3 S4"
            if path in s.PINNED:
                with open(os.path.join(HERE, path), "rb") as f:
                    return f.read()
            return b"qid,website\nQ1,https://a.gov/\n"
        with tempfile.TemporaryDirectory() as d:
            s.main(["--out-dir", d], fetch=fetch, get=fake_get({}), sleep=no_sleep)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertEqual(result["status"], "not_run")
        self.assertIs(result["gates"]["P0_prereg_public"], True)
        self.assertIs(result["gates"]["G0_tables"], False)
        self.assertEqual(result["tables"]["large"]["rows"], 1)
        self.assertIn("predictions: not graded", text)


class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(os.path.join(HERE, "results", "stock-153", "PREREG.md"), encoding="utf-8") as f:
            plan = f.read()
        for phrase in ("**40**", "**5**", "**20%**", "**800**", "**50**", "4,800 to 5,245",
                       "80%", "/153/Accessibility", "S4"):
            self.assertIn(phrase, plan)
        self.assertEqual((s.S1_MIN_FLAGGED, s.S2_MIN_HIDDEN, s.S3_MIN_SHARE, s.S3_MIN_PAGES,
                          s.S4_MIN_PROBED, s.F1_MIN, s.F1_MAX, s.G1_MIN_ANSWERED),
                         (40, 5, 0.20, 50, 800, 4800, 5245, 0.80))


if __name__ == "__main__":
    unittest.main()
