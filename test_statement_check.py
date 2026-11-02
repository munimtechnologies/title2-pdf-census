"""Tests for statement_check.py (no network: every page comes from a fake fetcher).

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statement_check as sc  # noqa: E402

STOCK_HTML = b"""<html><head><title>Accessibility</title>
<script>var standard = "WCAG 2.2";</script></head><body>
<h1>Accessibility</h1>
<p>The County is committed to making its website accessible to everyone. We work to comply
with Section 508 as well as WCAG 2.0 A and AA referring to website accessibility standards.</p>
<p>Under Title II of the ADA, the first compliance date is April 24, 2026.</p>
<p>To report a barrier, email webmaster@example.gov.</p>
</body></html>"""

GOOD_HTML = b"""<html><body><h1>Accessibility statement</h1>
<p>The City of Example aims to meet the Web Content Accessibility Guidelines (WCAG) version 2.1
Level AA, the standard adopted by the Justice Department's rule under Title II of the Americans
with Disabilities Act. The first compliance date for governments of 50,000 or more is
April 26, 2027. Success criterion 2.4.7 asks for a visible focus indicator.
Call 555-123-4567 to report a barrier.</p></body></html>"""

HOME_HTML = b"""<html><body><a href="/news">News</a>
<a href="https://other.org/accessibility">Accessibility partner</a>
<a href="/accessibility">Accessibility</a></body></html>"""


def fake(pages):
    calls = []

    def get(url):
        calls.append(url)
        return pages.get(url, (404, url, "", b""))
    get.calls = calls
    return get


def no_sleep(_seconds):
    pass


def run(argv, get=None):
    buf = io.StringIO()
    code = sc.main(argv, get=get or fake({}), sleep=no_sleep, out=buf)
    return code, buf.getvalue()


class CheckTextTests(unittest.TestCase):
    def ids(self, r):
        return [f["id"] for f in r["findings"]]

    def test_stock_page(self):
        r = sc.check_text(sc.ap.visible_text(sc.ap.parse(STOCK_HTML)))
        self.assertEqual(self.ids(r), ["wcag-2.0", "stock-sentence", "old-date"])
        self.assertEqual(r["versions"], "2.0")  # the script's "WCAG 2.2" is not page text
        self.assertTrue(r["section508"] and r["title2"] and r["contact"] and r["stock_sentence"])
        self.assertTrue(r["date_2026_04_24"])
        self.assertFalse(r["date_2027_04_26"] or r["date_2028_04_26"])
        self.assertIn("WCAG 2.0 A and AA", r["version_snippet"])
        self.assertEqual(r["notes"], [])

    def test_good_page(self):
        r = sc.check_text(sc.ap.visible_text(sc.ap.parse(GOOD_HTML)))
        self.assertEqual(self.ids(r), [])
        self.assertEqual((r["versions"], r["highest"]), ("2.1", "2.1"))  # 2.4.7 is not a version
        self.assertTrue(r["date_2027_04_26"] and r["title2"] and r["contact"])
        self.assertFalse(r["section508"] or r["stock_sentence"])
        self.assertEqual(r["notes"], [])

    def test_small_government_date(self):
        text = sc.ap.visible_text(sc.ap.parse(GOOD_HTML))
        self.assertEqual(self.ids(sc.check_text(text, small=True)), ["small-2027"])
        both = text + " Smaller governments have until April 26, 2028."
        r = sc.check_text(both, small=True)
        self.assertEqual(self.ids(r), [])
        self.assertTrue(r["date_2028_04_26"])

    def test_both_dates_is_a_note(self):
        r = sc.check_text("We follow WCAG 2.1 AA. The April 24, 2026 date moved to April 26, 2027.")
        self.assertEqual(self.ids(r), [])
        self.assertIn(sc.BOTH_DATES, r["notes"])

    def test_old_date_forms(self):
        for d in ("April 24, 2026", "Apr. 24 2026", "4/24/2026", "2026-04-24", "24 April 2026"):
            r = sc.check_text("We follow WCAG 2.1 AA by %s." % d)
            self.assertEqual(self.ids(r), ["old-date"], d)

    def test_2028_forms(self):
        for d in ("April 26, 2028", "Apr 26th, 2028", "04/26/28", "2028-04-26"):
            self.assertTrue(sc.check_text("Due %s." % d)["date_2028_04_26"], d)
        self.assertFalse(sc.check_text("Due April 26, 2027.")["date_2028_04_26"])

    def test_two_versions_take_the_highest(self):
        r = sc.check_text("We follow WCAG 2.0 and 2.1 Level AA.")
        self.assertEqual((r["versions"], r["highest"]), ("2.0+2.1", "2.1"))
        self.assertEqual(self.ids(r), [])

    def test_stock_sentence_with_a_later_version_elsewhere(self):
        r = sc.check_text("We work to comply with Section 508 as well as WCAG 2.0 A and AA. "
                          "We are moving to WCAG 2.1 AA.")
        self.assertEqual(r["highest"], "2.1")
        self.assertEqual(self.ids(r), ["stock-sentence"])

    def test_success_criterion_is_not_a_version(self):
        r = sc.check_text("Keyboard access follows WCAG 2.1.1 and success criterion 2.4.7.")
        self.assertEqual(r["highest"], "")
        self.assertIn(sc.WCAG_NO_VERSION, r["notes"])

    def test_no_version_no_contact_short(self):
        r = sc.check_text("We are committed to accessibility.")
        self.assertEqual(self.ids(r), [])
        self.assertEqual(r["notes"], [sc.NO_VERSION, sc.NO_CONTACT, sc.SHORT % 34])

    def test_nbsp_and_spacing(self):
        r = sc.check_text("We\xa0work to  comply with\nSection\xa0508 as well as WCAG\xa02.0 AA.")
        self.assertTrue(r["stock_sentence"])
        self.assertEqual(r["highest"], "2.0")


class MainTests(unittest.TestCase):
    def test_file_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "page.html")
            with open(path, "wb") as f:
                f.write(STOCK_HTML)
            code, text = run([path, "--json"])
        self.assertEqual(code, 1)
        r = json.loads(text)
        self.assertEqual(r["status"], "ok")
        self.assertEqual([f["id"] for f in r["findings"]], ["wcag-2.0", "stock-sentence", "old-date"])
        self.assertEqual(r["version"], sc.__version__)

    def test_file_text_report(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "page.html")
            with open(path, "wb") as f:
                f.write(STOCK_HTML)
            code, text = run([path])
        lines = text.splitlines()
        self.assertEqual(code, 1)
        self.assertEqual(lines[0], "statement_check %s" % sc.__version__)
        self.assertIn("WCAG versions named: 2.0 (highest 2.0)", lines)
        self.assertIn("stock sentence: yes", lines)
        self.assertIn("FINDING wcag-2.0: " + sc.WCAG20, lines)
        self.assertIn(sc.DISCLAIMER, lines)
        self.assertEqual(lines[-1], "statement_check: 3 findings")

    def test_stdin(self):
        buf = io.StringIO()
        code = sc.main(["-"], get=fake({}), sleep=no_sleep, out=buf,
                       stdin=io.BytesIO(GOOD_HTML))
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().splitlines()[-1], "statement_check: 0 findings")

    def test_find_follows_the_census_link_rules(self):
        get = fake({
            "http://example.gov/": (200, "http://example.gov/", "text/html; charset=utf-8",
                                    HOME_HTML),
            "http://example.gov/accessibility": (200, "http://example.gov/accessibility",
                                                 "text/html", GOOD_HTML)})
        code, text = run(["example.gov", "--find", "--json"], get=get)
        r = json.loads(text)
        self.assertEqual(code, 0)
        self.assertEqual(r["page_url"], "http://example.gov/accessibility")
        self.assertEqual(get.calls, ["http://example.gov/robots.txt", "http://example.gov/",
                                     "http://example.gov/accessibility"])
        self.assertNotIn("https://other.org/accessibility", get.calls)

    def test_find_without_a_link(self):
        get = fake({"http://example.gov/": (200, "http://example.gov/", "text/html",
                                            b"<html><body><a href='/news'>News</a></body></html>")})
        code, text = run(["http://example.gov", "--find"], get=get)
        self.assertEqual(code, 2)
        self.assertIn("could not read the page: no_link", text.splitlines())

    def test_direct_url(self):
        url = "https://example.gov/accessibility"
        get = fake({url: (200, url, "text/html", STOCK_HTML)})
        code, text = run([url, "--json"], get=get)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(text)["page_url"], url)
        self.assertEqual(get.calls, ["https://example.gov/robots.txt", url])

    def test_robots_disallow(self):
        url = "https://example.gov/accessibility"
        get = fake({"https://example.gov/robots.txt": (200, "", "text/plain",
                                                       b"User-agent: *\nDisallow: /\n"),
                    url: (200, url, "text/html", STOCK_HTML)})
        code, text = run([url, "--json"], get=get)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(text)["status"], "robots")
        self.assertNotIn(url, get.calls)

    def test_http_error_and_not_html(self):
        code, text = run(["https://example.gov/missing", "--json"])
        self.assertEqual((code, json.loads(text)["status"]), (2, "http_404"))
        url = "https://example.gov/statement.pdf"
        get = fake({url: (200, url, "application/pdf", b"%PDF-1.4")})
        code, text = run([url, "--json"], get=get)
        self.assertEqual((code, json.loads(text)["status"]), (2, "not_html"))

    def test_find_with_a_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "page.html")
            with open(path, "wb") as f:
                f.write(GOOD_HTML)
            code, text = run([path, "--find"])
        self.assertEqual(code, 2)
        self.assertEqual(text.splitlines()[-1], "statement_check: not checked")


if __name__ == "__main__":
    unittest.main()
