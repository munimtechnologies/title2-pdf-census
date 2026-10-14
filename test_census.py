"""Offline tests for title2-pdf-census (no network). Apache-2.0 licensed."""

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


def raw_pdf(objs, info=None):
    """A PDF file from object bodies (object 1 is the catalog), with a correct xref table."""
    out = b"%PDF-1.7\n"
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    trailer = b"<< /Size %d /Root 1 0 R" % (len(objs) + 1)
    if info:
        trailer += b" /Info %d 0 R" % info
    out += b"trailer\n" + trailer + b" >>\nstartxref\n%d\n%%%%EOF\n" % xref
    return out


def stream(data):
    return b"<< /Length %d >>\nstream\n" % len(data) + data + b"\nendstream"


TEXT = b"BT /F1 12 Tf 20 200 Td (Public notice of the city council meeting) Tj ET"

TAGGED_PDF = raw_pdf([
    b"<< /Type /Catalog /Pages 2 0 R /MarkInfo << /Marked true >> /StructTreeRoot 6 0 R"
    b" /Lang (en-US) /ViewerPreferences << /DisplayDocTitle true >> >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R"
    b" /Resources << /Font << /F1 5 0 R >> >> >>",
    stream(TEXT),
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    b"<< /Type /StructTreeRoot /K [7 0 R 8 0 R] /RoleMap << /Image /Figure >> >>",
    b"<< /Type /StructElem /S /Figure /Alt (City seal) >>",
    b"<< /Type /StructElem /S /Image >>",
    b"<< /Title (Agenda) /Producer (Microsoft Word for Microsoft 365)"
    b" /CreationDate (D:20250102030405-05'00') >>",
], info=9)

SCANNED_PDF = raw_pdf([
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>",
    b"<< /Producer (KONICA MINOLTA bizhub C458) /CreationDate (D:20230101120000) >>",
], info=4)


def resp(url, body=b"", status=200, ctype="text/html; charset=utf-8"):
    return c.Response(status, url, ctype, body, False, None if status == 200 else "http %d" % status)


class LinkTests(unittest.TestCase):
    def test_extract_links_resolves_and_dedupes(self):
        page = ('<a href="/news">News</a><a href="news#top">again</a><a href="mailto:a@b.c">m</a>'
                '<a href="https://other.example/x.PDF">x</a><a href="/news">dup</a>')
        self.assertEqual(c.extract_links(page, "http://city.example/"),
                         ["http://city.example/news", "https://other.example/x.PDF"])

    def test_looks_like_pdf(self):
        for url in ("http://a.gov/x/Report.PDF", "https://a.gov/DocumentCenter/View/123/Budget-2026",
                    "https://a.gov/AgendaCenter/ViewFile/Agenda/_10142026-1", "https://a.gov/Archive.aspx?ADID=55"):
            self.assertTrue(c.looks_like_pdf(url), url)
        for url in ("http://a.gov/pdf-library", "http://a.gov/news?file=x.pdfs", "http://a.gov/"):
            self.assertFalse(c.looks_like_pdf(url), url)

    def test_same_site(self):
        self.assertTrue(c.same_site("https://www.city.gov/a", "http://city.gov/"))
        self.assertTrue(c.same_site("https://docs.city.gov/a.pdf", "https://www.city.gov/"))
        self.assertFalse(c.same_site("https://notcity.gov/a", "https://city.gov/"))

    def test_sample_is_stable_and_independent_of_order(self):
        items = ["u%d" % i for i in range(20)]
        self.assertEqual(c.sample(items, 5, "s"), c.sample(list(reversed(items)), 5, "s"))
        self.assertEqual(len(c.sample(items, 5, "s")), 5)

    def test_robots(self):
        rp = c.robots_for(resp("x", b"User-agent: *\nDisallow: /private/\n", ctype="text/plain"))
        self.assertFalse(rp.can_fetch(c.UA, "http://a.gov/private/x"))
        self.assertTrue(rp.can_fetch(c.UA, "http://a.gov/public"))
        self.assertTrue(c.robots_for(resp("x", status=404)).can_fetch(c.UA, "http://a.gov/x"))
        self.assertFalse(c.robots_for(resp("x", status=403)).can_fetch(c.UA, "http://a.gov/x"))

    def test_normalize_site(self):
        self.assertEqual(c.normalize_site("WWW.City.gov"), "http://www.city.gov/")
        self.assertEqual(c.normalize_site("https://City.gov/home?x=1"), "https://city.gov/home")


