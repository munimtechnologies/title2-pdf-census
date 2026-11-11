# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests for nhs_frame.py and nhs_stock.py (no network: the ODS API and every website are
fakes).

python -m unittest discover -p test_nhs_stock.py
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
import nhs_stock as ns  # noqa: E402

cs, nf = ns.cs, ns.nf
PREREG = os.path.join(ROOT, *ns.PREREG_PATH.split("/"))
CHECKER = os.path.join(ROOT, "statement_template_check.py")

STATEMENT = (b"<html><head><title>Accessibility statement | A Trust</title></head><body>"
             b"<h1>Accessibility statement for A Trust</h1><p>This accessibility statement "
             b"applies to the trust website. This website is run by A Trust. We want as many "
             b"people as possible to be able to use this website.</p><h2>Compliance status</h2>"
             b"<p>This website is partially compliant with the Web Content Accessibility "
             b"Guidelines version 2.2 AA standard, due to the non-compliances listed below.</p>"
             b"<h2>Enforcement procedure</h2><p>The Equality and Human Rights Commission (EHRC) is "
             b"responsible for enforcing the accessibility regulations.</p><p>This statement was "
             b"prepared on 23 September 2020. It was last reviewed on 4 October 2025.</p>"
             b"</body></html>")
HTML = "text/html; charset=utf-8"


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
    """The ODS API by exact address; anything else raises (as a 404 would)."""

    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def __call__(self, url):
        self.calls.append(url)
        if url in self.answers:
            return self.answers[url]
        raise OSError("404 " + url)


def nosleep(_):
    return None


def name_of(i):
    return "TRUST %d NHS FOUNDATION TRUST" % i if i % 2 else "TRUST %d NHS TRUST" % i


def ord_answers(n_orgs=210, n_web=200):
    """n_orgs active RO197 trusts RX000...; trust i < n_web has a website: i < 198 on host
    tNNN.nhs.uk, 198 and 199 on t197.nhs.uk (3 trusts on one host). The list also holds an
    inactive trust and one with another primary role, which are left out."""
    entries = [{"Name": name_of(i), "OrgId": "RX%03d" % i, "Status": "Active",
                "OrgRecordClass": "RC1", "PostCode": "X", "LastChangeDate": "2026-01-01",
                "PrimaryRoleId": "RO197", "PrimaryRoleDescription": "NHS TRUST",
                "OrgLink": nf.ORD_BASE + "/organisations/RX%03d" % i} for i in range(n_orgs)]
    entries.append(dict(entries[0], OrgId="RZ001", Status="Inactive"))
    entries.append(dict(entries[0], OrgId="RZ002", PrimaryRoleId="RO57"))
    answers = {nf.LIST_URL: {"Organisations": entries}}
    for i in range(n_orgs):
        org = {"Name": name_of(i), "Status": "Active"}
        if i < n_web:
            url = "HTTPS://WWW.T%03d.NHS.UK/HOME.ASPX" % i if i < 198 else "t197.nhs.uk"
            org["Contacts"] = {"Contact": [{"type": "tel", "value": "0"},
                                           {"type": "http", "value": url}]}
        answers[nf.detail_url("RX%03d" % i)] = {"Organisation": org}
    return answers


def site_pages(n_found=160):
    return {"https://www.t%03d.nhs.uk/accessibility-statement" % j: STATEMENT
            for j in range(n_found)}


def read_checker(_url):
    with open(CHECKER, "rb") as f:
        return f.read()


def synthetic():
    rows = []
    for i in range(200):
        r = cs.blank({"host": "t%03d.nhs.uk" % i, "org_id": "RX%03d" % i, "name": name_of(i),
                      "kind": "foundation_trust" if i % 2 else "trust",
                      "organisations": 1 + (i % 3 == 0)})
        if i < 4:
            r["status"] = "http_0"
        else:
            j = i - 4
            r.update(status="ok", found_by="link", home_status="200",
                     highest="2.2" if j < 120 else "2.1",
                     statement_date="2024-01-01" if j < 70 else "2026-01-01",
                     date_source="reviewed", review_date="2024-01-01" if j < 70 else "2026-01-01",
                     text_sha256="%064x" % j, placeholder=j < 5,
                     placeholder_ids="gov-uk/email_address" if j < 5 else "")
        rows.append(r)
    return rows


