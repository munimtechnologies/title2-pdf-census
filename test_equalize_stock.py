"""Offline tests of equalize_stock.py (no network is used).

Apache-2.0. Made by MV2 of Munim, Inc. with AI agents.
"""

import csv
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import equalize_stock as s  # noqa: E402

TEMPLATE = ("Our Commitment to Web Accessibility [YOUR COMPANY NAME] is committed to providing a "
            "fully accessible website experience for all users of all abilities, including those "
            "who rely on assistive technologies like screen readers. Ongoing Efforts to Ensure "
            "Accessibility We follow [ SPECIFIC STANDARD, VERSION, LEVEL ] as our guiding "
            "principle for determining accessibility. Accessibility features of this website "
            "include: [LIST ACCESSIBILITY FEATURES HERE] Where We're Improving "
            "[LIST ITEMS YOU’RE WORKING TO FIX HERE] [IT MAY HELP TO REVIEW THE OPEN ISSUES "
            "TAB TO SEE THE MOST COMMON PROBLEMS] [COMPANY NAME] welcomes your feedback: please "
            "email [YOUR ACCESSIBILITY EMAIL ADDRESS] or give us a call at [YOUR PHONE NUMBER].")
PARTIAL = ("Our Commitment to Web Accessibility The City of Foo is committed to providing a fully "
           "accessible website experience for all users of all abilities, including those who "
           "rely on assistive technologies like screen readers. Ongoing Efforts to Ensure "
           "Accessibility We follow the Web Content Accessibility Guidelines (WCAG) version 2.1 "
           "as our guiding principle for determining accessibility. Where We're Improving "
           "[LIST ITEMS YOU'RE WORKING TO FIX HERE] Please email clerk at the city or give us a "
           "call at [YOUR PHONE NUMBER].")
FILLED = ("Our Commitment to Web Accessibility The City of Foo is committed to providing a fully "
          "accessible website experience for all users of all abilities, including those who "
          "rely on assistive technologies like screen readers. Ongoing Efforts to Ensure "
          "Accessibility We follow the Web Content Accessibility Guidelines (WCAG) version 2.1 "
          "as our guiding principle for determining accessibility. Please email the city clerk "
          "or call the front desk during office hours if anything is hard to use.")
REWRITTEN = ("The City of Foo wants everyone to use this website. Ongoing Efforts to Ensure "
             "Accessibility We follow the Web Content Accessibility Guidelines (WCAG) version 2.1 "
             "as our guiding principle for determining accessibility. Please call "
             "[YOUR PHONE NUMBER] if a page is hard to use, and we will answer as soon as we can.")


def page(text, plugin=True):
    foot = ('<footer>Tested with the <a href="https://a11ychecker.com/">Accessibility Checker '
            'WordPress Plugin</a></footer>') if plugin else ""
    return ("<html><body><main><p>" + text + "</p></main>" + foot + "</body></html>").encode()


def fake_get(pages, robots=None):
    robots = robots or {}

    def get(url):
        if url.endswith("/robots.txt"):
            body = robots.get(url)
            return (200, url, "text/plain", body) if body else (404, url, "", b"")
        if url in pages:
            status, final, body = pages[url]
            return status, final, "text/html; charset=utf-8", body
        return 404, url, "", b""
    return get


def frow(census="home_ok", found=False, host="foo.gov", cohort="small", qid="Q1"):
    return {"cohort": cohort, "qid": qid, "name": "Foo", "kind": "city", "state": "Ohio",
            "population": "12000", "host": host,
            "probe_url": "https://www." + host + "/accessibility-statement/",
            "dupes": 0, "census": census, "census_page_as": found}


def no_sleep(_):
    return None


def read(row, pages, robots=None):
    return s.read_one(row, get=fake_get(pages, robots), delay=0, sleep=no_sleep)


class TextTests(unittest.TestCase):
    def test_unfilled_template(self):
        r = s.check_text(TEMPLATE)
        for k in s.PH_KEYS + ("stock_page", "placeholder", "unfilled", "other_bracket"):
            self.assertIs(r[k], True, k)
        self.assertEqual(r["n_placeholders"], 7)
        self.assertEqual(r["other_text"], "[YOUR COMPANY NAME]")
        self.assertIs(r["second"], False)

    def test_partly_filled(self):
        r = s.check_text(PARTIAL)
        self.assertEqual([k for k in s.PH_KEYS if r[k]], ["ph_fix", "ph_phone"])
        self.assertEqual(r["n_placeholders"], 2)
        self.assertIs(r["stock_page"], True)
        self.assertIs(r["second"], True)
        self.assertIs(r["placeholder"], True)
        self.assertIs(r["unfilled"], False)

    def test_filled(self):
        r = s.check_text(FILLED)
        self.assertIs(r["stock_page"], True)
        self.assertIs(r["placeholder"], False)
        self.assertEqual(r["n_placeholders"], 0)
        self.assertIs(r["other_bracket"], False)

    def test_rewritten_top_is_not_graded(self):
        r = s.check_text(REWRITTEN)
        self.assertIs(r["stock_page"], False)
        self.assertIs(r["second"], True)
        self.assertIs(r["ph_phone"], True)
        self.assertIs(r["placeholder"], False)

    def test_spacing_and_case(self):
        odd = FILLED.replace("fully accessible website", "Fully  Accessible\nwebsite")
        self.assertIs(s.check_text(odd)["stock_page"], True)
        self.assertIs(s.check_text("x [your company name] y")["ph_name"], True)
        self.assertIs(s.check_text("x [ Company Name ] y")["ph_name"], True)


