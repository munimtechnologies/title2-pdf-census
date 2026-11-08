"""Offline tests of district_stock.py (no network is used).

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
import a11y_pages as ap  # noqa: E402
import district_stock as s  # noqa: E402

T2017 = ("Accessibility Statement To help us make the Your School website a positive place for "
         "everyone, we've been using the Web Content Accessibility Guidelines (WCAG) 2.0. These "
         "guidelines explain how to make web content more accessible for people with "
         "disabilities, and user friendly for everyone. Let us know if you have any problems "
         "accessing the site: email us at accessibility@yourschool.com - call us on "
         "555-555-5555 ext:555. This accessibility statement was generated on 16th May 2017 "
         "using the Accessibility Statement Generator.")
T2026 = ("Accessibility Statement [Your School] is committed to ensuring digital accessibility "
         "for people with disabilities. [Your School] is built with WCAG 2.1 AA guidelines in "
         "mind. Accessibility is never a one-time checkbox. If you have trouble using this site, "
         "please contact us: Phone: 555-555-5555 ext:555 - Email: accessibility@yourschool.com. "
         "We aim to respond within # business days.")
FILLED = ("Accessibility Statement To help us make the Springfield Public Schools website a "
          "positive place for everyone, we've been using the Web Content Accessibility "
          "Guidelines (WCAG) 2.1. These guidelines explain how to make web content more "
          "accessible for people with disabilities, and user friendly for everyone. Let us know "
          "if you have any problems accessing the site: email the webmaster of the district or "
          "call the district office during school hours.")
OTHER = ("Website Accessibility. The district is committed to making its website accessible to "
         "everyone and follows the Web Content Accessibility Guidelines 2.1 Level AA. Please "
         "contact the technology department if any page is hard to use and we will help.")


def page(text, finalsite=True):
    foot = '<footer class="fsFooter">Powered by Finalsite</footer>' if finalsite else ""
    return ("<html><body><main><p>" + text + "</p></main>" + foot + "</body></html>").encode()


def text_sha(body):
    return ap.sha256(ap.visible_text(ap.parse(body, "text/html")).encode("utf-8"))


def fake_get(pages, robots=None, calls=None):
    """pages: url -> list of (status, body) answers, used in turn (the last one repeats)."""
    robots = robots or {}
    seen = {}

    def get(url):
        if calls is not None:
            calls.append(url)
        if url.endswith("/robots.txt"):
            body = robots.get(url)
            return (200, url, "text/plain", body) if body else (404, url, "", b"")
        if url in pages:
            i = seen.get(url, 0)
            seen[url] = i + 1
            status, body = pages[url][min(i, len(pages[url]) - 1)]
            return status, url, ("text/html; charset=utf-8" if status == 200 else ""), body
        return 404, url, "", b""
    return get


def frow(i=1, band="under50k", census="not_sampled", census_placeholder=False, sha=""):
    return {"leaid": "%07d" % i, "name": "District %d" % i, "state": "OH", "lea_type": "1",
            "population": "60000" if band == "50k+" else "12000", "band": band,
            "host": "d%d.org" % i, "base": "https://www.d%d.org" % i, "census": census,
            "census_placeholder": census_placeholder, "_census_sha": sha}


class Sleeps(list):
    def __call__(self, seconds):
        self.append(seconds)


def read(row, pages, robots=None, sleep=None):
    # An empty Sleeps is falsy (it is a list), so test against None, not truthiness.
    return s.read_one(row, get=fake_get(pages, robots), delay=0,
                      sleep=Sleeps() if sleep is None else sleep)


class TextTests(unittest.TestCase):
    def test_2017_template(self):
        r = s.check_text(T2017, page(T2017))
        self.assertIs(r["placeholder"], True)
        self.assertEqual(r["placeholder_kinds"], "your_school+your_domain+fake_phone")
        for k in ("t2017", "generator", "finalsite_markup"):
            self.assertIs(r[k], True, k)
        self.assertIs(r["t2026"], False)

    def test_2026_template(self):
        r = s.check_text(T2026, page(T2026, finalsite=False))
        self.assertIs(r["placeholder"], True)
        self.assertIn("school_bracket", r["placeholder_kinds"])
        self.assertIs(r["t2026"], True)
        self.assertIs(r["t2017"], False)
        self.assertIs(r["finalsite_markup"], False)

    def test_filled_and_other(self):
        r = s.check_text(FILLED, page(FILLED))
        self.assertIs(r["t2017"], True)
        self.assertIs(r["placeholder"], False)
        r = s.check_text(OTHER, page(OTHER, finalsite=False))
        for k in ("t2017", "t2026", "placeholder", "generator", "finalsite_markup"):
            self.assertIs(r[k], False, k)


class FrameTests(unittest.TestCase):
    CENSUS = {"0100001": {"home": "ok", "page_status": "ok", "placeholder": "True",
                          "page_url": "https://www.a.org/Accessibility-Statement/",
                          "text_sha256": "abc"},
              "0100002": {"home": "ok", "page_status": "ok", "placeholder": "True",
                          "page_url": "https://b.org/accessibility", "text_sha256": "def"},
              "0100003": {"home": "ok", "page_status": "no_link", "placeholder": ""},
              "0100004": {"home": "http_403", "page_status": "", "placeholder": ""}}

    def test_census_info(self):
        self.assertEqual(s.census_info("0100001", self.CENSUS), ("found_here", True, "abc"))
        self.assertEqual(s.census_info("0100002", self.CENSUS), ("found_elsewhere", True, "def"))
        self.assertEqual(s.census_info("0100003", self.CENSUS), ("no_page", False, ""))
        self.assertEqual(s.census_info("0100004", self.CENSUS), ("home_failed", False, ""))
        self.assertEqual(s.census_info("0100005", self.CENSUS), ("not_sampled", False, ""))

    def test_build_frame_drops_the_withheld_district(self):
        rows = [{"leaid": l, "name": "D", "state": "XX", "lea_type": "1", "population": 9000,
                 "band": "under50k", "website": w, "host": "h%s.org" % l}
                for l, w in (("0100001", "http://www.a.org/district"), ("0100005", "c.org"),
                             (s.DROP_LEAIDS[0], "http://x.org"))]
        frame, dropped = s.build_frame(rows, self.CENSUS)
        self.assertEqual(dropped, 1)
        self.assertEqual([r["leaid"] for r in frame], ["0100001", "0100005"])
        self.assertEqual(frame[0]["base"], "http://www.a.org")
        self.assertEqual(frame[1]["base"], "http://c.org")
        self.assertEqual((frame[0]["census"], frame[0]["census_placeholder"]), ("found_here", True))
        self.assertNotIn("website", frame[0])

    def test_crawl_order_is_fixed(self):
        frame = [frow(i) for i in range(1, 30)]
        self.assertEqual(s.crawl_order(frame), s.crawl_order(list(reversed(frame))))
        self.assertNotEqual([r["leaid"] for r in s.crawl_order(frame)],
                            [r["leaid"] for r in frame])


class ReadTests(unittest.TestCase):
    def url(self, row):
        return row["base"] + s.PROBE_PATH

    def test_placeholder_page_not_sampled(self):
        row = frow()
        out = read(row, {self.url(row): [(200, page(T2017))]})
        self.assertEqual(out["status"], "ok")
        self.assertIs(out["placeholder"], True)
        self.assertIs(out["uncounted"], False)
        self.assertIs(out["retried"], False)

    def test_placeholder_page_the_census_missed(self):
        for census in ("no_page", "home_failed", "found_elsewhere"):
            row = frow(census=census)
            out = read(row, {self.url(row): [(200, page(T2017))]})
            self.assertIs(out["uncounted"], True, census)

    def test_same_page_as_the_census(self):
        body = page(T2017)
        row = frow(census="found_here", census_placeholder=True, sha=text_sha(body))
        out = read(row, {self.url(row): [(200, body)]})
        self.assertIs(out["same_text"], True)
        self.assertIs(out["uncounted"], False)
        row = frow(census="found_here", census_placeholder=True, sha="0" * 64)
        self.assertIs(read(row, {self.url(row): [(200, body)]})["same_text"], False)

    def test_retry_once_after_429(self):
        row = frow()
        sleeps = Sleeps()
        out = read(row, {self.url(row): [(429, b""), (200, page(T2017))]}, sleep=sleeps)
        self.assertEqual(out["status"], "ok")
        self.assertIs(out["retried"], True)
        self.assertIn(s.RETRY_PAUSE, sleeps)
        out = read(row, {self.url(row): [(429, b""), (429, b"")]})
        self.assertEqual(out["status"], "http_429")

    def test_statuses(self):
        row = frow()
        self.assertEqual(read(row, {})["status"], "http_404")
        robots = {row["base"] + "/robots.txt": b"User-agent: *\nDisallow: /accessibility\n"}
        self.assertEqual(read(row, {}, robots)["status"], "robots")
        short = {self.url(row): [(200, page("Hi", finalsite=False))]}
        self.assertEqual(read(row, short)["status"], "short")
        bad = dict(row, base="")
        self.assertEqual(read(bad, {})["status"], "bad_url")


def synthetic():
    """11,200 hosts (1,270 of 50k+): 560 placeholder pages."""
    rows = []

    def add(n, band, **kw):
        for _ in range(n):
            r = frow(len(rows) + 1, band=band)
            r.pop("_census_sha")
            r.update(status="http_404", retried=False, same_text=False, finalsite_markup=False,
                     t2017=False, t2026=False, generator=False, placeholder=False,
                     placeholder_kinds="", highest="", title2=False, uncounted=False)
            r.update(kw)
            rows.append(r)
    ph = dict(status="ok", placeholder=True, finalsite_markup=True, t2017=True,
              placeholder_kinds="your_school+your_domain+fake_phone", highest="2.0")
    add(450, "under50k", **ph)
    add(30, "50k+", census="found_here", census_placeholder=True, same_text=True, **ph)
    add(60, "under50k", census="found_here", census_placeholder=True, **ph)
    add(5, "under50k", census="found_here", census_placeholder=True)
    add(2, "under50k", census="found_here", census_placeholder=True, status="http_429",
        retried=True)
    add(20, "under50k", census="no_page", uncounted=True,
        **dict(ph, finalsite_markup=False))
    add(1240, "50k+")
    add(9000, "under50k")
    add(393, "under50k", status="http_0")
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        rows = synthetic()
        self.assertEqual(len(rows), 11200)
        measures, gates, preds = s.grade(rows)
        self.assertEqual(gates, {"F1_frame": True, "G1_answered": True})
        self.assertEqual(measures["F1_hosts_50k+"], 1270)
        self.assertEqual(measures["G1_answered"][:2], [10807, 11200])
        self.assertEqual(measures["K1_placeholder_hosts"], 560)
        self.assertEqual(measures["K2_uncounted_of_sampled"][:2], [20, 110])
        self.assertEqual(measures["K3_kept_of_census_here"][:2], [90, 95])
        self.assertEqual(measures["K4_markup_of_placeholder"][:2], [540, 560])
        self.assertEqual(preds, {"K1": True, "K2": True, "K3": True, "K4": True})

    def test_too_few_pages_are_not_graded(self):
        rows = synthetic()
        for r in rows:
            if r.get("census") != "not_sampled":
                r["placeholder"] = False
        _, _, preds = s.grade(rows)
        self.assertEqual(preds, {"K1": True, "K2": None, "K3": False, "K4": True})

    def test_gate_fails(self):
        rows = [r for r in synthetic() if r["band"] != "50k+" or r["status"] != "http_404"]
        _, gates, preds = s.grade(rows)
        self.assertIs(gates["F1_frame"], False)
        self.assertEqual(preds, {"K1": None, "K2": None, "K3": None, "K4": None})

    def test_tables_round_trip_grade_the_same(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            sizes = s.write_tables(d, rows)
            back = []
            for _, name in s.OUT_FILES:
                with open(os.path.join(d, name), encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    self.assertEqual(reader.fieldnames, s.COLUMNS)
                    back.extend(reader)
        self.assertEqual(set(sizes), {"hosts-50k.csv", "hosts-under50k.csv"})
        back = s.typed(back)
        self.assertEqual(s.grade(back), s.grade(rows))
        d = s.described(back)
        self.assertEqual(d["placeholder_by_census"],
                         {"not_sampled": 450, "found_here": 90, "no_page": 20})
        self.assertEqual(d["census_here_placeholder"], 97)
        self.assertEqual(d["census_here_same_text"], 30)
        self.assertEqual(d["retried"], 2)
        self.assertEqual(d["placeholder_t2017"], 560)
        self.assertEqual(d["markup_pages"], 540)
        self.assertEqual(d["placeholder_of_answered"]["50k+"][:2], [30, 1270])


class RunTests(unittest.TestCase):
    def test_not_run_without_plan(self):
        def fetch(url, **kw):
            raise OSError("404")
        with tempfile.TemporaryDirectory() as d:
            s.main(["--out-dir", d], fetch=fetch, get=fake_get({}), sleep=Sleeps())
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
        self.assertEqual(result["status"], "not_run")
        self.assertIs(result["gates"]["P0_prereg_public"], False)

    def test_not_run_on_wrong_census_table(self):
        def fetch(url, **kw):
            path = url[len(s.REPO_RAW):].split("?")[0]
            if path == s.PREREG_PATH:
                return b"plan K1 K2 K3 K4"
            if path in s.PINNED:
                with open(os.path.join(HERE, path), "rb") as f:
                    return f.read()
            return b"leaid,home\n0100001,ok\n"
        with tempfile.TemporaryDirectory() as d:
            s.main(["--out-dir", d], fetch=fetch, get=fake_get({}), sleep=Sleeps())
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertEqual(result["status"], "not_run")
        self.assertIs(result["gates"]["P0_prereg_public"], True)
        self.assertIs(result["gates"]["G0_census"], False)
        self.assertEqual(result["census_rows"], 1)
        self.assertIn("predictions: not graded", text)


class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(os.path.join(HERE, "results", "district-stock", "PREREG.md"),
                  encoding="utf-8") as f:
            plan = f.read()
        for phrase in ("**400**", "**15%**", "**90%**", "**95%**", "11,000 to 11,700",
                       "1,250 to 1,400", "80%", "`/accessibility-statement`", "K4",
                       "at least **30**", "at least **80**", "at least **50**",
                       "2,500 rows", "0903180", "a positive place for everyone",
                       "built with WCAG 2.1 AA guidelines in mind"):
            self.assertIn(phrase, plan)
        self.assertEqual((s.K1_MIN_HOSTS, s.K2_MIN_UNCOUNTED, s.K2_MIN_PAGES, s.K3_MIN_KEPT,
                          s.K3_MIN_PAGES, s.K4_MIN_MARKUP, s.K4_MIN_PAGES),
                         (400, 0.15, 30, 0.90, 80, 0.95, 50))
        self.assertEqual((s.F1_MIN, s.F1_MAX, s.F1_BIG_MIN, s.F1_BIG_MAX, s.G1_MIN_ANSWERED),
                         (11000, 11700, 1250, 1400, 0.80))
        self.assertEqual((s.PROBE_PATH, s.CENSUS_ROWS, s.DROP_LEAIDS),
                         ("/accessibility-statement", 2500, ("0903180",)))


if __name__ == "__main__":
    unittest.main()
