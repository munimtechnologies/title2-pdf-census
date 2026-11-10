# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for council_reread.py (no network: every page comes from a fake).

python -m unittest discover -p test_council_reread.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import datetime
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import council_reread as cr  # noqa: E402

cs, stc = cr.cs, cr.stc
TABLE = os.path.join(ROOT, *cr.TABLE_PATH.split("/"))
RESULT = os.path.join(ROOT, *cr.RESULT_PATH.split("/"))
PREREG = os.path.join(ROOT, *cr.PREREG_PATH.split("/"))
HAVE_ALL = all(os.path.exists(p) for p in (TABLE, RESULT, PREREG,
                                           os.path.join(ROOT, "council_stock.py"),
                                           os.path.join(ROOT, "statement_template_check.py")))

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
HUB = (b"<html><body><h1>Accessibility</h1><p>Use our accessibility tools to change colours.</p>"
       b"<a href=\"/accessibility/statement\">Accessibility statement</a></body></html>")
HTML = "text/html; charset=utf-8"
STATEMENT_SHA = cs.read_statement(stc.visible_text(STATEMENT, HTML))["text_sha256"]


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


def nov_row(host, url, date="2024-05-01", highest="2.1", sha=""):
    return {"host": host, "name": "X Council", "gss": "E0", "kind": "england_district",
            "authorities": "1", "status": "ok", "statement_url": url, "statement_date": date,
            "highest": highest, "text_sha256": sha}


def run(row, get):
    return cr.reread_one(row, get=get, delay=0, sleep=nosleep)


class ReadTests(unittest.TestCase):
    def test_saved_address_read_and_newer(self):
        url = "https://www.a.gov.uk/about/accessibility"
        get = FakeGet({url: (HTML, STATEMENT)})
        r = run(nov_row("a.gov.uk", url), get)
        self.assertEqual(get.calls, ["https://www.a.gov.uk/robots.txt", url])
        self.assertEqual((r["status"], r["found_by"], r["saved_status"]), ("ok", "saved", "200"))
        self.assertEqual((r["statement_date"], r["date_source"], r["highest"]),
                         ("2025-10-04", "reviewed", "2.2"))
        self.assertEqual((r["newer"], r["date_lost"], r["url_changed"], r["text_changed"]),
                         (True, False, False, True))
        self.assertEqual(cr.nov_group(r), "stale")

    def test_unchanged_statement(self):
        url = "https://www.a2.gov.uk/accessibility-statement"
        get = FakeGet({url: (HTML, STATEMENT)})
        r = run(nov_row("a2.gov.uk", url, date="2025-10-04", highest="2.2", sha=STATEMENT_SHA), get)
        self.assertEqual((r["status"], r["newer"], r["text_changed"]), ("ok", False, False))
        self.assertEqual(cr.nov_group(r), "stale")

    def test_moved_statement_is_found_again(self):
        get = FakeGet({"https://www.b.gov.uk/": (HTML, HOME_LINK),
                       "https://www.b.gov.uk/about/accessibility": (HTML, STATEMENT)})
        r = run(nov_row("b.gov.uk", "https://www.b.gov.uk/old-statement"), get)
        self.assertEqual((r["saved_status"], r["fallback_status"]), ("404", "ok"))
        self.assertEqual((r["status"], r["found_by"]), ("ok", "rediscovered:link"))
        self.assertEqual(r["statement_url"], "https://www.b.gov.uk/about/accessibility")
        self.assertTrue(r["url_changed"])
        self.assertTrue(r["newer"])

    def test_saved_address_now_a_hub(self):
        get = FakeGet({"https://www.h.gov.uk/": (HTML, HOME_NOLINK),
                       "https://www.h.gov.uk/accessibility": (HTML, HUB),
                       "https://www.h.gov.uk/accessibility/statement": (HTML, STATEMENT)})
        r = run(nov_row("h.gov.uk", "https://www.h.gov.uk/accessibility"), get)
        self.assertEqual(r["saved_status"], "not_statement")
        self.assertEqual((r["status"], r["found_by"]), ("ok", "rediscovered:hub"))

    def test_no_answer(self):
        get = FakeGet(dead=("https://www.n.gov.uk", "https://n.gov.uk"))
        r = run(nov_row("n.gov.uk", "https://www.n.gov.uk/acc"), get)
        self.assertEqual((r["status"], r["saved_status"], r["fallback_status"]),
                         ("not_read", "0", "http_0"))
        self.assertFalse(r["newer"])

    def test_robots_honoured(self):
        url = "https://www.c.gov.uk/accessibility"
        get = FakeGet({"https://www.c.gov.uk/robots.txt": ("text/plain",
                                                           b"User-agent: *\nDisallow: /\n"),
                       url: (HTML, STATEMENT), "https://www.c.gov.uk/": (HTML, HOME_LINK)})
        r = run(nov_row("c.gov.uk", url), get)
        self.assertEqual((r["status"], r["saved_status"], r["fallback_status"]),
                         ("not_read", "robots", "robots"))
        self.assertTrue(r["robots_blocked"])
        self.assertNotIn(url, get.calls)
        self.assertNotIn("https://www.c.gov.uk/", get.calls)

    def test_retry_once_after_503(self):
        url = "https://www.g.gov.uk/accessibility-statement"

        class Flaky(FakeGet):
            def __call__(self, u, timeout=20):
                if u == url and u not in self.calls:
                    self.calls.append(u)
                    return 503, u, "", b""
                return FakeGet.__call__(self, u, timeout)
        get = Flaky({url: (HTML, STATEMENT)})
        r = run(nov_row("g.gov.uk", url), get)
        self.assertEqual((r["status"], r["found_by"], r["retried"]), ("ok", "saved", True))

    def test_groups(self):
        self.assertEqual(cr.nov_group({"nov_statement_date": "2025-10-31"}), "stale")
        self.assertEqual(cr.nov_group({"nov_statement_date": "2025-11-01"}), "due")
        self.assertEqual(cr.nov_group({"nov_statement_date": "2025-12-31"}), "due")
        self.assertEqual(cr.nov_group({"nov_statement_date": "2026-01-01"}), "fresh")
        self.assertEqual(cr.nov_group({"nov_statement_date": ""}), "undated")


