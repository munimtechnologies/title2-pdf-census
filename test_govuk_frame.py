# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Offline tests of govuk_frame.py (every API answer comes from a fake; no network).

Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import govuk_frame as gf  # noqa: E402

ORG = "https://www.gov.uk/government/organisations/"
API = "https://www.gov.uk/api/organisations/"


def res(slug, title, status, fmt="Executive agency", abbr=None, parents=()):
    return {"id": API + slug, "title": title, "format": fmt, "web_url": ORG + slug,
            "details": {"slug": slug, "abbreviation": abbr, "govuk_status": status},
            "parent_organisations": [{"id": API + p, "web_url": ORG + p} for p in parents]}


PAGE1 = {"total": 6, "pages": 2, "page_size": 3, "current_page": 1,
         "next_page_url": "https://www.gov.uk/api/organisations?page=2",
         "results": [res("alpha-agency", "Alpha  Agency", "exempt", abbr="AA",
                         parents=("dept-b", "dept-a")),
                     res("beta-office", "Beta Office", "live"),
                     res("gamma-board", "Gamma Board", "joining", fmt="Advisory NDPB")]}
PAGE2 = {"total": 6, "current_page": 2,
         "results": [res("delta-trust", "Delta Trust", "closed"),
                     res("alpha-agency", "Alpha Agency (again)", "exempt"),
                     res("epsilon-unit", "Epsilon Unit", "exempt"),
                     res("zeta-body", "Zeta Body", "transitioning")]}


def content(otype, url):
    return {"document_type": "organisation",
            "details": {"organisation_type": otype,
                        "organisation_govuk_status": {"status": "x", "updated_at": None,
                                                      "url": url}}}


ANSWERS = {
    "https://www.gov.uk/api/organisations?page=1": PAGE1,
    "https://www.gov.uk/api/organisations?page=2": PAGE2,
    "https://www.gov.uk/api/content/government/organisations/alpha-agency":
        content("executive_agency", "https://www.Alpha-Agency.gov.uk/"),
    "https://www.gov.uk/api/content/government/organisations/epsilon-unit":
        content("other", "https://www.gov.uk/epsilon"),
    "https://www.gov.uk/api/content/government/organisations/zeta-body":
        content("executive_ndpb", None),
    # gamma-board's content item is missing: both tries fail
}


class FakeFetch:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def __call__(self, url):
        self.calls.append(url)
        if url in self.answers:
            return self.answers[url]
        raise OSError("404 " + url)


def nosleep(_):
    return None


class UnitTests(unittest.TestCase):
    def test_host_of(self):
        self.assertEqual(gf.host_of("https://www.Example.gov.uk/x"), "example.gov.uk")
        self.assertEqual(gf.host_of("example.org.uk"), "example.org.uk")
        self.assertEqual(gf.host_of(""), "")
        self.assertEqual(gf.host_of("http://localhost/"), "")

    def test_own_host(self):
        self.assertTrue(gf.own_host("activetravelengland.gov.uk"))
        self.assertFalse(gf.own_host("gov.uk"))
        self.assertFalse(gf.own_host("assets.publishing.service.gov.uk"))
        self.assertFalse(gf.own_host(""))

    def test_org_row(self):
        r = gf.org_row(PAGE1["results"][0])
        self.assertEqual(r, {"slug": "alpha-agency", "title": "Alpha Agency", "abbreviation": "AA",
                             "format": "Executive agency", "govuk_status": "exempt",
                             "web_url": ORG + "alpha-agency", "parents": "dept-a;dept-b"})

    def test_content_url(self):
        self.assertEqual(gf.content_url({"slug": "x", "web_url": ORG + "x"}),
                         "https://www.gov.uk/api/content/government/organisations/x")
        self.assertEqual(gf.content_url({"slug": "y", "web_url": ""}),
                         "https://www.gov.uk/api/content/government/organisations/y")

    def test_read_content(self):
        self.assertEqual(gf.read_content(content("executive_agency", " https://a.gov.uk ")),
                         ("executive_agency", "https://a.gov.uk"))
        self.assertEqual(gf.read_content({}), ("", ""))

    def test_get_json_retries_once(self):
        f = FakeFetch({})
        self.assertEqual(gf.get_json("https://x.example/a", f, nosleep), (None, "OSError"))
        self.assertEqual(len(f.calls), 2)


class RunTests(unittest.TestCase):
    def test_collect(self):
        orgs, info = gf.collect(FakeFetch(ANSWERS), nosleep)
        self.assertEqual(info, {"list_pages": 2, "list_total": 6})
        self.assertEqual([o["slug"] for o in orgs], ["alpha-agency", "beta-office", "gamma-board",
                                                     "delta-trust", "epsilon-unit", "zeta-body"])
        self.assertEqual(orgs[0]["title"], "Alpha Agency")

    def test_main(self):
        f = FakeFetch(ANSWERS)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(gf.main(d, fetch=f, sleep=nosleep), 0)
            with open(os.path.join(d, "govuk-frame.csv"), encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                self.assertEqual(reader.fieldnames, gf.COLUMNS)
                rows = {r["slug"]: r for r in reader}
            with open(os.path.join(d, "govuk-frame.json"), encoding="utf-8") as fh:
                info = json.load(fh)
        self.assertEqual(sorted(rows), ["alpha-agency", "epsilon-unit", "gamma-board", "zeta-body"])
        a = rows["alpha-agency"]
        self.assertEqual((a["host"], a["own_host"], a["organisation_type"], a["fetch"], a["parents"]),
                         ("alpha-agency.gov.uk", "True", "executive_agency", "ok", "dept-a;dept-b"))
        self.assertEqual((rows["epsilon-unit"]["host"], rows["epsilon-unit"]["own_host"]),
                         ("gov.uk", "False"))
        self.assertEqual((rows["zeta-body"]["url"], rows["zeta-body"]["fetch"]), ("", "ok"))
        self.assertEqual(rows["gamma-board"]["fetch"], "failed:OSError")
        self.assertEqual((info["organisations"], info["rows"], info["dropped"], info["with_url"],
                          info["own_hosts"]), (6, 4, 0, 2, 1))
        self.assertEqual(info["by_status_all"], {"exempt": 2, "closed": 1, "joining": 1, "live": 1,
                                                 "transitioning": 1})
        self.assertEqual(info["by_status"], {"exempt": 2, "joining": 1, "transitioning": 1})
        self.assertEqual(info["without_url"], ["gamma-board", "zeta-body"])
        self.assertEqual(info["not_own_host"], [["epsilon-unit", "https://www.gov.uk/epsilon"]])
        self.assertEqual(info["fetch_failed"], ["gamma-board"])
        self.assertEqual(len(info["frame_sha256"]), 64)
        # only GOV.UK's API was asked, never an organisation's own site
        self.assertTrue(all(u.startswith("https://www.gov.uk/api/") for u in f.calls))
        self.assertNotIn("https://www.gov.uk/api/content/government/organisations/beta-office",
                         f.calls)

    def test_guard_rows_are_dropped(self):
        word = "S" + "aybr" + "ook"
        answers = dict(ANSWERS)
        answers["https://www.gov.uk/api/organisations?page=1"] = {
            "total": 1, "results": [res("x-" + word.lower(), word + " Board", "exempt")]}
        rows, dropped = gf.build(gf.collect(FakeFetch(answers), nosleep)[0], FakeFetch(answers),
                                 nosleep)
        self.assertEqual((rows, dropped), ([], 1))


if __name__ == "__main__":
    unittest.main()
