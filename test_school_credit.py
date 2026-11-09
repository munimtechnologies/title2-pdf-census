# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for school_credit.py (no network). Made by MV2 of Munim, Inc. with AI agents."""

import datetime
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import school_credit as sc  # noqa: E402
import school_stock as ss  # noqa: E402
import statement_template_check as stc  # noqa: E402

HTML = "text/html; charset=utf-8"
FINISHED = "2026-11-09T14:18:04Z"
NOW = datetime.datetime(2026, 11, 10, 9, 0, tzinfo=datetime.timezone.utc)
CLOSING = ("values diversity and inclusion and is committed to providing an accessible online "
           "experience for everyone in our school community.")
GOV_THREE_TEXT = (
    "Accessibility statement. This accessibility statement applies to our school website. We want "
    "as many people as possible to be able to use this website. If you need information in a "
    "different format contact us. Email: [email address] Call: [phone number] We will consider "
    "your request and get back to you in [number] days. Example Academy " + CLOSING)
JUNIPER_TEXT = (
    "Accessibility Statement. This website is run by [School Name] and this statement applies to "
    "the whole website. We want as many people as possible to be able to use this website. This "
    "website is partially compliant with the Web Content Accessibility Guidelines version 2.2 AA "
    "standard. [School Name] " + CLOSING)
GREENHOUSE = (b"<footer><a href='https://www.greenhouseschoolwebsites.co.uk/school-website-design/'>"
              b"Website design</a> by <a href='https://www.greenhouseschoolwebsites.co.uk'>"
              b"Greenhouse School Websites</a></footer>")
JUNIPER = b"<footer>School Website by <a href='https://example.invalid/'>Juniper Websites</a></footer>"
E4 = (b"<footer>School Website Design by <a href='https://www.e4education.co.uk'>e4education</a>"
      b"</footer>")


def page(text, footer=b""):
    return (b"<!doctype html><html><head><title>Accessibility Statement</title></head><body><main>"
            b"<p>" + text.encode("utf-8") + b"</p></main>" + footer + b"</body></html>")


def text_hash(body):
    return ss.sha256(stc.visible_text(body, HTML).encode("utf-8"))


def no_sleep(_):
    pass


def make_get(responses):
    calls = []

    def get(url):
        calls.append(url)
        r = responses.get(url)
        return r if r is not None else (404, url, "", b"")
    get.calls = calls
    return get


def stock_row(host, **kw):
    r = ss.blank({"host": host, "urn": "1", "name": "Example School", "type_group": "Academies",
                  "phase": "Primary", "la_name": "Example", "region": "London",
                  "establishments": 1, "base": "http://www.%s" % host})
    r.update(status="ok", placeholder=True)
    r.update(kw)
    return r


def url_of(host):
    return "http://www.%s/accessibility-statement/" % host


class CreditTests(unittest.TestCase):
    def test_each_company(self):
        self.assertEqual(sc.CREDITS, ("juniper", "e4education", "primarysite", "greenhouse",
                                      "finalsite"))
        c = sc.credits(GREENHOUSE)
        self.assertTrue(c["greenhouse"])
        self.assertFalse(c["family"])
        c = sc.credits(E4)
        self.assertTrue(c["e4education"])
        self.assertFalse(c["juniper"])
        self.assertTrue(c["family"])
        c = sc.credits(JUNIPER)
        self.assertTrue(c["juniper"] and c["family"])
        self.assertTrue(sc.credits(b"href='https://www.primarysite.net/'")["primarysite"])
        self.assertTrue(sc.credits(b"<script src='https://cdn.finalsite.net/x.js'>")["finalsite"])
        self.assertTrue(sc.credits(b"Greenhouse&nbsp;School Websites")["greenhouse"])

    def test_ordinary_words_are_not_credits(self):
        for body in (b"our primary site at Elm Road", b"greenhouse gases and the school garden",
                     b"Juniper Green Primary School", b""):
            with self.subTest(body=body):
                self.assertFalse(any(sc.credits(body)[k] for k in sc.CREDITS + ("family",)))

    def test_the_juniper_pattern_is_school_stocks(self):
        self.assertIs(dict(sc.CREDIT_RES)["juniper"], ss.JUNIPER_CREDIT_RE)


