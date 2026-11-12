# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for transit_pages.py (no network: the NTD table, the repository and every website
are fakes).

python -m unittest discover -p test_transit_pages.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import transit_pages as tp  # noqa: E402

sp = tp.sp
PREREG = os.path.join(HERE, *tp.PREREG_PATH.split("/"))
WORD = "s" + "aybr" + "ook"
IPA = "Independent Public Agency or Authority of Transit Service"
PAD = " Customers can ask for help with any page or document on this site." * 5
STATEMENT_2028 = ("<html><head><title>Accessibility</title></head><body><h1>Accessibility</h1>"
                  "<p>The authority follows WCAG 2.1 Level AA. Under the ADA Title II rule, special "
                  "district governments must meet it by April 26, 2028. Email access@ex.org to "
                  "report a barrier." + PAD + "</p></body></html>").encode("utf-8")
HOME = (b'<html><body><a href="/accessibility">Accessibility</a>'
        b'<a href="/rates">Rates</a></body></html>')


def rec(ntd_id, name, org_type, url, reporter="Full Reporter", city="Town", state="CA"):
    r = {"ntd_id": ntd_id, "agency_name": name, "reporter_type": reporter, "city": city,
         "state": state, "address_line_1": "1 Main St", "url": url}
    if org_type is not None:
        r["organization_type"] = org_type
    return r


NTD = json.dumps([
    rec("90026", "Second Riverside Agency", IPA, "WWW.RiversideTransit.com"),
    rec("90024", "Riverside Transit Agency", IPA,
        "https://www.riversidetransit.com/index.php/riding-the-bus", city="Riverside"),
    rec("10001", "City of X", "City, County or Local Government Unit or Department of "
        "Transportation", "http://cityx.gov"),
    rec("30001", "Rural Transit Authority", IPA, "", reporter="Rural Reporter", state="pa"),
    rec("40001", "Spaced Transit", IPA, "not a url"),
    rec("50001", "Estuary Transit District", IPA, "http://estuary.example.org",
        city="Old " + WORD.capitalize()),
    rec("60001", "Metro Transit Authority", IPA, "ex.org", reporter="Reduced Reporter",
        city="Austin", state="tx"),
    rec("70001", "Bay Transit", IPA, "http://10.0.0.1/", reporter="Group Plan Sponsor"),
    rec("80001", "State DOT", None, "http://dot.example.gov", reporter="State Reporter"),
    rec("20001", "Capital Area Transit", IPA, "http://www.cat-transit.org:8080/home",
        reporter="Reduced Asset Reporter", city="Harrisburg", state="PA"),
]).encode("utf-8")


class FakeGet:
    """Pages by exact address; addresses under a dead prefix get no answer (0); else 404."""

    def __init__(self, pages, dead=()):
        self.pages, self.dead, self.calls = pages, dead, []

    def __call__(self, url, max_bytes=3_000_000, timeout=20):
        self.calls.append(url)
        if url in self.pages:
            return 200, url, "text/html; charset=utf-8", self.pages[url]
        if any(url.startswith(d) for d in self.dead):
            return 0, url, "", b""
        return 404, url, "", b""


def no_sleep(_s):
    return None