class FrameTests(unittest.TestCase):
    def test_build_frame(self):
        large = [{"qid": "Q2", "name": "Big", "kind": "city", "state": "Ohio",
                  "population": "60000", "website": "https://www.foo.gov/", "home": "ok",
                  "page_status": "ok",
                  "page_url": "https://www.foo.gov/accessibility-statement/"}]
        small = [{"qid": "Q3", "name": "Foo2", "website": "http://foo.gov"},
                 {"qid": "Q4", "name": "[withheld]", "website": "[withheld]"},
                 {"qid": "Q5", "name": "Bar", "website": "https://bar.org/"},
                 {"qid": "Q6", "name": "Baz", "website": "https://baz.us/"},
                 {"qid": "Q7", "name": "Qux", "website": "https://qux.us/"}]
        sample = [{"qid": "Q5", "home": "ok", "page_status": "ok",
                   "page_url": "https://bar.org/accessibility"},
                  {"qid": "Q7", "home": "robots", "page_status": "", "page_url": ""}]
        frame, dropped = s.build_frame(large, small, sample)
        self.assertEqual(dropped, 1)
        self.assertEqual([r["host"] for r in frame], ["foo.gov", "bar.org", "baz.us", "qux.us"])
        self.assertEqual(frame[0]["dupes"], 1)
        self.assertEqual(frame[0]["probe_url"], "https://www.foo.gov/accessibility-statement/")
        self.assertEqual(frame[1]["probe_url"], "https://bar.org/accessibility-statement/")
        self.assertEqual((frame[0]["census"], frame[0]["census_page_as"]), ("home_ok", True))
        self.assertEqual((frame[1]["census"], frame[1]["census_page_as"]), ("home_ok", False))
        self.assertEqual((frame[2]["census"], frame[2]["census_page_as"]), ("not_sampled", False))
        self.assertEqual((frame[3]["census"], frame[3]["census_page_as"]), ("home_failed", False))


class ReadTests(unittest.TestCase):
    def test_template_hidden(self):
        row = frow()
        out = read(row, {row["probe_url"]: (200, row["probe_url"], page(TEMPLATE))})
        self.assertEqual(out["status"], "ok")
        for k in ("plugin", "stock_page", "placeholder", "unfilled", "hidden"):
            self.assertIs(out[k], True, k)

    def test_template_found_or_unsampled_is_not_hidden(self):
        for census, found in (("home_ok", True), ("not_sampled", False), ("home_failed", False)):
            row = frow(census=census, found=found)
            out = read(row, {row["probe_url"]: (200, row["probe_url"], page(TEMPLATE))})
            self.assertIs(out["placeholder"], True)
            self.assertIs(out["hidden"], False, census)

    def test_filled_page_without_plugin_markup(self):
        row = frow()
        out = read(row, {row["probe_url"]: (200, row["probe_url"], page(FILLED, plugin=False))})
        self.assertEqual(out["status"], "ok")
        self.assertIs(out["plugin"], False)
        self.assertIs(out["stock_page"], True)
        self.assertIs(out["placeholder"], False)
        self.assertIs(out["hidden"], False)

    def test_statuses(self):
        row = frow()
        self.assertEqual(read(row, {})["status"], "http_404")
        robots = {"https://www.foo.gov/robots.txt":
                  b"User-agent: *\nDisallow: /accessibility-statement/\n"}
        self.assertEqual(read(row, {}, robots)["status"], "robots")
        short = {row["probe_url"]: (200, row["probe_url"], page("Hi", plugin=False))}
        self.assertEqual(read(row, short)["status"], "short")


