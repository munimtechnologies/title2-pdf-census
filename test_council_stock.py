# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for council_stock.py (no network: every page comes from a fake).

python -m unittest discover -p test_council_stock.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import council_stock as cs  # noqa: E402

FRAME = os.path.join(ROOT, *cs.FRAME_PATH.split("/"))
PREREG = os.path.join(ROOT, *cs.PREREG_PATH.split("/"))

STATEMENT = (b"<html><head><title>Accessibility statement | A Council</title></head><body>"
             b"<h1>Accessibility statement for A Council</h1><p>This accessibility statement "
             b"applies to the council website. This website is run by A Council. We want as many "
             b"people as possible to be able to use this website.</p><h2>Compliance status</h2>"
             b"<p>This website is partially compliant with the Web Content Accessibility "
             b"Guidelines version 2.2 AA standard, due to the non-compliances listed below.</p>"
             b"<h2>Enforcement procedure</h2><p>The Equality and Human Rights Commission (EHRC) is "
             b"responsible for enforcing the accessibility regulations.</p><p>This statement was "
             b"prepared on 23 September 2020. It was last reviewed on 4 October 2025.</p>"
             b"</body></html>")
HOME_LINK = (b"<html><body><a href=\"/news\">News</a><footer><a href=\"/about/accessibility\">"
             b"Accessibility statement</a></footer></body></html>")
HOME_NOLINK = b"<html><body><a href=\"/news\">News</a><p>Welcome to the council.</p></body></html>"
HOME_HUBLINK = b"<html><body><a href=\"/accessibility\">Accessibility</a></body></html>"
HUB = (b"<html><body><h1>Accessibility</h1><p>Use our accessibility tools to change colours.</p>"
       b"<a href=\"/accessibility/statement\">Accessibility statement</a></body></html>")
HOME_OFFSITE = (b"<html><body><a href=\"https://statements.example.com/e\">Accessibility statement"
                b"</a></body></html>")
HOME_HOMELINK = (b"<html><body><a href=\"/accessibility-statement-x\">Accessibility statement</a>"
                 b"</body></html>")
HTML = "text/html; charset=utf-8"


class FakeGet:
    """Pages by exact address; any address starting with a dead prefix gets no answer (status 0);
    everything else is a 404."""

    def __init__(self, pages=None, dead=()):
        self.pages, self.dead, self.calls = pages or {}, dead, []

    def __call__(self, url, timeout=20):
        self.calls.append(url)
        if any(url.startswith(d) for d in self.dead):
            return 0, url, "", b""
        if url in self.pages:
            p = self.pages[url]
            if len(p) == 2:
                return 200, url, p[0], p[1]
            return p
        return 404, url, "", b""


def nosleep(_):
    return None


def run(host, get):
    return cs.read_one({"host": host, "name": "X Council", "gss": "E0", "kind": "england_district",
                        "authorities": 1}, get=get, delay=0, sleep=nosleep)


