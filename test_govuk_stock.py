# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for govuk_stock.py (no network: GOV.UK's API and every website are fakes).

python -m unittest discover -p test_govuk_stock.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import govuk_stock as gs  # noqa: E402

cs, gf = gs.cs, gs.gf
PREREG = os.path.join(ROOT, *gs.PREREG_PATH.split("/"))
CHECKER = os.path.join(ROOT, "statement_template_check.py")

STATEMENT = (b"<html><head><title>Accessibility statement | An Agency</title></head><body>"
             b"<h1>Accessibility statement for An Agency</h1><p>This accessibility statement "
             b"applies to the agency website. This website is run by An Agency. We want as many "
             b"people as possible to be able to use this website.</p><h2>Compliance status</h2>"
             b"<p>This website is partially compliant with the Web Content Accessibility "
             b"Guidelines version 2.2 AA standard, due to the non-compliances listed below.</p>"
             b"<h2>Enforcement procedure</h2><p>The Equality and Human Rights Commission (EHRC) is "
             b"responsible for enforcing the accessibility regulations.</p><p>This statement was "
             b"prepared on 23 September 2020. It was last reviewed on 4 October 2025.</p>"
             b"</body></html>")
HTML = "text/html; charset=utf-8"
API = "https://www.gov.uk/api/"
ORG = "https://www.gov.uk/government/organisations/"


class FakeGet:
    """Website pages by exact address; everything else is a 404."""

    def __init__(self, pages=None):
        self.pages, self.calls = pages or {}, []

    def __call__(self, url, timeout=20):
        self.calls.append(url)
        if url in self.pages:
            return 200, url, HTML, self.pages[url]
        return 404, url, "", b""


class FakeApi:
    """GOV.UK's API by exact address; anything else raises (as a 404 would)."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def __call__(self, url):
        self.calls.append(url)
        if url in self.answers:
            return self.answers[url]
        raise OSError("404 " + url)


def nosleep(_):
    return None


def api_answers(n_orgs=1010, n_own=106):
    """n_orgs organisations in pages of 20; the first n_own have an own-site status. Organisation
    i < 104 names https://www.hNNN.example.org.uk/; 104 and 105 name host h103 (3 on one host)."""
    res = []
    for i in range(n_orgs):
        if i < min(n_own, 106):
            status = "exempt" if i < 100 else "joining" if i < 105 else "transitioning"
        else:
            status = "live" if i % 2 else "closed"
        slug = "org-%04d" % i
        res.append({"id": API + "organisations/" + slug, "title": "Org %d" % i,
                    "format": "Executive agency", "web_url": ORG + slug,
                    "details": {"slug": slug, "abbreviation": None, "govuk_status": status},
                    "parent_organisations": []})
    answers = {}
    pages = [res[k:k + 20] for k in range(0, len(res), 20)]
    for p, rows in enumerate(pages, 1):
        page = {"total": n_orgs, "results": rows}
        if p < len(pages):
            page["next_page_url"] = API + "organisations?page=%d" % (p + 1)
        answers[API + "organisations?page=%d" % p] = page
    for i in range(min(n_own, 106)):
        url = ("https://www.h%03d.example.org.uk/" % i if i < 104
               else "https://www.h103.example.org.uk/about")
        answers[API + "content/government/organisations/org-%04d" % i] = {
            "details": {"organisation_type": "executive_agency" if i % 3 else "advisory_ndpb",
                        "organisation_govuk_status": {"status": "x", "url": url}}}
    return answers


def site_pages(n_found=84):
    return {"https://www.h%03d.example.org.uk/accessibility-statement" % j: STATEMENT
            for j in range(n_found)}


def read_checker(_url):
    with open(CHECKER, "rb") as f:
        return f.read()


