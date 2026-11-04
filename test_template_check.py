"""Offline tests for template_check.py (no network). Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import io
import os
import unittest

import a11y_pages as ap
import template_check as tc

HERE = os.path.dirname(os.path.abspath(__file__))
PREREG = os.path.join(HERE, "results", "template-pages", "PREREG.md")

TEMPLATE = ("Accessibility Statement Template This is only meant as a template local government "
            "accessibility statement. Please consult your legal counsel. YOURMUNICIPALITY is "
            "committed to providing electronic communication that is accessible to the widest "
            "possible audience, regardless of technology or ability. NAME TITLE EMAIL PHONE "
            "Accessibility Design Guidelines We work to comply with Section 508 as well as 2.0 A "
            "and AA referring to website accessibility standards.")
EDITED = ("The City of Example is committed to providing electronic communication that is "
          "accessible to the widest possible audience. We work to comply with Section 508 as well "
          "as WCAG 2.0 A and AA referring to website accessibility standards. In JAWS press "
          "[Insert] + [F7] for a list of links. Download the [PDF] or write to [email protected]. "
          "Staff directory: Name Title Email Phone.")


def page(text, footer="Government Websites by CivicPlus"):
    return ("<html><head><title>Accessibility</title></head><body><main><p>%s</p></main>"
            "<footer>%s</footer><script>var t = 'YOURMUNICIPALITY';</script></body></html>"
            % (text, footer)).encode("utf-8")


def fake_get(pages, robots=(404, b"")):
    calls = []

    def get(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return robots[0], url, "text/plain", robots[1]
        got = pages.get(url, (404, b""))
        status, body = got[0], got[1]
        ctype = got[2] if len(got) > 2 else ("text/html; charset=utf-8" if status == 200 else "")
        return status, url, ctype, body
    return get, calls


def row(cohort, qid, url="https://example.gov/153/Accessibility", sha="", highest="", stock=""):
    return {"cohort": cohort, "qid": qid, "name": "N" + qid, "kind": "city", "state": "S",
            "page_url": url, "old_sha256": sha, "old_highest": highest, "old_stock": stock}


class TextTests(unittest.TestCase):
    def test_template_is_flagged(self):
        r = tc.check_text(TEMPLATE)
        self.assertEqual((r["muni"], r["template_note"], r["contact_block"], r["bracket"]),
                         (True, True, True, False))
        self.assertTrue(r["placeholder"])
        self.assertTrue(r["no_wcag"])
        self.assertTrue(r["stock"])
        self.assertEqual(r["bracket_text"], "")

    def test_edited_page_is_not_flagged(self):
        r = tc.check_text(EDITED)
        self.assertFalse(any(r[k] for k in tc.FLAGS))
        self.assertFalse(r["placeholder"])
        self.assertFalse(r["no_wcag"])
        self.assertTrue(r["stock"])

    def test_brackets(self):
        for s in ("[URL OF WEBSITE]", "[NAME OF PARISH/TOWN COUNCIL]", "[CITY NAME]",
                  "[YOUR CITY]", "[INSERT DATE]", "call [PHONE NUMBER] today"):
            self.assertTrue(tc.check_text(s)["bracket"], s)
        self.assertEqual(tc.check_text("x [URL OF WEBSITE] y")["bracket_text"],
                         "[URL OF WEBSITE]")
        for s in ("[Insert]", "[PDF]", "[email protected]", "[F7]", "[Your City]",
                  "[1] WCAG 2.1"):
            self.assertFalse(tc.check_text(s)["bracket"], s)

    def test_other_patterns(self):
        self.assertTrue(tc.check_text("YOUR MUNICIPALITY is committed")["muni"])
        self.assertFalse(tc.check_text("Your municipality is committed")["muni"])
        self.assertTrue(tc.check_text("This is ONLY MEANT AS A TEMPLATE.")["template_note"])
        self.assertTrue(tc.check_text("NAME / TITLE / EMAIL / PHONE")["contact_block"])
        self.assertFalse(tc.check_text("Name / Title / Email / Phone")["contact_block"])
        self.assertFalse(tc.check_text("as well as WCAG 2.0 A and AA")["no_wcag"])

    def test_civicplus(self):
        self.assertTrue(tc.is_civicplus(b"<a>Government Websites by CivicPlus\xc2\xae</a>"))
        self.assertTrue(tc.is_civicplus(b"<title>Accessibility | CivicEngage</title>"))
        self.assertFalse(tc.is_civicplus(b"<p>Granicus</p>"))


class ReadTests(unittest.TestCase):
    def test_reads_a_template_page(self):
        url = "https://example.gov/153/Accessibility"
        body = page(TEMPLATE)
        get, calls = fake_get({url: (200, body)})
        out = tc.read_one(row("small", "Q1"), get=get, sleep=lambda s: None)
        self.assertEqual(calls, ["https://example.gov/robots.txt", url])
        self.assertEqual(out["status"], "ok")
        self.assertTrue(out["placeholder"] and out["civicplus"] and out["no_wcag"])
        text = ap.visible_text(ap.parse(body, "text/html; charset=utf-8"))
        self.assertEqual(out["text_sha256"], ap.sha256(text.encode("utf-8")))
        self.assertEqual(out["text_chars"], len(text))
        self.assertFalse(out["same_text"])
        same = tc.read_one(row("small", "Q1", sha=out["text_sha256"]), get=get,
                           sleep=lambda s: None)
        self.assertTrue(same["same_text"])

    def test_statuses(self):
        url = "https://example.gov/153/Accessibility"
        get, _ = fake_get({url: (403, b"")})
        self.assertEqual(tc.read_one(row("small", "Q1"), get=get, sleep=lambda s: None)["status"],
                         "http_403")
        get, calls = fake_get({url: (200, page(TEMPLATE))},
                              robots=(200, b"User-agent: *\nDisallow: /\n"))
        out = tc.read_one(row("small", "Q1"), get=get, sleep=lambda s: None)
        self.assertEqual(out["status"], "robots")
        self.assertEqual(calls, ["https://example.gov/robots.txt"])
        self.assertEqual(out["placeholder"], "")
        get, _ = fake_get({url: (200, page("Short page.", footer=""))})
        self.assertEqual(tc.read_one(row("small", "Q1"), get=get, sleep=lambda s: None)["status"],
                         "short")
        get, _ = fake_get({url: (200, b"%PDF-1.7 not a page", "application/pdf")})
        out = tc.read_one(row("small", "Q1"), get=get, sleep=lambda s: None)
        self.assertEqual(out["status"], "not_html")

    def test_read_table(self):
        data = ("qid,name,kind,state,population,website,page_status,page_url,text_sha256,highest,"
                "stock\nQ1,A,city,S,1,w,ok,https://a.gov/acc,abc,,True\n"
                "Q2,B,town,S,1,w,no_link,,,,\nQ3,C,county,S,1,w,ok,https://c.gov/acc,def,2.0,False\n")
        rows = tc.read_table(data.encode("utf-8"), "small")
        self.assertEqual([r["qid"] for r in rows], ["Q1", "Q3"])
        self.assertEqual(rows[0], row("small", "Q1", url="https://a.gov/acc", sha="abc",
                                      stock="True") | {"name": "A"})
        self.assertTrue(tc.in_group(rows[0]))
        self.assertFalse(tc.in_group(rows[1]))
        big = tc.read_table(b"qid,name,kind,state,page_status,page_url,text_sha256,highest\n"
                            b"Q9,Z,city,S,ok,https://z.gov/a,x,2.1\n", "large")
        self.assertEqual(big[0]["old_stock"], "")


def graded_rows(n_small=100, n_large=100, small_flagged=3, large_flagged=1, civic=4,
                grouped=3, no_wcag=60, unread_small=0):
    rows = []
    for i in range(n_small):
        r = row("small", "Qs%d" % i, stock="True" if i < grouped else "False")
        r.update(status="ok" if i >= unread_small else "http_0")
        for k in tc.BOOLS:
            r[k] = False
        r["placeholder"] = i < small_flagged
        r["civicplus"] = i < civic
        r["no_wcag"] = i < no_wcag
        rows.append(r)
    for i in range(n_large):
        r = row("large", "Ql%d" % i)
        r.update(status="ok")
        for k in tc.BOOLS:
            r[k] = False
        r["placeholder"] = i < large_flagged
        r["civicplus"] = i < max(0, civic - small_flagged)
        rows.append(r)
    return rows


class GradeTests(unittest.TestCase):
    def test_grades(self):
        rows = graded_rows()
        m, gate, p = tc.grade(rows, {"large": 100, "small": 100})
        self.assertTrue(gate)
        self.assertEqual(m["T1_placeholder_of_small"][:2], [3, 100])
        self.assertEqual(m["T2_placeholder_of_large"][:2], [1, 100])
        self.assertEqual(m["T3_civicplus_of_flagged"][:2], [4, 4])
        self.assertEqual(m["T4_no_wcag_of_small"][:2], [60, 100])
        self.assertEqual(m["T5_in_group_of_flagged_small"][:2], [3, 3])
        self.assertEqual(p, {"T1": True, "T2": True, "T3": None, "T4": True, "T5": None})

    def test_grades_with_enough_flagged(self):
        rows = graded_rows(small_flagged=12, large_flagged=0, civic=9, grouped=10, no_wcag=40)
        m, gate, p = tc.grade(rows, {"large": 100, "small": 100})
        self.assertEqual(m["T3_civicplus_of_flagged"][:2], [9, 12])
        self.assertEqual(p, {"T1": True, "T2": True, "T3": False, "T4": False, "T5": True})

    def test_gate(self):
        rows = graded_rows(unread_small=21)
        m, gate, p = tc.grade(rows, {"large": 100, "small": 100})
        self.assertFalse(gate)
        self.assertEqual(m["G1_reread_small"][:2], [79, 100])
        self.assertEqual(set(p.values()), {None})
        self.assertTrue(tc.grade(graded_rows(unread_small=20), {"large": 100, "small": 100})[1])

    def test_typed_round_trip_and_described(self):
        rows = graded_rows()
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=tc.COLUMNS, extrasaction="ignore",
                           lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in tc.COLUMNS})
        back = tc.typed(list(csv.DictReader(io.StringIO(buf.getvalue()))))
        self.assertEqual(tc.grade(back, {"large": 100, "small": 100}),
                         tc.grade(rows, {"large": 100, "small": 100}))
        d = tc.described(back)
        self.assertEqual(d["small"]["placeholder"], 3)
        self.assertEqual(d["small"]["placeholder_not_seen_before"], 3)
        self.assertEqual(d["large"]["placeholder_civicplus"], 1)
        self.assertEqual(len(d["flagged"]), 4)
        self.assertEqual(d["flagged"][0][:2], ["large", "NQl0"])
        self.assertEqual(d["status"]["small"], {"ok": 100})


class PlanTests(unittest.TestCase):
    def test_constants_are_the_preregistered_ones(self):
        self.assertEqual((tc.MIN_REREAD, tc.MIN_FLAGGED, tc.T1_MIN_SMALL, tc.T3_MIN_CIVICPLUS,
                          tc.T4_MIN_NO_WCAG, tc.T5_MIN_IN_GROUP),
                         (0.80, 10, 0.01, 0.80, 50, 0.80))
        self.assertEqual(tc.EXPECTED_PAGES, {"large": 808, "small": 1042})
        self.assertEqual(tc.PINNED, ("template_check.py", "a11y_pages.py"))
        self.assertEqual(len(tc.ALREADY_SEEN["small"]), 10)
        self.assertEqual(len(tc.ALREADY_SEEN["large"]), 6)

    def test_prereg_states_them(self):
        with open(PREREG, "rb") as f:
            md = f.read().decode("utf-8")
        for s in ("**T1.**", "**T2.**", "**T3.**", "**T4.**", "**T5.**", "at least 1.0%",
                  "at least 80%", "at least 50", "at least 10 flagged pages", "808", "1,042",
                  "not yet checked by a person"):
            self.assertIn(s, md)
        for qid in tc.ALREADY_SEEN["small"] + tc.ALREADY_SEEN["large"]:
            self.assertIn(qid, md)
        self.assertNotIn("MIT", md)


if __name__ == "__main__":
    unittest.main()
