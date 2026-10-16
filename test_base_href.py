"""Offline tests for census 0.2.2: relative links resolve against the page's <base href>.

The second full run (0.2.1) found that 536 of the 1,242 PDF links with a space in them came
back 404, against 211 of the 5,391 without one. A hand check of one Revize-hosted county site
showed why: its pages set <base href> to the site root and write links such as
"Complaint Form 20.04.02.pdf", which 0.2.1 resolved under each inner page's folder.
No network. Apache-2.0 licensed."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import census as c  # noqa: E402

try:
    import pypdf  # noqa: F401
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False

PAGE_URL = "https://www.county.example/government/commissioners/agendas.php"


def resp(url, body=b"", status=200, ctype="text/html; charset=utf-8"):
    return c.Response(status, url, ctype, body, False, None if status == 200 else "http %d" % status)


class BaseHrefTests(unittest.TestCase):
    def test_links_resolve_against_base_href(self):
        page = ('<head><base href="https://www.county.example/"></head>'
                '<a href="Complaint Form 20.04.02.pdf">Form</a><a href="/news">News</a>'
                '<a href="government/accessibility.php">Help</a>')
        self.assertEqual(c.extract_links(page, PAGE_URL),
                         ["https://www.county.example/Complaint Form 20.04.02.pdf",
                          "https://www.county.example/news",
                          "https://www.county.example/government/accessibility.php"])
        self.assertEqual(c.accessibility_links(page, PAGE_URL),
                         ["https://www.county.example/government/accessibility.php"])

    def test_first_base_counts_and_may_be_relative(self):
        page = '<base href="/files/"><base href="/other/"><a href="a.pdf">a</a>'
        self.assertEqual(c.extract_links(page, PAGE_URL), ["https://www.county.example/files/a.pdf"])

    def test_without_base_href_nothing_changes(self):
        expected = ["https://www.county.example/government/commissioners/a.pdf"]
        self.assertEqual(c.extract_links('<a href="a.pdf">a</a>', PAGE_URL), expected)
        self.assertEqual(c.extract_links('<base target="_blank"><a href="a.pdf">a</a>', PAGE_URL), expected)
        self.assertEqual(c.extract_links('<base href="javascript:void(0)"><a href="a.pdf">a</a>', PAGE_URL),
                         expected)

    def test_parser_keeps_the_base(self):
        self.assertEqual(c.parse_links('<base href=" https://x.example/ ">').base, "https://x.example/")
        self.assertIsNone(c.parse_links('<a href="/x">x</a>').base)

    def test_version(self):
        self.assertEqual(c.__version__, "0.2.2")
        self.assertIn("0.2.2", c.UA)

    @unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
    def test_crawl_site_follows_base_href(self):
        import test_census as t
        home = b'<base href="http://county.example/"><a href="government/agendas.php">Agendas</a>'
        inner = b'<base href="http://county.example/"><a href="Board Agenda.pdf">Agenda</a>'
        web = {
            "http://county.example/": resp("http://county.example/", home),
            "http://county.example/government/agendas.php":
                resp("http://county.example/government/agendas.php", inner),
            "http://county.example/Board Agenda.pdf": resp("p", t.TAGGED_PDF, ctype="application/pdf"),
        }
        calls = []

        def get(url, max_bytes, timeout=20):
            calls.append(url)
            return web.get(url, resp(url, status=404))

        site, found = c.crawl_site({"qid": "Q5", "website": "http://county.example"}, get=get,
                                   sleep=lambda s: None)
        self.assertEqual(site["status"], "ok")
        self.assertEqual((site["pages_read"], site["pdf_links"]), (1, 1))
        self.assertEqual((site["pdfs_tried"], site["pdfs_ok"]), (1, 1))
        self.assertEqual(found[0]["url"], "http://county.example/Board Agenda.pdf")
        self.assertNotIn("http://county.example/government/Board Agenda.pdf", calls)


if __name__ == "__main__":
    unittest.main()