class FrameTests(unittest.TestCase):
    def test_parse_frame(self):
        rows, info = tp.parse_frame(NTD)
        self.assertEqual([r["domain"] for r in rows],
                         ["cat-transit.org", "ex.org", "riversidetransit.com"])
        self.assertEqual([r["kind"] for r in rows], ["other", "reduced", "full"])
        self.assertEqual([r["agencies"] for r in rows], [1, 1, 2])
        self.assertEqual(info, {"source_rows": 10, "of_type": 8, "no_url": 3, "dropped": 1,
                                "eligible": 3, "agencies": 4,
                                "types": {"": 1, IPA: 8,
                                          "City, County or Local Government Unit or Department "
                                          "of Transportation": 1}})
        r = rows[2]
        self.assertEqual((r["ntd_id"], r["organization"], r["city"], r["reporter_type"]),
                         ("90024", "Riverside Transit Agency", "Riverside", "Full Reporter"))
        self.assertEqual(r["url"], "https://www.riversidetransit.com/index.php/riding-the-bus")
        self.assertEqual(rows[1]["state"], "TX")
        self.assertEqual(set(rows[0]), set(tp.FRAME_COLUMNS))
        self.assertFalse(any("Main St" in str(v) for r in rows for v in r.values()))

    def test_host_of(self):
        self.assertEqual(tp.host_of("http://www.rctc.org/"), "rctc.org")
        self.assertEqual(tp.host_of("WWW.RiversideTransit.com"), "riversidetransit.com")
        self.assertEqual(tp.host_of("https://www.riometro.org/193/Bus-Connections"), "riometro.org")
        self.assertEqual(tp.host_of("http://www.cat-transit.org:8080/home"), "cat-transit.org")
        self.assertEqual(tp.host_of({"url": "https://ex.org"}), "ex.org")
        for bad in ("", None, "not a url", "http://10.0.0.1/", "localhost", "http://[bad"):
            self.assertEqual(tp.host_of(bad), "", bad)

    def test_kind_of(self):
        self.assertEqual(tp.kind_of("Full Reporter"), "full")
        self.assertEqual(tp.kind_of("Rural Reporter"), "rural")
        self.assertEqual(tp.kind_of(" Reduced  Reporter "), "reduced")
        self.assertEqual(tp.kind_of("Reduced Asset Reporter"), "other")
        self.assertEqual(tp.kind_of(""), "other")

    def test_page_topic(self):
        for url, want in (("https://x.org/riders/paratransit-services", "paratransit"),
                          ("https://x.org/ada-paratransit", "paratransit"),
                          ("https://x.org/dial-a-ride", "paratransit"),
                          ("https://x.org/riders/ada-services", "paratransit"),
                          ("https://x.org/website-accessibility", "website"),
                          ("https://x.org/accessibility-statement", "website"),
                          ("https://x.org/Accessibility", "accessibility"),
                          ("https://x.org/about/accessibility/", "accessibility"),
                          ("https://x.org/ada", "ada"),
                          ("https://x.org/ada_compliance", "ada"),
                          ("https://x.org/canada", "other"),
                          ("https://x.org/adams-street", "other"),
                          ("", "")):
            self.assertEqual(tp.page_topic(url), want, url)

    def test_merge(self):
        out = [{"domain": "ex.org", "kind": "", "page_url": "https://ex.org/paratransit"}]
        frame = [{"domain": "ex.org", "kind": "rural", "ntd_id": "1", "agencies": 2,
                  "reporter_type": "Rural Reporter", "url": "ex.org"}]
        m = tp.merge(out, frame)
        self.assertEqual((m[0]["kind"], m[0]["agencies"], m[0]["ntd_id"], m[0]["page_topic"]),
                         ("rural", 2, "1", "paratransit"))
        self.assertEqual(out[0]["kind"], "")

    def test_sample_is_fixed_hash_order(self):
        rows = [{"domain": "d%d.org" % i} for i in range(10)]
        want = sorted(rows, key=lambda r: hashlib.sha256(
            ("transit-pages-2026-11-12" + r["domain"]).encode("utf-8")).hexdigest())[:3]
        self.assertEqual(tp.sample(rows, n=3), want)
        self.assertEqual(len(tp.sample(rows)), 10)


def base_row(domain, **kw):
    r = {c: "" for c in tp.COLUMNS}
    r.update({k: False for k in sp.BOOLS})
    r.update(domain=domain, candidates=0, state="OH", kind="other", agencies=1)
    r.update(kw)
    return r