def synthetic():
    rows = []
    for i in range(122):
        r = cs.blank({"host": "h%03d.example.gov.uk" % i, "slug": "o%d" % i, "title": "O%d" % i,
                      "organisation_type": "executive_agency" if i % 2 else "advisory_ndpb",
                      "govuk_status": "exempt", "organisations": 1 + (i % 3 == 0)})
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
        m, g, p = gs.grade(synthetic())
        self.assertEqual(g, {"F1_frame": True, "G1_answered": True})
        self.assertEqual(p, {"O1": True, "O2": False, "O3": False, "O4": True})
        self.assertEqual(m["O1_found"], {"k": 120, "n": 122, "pct": 98.36})
        self.assertEqual(m["O3_wcag22_of_found"], {"k": 80, "n": 120, "pct": 66.67})
        self.assertEqual(m["O4_stale_of_dated"], {"k": 40, "n": 120, "pct": 33.33})
        self.assertEqual(m["O2_placeholder_hosts"], 6)

    def test_small_sets_are_not_graded(self):
        _, _, p = gs.grade(synthetic()[:50])
        self.assertIsNone(p["O3"])
        self.assertIsNone(p["O4"])

    def test_gate_fails_below_90_percent_answered(self):
        rows = synthetic()
        for r in rows[:20]:
            r["status"] = "http_0"
        _, g, p = gs.grade(rows)
        self.assertFalse(g["G1_answered"])
        self.assertEqual(p, {"O1": None, "O2": None, "O3": None, "O4": None})

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            t = gs.write_table(d, rows)
            with open(os.path.join(d, "hosts.csv"), encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, gs.COLUMNS)
                back = gs.typed(list(reader))
        self.assertEqual(t["rows"], 122)
        self.assertEqual(gs.grade(back), gs.grade(rows))
        self.assertEqual(gs.described(back), gs.described(rows))
        self.assertEqual(gs.described(back)["statement_year"], {"2026": 80, "2024": 40})
        self.assertEqual(gs.described(back)["found_organisations"], 160)


