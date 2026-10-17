"""Offline tests for site_check and the Apify Actor files (no network). Apache-2.0 licensed."""

import inspect
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import census as c  # noqa: E402
import site_check as sc  # noqa: E402
from test_census import HAVE_PYPDF, SCANNED_PDF, TAGGED_PDF, resp  # noqa: E402


def web_get(web, calls=None):
    def get(url, max_bytes, timeout=20):
        if calls is not None:
            calls.append(url)
        return web.get(url, resp(url, status=404))
    return get


def no_sleep(seconds):
    pass


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


class AdviceTests(unittest.TestCase):
    def test_scan_fails_everything(self):
        rec = {"result": "ok", "tagged": False, "lang": False, "title": False, "image_only": True,
               "producer_family": "scanner", "figures": 0, "figures_alt": 0}
        self.assertEqual(sc.failures(rec), ["image_only", "tagged", "lang", "title"])
        self.assertEqual(sc.notes(rec), [sc.SCANNER_NOTE])

    def test_good_pdf_with_missing_alt(self):
        rec = {"tagged": True, "lang": True, "title": True, "image_only": False, "display_doc_title": True,
               "figures": 3, "figures_alt": 1, "producer_family": "word"}
        self.assertEqual(sc.failures(rec), [])
        self.assertEqual(sc.notes(rec), ["2 of 3 tagged figures have no alt text."])

    def test_print_to_pdf(self):
        rec = {"tagged": False, "lang": True, "title": True, "image_only": False,
               "display_doc_title": False, "producer_family": "print-to-pdf"}
        self.assertEqual(sc.failures(rec), ["tagged"])
        notes = sc.notes(rec)
        self.assertEqual(len(notes), 2)
        self.assertIn("Show: Document Title", notes[0])
        self.assertEqual(notes[1], sc.PRINT_NOTE)

    def test_advice_names_the_word_option(self):
        advice = dict((k, a) for k, _, a in sc.BASICS)
        self.assertIn("Document structure tags for accessibility", advice["tagged"])
        self.assertEqual([k for k, _, _ in sc.BASICS], ["image_only", "tagged", "lang", "title"])

    def test_quoted_census_numbers(self):
        # 0.1.2: quotes the third full run (0.2.2), the census's headline.
        s = json.loads(read("results", "v0.2.2", "summary.json"))
        o, by = s["overall"], s["by_producer"]
        pdfs = "{:,} PDFs from {:,}".format(s["pdf_results"]["ok"], s["sites_with_ok_pdf"])
        self.assertIn("of %s US cities and counties" % pdfs, sc.BASELINE)
        self.assertIn("%.1f%% were tagged and %.1f%% passed all four basics" % (
            100 * o["tagged"]["share"], 100 * o["basic4"]["share"]), sc.BASELINE)
        self.assertIn("(%.1f%% in the census)" % (100 * by["print-to-pdf"]["tagged"]["share"]), sc.PRINT_NOTE)
        self.assertIn("(%.1f%% of scanner output" % (100 * by["scanner"]["tagged"]["share"]), sc.SCANNER_NOTE)
        readme = " ".join(read(".actor", "README.md").split())
        self.assertIn("%.1f%% of %s large US cities and counties were tagged, and only %.1f%% passed" % (
            100 * o["tagged"]["share"], pdfs, 100 * o["basic4"]["share"]), readme)


