"""Offline tests for census 0.2.3: miss-reason records, miss_reason and the retry command.

The 2026 same-day retest (docs/panel-retest-results.md, docs/miss-reasons-results.md) found that
a re-crawl's misses must be told apart (no response, link gone, page not read, quota) before a
2027 panel can say a failing PDF was taken down. 0.2.3 records what is needed for that, and
these tests check that it changes nothing else: the frozen 0.2.2 crawl_site in
fixtures/census_0_2_2.py, run on the same synthetic site, makes the very same requests in the
same order and writes the very same values for every field it has.
No network and no pypdf: PDF parsing is replaced by a stub. Apache-2.0 licensed.
Made by MV2 of Munim, Inc. with AI agents.
"""

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import census as c  # noqa: E402


def load_022():
    spec = importlib.util.spec_from_file_location(
        "census_0_2_2", os.path.join(ROOT, "fixtures", "census_0_2_2.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


OLD = load_022()
HOME = "http://town.example/"
ROBOTS = b"User-agent: *\nDisallow: /p7\n"


def stub_analyze(data, text_pages=2):
    """Checks of a fake PDF: its body says which ones pass; b"BAD" raises like pypdf would."""
    if b"BAD" in data:
        raise ValueError("cannot read")
    tagged = b"TAGGED" in data
    return {"pages": 1, "tagged": tagged, "lang": tagged, "title": True, "image_only": False,
            "created": "2025-01-02", "producer_family": "word", "basic4": tagged}


def resp(module, url, body=b"", status=200, ctype="text/html", truncated=False, error=None):
    return module.Response(status, url, ctype, body, truncated, error)


def page(*hrefs, base=None):
    head = '<base href="%s">' % base if base else ""
    return (head + "".join('<a href="%s">x</a>' % h for h in hrefs)).encode()


def pdf_response(module, url):
    """Every outcome a PDF fetch can have, chosen by the file name."""
    name = url.rsplit("/", 1)[-1]
    if name.startswith("t0"):
        return resp(module, url, status=0, error="URLError: <urlopen error timed out>")
    if name.startswith("d0"):
        return resp(module, url, status=0,
                    error="URLError: <urlopen error [Errno -2] Name or service not known>")
    if name.startswith("e4"):
        return resp(module, url, status=404, error="http 404")
    if name.startswith("big"):
        return resp(module, url, b"%PDF-1.7", ctype="application/pdf", truncated=True)
    if name.startswith("htm"):
        return resp(module, url, b"<html>not a pdf</html>")
    if name.startswith("bad"):
        return resp(module, url, b"%PDF-1.7 BAD", ctype="application/pdf")
    tag = b" TAGGED" if "tag" in name else b""
    return resp(module, url, b"%PDF-1.7" + tag, ctype="application/pdf")


def web_for(module):
    """A town site: a home page with PDFs and twelve inner pages of every kind."""
    names = ["tag%d.pdf" % i for i in range(6)] + ["plain%d.pdf" % i for i in range(6)] + [
        "t0a.pdf", "t0b.pdf", "d0a.pdf", "e4a.pdf", "e4b.pdf", "biga.pdf", "htma.pdf", "bada.pdf"]
    home_links = ["/p%d/" % i for i in range(12)] + ["/files/" + n for n in names[:5] + names[-3:]] + [
        "http://docs.other.example/tag-off.pdf", "/DocumentCenter/View/12", "/files/x.jpg"]
    web = {HOME + "robots.txt": resp(module, HOME + "robots.txt", ROBOTS, ctype="text/plain"),
           HOME: resp(module, HOME, page(*home_links))}
    for i in range(12):
        url = HOME + "p%d/" % i
        if i == 3:
            web[url] = resp(module, url, status=404, error="http 404")
        elif i == 4:
            web[url] = resp(module, url, status=0, error="TimeoutError: timed out")
        elif i == 5:
            web[url] = resp(module, url, b"{}", ctype="application/json")
        elif i == 6:
            web[url] = resp(module, url, page("rel-tag.pdf", "plain0.pdf", base=HOME + "files/"))
        else:
            mine = ["/files/" + n for n in names[i:i + 6]] + ["/p%d/own%d-tag.pdf" % (i, i)]
            web[url] = resp(module, url, page(*mine))
    return web


def run_crawl(module, **kw):
    web, calls = web_for(module), []

    def get(url, max_bytes, timeout=20):
        calls.append(("get", url, max_bytes))
        if url in web:
            return web[url]
        if c.looks_like_pdf(url):
            return pdf_response(module, url)
        return resp(module, url, status=404, error="http 404")

    def sleep(s):
        calls.append(("sleep", s))

    with mock.patch.object(module, "analyze_pdf", stub_analyze):
        site, found = module.crawl_site({"qid": "Q1", "name": "Town", "kind": "city",
                                         "state": "X", "population": 60000, "website": HOME},
                                        get=get, sleep=sleep, **kw)
    return site, found, calls


def published(found):
    """PDF records as redact.py publishes them: the URL replaced by its SHA-256."""
    out = []
    for rec in found:
        rec = dict(rec)
        rec["url_sha256"] = hashlib.sha256(rec.pop("url").encode("utf-8")).hexdigest()
        out.append(rec)
    return out


class SameAsOldTests(unittest.TestCase):
    """0.2.3 makes the same requests as 0.2.2 and only adds fields."""

    SETTINGS = [dict(), dict(pages=8, pdfs=1), dict(pages=3, pdfs=2), dict(pages=12, pdfs=20),
                dict(pages=12, pdfs=40), dict(pages=0, pdfs=8), dict(pages=8, pdfs=3, delay=0.5)]

    def test_fixture_is_0_2_2(self):
        self.assertEqual(OLD.__version__, "0.2.2")

    def test_same_requests_and_values(self):
        for kw in self.SETTINGS:
            with self.subTest(**kw):
                old_site, old_found, old_calls = run_crawl(OLD, **kw)
                new_site, new_found, new_calls = run_crawl(c, **kw)
                self.assertEqual(new_calls, old_calls)
                self.assertEqual({k: new_site[k] for k in old_site}, old_site)
                self.assertEqual(set(new_site) - set(old_site),
                                 {"pages", "pdf_links_sha256", "candidates_sha256",
                                  "candidates_looked_at", "stopped"})
                self.assertEqual(len(new_found), len(old_found))
                for old, new in zip(old_found, new_found):
                    self.assertEqual({k: new[k] for k in old}, old)
                    self.assertLessEqual(set(new) - set(old),
                                         {"found_on", "candidate_rank", "no_response"})

    def test_the_synthetic_site_covers_every_outcome(self):
        site, found, _ = run_crawl(c, pages=12, pdfs=40)
        results = {r["result"] for r in found}
        self.assertEqual(results, {"ok", "http_error", "too_large", "not_pdf", "parse_error"})
        self.assertEqual({r.get("no_response") for r in found if r["status"] == 0},
                         {"timeout", "dns"})
        self.assertTrue(any(not r["same_site"] for r in found))
        self.assertEqual(site["stopped"], "candidates_done")
        self.assertEqual(site["candidates_looked_at"], len(site["candidates_sha256"]))
        quota = [run_crawl(c, pages=8, pdfs=k)[0] for k in (1, 2, 3, 4, 5)]
        self.assertTrue(any(s["stopped"] == "quota" and
                            s["candidates_looked_at"] < len(s["candidates_sha256"]) for s in quota))

    def test_summary_is_unchanged(self):
        site, found, _ = run_crawl(c, pages=12, pdfs=40)
        old_site, old_found, _ = run_crawl(OLD, pages=12, pdfs=40)
        new = c.summarize([site], found)
        old = OLD.summarize([old_site], old_found)
        new.pop("version")
        old.pop("version")
        self.assertEqual(new, old)


class RecordTests(unittest.TestCase):
    def test_hashes_are_what_redact_publishes(self):
        url = "https://www.county.example/files/Board Agenda.pdf"
        self.assertEqual(c.url_hash(url), hashlib.sha256(url.encode("utf-8")).hexdigest())

    def test_site_lists_links_and_candidates_by_hash(self):
        site, found, _ = run_crawl(c, pages=8, pdfs=3)
        self.assertEqual(len(site["pdf_links_sha256"]), site["pdf_links"])
        self.assertEqual(len(set(site["pdf_links_sha256"])), site["pdf_links"])
        self.assertEqual(len(site["candidates_sha256"]), min(6, site["pdf_links"]))
        self.assertLessEqual(set(site["candidates_sha256"]), set(site["pdf_links_sha256"]))
        for rec in published(found):
            self.assertEqual(site["candidates_sha256"][rec["candidate_rank"]], rec["url_sha256"])
        self.assertNotIn("http", json.dumps(site["pages"]))

    def test_found_on_names_the_first_page_with_the_link(self):
        site, found, _ = run_crawl(c, pages=12, pdfs=40)
        read = {p["sha256"] for p in site["pages"] if p["status"] == 200}
        by_url = {r["url"]: r for r in found}
        for url, rec in by_url.items():
            self.assertTrue(rec["found_on"] == "home" or rec["found_on"] in read, url)
        own = [r for u, r in by_url.items() if "/own" in u]
        self.assertTrue(own)
        for rec in own:
            self.assertEqual(rec["found_on"], c.url_hash(rec["url"].rsplit("/", 1)[0] + "/"))
        home_pdf = by_url.get(HOME + "files/tag0.pdf")
        if home_pdf:
            self.assertEqual(home_pdf["found_on"], "home")

    def test_pages_record_every_inner_page_tried(self):
        site, _, _ = run_crawl(c, pages=12, pdfs=8)
        statuses = sorted(str(p["status"]) for p in site["pages"])
        self.assertEqual(len(site["pages"]), 12)
        self.assertIn("robots", statuses)
        self.assertIn("404", statuses)
        self.assertIn("0", statuses)
        self.assertEqual(site["pages_read"], 11)

    def test_no_response_kinds(self):
        def kind(error, status=0):
            return c.no_response_kind(c.Response(status, "u", "", b"", False, error))
        self.assertEqual(kind("TimeoutError: The read operation timed out"), "timeout")
        self.assertEqual(kind("URLError: <urlopen error [Errno -3] Temporary failure in name "
                              "resolution>"), "dns")
        self.assertEqual(kind("URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] "
                              "certificate verify failed>"), "tls")
        self.assertEqual(kind("URLError: <urlopen error [Errno 111] Connection refused>"),
                         "refused")
        self.assertEqual(kind("ConnectionResetError: [Errno 104] Connection reset by peer"),
                         "reset")
        self.assertEqual(kind("RemoteDisconnected: Remote end closed connection"), "reset")
        self.assertEqual(kind("OSError: something else"), "other")
        self.assertEqual(kind(None), "other")
        self.assertIsNone(kind("http 404", status=404))


class MissReasonTests(unittest.TestCase):
    SITE = {"status": "ok", "pdf_links_sha256": ["a", "b", "c", "d", "e"],
            "candidates_sha256": ["c", "a", "d", "e"], "candidates_looked_at": 3,
            "stopped": "quota",
            "pages": [{"sha256": "P1", "status": 200, "pdf_links": 2},
                      {"sha256": "P2", "status": 404, "pdf_links": 0},
                      {"sha256": "P3", "status": "robots", "pdf_links": 0}]}
    ROWS = [{"url_sha256": "c", "status": 200, "result": "ok"},
            {"url_sha256": "a", "status": 0, "result": "http_error"},
            {"url_sha256": "x404", "status": 404, "result": "http_error"},
            {"url_sha256": "xbig", "status": 200, "result": "too_large"}]

    def reason(self, sha, found_on=None, site=SITE):
        return c.miss_reason(sha, site, self.ROWS, found_on)

    def test_each_reason(self):
        self.assertEqual(self.reason("c"), "read")
        self.assertEqual(self.reason("a"), "no_response")
        self.assertEqual(self.reason("x404"), "http_error")
        self.assertEqual(self.reason("xbig"), "too_large")
        self.assertEqual(self.reason("b"), "outranked")
        self.assertEqual(self.reason("d"), "robots")
        self.assertEqual(self.reason("e"), "quota")
        self.assertEqual(self.reason("z"), "link_absent")
        self.assertEqual(self.reason("z", "home"), "link_absent")
        self.assertEqual(self.reason("z", "P1"), "link_absent")
        self.assertEqual(self.reason("z", "P2"), "page_not_read")
        self.assertEqual(self.reason("z", "P3"), "page_not_read")
        self.assertEqual(self.reason("z", "P9"), "page_not_read")

    def test_site_not_read(self):
        self.assertEqual(c.miss_reason("c", None, []), "site_not_read")
        self.assertEqual(c.miss_reason("c", {"status": "home_404"}, []), "site_not_read")
        deadline = dict(self.SITE, stopped="deadline")
        self.assertEqual(c.miss_reason("e", deadline, []), "deadline")

    def test_every_link_of_a_real_crawl_gets_a_reason(self):
        site, found, _ = run_crawl(c, pages=8, pdfs=2)
        rows = published(found)
        allowed = {"read", "no_response", "http_error", "too_large", "not_pdf", "parse_error",
                   "outranked", "robots", "quota"}
        reasons = [c.miss_reason(h, site, rows) for h in site["pdf_links_sha256"]]
        self.assertLessEqual(set(reasons), allowed)
        self.assertEqual(reasons.count("read"), site["pdfs_ok"])
        self.assertEqual(len(reasons) - reasons.count("outranked"), len(site["candidates_sha256"]))
        tried = [r for r in reasons if r not in ("outranked", "robots", "quota")]
        self.assertEqual(len(tried), site["pdfs_tried"])


class RetryTests(unittest.TestCase):
    ROWS = [
        {"qid": "Q1", "kind": "city", "state": "X", "url": "http://town.example/files/t0x.pdf",
         "host": "town.example", "same_site": True, "status": 0, "bytes": 0,
         "result": "http_error", "no_response": "timeout", "found_on": "home",
         "candidate_rank": 2},
        {"qid": "Q1", "kind": "city", "state": "X", "url": "http://town.example/files/ok.pdf",
         "host": "town.example", "same_site": True, "status": 200, "result": "ok"},
        {"qid": "Q2", "kind": "county", "state": "Y", "url": "http://county.example/p7/x.pdf",
         "host": "county.example", "same_site": True, "status": 0, "result": "http_error"},
        {"qid": "Q2", "kind": "county", "state": "Y", "url": "http://county.example/gone.pdf",
         "host": "county.example", "same_site": True, "status": 404, "result": "http_error"},
    ]

    def run_retry(self):
        calls = []

        def get(url, max_bytes, timeout=20):
            calls.append(url)
            if url == "http://county.example/robots.txt":
                return resp(c, url, ROBOTS, ctype="text/plain")
            if url.endswith("robots.txt"):
                return resp(c, url, status=404, error="http 404")
            return resp(c, url, b"%PDF-1.7 TAGGED", ctype="application/pdf")

        rows = copy.deepcopy(self.ROWS)
        with mock.patch.object(c, "analyze_pdf", stub_analyze):
            out = c.retry_no_response(rows, get=get, sleep=lambda s: None, workers=2)
        self.assertEqual(rows, self.ROWS)
        return out, calls

    def test_only_no_response_rows_are_retried(self):
        out, calls = self.run_retry()
        self.assertEqual([r["url"] for r in out], ["http://town.example/files/t0x.pdf",
                                                   "http://county.example/p7/x.pdf"])
        pdf_calls = [u for u in calls if not u.endswith("robots.txt")]
        self.assertEqual(pdf_calls, ["http://town.example/files/t0x.pdf"])
        first, blocked = out
        self.assertEqual((first["retry"], first["first_status"], first["status"],
                          first["result"], first["first_no_response"]),
                         (True, 0, 200, "ok", "timeout"))
        self.assertEqual((first["found_on"], first["candidate_rank"]), ("home", 2))
        self.assertTrue(first["tagged"])
        self.assertEqual((blocked["result"], blocked["status"]), ("robots_disallow", None))
        self.assertEqual(c.retry_counts(out), {"result_ok": 1, "result_robots_disallow": 1,
                                               "retried": 2})

    def test_retry_command_with_nothing_to_retry_goes_nowhere(self):
        tmp = tempfile.mkdtemp()
        try:
            src, dst = os.path.join(tmp, "pdfs.jsonl"), os.path.join(tmp, "retry.jsonl")
            with open(src, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.ROWS[1]) + "\n")
            with mock.patch.object(c, "http_get", side_effect=AssertionError("network")), \
                    mock.patch("sys.stdout"):
                self.assertEqual(c.main(["retry", "--pdfs", src, "--out", dst,
                                         "--wait-minutes", "0"]), 0)
            with open(dst, encoding="utf-8") as f:
                self.assertEqual(f.read(), "")
        finally:
            shutil.rmtree(tmp)

    def test_summarize_command_still_works(self):
        site, found, _ = run_crawl(c, pages=8, pdfs=3)
        tmp = tempfile.mkdtemp()
        try:
            paths = [os.path.join(tmp, n) for n in ("sites.jsonl", "pdfs.jsonl")]
            for path, rows in zip(paths, ([site], found)):
                with open(path, "w", encoding="utf-8") as f:
                    f.write("".join(json.dumps(r) + "\n" for r in rows))
            with mock.patch("sys.stdout"):
                c.main(["summarize", "--sites", paths[0], "--pdfs", paths[1], "--out-dir", tmp])
            with open(os.path.join(tmp, "summary.json"), encoding="utf-8") as f:
                summary = json.load(f)
            self.assertEqual(summary["version"], "0.2.3")
            self.assertEqual(summary["pdfs_tried"], len(found))
        finally:
            shutil.rmtree(tmp)


class VersionTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(c.__version__, "0.2.3")
        self.assertIn("0.2.3", c.UA)


if __name__ == "__main__":
    unittest.main()