def synthetic():
    rows = []
    for i in range(200):
        rows.append(base_row(
            "d%03d.org" % i, home="ok", home_host="h%d.org" % i, candidates=1, page_status="ok",
            page_url="https://h%d.org/accessibility" % i, wcag_any=i < 60,
            highest="2.0" if i < 15 else "2.1" if i < 50 else "",
            title2=i < 30, old_date=i < 4, date_2028=4 <= i < 6,
            kind="full" if i < 80 else "rural",
            page_topic="accessibility" if i < 100 else "paratransit"))
    for i in range(20):  # lead to d000's site and page (www and a trailing slash)
        rows.append(base_row("e%03d.org" % i, home="ok", home_host="h0.org", candidates=1,
                             page_status="ok", page_url="https://www.h0.org/accessibility/",
                             wcag_any=True, highest="2.0", old_date=True))
    for i in range(100):
        rows.append(base_row("f%03d.org" % i, home="ok", home_host="g%d.org" % i,
                             page_status="no_link"))
    for i in range(10):
        rows.append(base_row("z%03d.org" % i, home="http_0"))
    return rows


class GradeTests(unittest.TestCase):
    def test_grade_on_distinct_pages_and_homes(self):
        m, p = tp.grade(synthetic())
        self.assertEqual(m["TR1_wcag_of_pages"][:3], [60, 200, 0.3])
        self.assertEqual(m["TR2_linked_of_homes"][:3], [200, 300, 0.6667])
        self.assertEqual(m["TR3_title2_of_pages"][:3], [30, 200, 0.15])
        self.assertEqual(m["TR4_only_2.0_of_versioned"][:3], [15, 50, 0.3])
        self.assertEqual(m["TR5_dated_of_pages"][:3], [6, 200, 0.03])
        self.assertEqual(m["highest_counts"], {"2.0": 15, "2.1": 35, "2.2": 0})
        self.assertEqual(p, {"TR1": True, "TR2": True, "TR3": False, "TR4": True, "TR5": True})

    def test_small_sets_are_not_graded(self):
        _, p = tp.grade(synthetic()[:99])  # 99 pages and homes, 50 versioned: only TR4
        self.assertEqual(p, {"TR1": None, "TR2": None, "TR3": None, "TR4": True, "TR5": None})
        _, p = tp.grade(synthetic()[:39])  # 39 versioned pages: one short of MIN_VERSIONED
        self.assertEqual(set(p.values()), {None})
        m, p = tp.grade([])
        self.assertEqual(set(p.values()), {None})
        self.assertEqual(m["TR2_linked_of_homes"], [0, 0, None, None])

    def test_described(self):
        d = tp.described(synthetic())
        self.assertEqual((d["domains"], d["agencies"], d["distinct_pages"],
                          d["distinct_home_hosts"], d["domain_pages_ok"]), (330, 330, 200, 300, 220))
        self.assertEqual(d["home"], {"ok": 320, "http_0": 10})
        self.assertEqual(d["frame_kinds"], {"other": 130, "rural": 120, "full": 80})
        self.assertEqual(d["page_topic"], {"accessibility": 100, "paratransit": 100})
        self.assertEqual(d["dates"], {"none": 194, "2026-04-24": 4, "2028-04-26": 2})
        self.assertEqual(d["wcag_any"], 60)
        self.assertEqual(d["by_kind"]["full"], {"pages": 80, "wcag_any": 60, "versioned": 50,
                                                "only_2.0": 15, "title2": 30, "dated": 6})
        self.assertEqual(d["by_kind"]["rural"], {"pages": 120, "wcag_any": 0, "versioned": 0,
                                                 "only_2.0": 0, "title2": 0, "dated": 0})
        self.assertEqual(set(d["by_kind"]), {"full", "rural"})
        self.assertEqual(d["by_topic"]["paratransit"]["pages"], 100)
        self.assertEqual(d["by_topic"]["paratransit"]["wcag_any"], 0)
        self.assertEqual(d["by_state"]["OH"]["pages"], 200)

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "rows.csv")
            sp.write_csv(path, rows, tp.COLUMNS)
            with open(path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, tp.COLUMNS)
                back = sp.typed(list(reader))
        self.assertEqual(len(back), 330)
        self.assertEqual(tp.grade(back), tp.grade(rows))
        self.assertEqual(tp.described(back), tp.described(rows))


class PreregWaitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.files = {}
        for name in tp.PINNED:
            data = ("# %s\nprint('x')\n" % name).encode("utf-8")
            with open(os.path.join(self.tmp.name, name), "wb") as f:
                f.write(data)
            self.files[name] = data

    def tearDown(self):
        self.tmp.cleanup()

    def fetch_for(self, remote):
        def fetch(url, **kw):
            path = url.split("?n=")[0][len(tp.REPO_RAW):]
            if path in remote:
                return remote[path]
            raise OSError("404")
        return fetch

    def test_waits_until_all_pinned_files_match(self):
        remote = dict(self.files)
        remote[tp.PREREG_PATH] = b"# prereg\nTR1 TR2 TR3 TR4 TR5\n"
        remote["state_pages.py"] = remote["state_pages.py"].replace(b"\n", b"\r\n")
        self.assertEqual(tp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=3, pause=0), (True, 1))

    def test_refuses_a_changed_file_or_missing_prereg(self):
        remote = dict(self.files)
        remote[tp.PREREG_PATH] = b"TR5"
        remote["transit_pages.py"] = b"changed"
        self.assertEqual(tp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(remote),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))
        self.assertEqual(tp.wait_for_prereg(self.tmp.name, fetch=self.fetch_for(dict(self.files)),
                                            sleep=no_sleep, tries=2, pause=0), (False, 2))