class CheckPdfTests(unittest.TestCase):
    def test_robots_bad_links_errors_and_duplicates(self):
        web = {
            "https://a.gov/robots.txt": resp("r", b"User-agent: *\nDisallow: /private/\n", ctype="text/plain"),
            "https://a.gov/page.pdf": resp("https://a.gov/page.pdf", b"<html>login</html>"),
        }
        calls = []
        found = sc.check_pdfs(["https://a.gov/private/x.pdf", "ftp://a.gov/x.pdf", " https://a.gov/missing.pdf",
                               "https://a.gov/page.pdf", "https://a.gov/missing.pdf", ""],
                              get=web_get(web, calls), sleep=no_sleep)
        self.assertEqual([(r["url"], r["result"]) for r in found],
                         [("https://a.gov/private/x.pdf", "robots_disallow"), ("ftp://a.gov/x.pdf", "bad_url"),
                          ("https://a.gov/missing.pdf", "http_error"), ("https://a.gov/page.pdf", "not_pdf")])
        self.assertEqual(calls.count("https://a.gov/robots.txt"), 1)
        self.assertNotIn("https://a.gov/private/x.pdf", calls)

    def test_unread_only_report(self):
        result = sc.run(pdf_urls=["https://a.gov/x.pdf"], get=web_get({}), sleep=no_sleep, checked="2026-10-16")
        self.assertIsNone(result["site"])
        self.assertEqual(result["summary"], {"pdfs_checked": 0, "pdfs_not_read": 1, "pass_all_four": 0,
                                             "fail": {"image_only": 0, "tagged": 0, "lang": 0, "title": 0}})
        md = sc.markdown(result)
        self.assertIn("# PDF basics check: PDF links", md)
        self.assertIn("0 PDFs checked; 0 pass all four basics; 1 could not be read.", md)
        self.assertIn("- https://a.gov/x.pdf: http_error", md)
        self.assertNotIn("## What to fix", md)
        self.assertNotIn("| PDF |", md)
        self.assertNotIn(sc.NO_PDFS, md)
        self.assertEqual(sc.dataset_rows(result), [{"name": "x.pdf", "url": "https://a.gov/x.pdf",
                                                    "result": "http_error"}])

    def test_cli_needs_a_site_or_pdf(self):
        with self.assertRaises(SystemExit):
            sc.main([])

    def test_names_and_links(self):
        self.assertEqual(sc.name_of("https://a.gov/media/Burn%20Ban.pdf"), "Burn Ban.pdf")
        self.assertEqual(sc.name_of("https://a.gov/"), "https://a.gov/")
        self.assertEqual(sc.link("https://a.gov/Annual Report (2025).pdf"),
                         "https://a.gov/Annual%20Report%20%282025%29.pdf")
        self.assertEqual(sc.cell("a|b"), "a\\|b")


