"""Offline tests for district_pages.py (no network). Apache-2.0.
Made by MV2 of Munim, Inc. with AI agents."""

import csv
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import district_pages as dp  # noqa: E402

HEADER = ["SCHOOL_YEAR", "ST", "LEA_NAME", "LEAID", "WEBSITE", "SY_STATUS", "LEA_TYPE"]


def ccd_zip(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(HEADER)
    for r in rows:
        w.writerow(r)
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("ccd_lea_029_2425_w_1a_073025.csv", buf.getvalue().encode("utf-8"))
    return z.getvalue()


def saipe_line(st, dist, name, pop):
    return "%s %s %-73s%8d %8d %8d ussd24.txt 17FEB2026  " % (st, dist, name, pop, pop // 5, 10)


class FrameTests(unittest.TestCase):
    def test_parse_saipe_columns(self):
        line = saipe_line("01", "00190", "Alabaster City School District", 35276)
        self.assertEqual(line[82:90].strip(), "35276")
        self.assertEqual(dp.parse_saipe(line + "\nshort\n"), {"0100190": 35276})

    def test_host_of(self):
        self.assertEqual(dp.host_of("www.Example.k12.ny.us/home"), "example.k12.ny.us")
        self.assertEqual(dp.host_of("https://district.org"), "district.org")
        for bad in ("", "M", "N/A", "-1", "localhost"):
            self.assertEqual(dp.host_of(bad), "")

    def test_build_frame_rules(self):
        rows = [dict(zip(HEADER, r)) for r in (
            ("2024-2025", "AL", "Big District", "0100001", "www.big.org", "1", "1"),
            ("2024-2025", "AL", "Charter LEA", "0100002", "www.charter.org", "1", "7"),
            ("2024-2025", "AL", "Closed District", "0100003", "www.closed.org", "2", "1"),
            ("2024-2025", "AL", "No Site", "0100004", "", "1", "1"),
            ("2024-2025", "AL", "No SAIPE", "0100005", "www.nosaipe.org", "1", "1"),
            ("2024-2025", "AL", "Shared Small", "0100006", "www.shared.org", "1", "2"),
            ("2024-2025", "AL", "Shared Big", "0100007", "http://shared.org/", "3", "1"))]
        pops = {"0100001": 60000, "0100002": 5000, "0100003": 9000, "0100004": 9000,
                "0100006": 4000, "0100007": 12000}
        frame = dp.build_frame(rows, pops)
        self.assertEqual([r["leaid"] for r in frame], ["0100001", "0100007"])
        self.assertEqual(frame[0]["band"], "50k+")
        self.assertEqual(frame[1]["band"], "under50k")
        self.assertEqual(frame[1]["host"], "shared.org")

    def test_sample_is_fixed_and_banded(self):
        frame = [{"leaid": "%07d" % i, "band": "50k+" if i % 10 == 0 else "under50k"}
                 for i in range(200)]
        s1 = dp.sample(frame, n_big=5, n_small=7)
        s2 = dp.sample(list(reversed(frame)), n_big=5, n_small=7)
        self.assertEqual(s1, s2)
        self.assertEqual(sum(1 for r in s1 if r["band"] == "50k+"), 5)
        self.assertEqual(sum(1 for r in s1 if r["band"] == "under50k"), 7)
        keys = [dp.hash_key(r["leaid"]) for r in s1[:5]]
        self.assertEqual(keys, sorted(keys))


HOME = (b"<html><body><a href='/page/accessibility'>Accessibility</a>"
        b"<a href='https://other.org/ada'>ADA</a><script src='https://cdn.userway.org/w.js'>"
        b"</script><div class='finalsite'></div></body></html>")
PAGE = ("<html><body><p>[Your School] is built with WCAG 2.1 AA guidelines in mind. "
        "Districts with 50,000 or more students must comply by April 26, 2027. %s</p>"
        "</body></html>" % ("Accessibility matters to every family. " * 10)).encode("utf-8")


def fake_get(url):
    if url.endswith("/robots.txt"):
        return 404, url, "", b""
    if url.rstrip("/").endswith("example.org"):
        return 200, url, "text/html", HOME
    if url.endswith("/page/accessibility"):
        return 200, url, "text/html; charset=utf-8", PAGE
    return 404, url, "", b""


class CrawlTests(unittest.TestCase):
    def test_crawl_site_reads_the_page(self):
        row = {"leaid": "0100001", "name": "X", "state": "AL", "lea_type": "1",
               "population": 60000, "band": "50k+", "website": "www.example.org", "host": "x"}
        out = dp.crawl_site(row, get=fake_get, sleep=lambda s: None)
        self.assertEqual(out["home"], "ok")
        self.assertEqual(out["platform"], "finalsite")
        self.assertEqual(out["overlay"], "userway")
        self.assertEqual(out["candidates"], 1)
        self.assertEqual(out["offsite_links"], 1)
        self.assertEqual(out["page_status"], "ok")
        self.assertEqual(out["page_rank"], 0)
        self.assertTrue(out["placeholder"])
        self.assertTrue(out["students_threshold"])
        self.assertTrue(out["finalsite_line"])
        self.assertEqual(out["highest"], "2.1")
        self.assertTrue(set(dp.COLUMNS) >= set(out))

    def test_home_failure(self):
        row = {"leaid": "1", "website": "www.down.org", "band": "under50k"}
        out = dp.crawl_site(row, get=fake_get, sleep=lambda s: None)
        self.assertEqual(out["home"], "http_404")


def page_row(band, highest="", stock=False, title2=False, placeholder=False, linked=True):
    return {"band": band, "home": "ok", "candidates": 1 if linked else 0, "page_status": "ok",
            "highest": highest, "stock": stock, "title2": title2, "placeholder": placeholder}


class GradeTests(unittest.TestCase):
    def rows(self):
        rows = []
        for i in range(400):  # under 50k: 300 versioned (120 only 2.0), 20 stock, 100 Title II
            rows.append(page_row("under50k", highest=("2.0" if i < 120 else "2.1") if i < 300
                                 else "", stock=i < 20, title2=i < 100, placeholder=i < 3))
        for i in range(300):
            rows.append({"band": "under50k", "home": "ok", "candidates": 1 if i < 180 else 0,
                         "page_status": "no_link" if i >= 180 else "http_404"})
        for i in range(200):  # 50k+: 150 versioned, 120 of them 2.1 or 2.2
            rows.append(page_row("50k+", highest=("2.1" if i < 120 else "2.0") if i < 150 else "",
                                 placeholder=i < 1))
        return rows

    def test_grade(self):
        measures, preds = dp.grade(self.rows())
        self.assertEqual(measures["D1_only_2.0_of_versioned_under50k"][:3], [120, 300, 0.4])
        self.assertEqual(preds["D1"], True)
        self.assertEqual(preds["D2"], True)          # 20 of 400 = 5% < 10%
        self.assertEqual(measures["D3_newer_of_versioned_50k+"][:2], [120, 150])
        self.assertEqual(preds["D3"], True)          # 80% vs 60%
        self.assertEqual(measures["D4_placeholder_of_pages_all"][:2], [4, 600])
        self.assertEqual(preds["D4"], True)          # 4 of 600 = 0.67%
        self.assertEqual(measures["D5_linked_of_homes_under50k"][:2], [580, 700])
        self.assertEqual(preds["D5"], True)          # 82.9%
        self.assertEqual(preds["D6"], True)          # 25% >= 22.15%

    def test_grade_reads_csv_strings_and_ungraded(self):
        rows = [{k: str(v) for k, v in r.items()} for r in self.rows()[:50]]
        measures, preds = dp.grade(rows)
        self.assertEqual(set(preds.values()), {None})
        self.assertEqual(measures["D2_stock_of_pages_under50k"][:2], [20, 50])

    def test_described_by_band(self):
        d = dp.described(self.rows())
        self.assertEqual(d["by_band"]["50k+"]["pages_ok"], 200)
        self.assertEqual(d["by_band"]["under50k"]["homes_ok"], 700)
        self.assertEqual(d["by_band"]["under50k"]["placeholder"], 3)


class DryRunTests(unittest.TestCase):
    def test_dry_run_reads_no_district_page(self):
        rows = [("2024-2025", "AL", "D%d" % i, "01%05d" % i, "www.d%d.org" % i, "1", "1")
                for i in range(9000)]
        zbytes = ccd_zip(rows)
        saipe = "\n".join(saipe_line("01", "%05d" % i, "D%d" % i, 60000 if i < 900 else 8000)
                          for i in range(9000)).encode("latin-1")
        asked = []

        def fetch(url, tries=4, timeout=60):
            asked.append(url)
            return zbytes if url.endswith(".zip") else saipe

        def no_get(url):
            raise AssertionError("dry run read a page: %s" % url)
        with tempfile.TemporaryDirectory() as out:
            code = dp.main(["--out-dir", out, "--dry-run"], fetch=fetch, get=no_get,
                           sleep=lambda s: None)
            with open(os.path.join(out, "result.json"), encoding="utf-8") as f:
                result = json.load(f)
            with open(os.path.join(out, "sample.csv"), encoding="utf-8") as f:
                sample = list(csv.DictReader(f))
        self.assertEqual(code, 0)
        self.assertEqual(len(asked), 2)
        self.assertEqual(result["frame"], 9000)
        self.assertEqual(result["frame_by_band"], {"50k+": 900, "under50k": 8100})
        self.assertTrue(result["gates"]["F1_frame"])
        self.assertEqual(result["sampled_by_band"], {"50k+": 800, "under50k": 1700})
        self.assertEqual(len(sample), 2500)
        self.assertNotIn("P0_prereg_public", result["gates"])


if __name__ == "__main__":
    unittest.main()
