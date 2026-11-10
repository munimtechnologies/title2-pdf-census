# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for council_agree.py (no network: every page comes from a fake).

python -m unittest discover -p test_council_agree.py
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
import council_agree as ca  # noqa: E402

cs, stc = ca.cs, ca.stc
TABLE = os.path.join(ROOT, *ca.TABLE_PATH.split("/"))
RESULT = os.path.join(ROOT, *ca.RESULT_PATH.split("/"))
PREREG = os.path.join(ROOT, *ca.PREREG_PATH.split("/"))
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
HUB = (b"<html><body><h1>Accessibility</h1><p>Use our accessibility tools to change colours.</p>"
       b"<a href=\"/accessibility/statement\">Accessibility statement</a></body></html>")
HTML = "text/html; charset=utf-8"
HEADER = "name,host,statementUrl,percent,verdict,mandatoryPassed,mandatoryTotal,via\n"
GUARDED = "S" + "aybr" + "ook Council"


class FakeGet:
    """Pages by exact address; everything else is a 404 (so robots.txt allows everything)."""

    def __init__(self, pages=None):
        self.pages, self.calls = pages or {}, []

    def __call__(self, url, timeout=20):
        self.calls.append(url)
        if url in self.pages:
            p = self.pages[url]
            if len(p) == 2:
                return 200, url, p[0], p[1]
            return p
        return 404, url, "", b""


def nosleep(_):
    return None


def a_row(host, url, passed=8, name="X Council"):
    return {"name": name, "host": host, "statementUrl": url, "verdict": "v", "via": "footer-link",
            "passed": passed, "total": 8}


def b_row(host, url, status="ok", found_by="link", date="2025-10-02", highest="2.2"):
    return {"host": host, "status": status, "found_by": found_by, "statement_url": url,
            "highest": highest, "statement_date": date}


def joined(a_url, b_url, passed=1):
    return ca.match([a_row("h.gov.uk", a_url, passed)], [b_row("h.gov.uk", b_url, found_by="hub")])[0]


def csv_bytes(lines):
    return (HEADER + "".join(l + "\n" for l in lines)).encode("utf-8")


class UnitTests(unittest.TestCase):
    def test_norm_url(self):
        self.assertEqual(ca.norm_url("https://WWW.York.gov.uk/AccessibilityStatement/?x=1#y"),
                         "york.gov.uk/accessibilitystatement")
        self.assertEqual(ca.norm_url("http://derby.gov.uk/site-info/accessibility/"),
                         "derby.gov.uk/site-info/accessibility")
        self.assertEqual(ca.norm_url("https://a.gov.uk/Accessibility%20Statement"),
                         "a.gov.uk/accessibility statement")
        self.assertEqual(ca.norm_url("https://a.gov.uk"), "a.gov.uk")
        self.assertEqual(ca.norm_url("[withheld]"), "")
        self.assertEqual(ca.norm_url(""), "")

    def test_group(self):
        self.assertEqual([ca.group(p, 8) for p in (0, 3, 4, 7, 8)],
                         ["low", "low", "partial", "partial", "full"])

    def test_parse_a(self):
        lines = ["C%d,c%d.gov.uk,https://www.c%d.gov.uk/accessibility,100,compliant,8,8,footer-link"
                 % (i, i, i) for i in range(149)]
        lines.append("%s,x.gov.uk,https://x.gov.uk/a,13,not-compliant,1,8,common-path" % GUARDED)
        rows, ok, dropped = ca.parse_a(b"\xef\xbb\xbf" + csv_bytes(lines))
        self.assertTrue(ok)
        self.assertEqual((len(rows), dropped), (149, 1))
        self.assertEqual((rows[0]["passed"], rows[0]["total"], rows[0]["host"]), (8, 8, "c0.gov.uk"))
        back, ok2, d2 = ca.parse_a(ca.a_copy(rows))
        self.assertEqual((len(back), d2), (149, 0))
        self.assertFalse(ok2)  # 149 rows is below the registered minimum
        self.assertNotIn(b"aybr", ca.a_copy(rows))

    def test_parse_a_refuses_other_tables(self):
        lines = ["C%d,c%d.gov.uk,https://c%d.gov.uk/a,100,compliant,8,8,footer-link" % (i, i, i)
                 for i in range(160)]
        self.assertTrue(ca.parse_a(csv_bytes(lines))[1])
        self.assertFalse(ca.parse_a(csv_bytes(lines[:100]))[1])
        bad_total = lines + ["Z,z.gov.uk,https://z.gov.uk/a,100,compliant,7,7,footer-link"]
        self.assertFalse(ca.parse_a(csv_bytes(bad_total))[1])
        self.assertFalse(ca.parse_a(b"name,host\nA,a.gov.uk\n")[1])
        self.assertFalse(ca.parse_a(b"\xff\xfe")[1])

    def test_match(self):
        b = [b_row("york.gov.uk", "https://www.york.gov.uk/AccessibilityStatement", found_by="hub"),
             b_row("anglesey.gov.uk", "https://www.anglesey.gov.wales/en/Accessibility-statement.aspx"),
             b_row("bar.gov.uk", "https://www.bar.gov.uk/accessibility"),
             b_row("x.gov.uk", "", status="not_found")]
        a = [a_row("york.gov.uk", "https://www.york.gov.uk/accessibility", 1),
             a_row("anglesey.gov.wales", "https://www.anglesey.gov.wales/en/Accessibility-statement.aspx"),
             a_row("services.bar.gov.uk", "https://services.bar.gov.uk/acc", 5),
             a_row("x.gov.uk", "https://x.gov.uk/a"),
             a_row("www.york.gov.uk", "https://www.york.gov.uk/x"),
             a_row("nowhere.org", "https://nowhere.org/a")]
        j = ca.match(a, b)
        self.assertEqual([r["match"] for r in j],
                         ["host", "statement_host", "url_host", "host", "duplicate", "none"])
        self.assertEqual([r["b_host"] for r in j],
                         ["york.gov.uk", "anglesey.gov.uk", "bar.gov.uk", "x.gov.uk", "", ""])
        self.assertEqual([r["both_found"] for r in j], [True, True, True, False, False, False])
        self.assertEqual([r["same_url"] for r in j], [False, True, False, False, False, False])
        self.assertEqual([r["a_group"] for r in j], ["low", "full", "partial", "full", "full", "full"])
        self.assertEqual((j[0]["b_found_by"], j[0]["b_statement_date"]), ("hub", "2025-10-02"))


