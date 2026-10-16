"""Offline tests for site_check and the Apify Actor files (no network). Apache-2.0 licensed."""

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
        s = json.loads(read("results", "v0.2.0", "summary.json"))
        o, by = s["overall"], s["by_producer"]
        self.assertIn("of {:,} PDFs from {:,} US cities and counties".format(s["pdf_results"]["ok"],
                                                                           s["sites_with_ok_pdf"]), sc.BASELINE)
        self.assertIn("%.1f%% were tagged and %.1f%% passed all four basics" % (
            100 * o["tagged"]["share"], 100 * o["basic4"]["share"]), sc.BASELINE)
        self.assertIn("(%.1f%% in the census)" % (100 * by["print-to-pdf"]["tagged"]["share"]), sc.PRINT_NOTE)
        self.assertIn("(%.1f%% of scanner output" % (100 * by["scanner"]["tagged"]["share"]), sc.SCANNER_NOTE)


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
                     "Checked 2026-10-16 with site_check 0.1.0",
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
        self.assertIn("clamp(inp.get(\"maxPages\"), 0, 30, 8)", main)
        self.assertEqual((schema["properties"]["maxPages"]["minimum"], schema["properties"]["maxPages"]["maximum"],
                          schema["properties"]["maxPages"]["default"]), (0, 30, 8))
        self.assertIn("clamp(inp.get(\"maxPdfs\"), 1, 50, 8)", main)
        self.assertEqual((schema["properties"]["maxPdfs"]["minimum"], schema["properties"]["maxPdfs"]["maximum"],
                          schema["properties"]["maxPdfs"]["default"]), (1, 50, 8))

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