class GradeTests(unittest.TestCase):
    def test_grade(self):
        m, g, p = ns.grade(synthetic())
        self.assertEqual(g, {"F1_frame": True, "G1_answered": True})
        self.assertEqual(p, {"T1": True, "T2": False, "T3": False, "T4": True})
        self.assertEqual(m["T1_found"], {"k": 196, "n": 200, "pct": 98.0})
        self.assertEqual(m["T3_wcag22_of_found"], {"k": 120, "n": 196, "pct": 61.22})
        self.assertEqual(m["T4_stale_of_dated"], {"k": 70, "n": 196, "pct": 35.71})
        self.assertEqual(m["T2_placeholder_hosts"], 5)

    def test_small_sets_are_not_graded(self):
        _, _, p = ns.grade(synthetic()[:50])
        self.assertIsNone(p["T3"])
        self.assertIsNone(p["T4"])

    def test_gate_fails_below_90_percent_answered(self):
        rows = synthetic()
        for r in rows[:21]:
            r["status"] = "http_0"
        _, g, p = ns.grade(rows)
        self.assertFalse(g["G1_answered"])
        self.assertEqual(p, {"T1": None, "T2": None, "T3": None, "T4": None})

    def test_table_round_trip(self):
        rows = synthetic()
        with tempfile.TemporaryDirectory() as d:
            t = ns.write_table(d, rows)
            with open(os.path.join(d, "hosts.csv"), encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, ns.COLUMNS)
                back = ns.typed(list(reader))
        self.assertEqual(t["rows"], 200)
        self.assertEqual(ns.grade(back), ns.grade(rows))
        self.assertEqual(ns.described(back), ns.described(rows))
        self.assertEqual(ns.described(back)["statement_year"], {"2026": 126, "2024": 70})
        self.assertEqual(ns.described(back)["found_organisations"], 261)


class OdsTests(unittest.TestCase):
    def test_website_in_each_json_shape(self):
        two = {"Organisation": {"Contacts": {"Contact": [
            {"type": "tel", "value": "1"}, {"type": "http", "value": "HTTPS://WWW.A.NHS.UK/"}]}}}
        self.assertEqual(nf.website(two), "HTTPS://WWW.A.NHS.UK/")
        self.assertEqual(nf.website({"Organisation": {"Contacts": [
            {"type": "http", "value": "x.nhs.uk"}]}}), "x.nhs.uk")
        self.assertEqual(nf.website({"Organisation": {"Contacts": {"Contact": {
            "type": "http", "value": "y.nhs.uk"}}}}), "y.nhs.uk")
        self.assertEqual(nf.website({"Organisation": {"Name": "X"}}), "")
        self.assertEqual(nf.website({"Organisation": {"Contacts": {"Contact": [
            {"type": "tel", "value": "1"}]}}}), "")

    def test_host_and_kind(self):
        self.assertEqual(nf.host_of("HTTPS://WWW.GUYSANDSTTHOMAS.NHS.UK/HOME.ASPX"),
                         "guysandstthomas.nhs.uk")
        self.assertEqual(nf.host_of("www.mft.nhs.uk"), "mft.nhs.uk")
        self.assertEqual(nf.host_of(""), "")
        self.assertEqual(nf.host_of("localhost"), "")
        self.assertEqual(nf.kind_of("MANCHESTER UNIVERSITY NHS FOUNDATION TRUST"),
                         "foundation_trust")
        self.assertEqual(nf.kind_of("BARTS HEALTH NHS TRUST"), "trust")
        self.assertEqual(nf.kind_of("SOMETHING ELSE"), "other")

    def test_collect_keeps_active_ro197_once(self):
        api = FakeApi(ord_answers(n_orgs=5, n_web=5))
        api.answers[nf.LIST_URL]["Organisations"].append(
            dict(api.answers[nf.LIST_URL]["Organisations"][1]))
        orgs, info = nf.collect(api, nosleep)
        self.assertEqual([o["org_id"] for o in orgs], ["RX000", "RX001", "RX002", "RX003", "RX004"])
        self.assertEqual(info, {"list_entries": 8})
        self.assertEqual(api.calls, [nf.LIST_URL])

    def test_build_drops_guard_word_and_records_failures(self):
        word = "S" + "aybr" + "ook"
        answers = ord_answers(n_orgs=4, n_web=4)
        del answers[nf.detail_url("RX003")]
        orgs = [{"org_id": "RX%03d" % i, "name": name_of(i)} for i in range(4)]
        orgs.append({"org_id": "RX009", "name": word.upper() + " NHS TRUST"})
        rows, dropped = nf.build(orgs, FakeApi(answers), nosleep)
        self.assertEqual(dropped, 1)
        self.assertEqual([(r["org_id"], r["host"], r["fetch"]) for r in rows],
                         [("RX000", "t000.nhs.uk", "ok"), ("RX001", "t001.nhs.uk", "ok"),
                          ("RX002", "t002.nhs.uk", "ok"), ("RX003", "", "failed:OSError")])
        self.assertEqual([r["kind"] for r in rows[:2]], ["trust", "foundation_trust"])


