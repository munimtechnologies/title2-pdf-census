"""Tests for a11y_pages (no network). Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import csv
import json
import os
import tempfile
import unittest
import urllib.parse

import a11y_pages as ap

FILLER = "The city is committed to making its website usable by everyone. " * 4
HOME = ('<html><body><a href="/accessibility">Accessibility</a>'
        '<a href="https://www.ada.gov/">ADA</a><a href="/docs/ada.pdf">ADA plan</a>'
        '<a href="#main">Skip</a></body></html>')


def local_bytes():
    with open(ap.__file__, "rb") as f:
        return f.read()


def page(sentence):
    return ("<html><head><title>Accessibility</title></head><body><p>%s%s</p>"
            "<script>var x = 'WCAG 2.2';</script></body></html>" % (FILLER, sentence)).encode()


class FakeWeb:
    """Site i: robots.txt 404, the home page above, and an accessibility page that names WCAG
    2.0 (i % 3 == 0), WCAG 2.1 (i % 3 == 1) or is too short (i % 3 == 2)."""

    def __init__(self):
        self.calls = 0

    def __call__(self, url):
        self.calls += 1
        p = urllib.parse.urlsplit(url)
        i = int(p.hostname.split(".")[0][1:])
        if p.path == "/robots.txt":
            return 404, url, "", b""
        if p.path == "/":
            return 200, url, "text/html; charset=utf-8", HOME.encode()
        if p.path == "/accessibility":
            body = (page("We follow WCAG 2.0 Level AA.") if i % 3 == 0 else
                    page("We follow WCAG 2.1 Level AA.") if i % 3 == 1 else
                    b"<html><body><p>Loading</p></body></html>")
            return 200, url, "text/html", body
        return 404, url, "", b""


def cohort_csv(n):
    lines = ["qid,name,kind,state,population,website"]
    lines += ["Q%d,Town %d,city,Ohio,60000,https://s%d.example.gov/" % (i, i, i) for i in range(n)]
    return ("\n".join(lines) + "\n").encode()


def fake_fetch(prereg=b"# Pre-registration\nH1 ...\n", script=None, cohort=None):
    def fetch(url):
        if ap.PREREG_PATH in url:
            if prereg is None:
                raise OSError("404")
            return prereg
        if url.startswith(ap.REPO_RAW + ap.SCRIPT_PATH):
            return script if script is not None else local_bytes()
        if url == ap.COHORT_URL:
            return cohort
        raise OSError("unexpected " + url)
    return fetch


def row(highest, pop=60000, old=False, new=False, status="ok"):
    return {"qid": "Q1", "kind": "city", "population": str(pop), "home": "ok",
            "page_status": status, "highest": highest, "versions": highest, "wcag_any": bool(highest),
            "section508": False, "title2": False, "old_date": old, "new_date": new, "overlay": ""}


class Patterns(unittest.TestCase):
    def test_versions(self):
        cases = {"Our site aims to meet WCAG 2.1 Level AA.": "2.1",
                 "Web Content Accessibility Guidelines (WCAG) version 2.0 AA": "2.0",
                 "We test against WCAG 2.0, 2.1, and 2.2 at level AA.": "2.0+2.1+2.2",
                 "conform with WCAG 2.0 and 2.1.": "2.0+2.1",
                 "Web Content Accessibility Guidelines 2.2 (WCAG 2.2)": "2.2",
                 "WCAG2.1AA": "2.1",
                 "see WCAG 2.1.1 Keyboard": "",
                 "the WCAG 2 guidelines": ""}
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(ap.classify(text)["versions"], want)
        self.assertEqual(ap.classify("WCAG 2.0, 2.1, and 2.2")["highest"], "2.2")
        self.assertTrue(ap.classify("see WCAG 2.1.1 Keyboard")["wcag_any"])
        self.assertFalse(ap.classify("no guidelines named")["wcag_any"])

    def test_dates(self):
        old = ("by April 24, 2026", "Apr. 24 2026", "on 4/24/2026", "24 April 2026", "2026-04-24")
        for text in old:
            with self.subTest(text=text):
                c = ap.classify(text)
                self.assertTrue(c["old_date"])
                self.assertFalse(c["new_date"])
        for text in ("by April 26, 2027", "04/26/2027", "April 26th, 2027"):
            with self.subTest(text=text):
                self.assertTrue(ap.classify(text)["new_date"])
        for text in ("Last updated April 2026", "April 24, 2025", "April 2027"):
            with self.subTest(text=text):
                c = ap.classify(text)
                self.assertFalse(c["old_date"] or c["new_date"])
        both = ap.classify("The April 24, 2026 date moved to April 26, 2027.")
        self.assertTrue(both["old_date"] and both["new_date"])

    def test_other_marks(self):
        c = ap.classify("Under ADA Title II and Section 508 we follow WCAG 2.1.")
        self.assertTrue(c["title2"] and c["section508"])
        self.assertIn("WCAG 2.1", c["version_snippet"])
        self.assertFalse(ap.classify("Section 50 and title iii")["section508"])

    def test_scrub(self):
        self.assertEqual(ap.scrub("Call (555) 123-4567 or ada@city.gov"), "Call [phone] or [email]")
        self.assertEqual(ap.scrub("or 555-123-4567."), "or [phone].")
        self.assertEqual(ap.scrub("123-4567 then"), "[phone] then")
        self.assertEqual(ap.scrub("by 4/24/2026"), "by 4/24/2026")
        c = ap.classify("Questions to ada@city.gov about WCAG 2.1 compliance")
        self.assertNotIn("@", c["version_snippet"])

    def test_link_rank(self):
        self.assertEqual(ap.link_rank("https://a.gov/accessibility", "Help"), 0)
        self.assertEqual(ap.link_rank("https://a.gov/a11y", "Accessibility"), 1)
        self.assertEqual(ap.link_rank("https://a.gov/section-508", "Policy"), 2)
        self.assertEqual(ap.link_rank("https://a.gov/x", "ADA Coordinator"), 3)
        self.assertIsNone(ap.link_rank("https://a.gov/parks", "Ada County Parks"))
        self.assertIsNone(ap.link_rank("https://a.gov/x", "Adams Street"))

    def test_page_text_and_links(self):
        p = ap.parse(b'<p>Hi&nbsp;there</p><script>var WCAG = "2.0";</script>'
                     b'<a name="top"></a><a href="/a11y"><img src="i.png" alt="Accessibility"></a>'
                     b'<a href="/b" aria-label="ADA notice"><span>i</span></a>')
        self.assertEqual(ap.visible_text(p), "Hi there i")
        self.assertEqual(p.links, [("/a11y", "Accessibility"), ("/b", "ADA notice i")])

    def test_candidates(self):
        p = ap.parse(HOME.encode())
        cands, off, docs = ap.candidates(p, "https://s1.example.gov/")
        self.assertEqual(cands, [("https://s1.example.gov/accessibility", 0)])
        self.assertEqual((off, docs), (1, 1))
        p = ap.parse(b'<a href="/ada">ADA</a><a href="/Accessibility-Statement">Accessibility</a>'
                     b'<a href="https://www.city.gov/x">Accessibility</a>')
        cands, off, docs = ap.candidates(p, "https://city.gov/")
        self.assertEqual(cands, [("https://city.gov/Accessibility-Statement", 0),
                                 ("https://www.city.gov/x", 1), ("https://city.gov/ada", 3)])
        self.assertEqual((off, docs), (0, 0))

    def test_same_site(self):
        self.assertTrue(ap.same_site("https://www.city.gov/x", "https://city.gov/"))
        self.assertTrue(ap.same_site("https://ada.city.gov/x", "https://www.city.gov/"))
        self.assertFalse(ap.same_site("https://www.ada.gov/", "https://city.gov/"))


class Crawl(unittest.TestCase):
    def test_site(self):
        web = FakeWeb()
        r = ap.crawl_site({"qid": "Q1", "website": "https://s1.example.gov"}, get=web,
                          sleep=lambda s: None)
        self.assertEqual((r["home"], r["page_status"], r["page_rank"]), ("ok", "ok", 0))
        self.assertEqual((r["versions"], r["highest"], r["candidates"]), ("2.1", "2.1", 1))
        self.assertEqual(r["page_url"], "https://s1.example.gov/accessibility")
        self.assertEqual(web.calls, 3)
        short = ap.crawl_site({"qid": "Q2", "website": "https://s2.example.gov/"}, get=FakeWeb(),
                              sleep=lambda s: None)
        self.assertEqual(short["page_status"], "short")
        self.assertNotIn("highest", short)

    def test_robots_and_errors(self):
        def blocked(url):
            if url.endswith("/robots.txt"):
                return 200, url, "text/plain", b"User-agent: *\nDisallow: /\n"
            raise AssertionError("fetched " + url)
        r = ap.crawl_site({"website": "https://x.gov/"}, get=blocked, sleep=lambda s: None)
        self.assertEqual(r["home"], "robots")

        def forbidden(url):
            return (404 if url.endswith("/robots.txt") else 403), url, "", b""
        r = ap.crawl_site({"website": "https://x.gov/"}, get=forbidden, sleep=lambda s: None)
        self.assertEqual(r["home"], "http_403")


class Grade(unittest.TestCase):
    def rows(self):
        rs = [row("2.0", 300000)] * 20 + [row("2.1", 300000)] * 50 + [row("2.2", 300000)] * 10
        rs += [row("", 300000)] * 20
        rs += [row("2.0")] * 30 + [row("2.1")] * 100 + [row("2.2")] * 30 + [row("")] * 140
        rs += [row("", old=True)] * 12 + [row("", old=True, new=True)] * 10 + [row("", new=True)] * 8
        rs += [row("2.0", status="http_404")] * 50
        return rs

    def test_grade(self):
        m, p = ap.grade(self.rows())
        self.assertEqual(m["H1_only_2.0_of_versioned"][:3], [50, 240, 0.2083])
        self.assertEqual(m["H2_highest_counts"], {"2.0": 50, "2.1": 150, "2.2": 40})
        self.assertEqual(m["H3_versioned_of_pages"][:3], [240, 430, 0.5581])
        self.assertEqual(m["H4_old_only_of_dated"][:3], [12, 30, 0.4])
        self.assertEqual(m["H5_versioned_big"][:3], [80, 100, 0.8])
        self.assertEqual(m["H5_versioned_small"][:3], [160, 330, 0.4848])
        self.assertEqual(p, {"H1": True, "H2": True, "H3": True, "H4": True, "H5": True})

    def test_small_samples_not_graded(self):
        m, p = ap.grade([row("2.0", 300000)] * 10 + [row("2.1")] * 100)
        self.assertEqual((p["H1"], p["H2"], p["H4"], p["H5"]), (None, None, None, None))
        self.assertTrue(p["H3"])

    def test_pinned(self):
        self.assertEqual(ap.COHORT_COMMIT, "279e85ecf05268d8883c5887292ef5acdf555cd6")
        self.assertEqual((ap.MIN_COHORT, ap.MAX_COHORT, ap.MIN_HOMES, ap.MIN_PAGES, ap.MIN_TEXT),
                         (1600, 1700, 950, 500, 200))
        self.assertEqual((ap.MIN_VERSIONED, ap.MIN_DATED, ap.MIN_SIZE_GROUP, ap.BIG),
                         (200, 20, 80, 250000))
        self.assertEqual((ap.H1_MIN_ONLY_20, ap.H3_MIN_VERSIONED, ap.H4_MIN_OLD_ONLY, ap.H5_MIN_GAP),
                         (0.15, 0.40, 0.30, 0.05))
        self.assertEqual((ap.MAX_TRIES, ap.TRIES, ap.PAUSE), (3, 40, 90))


class Main(unittest.TestCase):
    def test_waits_for_exact_script(self):
        ok, n = ap.wait_for_prereg(b"abc", fetch=fake_fetch(script=b"abd"), sleep=lambda s: None,
                                   tries=3)
        self.assertEqual((ok, n), (False, 3))
        ok, n = ap.wait_for_prereg(b"a\r\nb", fetch=fake_fetch(script=b"a\nb"),
                                   sleep=lambda s: None, tries=3)
        self.assertEqual((ok, n), (True, 1))

    def test_no_prereg_nothing_fetched(self):
        web = FakeWeb()
        with tempfile.TemporaryDirectory() as d:
            code = ap.main(["--out-dir", d], fetch=fake_fetch(prereg=None), get=web,
                           sleep=lambda s: None)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
        self.assertEqual(code, 2)
        self.assertFalse(res["gates"]["P0_prereg_public"])
        self.assertEqual(res["polls"], ap.TRIES)
        self.assertEqual(web.calls, 0)

    def test_small_cohort_not_crawled(self):
        web = FakeWeb()
        with tempfile.TemporaryDirectory() as d:
            code = ap.main(["--out-dir", d], fetch=fake_fetch(cohort=cohort_csv(100)), get=web,
                           sleep=lambda s: None)
        self.assertEqual(code, 2)
        self.assertEqual(web.calls, 0)

    def test_graded_run(self):
        with tempfile.TemporaryDirectory() as d:
            code = ap.main(["--out-dir", d], fetch=fake_fetch(cohort=cohort_csv(1650)),
                           get=FakeWeb(), sleep=lambda s: None)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
            with open(os.path.join(d, "a11y-pages.csv"), encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["cohort"], res["homes_ok"], res["pages_ok"]), (1650, 1650, 1100))
        self.assertEqual(len(rows), 1650)
        self.assertEqual(res["measures"]["H2_highest_counts"], {"2.0": 550, "2.1": 550, "2.2": 0})
        self.assertEqual(res["predictions"], {"H1": True, "H2": False, "H3": True, "H4": None,
                                              "H5": None})
        self.assertEqual(res["described"]["page_status"], {"ok": 1100, "short": 550})
        self.assertNotIn("WCAG 2.2", "".join(r["version_snippet"] for r in rows))
        self.assertIn("predictions: H1=True, H2=False", text)


if __name__ == "__main__":
    unittest.main()