class CrawlTests(unittest.TestCase):
    """0.1.1: document-like pages are read first, one level deeper too, and reading stops
    once there are twice as many PDF links as PDFs to check. 0.1.2: once half the pages are
    read with no PDF link, the other pages go first. 0.1.3: 16 pages by default."""

    def pages(self, calls):
        return [u for u in calls if not u.endswith("/robots.txt") and not c.looks_like_pdf(u)]

    def test_doc_like(self):
        self.assertTrue(sc.doc_like("https://a.gov/DocumentCenter/Index/3"))
        self.assertTrue(sc.doc_like("https://a.gov/AgendaCenter"))
        self.assertTrue(sc.doc_like("https://a.gov/x.aspx?id=4", "Agendas &  Minutes"))
        self.assertTrue(sc.doc_like("https://a.gov/resources/", "Guidance & Resource Materials"))
        self.assertTrue(sc.doc_like("https://a.gov/Annual%20Reports/"))
        self.assertFalse(sc.doc_like("https://a.gov/parks", "Parks"))
        self.assertFalse(sc.doc_like("https://a.gov/docsis"))
        self.assertFalse(sc.doc_like("https://a.gov/accessibility", "Accessibility"))

    def test_page_links_merge_texts_and_follow_base_href(self):
        page = '<base href="https://a.gov/"><a href="x.htm">One</a><a href="x.htm#top"> Two\n</a><a href="mailto:a@a.gov">m</a>'
        self.assertEqual(sc.page_links(page, "https://a.gov/dept/page"), {"https://a.gov/x.htm": "One Two"})

    def test_doc_pages_first(self):
        home = (b'<a href="/about">About us</a><a href="/news">News</a><a href="/parks">Parks</a>'
                b'<a href="/departments/clerk">Clerk</a><a href="/DocumentCenter">Documents</a>')
        web = {"https://city.example/": resp("https://city.example/", home),
               "https://city.example/DocumentCenter": resp("https://city.example/DocumentCenter",
                                                           b'<a href="/DocumentCenter/View/12">Budget</a>')}
        calls = []
        site, found = sc.crawl("https://city.example/", get=web_get(web, calls), pages=1, pdfs=1, sleep=no_sleep)
        self.assertEqual(self.pages(calls), ["https://city.example/", "https://city.example/DocumentCenter"])
        self.assertEqual((site["pages_read"], site["doc_pages_read"], site["pdf_links"]), (1, 1, 1))
        self.assertFalse(site["fell_back"])
        self.assertEqual([r["url"] for r in found], ["https://city.example/DocumentCenter/View/12"])

    def test_follows_doc_links_one_level_deeper(self):
        # Two document-like pages without a PDF link use up half of the 4 pages, so the one
        # other page (News) is read before the deeper document-like page that has the PDF.
        web = {"https://a.gov/": resp("https://a.gov/", b'<a href="/news">News</a>'
                                                        b'<a href="/resources/">Guidance &amp; Resource Materials</a>'),
               "https://a.gov/resources/": resp("https://a.gov/resources/",
                                                b'<a href="/resources/primer/">Title II primer</a>'
                                                b'<a href="/news">News</a><a href="/web-guidance/">On the web</a>'),
               "https://a.gov/web-guidance/": resp("https://a.gov/web-guidance/",
                                                   b'<a href="/assets/pdfs/web-rule.pdf">the rule</a>')}
        calls = []
        site, _ = sc.crawl("https://a.gov/", get=web_get(web, calls), pages=4, pdfs=8, sleep=no_sleep)
        self.assertEqual(self.pages(calls), ["https://a.gov/", "https://a.gov/resources/",
                                             "https://a.gov/resources/primer/", "https://a.gov/news",
                                             "https://a.gov/web-guidance/"])
        self.assertEqual((site["pages_read"], site["doc_pages_read"], site["pdf_links"]), (4, 3, 1))
        self.assertTrue(site["fell_back"])
        self.assertIn("https://a.gov/assets/pdfs/web-rule.pdf", calls)

    def test_falls_back_to_other_pages(self):
        # The doc-first-reach test (docs/doc-first-results.md): on some sites every page read
        # was document-like and none had a PDF link, while random pages did.
        home = (b'<a href="/documents">Documents</a><a href="/forms">Forms</a><a href="/agendas">Agendas</a>'
                b'<a href="/news">News</a>')
        web = {"https://a.gov/": resp("https://a.gov/", home),
               "https://a.gov/news": resp("https://a.gov/news", b'<a href="/files/budget.pdf">Budget</a>')}
        for path in ("/documents", "/forms", "/agendas"):
            web["https://a.gov" + path] = resp("https://a.gov" + path, b"<p>Search our documents</p>")
        calls = []
        site, found = sc.crawl("https://a.gov/", get=web_get(web, calls), pages=4, pdfs=8, sleep=no_sleep)
        self.assertEqual(self.pages(calls), ["https://a.gov/", "https://a.gov/documents", "https://a.gov/forms",
                                             "https://a.gov/news", "https://a.gov/agendas"])
        self.assertEqual((site["pages_read"], site["doc_pages_read"], site["pdf_links"]), (4, 3, 1))
        self.assertTrue(site["fell_back"])
        self.assertEqual([r["url"] for r in found], ["https://a.gov/files/budget.pdf"])

    def test_default_reads_8_document_like_pages_before_falling_back(self):
        # The second doc-first test (docs/doc-first-v2-results.md): with 8 pages 0.1.2 fell back
        # after 4 document-like pages and lost hard sites where 0.1.1 found PDFs on its 5th to 8th.
        docs = ["/documents/%d" % i for i in range(10)]
        home = b"".join(b'<a href="%s">Documents</a>' % p.encode() for p in docs) + b'<a href="/news">News</a>'
        web = {"https://a.gov/": resp("https://a.gov/", home)}
        for p in docs:
            web["https://a.gov" + p] = resp("https://a.gov" + p, b"<p>Search our documents</p>")
        calls = []
        site, _ = sc.crawl("https://a.gov/", get=web_get(web, calls), pdfs=8, sleep=no_sleep)
        read_pages = self.pages(calls)[1:]
        self.assertEqual(read_pages[:8], ["https://a.gov" + p for p in docs[:8]])
        self.assertEqual(read_pages[8], "https://a.gov/news")
        self.assertEqual((site["pages_read"], site["doc_pages_read"]), (11, 10))
        self.assertTrue(site["fell_back"])

    def test_no_fall_back_once_a_pdf_link_is_found(self):
        home = b'<a href="/documents">Documents</a><a href="/forms">Forms</a><a href="/news">News</a>'
        web = {"https://a.gov/": resp("https://a.gov/", home),
               "https://a.gov/documents": resp("https://a.gov/documents", b'<a href="/a.pdf">a</a>'),
               "https://a.gov/forms": resp("https://a.gov/forms", b"<p>none</p>")}
        calls = []
        site, _ = sc.crawl("https://a.gov/", get=web_get(web, calls), pages=2, pdfs=8, sleep=no_sleep)
        self.assertEqual(self.pages(calls), ["https://a.gov/", "https://a.gov/documents", "https://a.gov/forms"])
        self.assertFalse(site["fell_back"])

    def test_stops_once_enough_pdf_links(self):
        home = b'<a href="/a.pdf">a</a><a href="/b.pdf">b</a><a href="/documents">Documents</a>'
        calls = []
        site, found = sc.crawl("https://a.gov/", get=web_get({"https://a.gov/": resp("https://a.gov/", home)}, calls),
                               pages=8, pdfs=1, sleep=no_sleep)
        self.assertEqual((site["pages_read"], site["pdf_links"]), (0, 2))
        self.assertNotIn("https://a.gov/documents", calls)
        self.assertEqual(site["pdfs_tried"], 2)
        self.assertEqual(site["pdfs_ok"], 0)
        self.assertEqual([r["result"] for r in found], ["http_error", "http_error"])

    def test_robots_and_other_pages_after_docs(self):
        web = {"https://a.gov/robots.txt": resp("r", b"User-agent: *\nDisallow: /private/\n", ctype="text/plain"),
               "https://a.gov/": resp("https://a.gov/", b'<a href="/news">News</a>'
                                                        b'<a href="/private/documents">Documents</a>'
                                                        b'<a href="https://elsewhere.example/forms">Forms</a>')}
        calls = []
        site, found = sc.crawl("https://a.gov/", get=web_get(web, calls), pages=8, pdfs=8, sleep=no_sleep)
        self.assertEqual(self.pages(calls), ["https://a.gov/", "https://a.gov/news"])
        self.assertEqual((site["pages_read"], site["doc_pages_read"], site["pdf_links"]), (1, 0, 0))
        self.assertFalse(site["fell_back"])
        self.assertEqual(found, [])
        md = sc.markdown(sc.run("https://a.gov/", get=web_get(web), sleep=no_sleep, checked="2026-10-16"))
        self.assertIn("- Pages read besides the home page: 1; PDF links found: 0", md)
        self.assertIn(sc.NO_PDFS, md)

    def test_home_failures(self):
        web = {"https://a.gov/robots.txt": resp("r", b"User-agent: *\nDisallow: /\n", ctype="text/plain")}
        self.assertEqual(sc.crawl("https://a.gov/", get=web_get(web), sleep=no_sleep)[0]["status"], "robots_disallow")
        self.assertEqual(sc.crawl("https://b.gov/", get=web_get({}), sleep=no_sleep)[0]["status"], "home_404")
        web = {"https://b.gov/": resp("https://b.gov/", b"%PDF-1.4", ctype="application/pdf")}
        site = sc.crawl("https://b.gov/", get=web_get(web), sleep=no_sleep)[0]
        self.assertEqual(site["status"], "home_not_html")
        md = sc.markdown(sc.run("https://b.gov/", get=web_get(web), sleep=no_sleep, checked="2026-10-16"))
        self.assertNotIn(sc.NO_PDFS, md)


@unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
class RunTests(unittest.TestCase):
    def setUp(self):
        home = (b'<a href="/news">n</a><a href="/docs/agenda.pdf">a</a>'
                b'<a href="/accessibility">Accessibility</a>')
        web = {
            "http://city.example/": resp("http://city.example/", home),
            "http://city.example/news": resp("http://city.example/news", b'<a href="/docs/minutes.pdf">m</a>'),
            "http://city.example/docs/agenda.pdf": resp("a", TAGGED_PDF, ctype="application/pdf"),
            "http://city.example/docs/minutes.pdf": resp("m", SCANNED_PDF, ctype="application/pdf"),
            "http://other.example/Annual Report (2025).pdf": resp("o", SCANNED_PDF, ctype="application/pdf"),
        }
        self.calls = []
        self.out = sc.run("City.Example", ["http://city.example/docs/agenda.pdf",
                                              "http://other.example/Annual Report (2025).pdf"],
                             get=web_get(web, self.calls), sleep=no_sleep, checked="2026-10-16")

    def test_result(self):
        r = self.out
        self.assertEqual(r["site"]["status"], "ok")
        self.assertEqual((r["site"]["pages_read"], r["site"]["pdf_links"]), (2, 2))
        self.assertIs(r["site"]["a11y_link"], True)
        self.assertEqual(len(r["pdfs"]), 3)
        self.assertEqual(self.calls.count("http://city.example/docs/agenda.pdf"), 1)
        self.assertEqual(r["summary"], {"pdfs_checked": 3, "pdfs_not_read": 0, "pass_all_four": 1,
                                        "fail": {"image_only": 2, "tagged": 2, "lang": 2, "title": 2}})
        self.assertEqual((r["version"], r["census_version"]), (sc.__version__, c.__version__))

    def test_markdown(self):
        md = sc.markdown(self.out)
        for text in ("# PDF basics check: city.example",
                     "Checked 2026-10-16 with site_check %s" % sc.__version__,
                     "- Home page links to a page about accessibility or the ADA: yes",
                     "- 3 PDFs checked; 1 pass all four basics; 0 could not be read.",
                     "| [agenda.pdf](http://city.example/docs/agenda.pdf) | yes | yes | yes | yes | word |",
                     "| [Annual Report (2025).pdf](http://other.example/Annual%20Report%20%282025%29.pdf) "
                     "| no | no | no | no | scanner |",
                     "### No text (likely a scan) (2 of 3)",
                     "### No tags (2 of 3)",
                     "- agenda.pdf: 1 of 2 tagged figures have no alt text.",
                     "- minutes.pdf: " + sc.SCANNER_NOTE,
                     sc.BASELINE, sc.DEADLINES, "mv2@munimtech.com", "with AI agents"):
            self.assertIn(text, md)
        self.assertNotIn("## Not read", md)
        self.assertNotIn(sc.NO_PDFS, md)

    def test_dataset_rows(self):
        rows = {r["name"]: r for r in sc.dataset_rows(self.out)}
        self.assertTrue(rows["agenda.pdf"]["all_four"])
        self.assertEqual(rows["agenda.pdf"]["fails"], [])
        self.assertEqual(rows["minutes.pdf"]["fails"],
                         ["No text (likely a scan)", "No tags", "No document language", "No title"])
        self.assertFalse(rows["minutes.pdf"]["has_text"])
        self.assertEqual(rows["minutes.pdf"]["producer_family"], "scanner")