class PdfFactTests(unittest.TestCase):
    def test_pdf_date(self):
        self.assertEqual(c.pdf_date("D:20240512103000-04'00'"), "2024-05-12")
        self.assertIsNone(c.pdf_date("D:19800101"))
        self.assertIsNone(c.pdf_date(None))

    def test_producer_family(self):
        self.assertEqual(c.producer_family("Microsoft® Word for Microsoft 365"), "word")
        self.assertEqual(c.producer_family("Adobe PDF Library 15.0", "Acrobat PDFMaker 21 for Word"), "adobe")
        self.assertEqual(c.producer_family("KONICA MINOLTA bizhub C458"), "scanner")
        self.assertEqual(c.producer_family(""), "unknown")
        self.assertEqual(c.producer_family("Something New 1.0"), "other")

    def test_wilson(self):
        lo, hi = c.wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2775, places=3)
        self.assertIsNone(c.wilson(0, 0))

    @unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
    def test_tagged_pdf(self):
        row = c.analyze_pdf(TAGGED_PDF)
        self.assertTrue(row["tagged"])
        self.assertTrue(row["marked"])
        self.assertTrue(row["lang"])
        self.assertTrue(row["title"])
        self.assertTrue(row["display_doc_title"])
        self.assertFalse(row["image_only"])
        self.assertGreater(row["text_chars"], 20)
        self.assertEqual((row["figures"], row["figures_alt"]), (2, 1))
        self.assertEqual(row["created"], "2025-01-02")
        self.assertEqual(row["producer_family"], "word")
        self.assertTrue(row["basic4"])

    @unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
    def test_scanned_pdf(self):
        row = c.analyze_pdf(SCANNED_PDF)
        self.assertFalse(row["tagged"])
        self.assertFalse(row["marked"])
        self.assertFalse(row["lang"])
        self.assertFalse(row["title"])
        self.assertTrue(row["image_only"])
        self.assertEqual(row["created"], "2023-01-01")
        self.assertEqual(row["producer_family"], "scanner")
        self.assertFalse(row["basic4"])


class CrawlTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
    def test_crawl_site(self):
        home = (b'<a href="/news">n</a><a href="/private/x">p</a><a href="/docs/agenda.pdf">a</a>'
                b'<a href="https://other.example/a.pdf">o</a><a href="/DocumentCenter/View/12/Budget">b</a>'
                b'<a href="mailto:x@y.z">m</a><a href="#top">t</a>')
        web = {
            "http://city.example/robots.txt": resp("r", b"User-agent: *\nDisallow: /private/\n", ctype="text/plain"),
            "http://city.example/": resp("http://city.example/", home),
            "http://city.example/news": resp("http://city.example/news", b'<a href="/docs/minutes.pdf">m</a>'),
            "http://city.example/docs/agenda.pdf": resp("a", TAGGED_PDF, ctype="application/pdf"),
            "http://city.example/docs/minutes.pdf": resp("m", SCANNED_PDF, ctype="application/pdf"),
            "http://city.example/DocumentCenter/View/12/Budget": resp("b", b"<html>login</html>"),
        }
        calls = []

        def get(url, max_bytes, timeout=20):
            calls.append(url)
            return web.get(url, resp(url, status=404))

        row = {"qid": "Q1", "name": "City", "kind": "city", "state": "X", "population": "60000",
               "website": "http://city.example"}
        site, found = c.crawl_site(row, get=get, sleep=lambda s: None)
        self.assertEqual(site["status"], "ok")
        self.assertEqual(site["pages_read"], 1)
        self.assertNotIn("http://city.example/private/x", calls)
        self.assertEqual(site["pdf_links"], 4)
        self.assertEqual((site["pdfs_tried"], site["pdfs_ok"]), (4, 2))
        results = sorted(r["result"] for r in found)
        self.assertEqual(results, ["http_error", "not_pdf", "ok", "ok"])
        self.assertIn("https://other.example/robots.txt", calls)

    def test_blocked_home(self):
        def get(url, max_bytes, timeout=20):
            return resp(url, status=403) if not url.endswith("robots.txt") else resp(url, status=404)
        site, found = c.crawl_site({"qid": "Q2", "website": "https://blocked.example/"}, get=get,
                                   sleep=lambda s: None)
        self.assertEqual(site["status"], "home_403")
        self.assertEqual(found, [])