class MainTests(unittest.TestCase):
    def make_fetch(self):
        remote = {tp.PREREG_PATH: b"# prereg TR1-TR5"}
        for name in tp.PINNED:
            with open(os.path.join(HERE, name), "rb") as f:
                remote[name] = f.read()

        def fetch(url, **kw):
            if url == tp.FRAME_URL:
                return NTD
            path = url.split("?n=")[0][len(tp.REPO_RAW):]
            if url.startswith(tp.REPO_RAW) and path in remote:
                return remote[path]
            raise OSError("404 " + url)
        return fetch

    def test_no_website_read_when_frame_is_outside_the_range(self):
        get = FakeGet({})
        with tempfile.TemporaryDirectory() as out:
            code = tp.main(["--out-dir", out], fetch=self.make_fetch(), get=get, sleep=no_sleep)
            with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertTrue(os.path.exists(os.path.join(out, "frame.csv")))
            self.assertFalse(os.path.exists(os.path.join(out, "rows.csv")))
        self.assertEqual(code, 1)
        self.assertTrue(res["status"].startswith("stopped: frame size"))
        self.assertEqual(res["gates"], {"P0_prereg_public": True, "C1_frame": False})
        self.assertEqual((res["eligible"], res["frame"]["dropped"]), (3, 1))
        self.assertEqual(res["frame"]["sha256"], hashlib.sha256(NTD).hexdigest())
        self.assertEqual(get.calls, [])

    def test_graded_run_end_to_end(self):
        saved = tp.MIN_COHORT
        tp.MIN_COHORT = 1
        try:
            get = FakeGet({"http://ex.org/": HOME, "http://ex.org/accessibility": STATEMENT_2028})
            with tempfile.TemporaryDirectory() as out:
                code = tp.main(["--out-dir", out, "--delay", "0", "--workers", "2"],
                               fetch=self.make_fetch(), get=get, sleep=no_sleep)
                with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                    res = json.load(f)
                with open(os.path.join(out, "rows.csv"), encoding="utf-8", newline="") as f:
                    rows = list(csv.DictReader(f))
                with open(os.path.join(out, "frame.csv"), encoding="utf-8") as f:
                    frame = f.read()
                with open(os.path.join(out, "result.txt"), encoding="utf-8") as f:
                    text = f.read()
        finally:
            tp.MIN_COHORT = saved
        self.assertEqual(code, 0)
        self.assertEqual(res["status"], "graded")
        self.assertEqual((res["sampled"], res["homes_ok"], res["pages_ok"]), (3, 1, 1))
        self.assertEqual(set(res["predictions"].values()), {None})
        self.assertEqual([r["domain"] for r in rows],
                         ["cat-transit.org", "ex.org", "riversidetransit.com"])
        self.assertEqual((rows[1]["page_status"], rows[1]["highest"], rows[1]["date_2028"],
                          rows[1]["kind"], rows[1]["ntd_id"], rows[1]["page_topic"]),
                         ("ok", "2.1", "True", "reduced", "60001", "accessibility"))
        self.assertEqual((rows[2]["agencies"], rows[2]["ntd_id"]), ("2", "90024"))
        self.assertEqual(rows[0]["home"], "http_404")
        self.assertEqual(res["described"]["dates"], {"2028-04-26": 1})
        self.assertEqual(res["described"]["page_topic"], {"accessibility": 1})
        self.assertNotIn("Main St", frame)
        self.assertIsNone(sp.GUARD_RE.search(frame))
        self.assertIn("predictions: TR1=None, TR2=None, TR3=None, TR4=None, TR5=None", text)
        hosts = ("cat-transit.org", "ex.org", "riversidetransit.com")
        self.assertTrue(all(any("//" + h + "/" in u or "//www." + h + "/" in u for h in hosts)
                            for u in get.calls))


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class PlanTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("TR1 (at most 35% of distinct pages name WCAG at all)",
                       "TR2 (at least 50% of distinct home sites link to an accessibility page on "
                       "the same site)",
                       "TR3 (at most 10% of distinct pages name Title II)",
                       "TR4 (of versioned pages, at most 40% name WCAG 2.0 as the highest version)",
                       "TR5 (at most 5% of distinct pages give any of the three Title II dates)",
                       "250 to 600 eligible hosts", "at most 1,000 are read",
                       "at least 100 distinct pages", "at least 150 distinct home sites",
                       "at least 40 versioned pages",
                       "`transit-pages-2026-11-12`", "`" + IPA + "`", "`" + tp.FRAME_URL + "`",
                       "within 150 minutes", "24 sites at a time",
                       "125 of 341 pages read (36.66%)", "345 of 873 home sites (39.52%)",
                       "8 of 341 pages (2.35%)", "48 of 114 versioned pages (42.11%)",
                       "2 of 341 pages (0.59%)", "815 of 1,195 home sites (68.20%)",
                       "1,053 of 1,942 (54.22%)", "436 of 2,914 reporters",
                       "435 of those 436 give a website"):
            self.assertIn(" ".join(phrase.split()), text)
        self.assertEqual((tp.TR1_MAX_WCAG, tp.TR2_MIN_LINKED, tp.TR3_MAX_TITLE2,
                          tp.TR4_MAX_ONLY_20, tp.TR5_MAX_DATED), (0.35, 0.50, 0.10, 0.40, 0.05))
        self.assertEqual((tp.MIN_PAGES, tp.MIN_HOMES, tp.MIN_VERSIONED), (100, 150, 40))
        self.assertEqual((tp.MIN_COHORT, tp.MAX_COHORT, tp.SAMPLE_N, tp.SEED, tp.FRAME_TYPE),
                         (250, 600, 1000, "transit-pages-2026-11-12", IPA))
        self.assertIsNone(tp.GUARD_RE.search(text))
        # The context figures quoted in the plan, recomputed.
        for k, n, pct in ((125, 341, "36.66"), (345, 873, "39.52"), (8, 341, "2.35"),
                          (48, 114, "42.11"), (2, 341, "0.59"), (815, 1195, "68.20"),
                          (1053, 1942, "54.22")):
            self.assertEqual("%.2f" % (100.0 * k / n), pct)

    def test_pinned_versions(self):
        self.assertEqual((tp.__version__, sp.__version__, tp.ap.__version__, tp.sc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0", "0.1.0"))
        self.assertEqual(tp.ap.MAX_TRIES, 3)
        self.assertEqual(tp.ap.MIN_TEXT, 200)


if __name__ == "__main__":
    unittest.main()