class ReadTests(unittest.TestCase):
    def test_hub_links_to_ours(self):
        a_url = "https://www.h.gov.uk/accessibility"
        get = FakeGet({a_url: (HTML, HUB)})
        r = ca.reread(joined(a_url, "https://www.h.gov.uk/accessibility/statement"), get=get,
                      delay=0, sleep=nosleep)
        self.assertEqual(get.calls, ["https://www.h.gov.uk/robots.txt", a_url])
        self.assertEqual((r["reread"], r["reread_status"], r["answered_html"]), (True, "200", True))
        self.assertEqual((r["is_statement"], r["links_to_ours"], r["final_is_ours"]),
                         (False, True, False))
        self.assertEqual(r["reread_chars"], len(stc.visible_text(HUB, HTML)))

    def test_statement_elsewhere(self):
        a_url = "https://www.h.gov.uk/old-statement"
        get = FakeGet({a_url: (HTML, STATEMENT)})
        r = ca.reread(joined(a_url, "https://www.h.gov.uk/accessibility/statement"), get=get,
                      delay=0, sleep=nosleep)
        self.assertEqual((r["is_statement"], r["links_to_ours"], r["final_is_ours"]),
                         (True, False, False))
        self.assertEqual((r["reread_highest"], r["reread_statement_date"]), ("2.2", "2025-10-04"))

    def test_redirect_to_ours(self):
        a_url = "https://www.h.gov.uk/accessibility"
        b_url = "https://www.h.gov.uk/accessibility/statement"
        get = FakeGet({a_url: (200, b_url, HTML, STATEMENT)})
        r = ca.reread(joined(a_url, b_url), get=get, delay=0, sleep=nosleep)
        self.assertTrue(r["final_is_ours"] and r["is_statement"])

    def test_robots_honoured(self):
        a_url = "https://www.h.gov.uk/accessibility"
        get = FakeGet({"https://www.h.gov.uk/robots.txt": ("text/plain",
                                                           b"User-agent: *\nDisallow: /\n"),
                       a_url: (HTML, HUB)})
        r = ca.reread(joined(a_url, "https://www.h.gov.uk/s"), get=get, delay=0, sleep=nosleep)
        self.assertEqual((r["reread_status"], r["robots_blocked"], r["answered_html"]),
                         ("robots", True, False))
        self.assertNotIn(a_url, get.calls)

    def test_retry_once_after_503(self):
        a_url = "https://www.h.gov.uk/accessibility"

        class Flaky(FakeGet):
            def __call__(self, u, timeout=20):
                if u == a_url and u not in self.calls:
                    self.calls.append(u)
                    return 503, u, "", b""
                return FakeGet.__call__(self, u, timeout)
        get = Flaky({a_url: (HTML, HUB)})
        r = ca.reread(joined(a_url, "https://www.h.gov.uk/accessibility/statement"), get=get,
                      delay=0, sleep=nosleep)
        self.assertEqual((r["retried"], r["reread_status"], r["links_to_ours"]), (True, "200", True))

    def test_not_found(self):
        r = ca.reread(joined("https://www.h.gov.uk/gone", "https://www.h.gov.uk/s"), get=FakeGet(),
                      delay=0, sleep=nosleep)
        self.assertEqual((r["reread_status"], r["answered_html"]), ("404", False))