class FrameTests(unittest.TestCase):
    def row(self, org_id, host, fetch="ok"):
        return {"org_id": org_id, "name": "TRUST " + org_id, "kind": "trust", "host": host,
                "fetch": fetch}

    def test_build_frame(self):
        word = "s" + "aybr" + "ook"
        rows = [self.row("RB2", "shared.nhs.uk"), self.row("RB1", "Shared.nhs.uk "),
                self.row("RC1", "c.nhs.uk"), self.row("RD1", "d.nhs.uk", fetch="failed:OSError"),
                self.row("RE1", ""), self.row("RF1", word + ".nhs.uk"),
                self.row("RG1", "g.nhs.wales")]
        hosts, dropped = ns.build_frame(rows)
        self.assertEqual(dropped, 1)
        self.assertEqual([(h["host"], h["org_id"], h["organisations"]) for h in hosts],
                         [("shared.nhs.uk", "RB1", 2), ("c.nhs.uk", "RC1", 1),
                          ("g.nhs.wales", "RG1", 1)])

    def test_frame_gate(self):
        hosts = [{"host": "h%d" % i} for i in range(150)]
        info = {"organisations": 200, "fetch_failed": ["a"] * 10, "dropped": 1}
        self.assertTrue(ns.frame_gate(info, hosts, 1))
        self.assertFalse(ns.frame_gate(info, hosts, 2))
        self.assertFalse(ns.frame_gate(info, hosts[:149], 0))
        self.assertFalse(ns.frame_gate(dict(info, organisations=199), hosts, 0))
        self.assertFalse(ns.frame_gate(dict(info, fetch_failed=["a"] * 11), hosts, 0))

    def test_crawl_order_is_a_permutation(self):
        hosts = [{"host": "t%d.nhs.uk" % i} for i in range(30)]
        order = ns.crawl_order(hosts)
        self.assertEqual(sorted(h["host"] for h in order), sorted(h["host"] for h in hosts))
        self.assertEqual(order, ns.crawl_order(list(reversed(hosts))))

    def test_pinned_versions(self):
        self.assertEqual((cs.__version__, nf.__version__, cs.stc.__version__),
                         ("0.1.0", "0.1.0", "0.3.0"))
        self.assertEqual(cs.STALE_BEFORE, "2025-11-01")
        self.assertEqual(ns.COLUMNS[:6], ns.ID_COLUMNS + ["status"])
        self.assertEqual(nf.LIST_URL, "https://directory.spineservices.nhs.uk/ORD/2-0-0/"
                                      "organisations?PrimaryRoleId=RO197&Status=Active&Limit=1000")