class ReadTests(unittest.TestCase):
    def test_link_found_and_read(self):
        get = FakeGet({"https://www.a.gov.uk/robots.txt": ("text/plain",
                                                           b"User-agent: *\nDisallow: /search\n"),
                       "https://www.a.gov.uk/": (HTML, HOME_LINK),
                       "https://www.a.gov.uk/about/accessibility": (HTML, STATEMENT)})
        r = run("a.gov.uk", get)
        self.assertEqual(get.calls[0], "https://www.a.gov.uk/robots.txt")
        self.assertEqual((r["status"], r["found_by"], r["home_status"]), ("ok", "link", "200"))
        self.assertEqual(r["statement_url"], "https://www.a.gov.uk/about/accessibility")
        self.assertFalse(r["other_host"])
        self.assertEqual((r["highest"], r["gov_uk_sample"], r["wcag_named"], r["placeholder"]),
                         ("2.2", True, True, False))
        self.assertEqual((r["review_date"], r["prepared_date"], r["statement_date"],
                          r["date_source"]), ("2025-10-04", "2020-09-23", "2025-10-04", "reviewed"))
        self.assertTrue(cs.stale(r))
        self.assertEqual(len(r["text_sha256"]), 64)
        self.assertNotIn("https://www.a.gov.uk/accessibility-statement", get.calls)

    def test_bare_host_when_www_does_not_answer(self):
        get = FakeGet({"https://b.gov.uk/": (HTML, HOME_NOLINK),
                       "https://b.gov.uk/accessibility-statement": (HTML, STATEMENT)},
                      dead=("https://www.b.gov.uk",))
        r = run("b.gov.uk", get)
        self.assertEqual((r["status"], r["found_by"]), ("ok", "probe1"))

    def test_second_address(self):
        get = FakeGet({"https://www.b2.gov.uk/": (HTML, HOME_NOLINK),
                       "https://www.b2.gov.uk/accessibility": (HTML, STATEMENT)})
        r = run("b2.gov.uk", get)
        self.assertEqual((r["status"], r["found_by"]), ("ok", "probe2"))

    def test_no_answer(self):
        get = FakeGet(dead=("https://www.n.gov.uk", "https://n.gov.uk"))
        self.assertEqual(run("n.gov.uk", get)["status"], "http_0")

    def test_robots_blocks_home(self):
        get = FakeGet({"https://www.c.gov.uk/robots.txt": ("text/plain",
                                                           b"User-agent: *\nDisallow: /\n"),
                       "https://www.c.gov.uk/": (HTML, HOME_LINK)})
        r = run("c.gov.uk", get)
        self.assertEqual(r["status"], "robots")
        self.assertTrue(r["robots_blocked"])
        self.assertNotIn("https://www.c.gov.uk/", get.calls)

    def test_one_hop_from_a_hub(self):
        get = FakeGet({"https://www.d.gov.uk/": (HTML, HOME_HUBLINK),
                       "https://www.d.gov.uk/accessibility": (HTML, HUB),
                       "https://www.d.gov.uk/accessibility/statement": (HTML, STATEMENT)})
        r = run("d.gov.uk", get)
        self.assertEqual((r["status"], r["found_by"]), ("ok", "hub"))

    def test_redirect_home_is_not_a_statement(self):
        get = FakeGet({"https://www.e.gov.uk/": (HTML, HOME_HOMELINK),
                       "https://www.e.gov.uk/accessibility-statement-x":
                           (200, "https://www.e.gov.uk/", HTML, STATEMENT)})
        r = run("e.gov.uk", get)
        self.assertEqual(r["status"], "not_found")

    def test_offsite_link_not_followed(self):
        get = FakeGet({"https://www.f.gov.uk/": (HTML, HOME_OFFSITE),
                       "https://statements.example.com/e": (HTML, STATEMENT)})
        r = run("f.gov.uk", get)
        self.assertEqual(r["status"], "not_found")
        self.assertTrue(r["offsite_link"])
        self.assertNotIn("https://statements.example.com/e", get.calls)

    def test_retry_once_after_503(self):
        class Flaky(FakeGet):
            def __call__(self, url, timeout=20):
                if url == "https://www.g.gov.uk/accessibility-statement" and url not in self.calls:
                    self.calls.append(url)
                    return 503, url, "", b""
                return FakeGet.__call__(self, url, timeout)
        get = Flaky({"https://www.g.gov.uk/": (HTML, HOME_NOLINK),
                     "https://www.g.gov.uk/accessibility-statement": (HTML, STATEMENT)})
        r = run("g.gov.uk", get)
        self.assertEqual((r["status"], r["retried"]), ("ok", True))


class RuleTests(unittest.TestCase):
    def test_link_scores(self):
        self.assertEqual(cs.link_score("/a", "Accessibility statement"), 3)
        self.assertEqual(cs.link_score("/accessibility-statement", "Accessibility"), 2)
        self.assertEqual(cs.link_score("/accessibility", "Accessibility"), 1)
        self.assertEqual(cs.link_score("/accessibility", "Accessibility tools"), 0)
        self.assertEqual(cs.link_score("/contact", "Contact us"), 0)

    def test_placeholder_is_read(self):
        page = STATEMENT.replace(b"</body>", b"<p>Email: [email address]</p></body>")
        d = cs.read_statement(cs.stc.visible_text(page, HTML))
        self.assertTrue(d["placeholder"])
        self.assertEqual(d["placeholder_ids"], "gov-uk/email_address")

    def test_not_a_statement(self):
        self.assertFalse(cs.is_statement(cs.stc.visible_text(HUB, HTML)))
        self.assertTrue(cs.is_statement(cs.stc.visible_text(STATEMENT, HTML)))

    def test_dates(self):
        sd = cs.statement_dates
        self.assertEqual(sd("Last reviewed: 01/09/2025"), ("2025-09-01", "", "2025-09-01", "reviewed"))
        self.assertEqual(sd("This statement was last updated in March 2024."),
                         ("2024-03-31", "", "2024-03-31", "reviewed"))
        self.assertEqual(sd("It was reviewed on Sept. 5, 2025."),
                         ("2025-09-05", "", "2025-09-05", "reviewed"))
        self.assertEqual(sd("This statement was prepared on 2021-02-03."),
                         ("", "2021-02-03", "2021-02-03", "prepared"))
        self.assertEqual(sd("It was last reviewed on 31/02/2025."), ("", "", "", ""))
        self.assertEqual(sd("It was last reviewed on 4 May 2015."), ("", "", "", ""))
        self.assertEqual(sd("It was last reviewed on [date]."), ("", "", "", ""))
        self.assertEqual(sd("Prepared on 1 June 2026. It was last reviewed on 4 May 2025."),
                         ("2025-05-04", "2026-06-01", "2026-06-01", "prepared"))

    def test_stale_cutoff(self):
        self.assertTrue(cs.stale({"statement_date": "2025-10-31"}))
        self.assertFalse(cs.stale({"statement_date": "2025-11-01"}))
        self.assertFalse(cs.stale({"statement_date": ""}))