def jrow(group, both=True, same=True, answered=False, links=False, dated=True, found_by="link"):
    passed = {"low": 1, "partial": 6, "full": 8}[group]
    r = {c: "" for c in ca.COLUMNS}
    r.update({k: False for k in ca.BOOLS})
    r.update(a_name="C", a_host="h.gov.uk", a_url="https://h.gov.uk/a", a_passed=passed, a_total=8,
             a_group=group, a_verdict="v", a_via="footer-link", match="host", b_host="h.gov.uk",
             b_status="ok" if both else "not_found", b_found_by=found_by if both else "",
             b_url="https://h.gov.uk/b", b_highest="2.2" if both else "",
             b_statement_date="2025-01-01" if (both and dated) else "", both_found=both,
             same_url=both and same, reread=both and not same, answered_html=answered,
             links_to_ours=links, reread_chars=0)
    if r["reread"]:
        r["reread_status"] = "200" if answered else "404"
    return r


def synthetic():
    rows = []
    for i in range(130):  # full: 120 at MV2's address, 115 of them dated
        rows.append(jrow("full", same=i < 120, dated=i < 115 or i >= 120))
    for i in range(20):   # low: 15 at another address, 12 answered, 9 link to MV2's statement
        rows.append(jrow("low", same=i >= 15, answered=i < 12, links=i < 9,
                         found_by="hub" if i < 15 else "link"))
    for i in range(30):
        rows.append(jrow("partial"))
    for i in range(20):
        rows.append(jrow("full", both=False))
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        m, g, p = ca.grade(synthetic())
        self.assertEqual(g, {"G1_both_found": True})
        self.assertEqual(p, {"H1": True, "H2": True, "H3": True, "H4": True})
        self.assertEqual((m["A_rows"], m["matched"], m["G1_both_found"]), (200, 200, 180))
        self.assertEqual(m["H1_low_diff"], {"k": 15, "n": 20, "pct": 75.0})
        self.assertEqual(m["H2_full_same"], {"k": 120, "n": 130, "pct": 92.31})
        self.assertEqual(m["H3_low_links_to_ours"], {"k": 9, "n": 12, "pct": 75.0})
        self.assertEqual(m["H4_full_same_dated"], {"k": 115, "n": 120, "pct": 95.83})

    def test_failures_and_minimums(self):
        rows = synthetic()
        for r in rows[130:142]:
            r["links_to_ours"] = False
        _, _, p = ca.grade(rows)
        self.assertFalse(p["H3"])
        for r in rows[130:137]:
            r["answered_html"] = False
        _, _, p = ca.grade(rows)
        self.assertIsNone(p["H3"])  # 5 answered pages, below 8

    def test_gate(self):
        rows = synthetic()
        for r in rows[:100]:
            r["both_found"] = False
        _, g, p = ca.grade(rows)
        self.assertFalse(g["G1_both_found"])
        self.assertEqual(p, {"H1": None, "H2": None, "H3": None, "H4": None})

    def test_described(self):
        d = ca.described(synthetic(), [])
        self.assertEqual(d["by_group"]["low"],
                         {"a_rows": 20, "both": 20, "same_url": 5, "diff_url": 15,
                          "b_found_by_hub": 15, "b_dated": 20, "b_wcag22": 20,
                          "reread_answered": 12, "reread_is_statement": 0,
                          "reread_links_to_ours": 9, "reread_final_is_ours": 0})
        self.assertEqual(d["a_group"], {"full": 150, "partial": 30, "low": 20})
        self.assertEqual(d["diff_url_b_found_by"], {"hub": 15, "link": 10})
        self.assertEqual(d["reread_status"], {"404": 13, "200": 12})

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as tmp:
            t = ca.write_table(tmp, rows)
            with open(os.path.join(tmp, "agree.csv"), encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, ca.COLUMNS)
                back = ca.typed(list(reader))
        self.assertEqual(t["rows"], 200)
        self.assertEqual(ca.grade(back), ca.grade(rows))
        self.assertEqual(ca.described(back, []), ca.described(rows, []))