def synthetic():
    """4,800 hosts: 20 template statements (8 with a placeholder, 5 of them unfilled)."""
    rows = []

    def add(n, cohort, **kw):
        for _ in range(n):
            r = frow(cohort=cohort, qid="Q%d" % (len(rows) + 1))
            r.update(status="http_404", stock_page=False, placeholder=False, unfilled=False,
                     hidden=False, plugin=False, second=False)
            r.update({k: False for k in s.PH_KEYS})
            r.update(kw)
            rows.append(r)
    add(4, "small", status="ok", stock_page=True, placeholder=True, unfilled=True, ph_name=True,
        census_page_as=True)
    add(3, "small", status="ok", stock_page=True, placeholder=True, ph_fix=True, ph_phone=True,
        hidden=True)
    add(8, "small", status="ok", stock_page=True)
    add(1, "large", status="ok", stock_page=True, placeholder=True, unfilled=True, ph_name=True,
        census_page_as=True)
    add(4, "large", status="ok", stock_page=True)
    add(1000, "large")
    add(3680, "small")
    add(100, "small", status="http_0")
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        rows = synthetic()
        self.assertEqual(len(rows), 4800)
        measures, gates, preds = s.grade(rows)
        self.assertEqual(gates, {"F1_frame": True, "G1_answered": True})
        self.assertEqual(measures["W1_stock_hosts"], 20)
        self.assertEqual(measures["W2_placeholder_hosts"], 8)
        self.assertEqual(measures["W3_placeholder_of_stock"][:2], [8, 20])
        self.assertEqual(measures["G1_answered"][:2], [4700, 4800])
        self.assertEqual(preds, {"W1": True, "W2": True, "W3": True})

    def test_too_few_template_pages(self):
        rows = synthetic()
        for r in rows[:11]:
            r["stock_page"] = False
        _, _, preds = s.grade(rows)
        self.assertEqual(preds, {"W1": False, "W2": False, "W3": None})

    def test_gate_fails(self):
        _, gates, preds = s.grade(synthetic()[:4799])
        self.assertIs(gates["F1_frame"], False)
        self.assertEqual(preds, {"W1": None, "W2": None, "W3": None})

    def test_csv_round_trip_grades_the_same(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "hosts.csv")
            s.write_csv(path, rows, s.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                back = s.typed(list(csv.DictReader(f)))
        self.assertEqual(s.grade(back), s.grade(rows))
        d = s.described(back)
        self.assertEqual(d["stock_by_cohort"], {"small": 15, "large": 5})
        self.assertEqual(d["placeholder_by_cohort"], {"small": 7, "large": 1})
        self.assertEqual(d["placeholder_by_census_group"], {"found_as": 5, "hidden": 3})
        self.assertEqual(d["unfilled"], 5)
        self.assertEqual(d["placeholder_counts"]["ph_name"], 5)
        self.assertEqual(d["placeholder_counts"]["ph_phone"], 3)
        self.assertEqual(d["placeholder_counts"]["ph_email"], 0)
        self.assertEqual(len(d["flagged"]), 8)
        self.assertEqual(d["flagged"][0][0], "large")
        self.assertEqual(d["flagged"][0][5], "name")
        self.assertEqual(d["flagged"][0][-1], "found_as")


class RunTests(unittest.TestCase):
    def test_not_run_without_plan(self):
        def fetch(url):
            raise OSError("404")
        with tempfile.TemporaryDirectory() as d:
            s.main(["--out-dir", d], fetch=fetch, get=fake_get({}), sleep=no_sleep)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
        self.assertEqual(result["status"], "not_run")
        self.assertIs(result["gates"]["P0_prereg_public"], False)

    def test_not_run_on_wrong_tables(self):
        def fetch(url):
            path = url[len(s.REPO_RAW):].split("?")[0]
            if path == s.PREREG_PATH:
                return b"plan W1 W2 W3"
            if path in s.PINNED:
                with open(os.path.join(HERE, path), "rb") as f:
                    return f.read()
            return b"qid,website\nQ1,https://a.gov/\n"
        with tempfile.TemporaryDirectory() as d:
            s.main(["--out-dir", d], fetch=fetch, get=fake_get({}), sleep=no_sleep)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertEqual(result["status"], "not_run")
        self.assertIs(result["gates"]["P0_prereg_public"], True)
        self.assertIs(result["gates"]["G0_tables"], False)
        self.assertEqual(result["tables"]["large"]["rows"], 1)
        self.assertIn("predictions: not graded", text)


class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(os.path.join(HERE, "results", "stock-equalize", "PREREG.md"),
                  encoding="utf-8") as f:
            plan = f.read()
        for phrase in ("**10**", "**5**", "**30%**", "4,800 to 5,245", "80%",
                       "`/accessibility-statement/`", "W3", "[YOUR COMPANY NAME]",
                       "[COMPANY NAME]", "[ SPECIFIC STANDARD, VERSION, LEVEL ]",
                       "[LIST ACCESSIBILITY FEATURES HERE]",
                       "[LIST ITEMS YOU'RE WORKING TO FIX HERE]",
                       "[IT MAY HELP TO REVIEW THE OPEN ISSUES TAB",
                       "[YOUR ACCESSIBILITY EMAIL ADDRESS]", "[YOUR PHONE NUMBER]",
                       "fully accessible website experience for all users of all abilities"):
            self.assertIn(phrase, plan)
        self.assertEqual((s.W1_MIN_STOCK, s.W2_MIN_PLACEHOLDER, s.W3_MIN_SHARE, s.W3_MIN_PAGES,
                          s.F1_MIN, s.F1_MAX, s.G1_MIN_ANSWERED),
                         (10, 5, 0.30, 10, 4800, 5245, 0.80))
        self.assertEqual(s.PROBE_PATH, "/accessibility-statement/")


if __name__ == "__main__":
    unittest.main()