@unittest.skipUnless(os.path.exists(PREREG), "plan not in this folder")
class RunTests(unittest.TestCase):
    def test_plan_matches_constants(self):
        with open(PREREG, encoding="utf-8") as f:
            text = " ".join(f.read().split())
        for phrase in ("T1 (at least 75% of hosts)", "T2 (at most 3 hosts)",
                       "T3 (at least 65% of read statements", "T4 (at least 30% of dated statements",
                       "before 2025-11-01", "G1 (at least 90% of hosts answered)",
                       "at least 200 trusts", "at most 10 trust records", "at most 2 rows",
                       "at least 150 distinct hosts", "at least 60 read statements",
                       "at least 60 dated statements", "`/accessibility-statement`",
                       "`/accessibility`", "`nhs-stock-2026-11`", "`RO197`"):
            self.assertIn(phrase, text)
        self.assertEqual((ns.T1_MIN_FOUND, ns.T2_MAX_PLACEHOLDER, ns.T3_MIN_22, ns.T3_MIN_PAGES,
                          ns.T4_MIN_STALE, ns.T4_MIN_PAGES, ns.G1_MIN_ANSWERED),
                         (0.75, 3, 0.65, 60, 0.30, 60, 0.90))
        self.assertEqual((ns.F1_MIN_ORGANISATIONS, ns.F1_MAX_FETCH_FAILED, ns.F1_MAX_DROPPED,
                          ns.F1_MIN_HOSTS, ns.CRAWL_SEED),
                         (200, 10, 2, 150, "nhs-stock-2026-11"))
        self.assertIsNone(cs.GUARD_RE.search(text))

    def test_nothing_requested_when_checker_differs(self):
        get, api = FakeGet(), FakeApi(ord_answers())
        with tempfile.TemporaryDirectory() as d:
            ns.main(["--out-dir", d], fetch=lambda url: b"not the release", get=get,
                    sleep=nosleep, fetch_json=api)
            with open(os.path.join(d, "result.txt"), encoding="utf-8") as f:
                text = f.read()
        self.assertIn("nhs_stock 0.1.0", text)
        self.assertIn("status: not_run", text)
        self.assertEqual((get.calls, api.calls), ([], []))

    def test_no_website_read_when_frame_too_small(self):
        get, api = FakeGet(site_pages()), FakeApi(ord_answers(n_web=120))
        with tempfile.TemporaryDirectory() as d:
            ns.main(["--out-dir", d], fetch=read_checker, get=get, sleep=nosleep, fetch_json=api)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            self.assertTrue(os.path.exists(os.path.join(d, "nhs-frame.csv")))
        self.assertEqual(result["status"], "not_run")
        self.assertFalse(result["gates"]["F1_frame"])
        self.assertEqual((result["frame"]["hosts"], result["frame"]["without_url"]), (120, 90))
        self.assertEqual(get.calls, [])
        self.assertTrue(all(u.startswith(nf.ORD_BASE) for u in api.calls))

    def test_full_run_on_fakes(self):
        get, api = FakeGet(site_pages()), FakeApi(ord_answers())
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(ns.main(["--out-dir", d], fetch=read_checker, get=get,
                                     sleep=nosleep, fetch_json=api), 0)
            with open(os.path.join(d, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(d, "nhs-frame.csv"), "rb") as f:
                frame = f.read()
            with open(os.path.join(d, "hosts.csv"), encoding="utf-8", newline="") as f:
                table = {r["host"]: r for r in csv.DictReader(f)}
        self.assertEqual(result["status"], "graded")
        self.assertEqual(result["frame"]["organisations"], 210)
        self.assertEqual((result["frame"]["rows"], result["frame"]["hosts"],
                          result["frame"]["dropped"], result["frame"]["fetch_failed"],
                          result["frame"]["without_url"]), (210, 198, 0, 0, 10))
        self.assertEqual(result["frame"]["sha256"], ns.sha256(frame))
        self.assertEqual(result["predictions"], {"T1": True, "T2": True, "T3": True, "T4": True})
        self.assertEqual(result["measures"]["T1_found"], {"k": 160, "n": 198, "pct": 80.81})
        self.assertEqual(result["measures"]["T4_stale_of_dated"],
                         {"k": 160, "n": 160, "pct": 100.0})
        self.assertEqual(result["described"]["found_by"], {"probe1": 160})
        self.assertEqual(result["described"]["found_organisations"], 160)
        self.assertEqual(len(table), 198)
        self.assertEqual((table["t197.nhs.uk"]["organisations"], table["t197.nhs.uk"]["org_id"],
                          table["t197.nhs.uk"]["status"]), ("3", "RX197", "not_found"))
        self.assertEqual(table["t000.nhs.uk"]["statement_url"],
                         "https://www.t000.nhs.uk/accessibility-statement")
        # ODS's API for the frame; the websites only on the frame's own hosts
        self.assertTrue(all(u.startswith(nf.ORD_BASE) for u in api.calls))
        self.assertEqual(sum(1 for u in api.calls if "/organisations/" in u), 210)
        self.assertTrue(all(u.startswith("https://www.t") and ".nhs.uk/" in u
                            for u in get.calls))


if __name__ == "__main__":
    unittest.main()