def fake_world(b_rows):
    """Accessibility.build's table built from MV2's own: 150 statements at MV2's address scored
    8 of 8, and 10 hub pages scored 1 of 8 that link to MV2's statement."""
    usable = [r for r in b_rows if r["status"] == "ok" and ca.norm_url(r["statement_url"])
              and r["statement_url"].startswith("https://")
              and not any(ch in r["statement_url"] for ch in ",&\"'<>")]
    lines, pages = [], {}
    for r in usable[:150]:
        lines.append("C,%s,%s,100,compliant,8,8,footer-link" % (r["host"], r["statement_url"]))
    for r in usable[150:160]:
        hub = "https://%s/agree-test-hub" % r["host"]
        lines.append("C,%s,%s,13,not-compliant,1,8,common-path" % (r["host"], hub))
        pages[hub] = (HTML, b"<html><body><h1>Accessibility</h1><a href=\"" +
                      r["statement_url"].encode("utf-8") + b"\">Accessibility statement</a>"
                      b"</body></html>")
    pages[ca.A_URL] = ("text/csv", csv_bytes(lines))
    return pages, [r["host"] for r in usable[150:160]]


class RunTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_ALL, "committed files not in this folder")
    def test_full_offline_run(self):
        b_rows, ok = ca.read_b(TABLE)
        self.assertTrue(ok)
        pages, hub_hosts = fake_world(b_rows)
        get = FakeGet(pages)
        with tempfile.TemporaryDirectory() as tmp:
            ca.main(["--out-dir", tmp], get=get, sleep=nosleep)
            with open(os.path.join(tmp, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(tmp, "result.txt"), encoding="utf-8") as f:
                self.assertEqual(f.read(), ca.result_text(result) + "\n")
            with open(os.path.join(tmp, ca.A_FILE), "rb") as f:
                self.assertEqual(ca.sha256(f.read()), result["a_table"]["copy_sha256"])
        g = result["gates"]
        self.assertEqual(g, {"P0_prereg": True, "P0_pins": True, "F1_mv2_table": True,
                             "A1_their_table": True, "G1_both_found": True})
        self.assertEqual(result["status"], "graded")
        self.assertEqual((result["a_table"]["rows"], result["crawl"]["pages"]), (160, 10))
        p = result["predictions"]
        self.assertEqual((p["H1"], p["H2"], p["H3"]), (True, True, True))
        self.assertEqual(result["measures"]["H4_full_same_dated"]["n"], 150)
        self.assertEqual(result["measures"]["H3_low_links_to_ours"], {"k": 10, "n": 10, "pct": 100.0})
        hubs = [u for u in get.calls if u.endswith("/agree-test-hub")]
        self.assertEqual(sorted(hubs), sorted("https://%s/agree-test-hub" % h for h in hub_hosts))

    @unittest.skipUnless(HAVE_ALL, "committed files not in this folder")
    def test_wrong_table_reads_nothing(self):
        get = FakeGet({ca.A_URL: ("text/csv", b"name,host\nA,a.gov.uk\n")})
        with tempfile.TemporaryDirectory() as tmp:
            ca.main(["--out-dir", tmp], get=get, sleep=nosleep)
            with open(os.path.join(tmp, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            self.assertFalse(os.path.exists(os.path.join(tmp, ca.A_FILE)))
        self.assertEqual(result["status"], "not_run")
        self.assertFalse(result["gates"]["A1_their_table"])
        self.assertEqual(get.calls, ["https://accessibility.build/robots.txt", ca.A_URL])


class CommittedTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_ALL, "committed files not in this folder")
    def test_pinned_scripts_are_the_ones_november_ran(self):
        self.assertTrue(ca.pins_match(ROOT))

    @unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("G1 (at least 120 councils where both tables found a statement)",
                       "H1 (at least 60% of the low-score rows",
                       "H2 (at least 80% of the full-score rows",
                       "H3 (at least 60% of the re-read low-score pages",
                       "H4 (at least 90% of the full-score rows at the same address",
                       "at least 10 rows", "at least 60 rows", "at least 8 pages",
                       "at least 50 rows", ca.TABLE_SHA256[:12], "`council-agree-2026-11`",
                       "2026-09-02", "CC BY 4.0"):
            self.assertIn(phrase, text)
        self.assertEqual((ca.G1_MIN_BOTH, ca.H1_MIN_DIFF, ca.H2_MIN_SAME, ca.H3_MIN_LINK,
                          ca.H4_MIN_DATED), (120, 0.60, 0.80, 0.60, 0.90))
        self.assertEqual((ca.H1_MIN_ROWS, ca.H2_MIN_ROWS, ca.H3_MIN_PAGES, ca.H4_MIN_ROWS),
                         (10, 60, 8, 50))
        self.assertIsNone(cs.GUARD_RE.search(text))


if __name__ == "__main__":
    unittest.main()