class FrameTests(unittest.TestCase):
    def test_frame_and_groups(self):
        rows = [stock_row("a.sch.uk", juniper_template=True, placeholder_ids=sc.L1_IDS),
                stock_row("b.sch.uk", juniper_template=True, juniper_credit=True,
                          placeholder_ids=sc.L1_IDS),
                stock_row("c.sch.uk", placeholder_ids="school/your_school;school/fake_phone"),
                stock_row("d.sch.uk", placeholder=False),
                stock_row("e.sch.uk", status="http_404", placeholder=False)]
        frame = sc.frame_of(rows)
        self.assertEqual([r["host"] for r in frame], ["a.sch.uk", "b.sch.uk", "c.sch.uk"])
        self.assertEqual([sc.l1_group(r) for r in frame], [True, False, False])
        self.assertEqual([sc.us_template(r) for r in frame], [False, False, True])

    def test_load_stock_checks_the_tables(self):
        rows = [stock_row("a.sch.uk", placeholder_ids=sc.L1_IDS), stock_row("b.sch.uk")]
        with tempfile.TemporaryDirectory() as tmp:
            tables = ss.write_tables(tmp, rows)
            back, ok = sc.load_stock(tmp, tables)
            self.assertTrue(ok)
            self.assertEqual(len(back), 2)
            self.assertIs(back[0]["placeholder"], True)
            bad = [dict(tables[0], sha256="0" * 64)]
            self.assertFalse(sc.load_stock(tmp, bad)[1])
            self.assertFalse(sc.load_stock(tmp, [dict(tables[0], file="missing.csv")])[1])
            self.assertFalse(sc.load_stock(tmp, [])[1])


class RereadTests(unittest.TestCase):
    def test_greenhouse_page(self):
        body = page(GOV_THREE_TEXT, GREENHOUSE)
        row = stock_row("g.sch.uk", juniper_template=True, placeholder_ids=sc.L1_IDS,
                        text_sha256=text_hash(body))
        get = make_get({url_of("g.sch.uk"): (200, url_of("g.sch.uk"), HTML, body)})
        r = sc.reread(row, get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "ok")
        self.assertTrue(r["graded"])
        self.assertTrue(r["same_text"])
        self.assertTrue(r["greenhouse"])
        self.assertFalse(r["family"])
        self.assertTrue(r["l1_group"])
        self.assertIn("gov-uk/email_address", r["placeholder_ids"])
        self.assertEqual(get.calls, ["http://www.g.sch.uk/robots.txt", url_of("g.sch.uk")])

    def test_changed_and_filled_page(self):
        body = page(JUNIPER_TEXT.replace("[School Name]", "Example School"), JUNIPER)
        row = stock_row("j.sch.uk", text_sha256="0" * 64)
        get = make_get({url_of("j.sch.uk"): (200, url_of("j.sch.uk"), HTML, body)})
        r = sc.reread(row, get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "ok")
        self.assertFalse(r["graded"])
        self.assertFalse(r["same_text"])
        self.assertTrue(r["juniper"])

    def test_robots_disallow_reads_nothing(self):
        robots = "http://www.r.sch.uk/robots.txt"
        get = make_get({robots: (200, robots, "text/plain", b"User-agent: *\nDisallow: /\n")})
        r = sc.reread(stock_row("r.sch.uk"), get=get, sleep=no_sleep)
        self.assertEqual(r["status"], "robots")
        self.assertFalse(r["graded"])
        self.assertFalse(any(r[k] for k in sc.CREDITS))
        self.assertEqual(get.calls, [robots])

    def test_retry_keeps_the_second_body(self):
        body = page(JUNIPER_TEXT, E4)
        u = url_of("t.sch.uk")
        answers = [(503, u, "", b"Juniper Websites"), (200, u, HTML, body)]

        def get(url):
            return answers.pop(0) if url == u else (404, url, "", b"")
        r = sc.reread(stock_row("t.sch.uk"), get=get, sleep=no_sleep)
        self.assertTrue(r["retried"])
        self.assertTrue(r["e4education"])
        self.assertFalse(r["juniper"])