class SummaryTests(unittest.TestCase):
    def setUp(self):
        base = {"result": "ok", "lang": True, "title": True, "image_only": False, "kind": "city",
                "producer_family": "word", "figures": 0, "figures_alt": 0}
        self.pdfs = [
            dict(base, qid="Q1", tagged=True, basic4=True, created="2025-03-01", figures=2, figures_alt=1),
            dict(base, qid="Q1", tagged=False, basic4=False, created="2023-03-01"),
            dict(base, qid="Q2", tagged=False, basic4=False, created=None),
            {"qid": "Q2", "result": "not_pdf"},
        ]
        self.sites = [{"qid": "Q1", "status": "ok"}, {"qid": "Q2", "status": "ok"},
                      {"qid": "Q3", "status": "home_403"}]

    def test_summarize(self):
        s = c.summarize(self.sites, self.pdfs)
        self.assertEqual(s["overall"]["tagged"]["k"], 1)
        self.assertEqual(s["overall"]["tagged"]["n"], 3)
        self.assertEqual(s["by_era"]["after_rule"]["tagged"]["share"], 1.0)
        self.assertEqual(s["by_era"]["before_rule"]["tagged"]["share"], 0.0)
        self.assertEqual(s["by_era"]["undated"]["tagged"]["n"], 1)
        self.assertEqual(s["paired_era"]["sites"], 1)
        self.assertEqual(s["paired_era"]["improved"], 1)
        self.assertEqual(s["pdf_results"], {"ok": 3, "not_pdf": 1})
        self.assertEqual(s["figures"]["total"], 2)
        self.assertIsNone(s["sites_rated"]["mean_tagged_share"])
        self.assertIn("33.3%", c.report(s))

    def test_site_table(self):
        rows = c.site_table(self.sites, self.pdfs)
        q1 = [r for r in rows if r["qid"] == "Q1"][0]
        self.assertEqual((q1["tagged"], q1["lang"]), (1, 2))

    def test_parse_cohort(self):
        def b(qid, label, kind, pop, site):
            return {"item": {"value": "http://www.wikidata.org/entity/" + qid}, "itemLabel": {"value": label},
                    "typeLabel": {"value": kind}, "population": {"value": str(pop)}, "website": {"value": site}}
        data = {"results": {"bindings": [
            b("Q1", "Big City", "city in the United States", 900000, "https://www.big.gov/"),
            b("Q2", "Big County", "county of the United States", 1200000, "https://big.gov"),
            b("Q3", "Metro", "consolidated city-county", 70000, "https://metro.gov"),
            b("Q4", "Bad", "city in the United States", "", "https://bad.gov"),
        ]}}
        rows = c.parse_cohort(data)
        self.assertEqual([r["qid"] for r in rows], ["Q2", "Q3"])
        self.assertEqual(rows[1]["kind"], "city-county")


if __name__ == "__main__":
    unittest.main()