class FrameTests(unittest.TestCase):
    def row(self, slug, host, status="exempt", own="True", fetch="ok"):
        return {"slug": slug, "title": slug.upper(), "organisation_type": "executive_agency",
                "govuk_status": status, "host": host, "own_host": own, "fetch": fetch}

    def test_build_frame(self):
        word = "S" + "aybr" + "ook"
        rows = [self.row("b-org", "shared.org.uk"), self.row("a-org", "Shared.org.uk "),
                self.row("c-org", "c.gov.uk", status="joining"),
                self.row("d-org", "d.gov.uk", status="live"),
                self.row("e-org", "gov.uk", own="False"),
                self.row("f-org", "f.gov.uk", fetch="failed:OSError"),
                self.row("g-org", "", own="True"),
                self.row("h-org", "h.gov.uk", status="transitioning"),
                self.row("x-" + word.lower(), "x.gov.uk")]
        hosts, dropped = gs.build_frame(rows)
        self.assertEqual(dropped, 1)
        self.assertEqual([(h["host"], h["slug"], h["organisations"]) for h in hosts],
                         [("shared.org.uk", "a-org", 2), ("c.gov.uk", "c-org", 1),
                          ("h.gov.uk", "h-org", 1)])

    def test_frame_gate(self):
        hosts = [{"host": "h%d" % i} for i in range(100)]
        info = {"organisations": 1000, "fetch_failed": ["a"] * 10, "dropped": 1}
        self.assertTrue(gs.frame_gate(info, hosts, 1))
        self.assertFalse(gs.frame_gate(info, hosts, 2))
        self.assertFalse(gs.frame_gate(info, hosts[:99], 0))
        self.assertFalse(gs.frame_gate(dict(info, organisations=999), hosts, 0))
        self.assertFalse(gs.frame_gate(dict(info, fetch_failed=["a"] * 11), hosts, 0))

    def test_crawl_order_is_a_permutation(self):
        hosts = [{"host": "h%d.gov.uk" % i} for i in range(30)]
        order = gs.crawl_order(hosts)
        self.assertEqual(sorted(h["host"] for h in order), sorted(h["host"] for h in hosts))
        self.assertEqual(order, gs.crawl_order(list(reversed(hosts))))

    def test_pinned_versions(self):
        self.assertEqual((cs.__version__, gf.__version__, cs.stc.__version__),
                         ("0.1.0", "0.1.0", "0.3.0"))
        self.assertEqual(cs.STALE_BEFORE, "2025-11-01")
        self.assertEqual(gs.COLUMNS[:7], gs.ID_COLUMNS + ["status"])


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class RunTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("O1 (at least 75% of own hosts)", "O2 (at most 3 hosts)",
                       "O3 (at least 70% of read statements", "O4 (at least 25% of dated statements",
                       "before 2025-11-01", "G1 (at least 90% of hosts answered)",
                       "at least 1,000 organisations", "at most 10 content items",
                       "at most 2 rows", "at least 100 distinct hosts",
                       "at least 60 read statements", "at least 60 dated statements",
                       "`/accessibility-statement`", "`/accessibility`", "`govuk-stock-2026-11`",
                       "exempt, joining or transitioning"):
            self.assertIn(phrase, text)
        self.assertEqual((gs.O1_MIN_FOUND, gs.O2_MAX_PLACEHOLDER, gs.O3_MIN_22, gs.O3_MIN_PAGES,
                          gs.O4_MIN_STALE, gs.O4_MIN_PAGES, gs.G1_MIN_ANSWERED),
                         (0.75, 3, 0.70, 60, 0.25, 60, 0.90))
        self.assertEqual((gs.F1_MIN_ORGANISATIONS, gs.F1_MAX_FETCH_FAILED, gs.F1_MAX_DROPPED,
                          gs.F1_MIN_HOSTS, gs.CRAWL_SEED),
                         (1000, 10, 2, 100, "govuk-stock-2026-11"))
        self.assertEqual(gf.OWN_SITE_STATUSES, ("exempt", "joining", "transitioning"))
        self.assertIsNone(cs.GUARD_RE.search(text))

    def test_nothing_requested_when_checker_differs(self):
        get, api = FakeGet(), FakeApi(api_answers())
        with tempfile.TemporaryDirectory() as d:
            gs.main(["--out-dir", d], fetch=lambda url: b"not the release", get=get,
                    sleep=nosleep, fetch_json=api)
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertIn("govuk_stock 0.1.0", text)
        self.assertIn("status: not_run", text)
        self.assertEqual((get.calls, api.calls), ([], []))

    def test_no_website_read_when_frame_too_small(self):
        get, api = FakeGet(site_pages()), FakeApi(api_answers(n_own=60))
        with tempfile.TemporaryDirectory() as d:
            gs.main(["--out-dir", d], fetch=read_checker, get=get, sleep=nosleep, fetch_json=api)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            self.assertTrue(os.path.exists(os.path.join(d, "govuk-frame.csv")))
        self.assertEqual(result["status"], "not_run")
        self.assertFalse(result["gates"]["F1_frame"])
        self.assertEqual(result["frame"]["hosts"], 60)
        self.assertEqual(get.calls, [])
        self.assertTrue(all(u.startswith(API) for u in api.calls))

    def test_full_run_on_fakes(self):
        get, api = FakeGet(site_pages()), FakeApi(api_answers())
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(gs.main(["--out-dir", d], fetch=read_checker, get=get,
                                     sleep=nosleep, fetch_json=api), 0)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(d, "govuk-frame.csv"), "rb") as f:
                frame = f.read()
            with open(os.path.join(d, "hosts.csv"), encoding="utf-8", newline="") as f:
                table = {r["host"]: r for r in csv.DictReader(f)}
        self.assertEqual(result["status"], "graded")
        self.assertEqual(result["frame"]["organisations"], 1010)
        self.assertEqual((result["frame"]["rows"], result["frame"]["hosts"],
                          result["frame"]["dropped"], result["frame"]["fetch_failed"]),
                         (106, 104, 0, 0))
        self.assertEqual(result["frame"]["sha256"], gs.sha256(frame))
        self.assertEqual(result["predictions"], {"O1": True, "O2": True, "O3": True, "O4": True})
        self.assertEqual(result["measures"]["O1_found"], {"k": 84, "n": 104, "pct": 80.77})
        self.assertEqual(result["measures"]["O4_stale_of_dated"], {"k": 84, "n": 84, "pct": 100.0})
        self.assertEqual(result["described"]["found_by"], {"probe1": 84})
        self.assertEqual(result["described"]["found_organisations"], 84)
        self.assertEqual(len(table), 104)
        self.assertEqual((table["h103.example.org.uk"]["organisations"],
                          table["h103.example.org.uk"]["status"]), ("3", "not_found"))
        self.assertEqual(table["h000.example.org.uk"]["statement_url"],
                         "https://www.h000.example.org.uk/accessibility-statement")
        # GOV.UK's API for the frame; the websites only on the frame's own hosts
        self.assertTrue(all(u.startswith(API) for u in api.calls))
        self.assertEqual(sum(1 for u in api.calls if "/api/content/" in u), 106)
        self.assertTrue(all(u.startswith("https://www.h") and ".example.org.uk/" in u
                            for u in get.calls))


if __name__ == "__main__":
    unittest.main()
