"""Tests for statement_reread.py (no network: the repository and every page are faked).

Also checks, from the census table committed in results/a11y-pages, that the panel gate's
pre-registered counts (1,657 rows, 808 pages, 280 stock, 283 only-2.0) are the table's own.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a11y_pages as ap  # noqa: E402
import statement_reread as rr  # noqa: E402

PANEL_CSV = os.path.join(HERE, "results", "a11y-pages", "a11y-pages.csv")
PANEL_SHA256 = "56b82a41258e6144c9467f3c4a64d510ad353ecdb8d59909fe0c73bca8cffce6"

STOCK_PAGE = b"""<html><body><h1>Accessibility</h1>
<p>The County is committed to making its website accessible to everyone who visits it.
We work to comply with Section 508 as well as WCAG 2.0 A and AA referring to website
accessibility standards. If you have trouble with any page, please let us know so that we
can help.</p></body></html>"""

GOOD_PAGE = b"""<html><body><h1>Accessibility statement</h1>
<p>The City of Beta aims to meet WCAG 2.1 Level AA, the standard adopted by the Justice
Department's rule under Title II of the Americans with Disabilities Act, by April 26, 2027.
Call 555-123-4567 or write to us to report a barrier on any page of this website.</p>
</body></html>"""


def visible(body):
    return ap.visible_text(ap.parse(body))


def panel_bytes():
    rows = [
        {"qid": "Q1", "name": "Alpha", "kind": "county", "state": "X", "population": "60000",
         "website": "https://alpha.gov/", "home": "ok", "page_status": "ok",
         "page_url": "https://alpha.gov/accessibility",
         "text_sha256": ap.sha256(visible(STOCK_PAGE).encode("utf-8")),
         "versions": "2.0", "highest": "2.0", "title2": "False", "old_date": "True",
         "new_date": "False",
         "version_snippet": "us. We work to comply with Section 508 as well as WCAG 2.0 A and AA "
                            "referring to website"},
        {"qid": "Q2", "name": "Beta", "kind": "city", "state": "Y", "population": "300000",
         "website": "https://beta.gov/", "home": "ok", "page_status": "ok",
         "page_url": "https://beta.gov/a11y", "text_sha256": "x", "versions": "2.1",
         "highest": "2.1", "title2": "False", "old_date": "False", "new_date": "False",
         "version_snippet": "We follow WCAG 2.1 AA"},
        {"qid": "Q3", "name": "Gamma", "kind": "city", "state": "Z", "population": "51000",
         "website": "https://gamma.gov/", "home": "robots", "page_status": ""}]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=ap.COLUMNS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in ap.COLUMNS})
    return buf.getvalue().encode("utf-8")


def fake_fetch(files):
    calls = []

    def fetch(url):
        calls.append(url)
        return files[url.split("?")[0]]  # KeyError stands for a 404
    fetch.calls = calls
    return fetch


def fake_get(pages):
    calls = []

    def get(url):
        calls.append(url)
        return pages.get(url, (404, url, "", b""))
    get.calls = calls
    return get


def repo_files(**changed):
    files = {rr.REPO_RAW + rr.PREREG_PATH: b"# PREREG\nP1 P2 P3 P4\n", rr.PANEL_URL: panel_bytes()}
    for name in rr.PINNED:
        files[rr.REPO_RAW + name] = changed.get(name.replace(".", "_"), rr.local_bytes(name))
    return files


PAGES = {"https://alpha.gov/accessibility": (200, "https://alpha.gov/accessibility",
                                             "text/html", STOCK_PAGE),
         "https://beta.gov/a11y": (200, "https://beta.gov/a11y", "text/html", GOOD_PAGE)}


def no_sleep(_s):
    pass


class SmallPanel(unittest.TestCase):
    """The gates' sizes shrunk to the three-row fake panel."""
    PATCH = {"PANEL_ROWS": 3, "PANEL_PAGES": 2, "PANEL_STOCK": 1, "PANEL_ONLY20": 1,
             "MIN_READABLE": 2, "MIN_GROUP": 1}

    def setUp(self):
        self.saved = {k: getattr(rr, k) for k in self.PATCH}
        for k, v in self.PATCH.items():
            setattr(rr, k, v)
        self.tmp = tempfile.TemporaryDirectory()
        self.out = self.tmp.name

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(rr, k, v)
        self.tmp.cleanup()

    def run_main(self, wave, today, fetch=None, get=None):
        self.fetch = fetch or fake_fetch(repo_files())
        self.get = get or fake_get(PAGES)
        code = rr.main(["--wave", wave, "--out-dir", self.out], fetch=self.fetch, get=self.get,
                       sleep=no_sleep, today=today)
        with open(os.path.join(self.out, "result.json"), encoding="utf-8") as f:
            return code, json.load(f)

    def test_wave_j_graded(self):
        code, r = self.run_main("J", "2027-01-20")
        self.assertEqual((code, r["status"]), (0, "graded"))
        self.assertEqual(r["gates"], {"W_window": True, "P0_prereg_public": True,
                                      "G1_panel": True, "G2_readable": True})
        self.assertEqual(r["predictions"], {"P1": True, "P2": True, "P3": True})
        self.assertEqual(r["measures"]["P1_stock_kept"][:3], [1, 1, 1.0])
        self.assertEqual(r["measures"]["P3_only20_of_versioned_now"][:3], [1, 2, 0.5])
        d = r["described"]
        self.assertEqual(d["moves_all"], {"2.0->2.0": 1, "2.1->2.1": 1})
        self.assertEqual((d["same_text"], d["moved_to_other_url"]), (1, 0))
        self.assertEqual((d["old_date_2026_pages"], d["old_date_2026_now_old_only"]), (1, 0))
        self.assertEqual(d["date_2027_now"], 1)
        with open(os.path.join(self.out, "statement-reread-J.csv"), encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([x["qid"] for x in rows], ["Q1", "Q2"])
        self.assertEqual((rows[0]["stock"], rows[0]["same_text"]), ("True", "True"))
        self.assertEqual((rows[1]["title2"], rows[1]["title2_2026"]), ("True", "False"))
        self.assertNotIn("https://gamma.gov/", self.get.calls)

    def test_wave_m_grades_p4(self):
        code, r = self.run_main("M", "2027-05-10")
        self.assertEqual(code, 0)
        self.assertEqual(r["predictions"], {"P1": True, "P2": True, "P3": True, "P4": True})
        self.assertEqual(r["measures"]["P4_title2_2026"][:2], [0, 2])
        self.assertEqual(r["measures"]["P4_title2_now"][:2], [1, 2])

    def test_outside_window_fetches_nothing(self):
        for wave, today in (("J", "2026-11-02"), ("J", "2027-03-01"), ("M", "2027-04-30")):
            code, r = self.run_main(wave, today)
            self.assertEqual(code, 2)
            self.assertFalse(r["gates"]["W_window"])
            self.assertTrue(r["status"].startswith("outside wave"))
            self.assertEqual((self.fetch.calls, self.get.calls), ([], []))

    def test_changed_pinned_file_stops_it(self):
        fetch = fake_fetch(repo_files(statement_check_py=b"# a different file\n"))
        code, r = self.run_main("J", "2027-02-01", fetch=fetch)
        self.assertEqual(code, 2)
        self.assertFalse(r["gates"]["P0_prereg_public"])
        self.assertEqual(r["polls"], rr.TRIES)
        self.assertEqual(self.get.calls, [])
        self.assertNotIn(rr.PANEL_URL, fetch.calls)

    def test_unreadable_pages_fail_the_gate(self):
        code, r = self.run_main("J", "2027-01-11", get=fake_get({}))
        self.assertEqual((code, r["status"]), (2, "readable gate failed; not graded"))
        self.assertEqual(r["readable"], 0)
        self.assertEqual(r["described"]["status"], {"http_404": 2})


class FullSizeGates(unittest.TestCase):
    def test_panel_gate_uses_the_real_counts(self):
        with tempfile.TemporaryDirectory() as d:
            code = rr.main(["--wave", "J", "--out-dir", d], fetch=fake_fetch(repo_files()),
                           get=fake_get(PAGES), sleep=no_sleep, today="2027-01-11")
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                r = json.load(f)
        self.assertEqual((code, r["status"]), (2, "panel gate failed; nothing re-read"))
        self.assertEqual(r["panel_counts"], [3, 2, 1, 1])

    def test_small_groups_are_not_graded(self):
        rows = [{"status": "ok", "stock_2026": True, "highest_2026": "2.0", "highest": "2.0",
                 "stock": True, "title2_2026": False, "title2": False}] * 5
        _, preds = rr.grade(rows, "M")
        self.assertEqual(preds, {"P1": None, "P2": None, "P3": None, "P4": None})

    def test_thresholds(self):
        def row(stock_then, stock_now, high_then, high_now, t2_then=False, t2_now=False):
            return {"status": "ok", "stock_2026": stock_then, "stock": stock_now,
                    "highest_2026": high_then, "highest": high_now,
                    "title2_2026": t2_then, "title2": t2_now}
        # 600 readable pages: 220 stock 2.0 pages (187 kept = 85%), 60 other 2.0 pages
        # (all moved to 2.1), 120 2.1 pages, 200 with no version; 18 newly name Title II.
        rows = ([row(True, True, "2.0", "2.0")] * 187 + [row(True, False, "2.0", "2.1")] * 33
                + [row(False, False, "2.0", "2.1")] * 60 + [row(False, False, "2.1", "2.1")] * 120
                + [row(False, False, "", "", False, True)] * 18 + [row(False, False, "", "")] * 182)
        m, p = rr.grade(rows, "J")
        self.assertEqual(m["P1_stock_kept"][:2], [187, 220])
        self.assertEqual(m["P2_only20_kept"][:2], [187, 280])
        self.assertEqual(m["P3_only20_of_versioned_now"][:2], [187, 400])
        self.assertEqual(p, {"P1": True, "P2": False, "P3": True})
        m, p = rr.grade(rows, "M")
        self.assertEqual(p, {"P1": True, "P2": True, "P3": True, "P4": True})
        self.assertEqual((m["P4_title2_2026"][0], m["P4_title2_now"][0]), (0, 18))


class PanelFile(unittest.TestCase):
    def test_committed_table_matches_the_gate(self):
        with open(PANEL_CSV, "rb") as f:
            data = f.read()
        self.assertEqual(ap.sha256(data), PANEL_SHA256)
        rows, pages = rr.load_panel(data)
        stock = sum(1 for r in pages if r["stock_2026"])
        only20 = sum(1 for r in pages if r["highest"] == "2.0")
        self.assertEqual((len(rows), len(pages), stock, only20),
                         (rr.PANEL_ROWS, rr.PANEL_PAGES, rr.PANEL_STOCK, rr.PANEL_ONLY20))
        self.assertTrue(all(r["page_url"].startswith(("http://", "https://")) for r in pages))


if __name__ == "__main__":
    unittest.main()