def synthetic():
    rows = []
    for i in range(284):
        if i < 105:
            d = "2024-01-01"
        elif i < 120:
            d = "2025-12-01"
        elif i < 271:
            d = "2026-03-01"
        else:
            d = ""
        r = cr.start({"host": "h%03d.gov.uk" % i, "name": "C%d" % i,
                      "kind": "england_district" if i % 2 else "london_borough",
                      "authorities": "1", "statement_date": d, "highest": "2.1" if i < 86 else "2.2",
                      "text_sha256": "%064x" % i, "statement_url": "https://h%03d.gov.uk/a" % i})
        if i % 10 == 9:
            r["status"] = "not_read"
        else:
            now = "2026-12-15" if i < 10 else d
            r.update(status="ok", found_by="saved", statement_url=r["nov_statement_url"],
                     text_sha256=r["nov_text_sha256"], highest="2.2" if i < 5 else r["nov_highest"],
                     statement_date=now, review_date=now, date_source="reviewed" if now else "",
                     newer=bool(d and now > d))
        rows.append(r)
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        m, g, p = cr.grade(synthetic())
        self.assertEqual(g, {"F1_panel": True, "G1_reread": True})
        self.assertEqual(p, {"R1": True, "R2": True, "R3": True})
        self.assertEqual((m["F1_panel"], m["F1_stale_panel"]), (284, 105))
        self.assertEqual(m["G1_reread"], {"k": 256, "n": 284, "pct": 90.14})
        self.assertEqual(m["R1_newer_of_stale_reread"], {"k": 9, "n": 95, "pct": 9.47})
        self.assertEqual(m["R2_before_2026_of_dated"], {"k": 99, "n": 244, "pct": 40.57})
        self.assertEqual(m["R3_to_wcag22_of_21"], {"k": 5, "n": 78, "pct": 6.41})

    def test_many_newer_fails_r1(self):
        rows = synthetic()
        for r in rows[:60]:
            if r["status"] == "ok":
                r.update(statement_date="2026-12-15", newer=True)
        _, _, p = cr.grade(rows)
        self.assertFalse(p["R1"])

    def test_gate_fails_below_80_percent(self):
        rows = synthetic()
        for r in rows[:100]:
            r["status"] = "not_read"
        _, g, p = cr.grade(rows)
        self.assertFalse(g["G1_reread"])
        self.assertEqual(p, {"R1": None, "R2": None, "R3": None})

    def test_described(self):
        d = cr.described(synthetic())
        self.assertEqual(d["status"], {"ok": 256, "not_read": 28})
        self.assertEqual(d["by_group"]["stale"],
                         {"panel": 105, "reread": 95, "newer": 9, "dated_now": 95, "text_changed": 0})
        self.assertEqual(d["by_group"]["due"]["reread"], 13)
        self.assertEqual(d["by_group"]["fresh"]["reread"], 136)
        self.assertEqual(d["by_group"]["undated"],
                         {"panel": 13, "reread": 12, "newer": 0, "dated_now": 0, "text_changed": 0})
        self.assertEqual(d["newer_month"], {"2026-12": 9})
        self.assertEqual((d["date_lost"], d["date_earlier"], d["url_changed"]), (0, 0, 0))

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as tmp:
            t = cr.write_table(tmp, rows)
            with open(os.path.join(tmp, "reread.csv"), encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, cr.COLUMNS)
                back = cr.typed(list(reader))
        self.assertEqual(t["rows"], 284)
        self.assertEqual(cr.grade(back), cr.grade(rows))
        self.assertEqual(cr.described(back), cr.described(rows))