class ActorFileTests(unittest.TestCase):
    def test_actor_json_points_at_existing_files(self):
        actor = json.loads(read(".actor", "actor.json"))
        self.assertEqual(actor["actorSpecification"], 1)
        for key in ("dockerfile", "input", "output", "readme"):
            self.assertTrue(os.path.exists(os.path.join(HERE, ".actor", actor[key])), key)
        self.assertTrue(os.path.exists(os.path.join(HERE, ".actor", actor["storages"]["dataset"])))
        self.assertIn("with AI agents", actor["description"])

    def test_input_schema_matches_actor_main(self):
        schema = json.loads(read(".actor", "input_schema.json"))
        main = read("actor_main.py")
        self.assertEqual(set(schema["properties"]), {"siteUrl", "pdfUrls", "maxPages", "maxPdfs"})
        for key in schema["properties"]:
            self.assertIn('inp.get("%s")' % key, main)
        self.assertIn("clamp(inp.get(\"maxPages\"), 0, 30, sc.PAGES)", main)
        self.assertEqual((schema["properties"]["maxPages"]["minimum"], schema["properties"]["maxPages"]["maximum"],
                          schema["properties"]["maxPages"]["default"]), (0, 30, sc.PAGES))
        self.assertIn("clamp(inp.get(\"maxPdfs\"), 1, 50, 8)", main)
        self.assertEqual((schema["properties"]["maxPdfs"]["minimum"], schema["properties"]["maxPdfs"]["maximum"],
                          schema["properties"]["maxPdfs"]["default"]), (1, 50, 8))

    def test_page_defaults_agree(self):
        # 0.1.3: the third doc-first test ran 16 pages; every entry point uses the same default.
        self.assertEqual(sc.PAGES, 16)
        self.assertEqual(inspect.signature(sc.crawl).parameters["pages"].default, sc.PAGES)
        self.assertEqual(inspect.signature(sc.run).parameters["pages"].default, sc.PAGES)
        self.assertEqual(sc.parser().parse_args(["https://a.gov/"]).pages, sc.PAGES)
        self.assertEqual(json.loads(read(".actor", "input_schema.json"))["properties"]["maxPages"]["default"],
                         sc.PAGES)

    def test_prefill_has_a_pdf(self):
        # 0.1.0's prefill (section508.gov) gave an empty report: no PDF links on the pages read.
        props = json.loads(read(".actor", "input_schema.json"))["properties"]
        self.assertTrue(props["siteUrl"]["prefill"].startswith("https://"))
        self.assertTrue(props["pdfUrls"]["prefill"])
        for url in props["pdfUrls"]["prefill"]:
            self.assertTrue(c.looks_like_pdf(url), url)

    def test_dataset_view_fields_exist(self):
        view = json.loads(read(".actor", "dataset_schema.json"))["views"]["overview"]
        fields = view["transformation"]["fields"]
        self.assertEqual(set(fields), set(view["display"]["properties"]))
        rec = {"result": "ok", "tagged": True, "lang": True, "title": True, "image_only": False,
               "display_doc_title": True, "url": "https://a.gov/x.pdf"}
        row = sc.dataset_rows({"pdfs": [dict(rec, fails=sc.failures(rec), notes=sc.notes(rec))]})[0]
        self.assertTrue(set(fields) <= set(row), set(fields) - set(row))

    def test_dockerfile_and_readme(self):
        docker = read(".actor", "Dockerfile")
        for name in ("census.py", "site_check.py", "actor_main.py", "requirements-actor.txt"):
            self.assertIn(name, docker)
            self.assertTrue(os.path.exists(os.path.join(HERE, name)), name)
        readme = read(".actor", "README.md")
        self.assertIn("Apache-2.0", readme)
        self.assertIn("with AI agents", readme)
        self.assertNotIn("MIT", readme)
        self.assertNotIn("an AI", readme)


if __name__ == "__main__":
    unittest.main()