def synthetic_site(tmp, now_ok=True):
    """A repository folder with school-stock's outputs for 71 hosts; returns (rows, get)."""
    rows, responses = [], {}

    def add(host, text, footer, same=True, **kw):
        body = page(text, footer)
        rows.append(stock_row(host, text_sha256=text_hash(body) if same else "0" * 64, **kw))
        responses[url_of(host)] = (200, url_of(host), HTML, body)

    for i in range(52):  # the three-field group: 50 credit Greenhouse, 2 credit no one
        add("g%d.sch.uk" % i, GOV_THREE_TEXT, GREENHOUSE if i < 50 else b"", same=i >= 3,
            juniper_template=True, placeholder_ids=sc.L1_IDS)
    for i in range(10):
        add("j%d.sch.uk" % i, JUNIPER_TEXT, JUNIPER, juniper_template=True, juniper_credit=True,
            placeholder_ids="school/school_bracket")
    for i in range(8):
        add("e%d.sch.uk" % i, JUNIPER_TEXT, E4, juniper_template=True,
            placeholder_ids="school/school_bracket")
    rows.append(stock_row("r.sch.uk", placeholder_ids="school/school_bracket"))
    robots = "http://www.r.sch.uk/robots.txt"
    responses[robots] = (200, robots, "text/plain", b"User-agent: *\nDisallow: /\n")
    res = os.path.join(tmp, "results", "uk-schools")
    os.makedirs(res)
    tables = ss.write_tables(res, rows)
    stock = {"status": "graded", "crawl": {"finished_utc": FINISHED}, "tables": tables,
             "gates": {"P0_prereg": True, "P0_checker": True, "F1_frame": True,
                       "G1_answered": True}}
    with open(os.path.join(res, "result.json"), "w", encoding="utf-8") as f:
        json.dump(stock, f)
    for name, text in (("CREDIT-FOLLOWUP-PREREG.md", "K1 K2 K3"),
                       ("CREDIT-FOLLOWUP-ADDENDUM.md", "L1"),
                       ("SCHOOL-STOCK-RESULT.md", "result")):
        with open(os.path.join(res, name), "w", encoding="utf-8") as f:
            f.write(text)
    return rows, make_get(responses)