class RunTests(unittest.TestCase):
    def test_nothing_read_before_the_wave(self):
        get = FakeGet()
        with tempfile.TemporaryDirectory() as tmp:
            cr.main(["--out-dir", tmp], get=get, sleep=nosleep, today=datetime.date(2026, 11, 10))
            with open(os.path.join(tmp, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
        self.assertEqual(result["status"], "not_run")
        self.assertFalse(result["gates"]["W1_window"])
        self.assertEqual(get.calls, [])

    def test_nothing_read_after_the_wave(self):
        get = FakeGet()
        with tempfile.TemporaryDirectory() as tmp:
            cr.main(["--out-dir", tmp], get=get, sleep=nosleep, today=datetime.date(2027, 2, 1))
            with open(os.path.join(tmp, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
        self.assertEqual(result["status"], "not_run")
        self.assertEqual(get.calls, [])

    @unittest.skipUnless(HAVE_ALL, "committed files not in this folder")
    def test_full_offline_run_in_the_wave(self):
        get = FakeGet()  # every address answers 404
        with tempfile.TemporaryDirectory() as tmp:
            cr.main(["--out-dir", tmp], get=get, sleep=nosleep, today=datetime.date(2027, 1, 11))
            with open(os.path.join(tmp, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(tmp, "result.txt"), encoding="utf-8") as f:
                self.assertEqual(f.read(), cr.result_text(result) + "\n")
        g = result["gates"]
        self.assertTrue(g["P0_prereg"] and g["P0_pins"] and g["W1_window"] and g["F1_panel"])
        self.assertFalse(g["G1_reread"])
        self.assertEqual(result["status"], "ungraded")
        self.assertEqual(result["panel"], {"rows": 379, "found": 284, "table_ok": True,
                                           "stale": 105})
        self.assertEqual(result["table"]["rows"], 284)
        self.assertEqual(result["described"]["status"], {"not_read": 284})
        self.assertEqual(result["predictions"], {"R1": None, "R2": None, "R3": None})


class CommittedTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_ALL, "committed files not in this folder")
    def test_panel(self):
        rows, ok = cr.read_table(TABLE)
        self.assertTrue(ok)
        pnl = [cr.start(r) for r in cr.panel(rows)]
        self.assertEqual(len(pnl), cr.PANEL_FOUND)
        groups = {g: sum(1 for r in pnl if cr.nov_group(r) == g) for g in cr.GROUPS}
        self.assertEqual(groups, {"stale": 105, "due": 15, "fresh": 151, "undated": 13})
        self.assertEqual(sum(1 for r in pnl if r["nov_highest"] == "2.1"), 86)
        self.assertTrue(all(r["nov_statement_url"] for r in pnl))
        self.assertEqual(len(set(r["host"] for r in pnl)), cr.PANEL_FOUND)

    @unittest.skipUnless(HAVE_ALL, "committed files not in this folder")
    def test_pinned_scripts_are_the_ones_november_ran(self):
        self.assertTrue(cr.pins_match(ROOT))

    @unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("G1 (at least 80% of the 284 statements read again)",
                       "R1 (at most 20% of the re-read statements dated before 2025-11-01",
                       "R2 (at least 35% of the dated re-read statements",
                       "R3 (at most 15% of the re-read statements that named WCAG 2.1",
                       "before 2026-01-01", "2027-01-11", "2027-01-31", cr.TABLE_SHA256[:12],
                       "`council-reread-2027-01`"):
            self.assertIn(phrase, text)
        self.assertEqual((cr.G1_MIN_REREAD, cr.R1_MAX_NEWER, cr.R2_MIN_OLD, cr.R3_MAX_TO_22),
                         (0.80, 0.20, 0.35, 0.15))
        self.assertEqual((cr.R1_MIN_PAGES, cr.R2_MIN_PAGES, cr.R3_MIN_PAGES), (60, 150, 50))
        self.assertEqual((cr.WAVE_START.isoformat(), cr.WAVE_END.isoformat(), cr.NEW_STALE_BEFORE,
                          cs.STALE_BEFORE), ("2027-01-11", "2027-01-31", "2026-01-01", "2025-11-01"))
        self.assertIsNone(cs.GUARD_RE.search(text))


if __name__ == "__main__":
    unittest.main()