def synthetic():
    rows = []
    for i in range(122):
        r = cs.blank({"host": "h%03d.gov.uk" % i, "name": "C%d" % i, "gss": "E%d" % i,
                      "kind": "england_district" if i % 2 else "scotland_council",
                      "authorities": 1})
        if i < 2:
            r["status"] = "http_0"
        else:
            j = i - 2
            r.update(status="ok", found_by="link", home_status="200",
                     highest="2.2" if j < 80 else "2.1",
                     statement_date="2024-01-01" if j < 40 else "2026-01-01",
                     date_source="reviewed", review_date="2024-01-01" if j < 40 else "2026-01-01",
                     text_sha256="%064x" % j, placeholder=j < 6,
                     placeholder_ids="gov-uk/email_address" if j < 6 else "")
        rows.append(r)
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        m, g, p = cs.grade(synthetic())
        self.assertEqual(g, {"F1_frame": True, "G1_answered": True})
        self.assertEqual(p, {"N1": True, "N2": False, "N3": True, "N4": True})
        self.assertEqual(m["N3_wcag22_of_found"], {"k": 80, "n": 120, "pct": 66.67})
        self.assertEqual(m["N4_stale_of_dated"], {"k": 40, "n": 120, "pct": 33.33})
        self.assertEqual(m["N2_placeholder_hosts"], 6)

    def test_small_sets_are_not_graded(self):
        rows = synthetic()[:50]
        _, _, p = cs.grade(rows)
        self.assertIsNone(p["N3"])
        self.assertIsNone(p["N4"])

    def test_gate_fails_below_90_percent_answered(self):
        rows = synthetic()
        for r in rows[:20]:
            r["status"] = "http_0"
        _, g, p = cs.grade(rows)
        self.assertFalse(g["G1_answered"])
        self.assertEqual(p, {"N1": None, "N2": None, "N3": None, "N4": None})

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            t = cs.write_table(d, rows)
            with open(os.path.join(d, "hosts.csv"), encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, cs.COLUMNS)
                back = cs.typed(list(reader))
        self.assertEqual(t["rows"], 122)
        self.assertEqual(cs.grade(back), cs.grade(rows))
        self.assertEqual(cs.described(back), cs.described(rows))
        self.assertEqual(cs.described(back)["statement_year"], {"2026": 80, "2024": 40})


class FrameTests(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(FRAME), "frame not in this folder")
    def test_committed_frame(self):
        rows, ok = cs.read_frame(FRAME)
        self.assertTrue(ok)
        hosts, dropped = cs.build_frame(rows)
        self.assertEqual((len(hosts), dropped), (cs.FRAME_HOSTS, 0))
        shared = {h["host"]: h["authorities"] for h in hosts if h["authorities"] > 1}
        self.assertEqual(shared, {"adur-worthing.gov.uk": 2, "bcpcouncil.gov.uk": 3,
                                  "southnorfolkandbroadland.gov.uk": 2,
                                  "lewes-eastbourne.gov.uk": 2, "northnorthants.gov.uk": 2})
        order = cs.crawl_order(hosts)
        self.assertEqual(sorted(h["host"] for h in order), sorted(h["host"] for h in hosts))

    @unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("N1 (at least 85% of the 379 hosts)", "N2 (at most 5 hosts)",
                       "N3 (at least 60% of read statements", "N4 (at least 25% of dated statements",
                       "before 2025-11-01", "`/accessibility-statement`", "`/accessibility`",
                       cs.FRAME_SHA256[:12], "G1 (at least 90% of hosts answered)"):
            self.assertIn(phrase, text)
        self.assertEqual((cs.N1_MIN_FOUND, cs.N2_MAX_PLACEHOLDER, cs.N3_MIN_22, cs.N4_MIN_STALE,
                          cs.G1_MIN_ANSWERED, cs.STALE_BEFORE),
                         (0.85, 5, 0.60, 0.25, 0.90, "2025-11-01"))
        self.assertIsNone(cs.GUARD_RE.search(text))

    @unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
    def test_nothing_read_when_checker_differs(self):
        get = FakeGet()
        with tempfile.TemporaryDirectory() as d:
            cs.main(["--out-dir", d], fetch=lambda url: b"not the release", get=get,
                    sleep=nosleep)
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertIn("status: not_run", text)
        self.assertEqual(get.calls, [])


if __name__ == "__main__":
    unittest.main()