class RunTests(unittest.TestCase):
    def run_main(self, now=NOW, drop=None):
        with tempfile.TemporaryDirectory() as tmp:
            _, get = synthetic_site(tmp)
            if drop:
                os.remove(os.path.join(tmp, "results", "uk-schools", drop))
            out = os.path.join(tmp, "out")
            code = sc.main(["--out-dir", out, "--workers", "4"], get=get, sleep=no_sleep, now=now,
                           root=tmp)
            with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
                txt = f.read()
            table = os.path.exists(os.path.join(out, "hosts.csv"))
        self.assertEqual(code, 0)
        return result, txt, table, get

    def test_graded_run(self):
        result, txt, table, _ = self.run_main()
        self.assertEqual(result["status"], "graded")
        self.assertTrue(all(result["gates"].values()), result["gates"])
        self.assertEqual(result["frame_hosts"], 71)
        m = result["measures"]
        self.assertEqual(m["graded_hosts"], 70)
        self.assertEqual(m["K1_family"], {"k": 18, "n": 70, "pct": 25.71})
        self.assertEqual(m["K2_missed_by_j2_pattern"], {"k": 8, "n": 70, "pct": 11.43})
        self.assertEqual(m["K3_unchanged_text"], {"k": 67, "n": 70, "pct": 95.71})
        self.assertEqual(m["L1_greenhouse_of_three_field_group"], {"k": 50, "n": 52, "pct": 96.15})
        self.assertEqual(result["predictions"], {"K1": False, "K2": True, "K3": True, "L1": True})
        d = result["described"]
        self.assertEqual(d["status"], {"ok": 70, "robots": 1})
        self.assertEqual(d["graded_no_credit"], 2)
        self.assertEqual(d["graded_greenhouse"], 50)
        self.assertEqual(d["graded_text_changed"], 3)
        self.assertEqual(d["credit_combinations"], {"greenhouse": 50, "juniper": 10,
                                                    "e4education": 8, "none": 2})
        self.assertEqual(d["graded_stock_template"]["hosts"], 70)
        self.assertTrue(table)
        self.assertTrue(txt.startswith("school_credit 0.1.0\nstatus: graded\n"))
        self.assertEqual(result["table"]["rows"], 71)

    def test_too_late_reads_nothing(self):
        late = datetime.datetime(2026, 12, 1, 0, 0, tzinfo=datetime.timezone.utc)
        result, _, table, get = self.run_main(now=late)
        self.assertEqual(result["status"], "not_run")
        self.assertFalse(result["gates"]["C2_within_21_days"])
        self.assertEqual(get.calls, [])
        self.assertFalse(table)

    def test_no_addendum_reads_nothing(self):
        result, _, _, get = self.run_main(drop="CREDIT-FOLLOWUP-ADDENDUM.md")
        self.assertFalse(result["gates"]["P0_registered"])
        self.assertEqual(get.calls, [])

    def test_unpublished_result_reads_nothing(self):
        result, _, _, get = self.run_main(drop="SCHOOL-STOCK-RESULT.md")
        self.assertFalse(result["gates"]["C0_published"])
        self.assertEqual(get.calls, [])


PREREG = os.path.join(HERE, *sc.PREREG_PATH.split("/"))
ADDENDUM = os.path.join(HERE, *sc.ADDENDUM_PATH.split("/"))


@unittest.skipUnless(os.path.exists(PREREG) and os.path.exists(ADDENDUM),
                     "the registration files are not here")
class RegistrationTests(unittest.TestCase):
    def text(self, path):
        with open(path, encoding="utf-8") as f:
            return " ".join(f.read().split())

    def test_constants_are_the_registered_ones(self):
        p, a = self.text(PREREG), self.text(ADDENDUM)
        for phrase in ("K1: at least 90% of the graded set carry a `family` credit",
                       "K2: at least 10% of the graded set carry an `e4education` or `primarysite` "
                       "credit and no `juniper` credit",
                       "K3: at least 90% of the graded set's pages are unchanged",
                       "graded set has at least 50 hosts", "no more than 21 days"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, p)
        for phrase in ("at least 80% carry a `greenhouse` credit", "at least 50 such hosts",
                       sc.L1_IDS):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, a)
        self.assertEqual((sc.K1_MIN_FAMILY, sc.K2_MIN_MISSED, sc.K3_MIN_SAME,
                          sc.L1_MIN_GREENHOUSE, sc.MIN_GRADED, sc.MAX_DAYS),
                         (0.90, 0.10, 0.90, 0.80, 50, 21))


STOCK_RESULT = os.path.join(HERE, *sc.STOCK_RESULT_PATH.split("/"))


@unittest.skipUnless(os.path.exists(STOCK_RESULT), "school-stock's result is not here")
class PublishedStockTests(unittest.TestCase):
    def test_the_published_frame(self):
        with open(STOCK_RESULT, encoding="utf-8") as f:
            stock = json.load(f)
        rows, ok = sc.load_stock(os.path.join(HERE, *sc.RES_DIR.split("/")), stock["tables"])
        self.assertTrue(ok)
        frame = sc.frame_of(rows)
        self.assertEqual(len(frame), stock["measures"]["J1_placeholder_hosts"])
        self.assertEqual(len(frame), 667)
        self.assertEqual(sum(1 for r in frame if sc.l1_group(r)), 327)
        self.assertEqual(sum(1 for r in frame if sc.us_template(r)), 30)


if __name__ == "__main__":
    unittest.main()
