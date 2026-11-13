# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered nhs-stock result from its saved tables.

Reads results/nhs-trusts/ (hosts.csv, nhs-frame.csv, nhs-frame.json, result.json and result.txt:
the output of sealed job nhs-stock-v1, unchanged). It rebuilds the frame's hosts from nhs-frame.csv
with the pinned nhs_stock.py 0.1.0, re-grades every measure, gate, prediction and described count
from hosts.csv, and checks every figure in results/nhs-trusts/NHS-STOCK-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_nhs_stock_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import collections
import csv
import hashlib
import json
import os
import sys
import unittest
from decimal import Decimal
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import nhs_stock as ns  # noqa: E402

cs = ns.cs
RES = os.path.join(ROOT, "results", "nhs-trusts")
NOTE = os.path.join(RES, "NHS-STOCK-RESULT.md")
TABLE = os.path.join(RES, "hosts.csv")
FRAME_CSV = os.path.join(RES, "nhs-frame.csv")
FRAME_JSON = os.path.join(RES, "nhs-frame.json")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED = {"T1": True, "T2": True, "T3": True, "T4": True}
STALE_BEFORE = "2025-11-01"
WELSH = ["ambulance.wales.nhs.uk", "phw.nhs.wales", "velindre-tr.wales.nhs.uk"]
# Earlier censuses read the same way (COUNCIL-STOCK-RESULT.md, GOVUK-STOCK-RESULT.md).
COUNCILS = ((284, 379, "74.93"), (191, 284, "67.25"), (105, 271, "38.75"))
CENTRAL = ((202, 283, "71.38"), (139, 202, "68.81"), (81, 191, "42.41"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def shas(data):
    return (sha(data), sha(data.replace(b"\r\n", b"\n")))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_rows():
    with open(TABLE, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), ns.typed(list(reader))


def norm(x):
    """The value as it reads back from result.json."""
    return json.loads(json.dumps(x))


def n(k):
    return format(k, ",")


def pct(k, total):
    """k of total as a percentage with two decimals, e.g. 171, 211 -> '81.04'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.info = load_json(FRAME_JSON)
        cls.header, cls.rows = load_rows()

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual(r["version"], ns.__version__)
        self.assertEqual((r["checker_version"], r["reader_version"], r["frame_version"]),
                         ("0.3.0", "0.1.0", "0.1.0"))
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]), {"P0_prereg", "P0_checker", "F1_frame", "G1_answered"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED)

    def test_pinned_files_are_the_ones_that_ran(self):
        self.assertEqual(set(self.result["files"]),
                         {"nhs_stock.py", "nhs_frame.py", "council_stock.py",
                          "statement_template_check.py", "results/nhs-trusts/PREREG.md"})
        for name, want in self.result["files"].items():
            with open(os.path.join(ROOT, *name.split("/")), "rb") as fh:
                self.assertIn(want, shas(fh.read()), name)
        self.assertEqual((ns.__version__, ns.nf.__version__, cs.__version__, ns.stc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0", "0.3.0"))

    def test_table_matches_result_json(self):
        t = self.result["table"]
        self.assertEqual(t["file"], "hosts.csv")
        with open(TABLE, "rb") as fh:
            data = fh.read()
        self.assertLess(len(data), LIMIT)
        self.assertIn(t["sha256"], shas(data))
        self.assertEqual(len(data.replace(b"\r\n", b"\n")), t["bytes"])
        self.assertEqual(self.header, ns.COLUMNS)
        self.assertEqual(len(self.rows), t["rows"])

    def test_frame_matches_result_json_and_rebuilds_the_hosts(self):
        f, info = self.result["frame"], self.info
        frame_rows, data = ns.read_frame_csv(FRAME_CSV)
        self.assertLess(len(data), LIMIT)
        self.assertIn(f["sha256"], shas(data))
        self.assertEqual(info["frame_sha256"], f["sha256"])
        self.assertEqual(len(data.replace(b"\r\n", b"\n")), f["bytes"])
        self.assertEqual(info["frame_bytes"], f["bytes"])
        self.assertEqual((len(frame_rows), info["rows"]), (f["rows"], f["rows"]))
        self.assertEqual(info["organisations"], f["organisations"])
        self.assertEqual(len(info["fetch_failed"]), f["fetch_failed"])
        self.assertEqual(len(info["without_url"]), f["without_url"])
        hosts, dropped = ns.build_frame(frame_rows)
        self.assertEqual((len(hosts), int(info["dropped"]) + dropped), (f["hosts"], f["dropped"]))
        self.assertTrue(ns.frame_gate(info, hosts, dropped))
        by_host = {r["host"]: r for r in self.rows}
        self.assertEqual(set(by_host), {h["host"] for h in hosts})
        for h in hosts:
            for c in ns.ID_COLUMNS:
                self.assertEqual(str(by_host[h["host"]][c]), str(h[c]), (h["host"], c))
        no_url = sorted(r["org_id"] for r in frame_rows if not (r.get("host") or "").strip())
        self.assertEqual(no_url, sorted(info["without_url"]))

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = ns.grade(self.rows, True)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED)
        self.assertEqual((ns.T1_MIN_FOUND, ns.T2_MAX_PLACEHOLDER, ns.T3_MIN_22, ns.T4_MIN_STALE),
                         (0.75, 3, 0.65, 0.30))
        self.assertEqual((ns.T3_MIN_PAGES, ns.T4_MIN_PAGES, ns.G1_MIN_ANSWERED), (60, 60, 0.90))
        self.assertEqual(cs.STALE_BEFORE, STALE_BEFORE)

    def test_described_counts(self):
        self.assertEqual(norm(ns.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), ns.result_text(self.result) + "\n")

    def test_no_page_text_and_no_blocked_word(self):
        for path in (TABLE, FRAME_CSV, FRAME_JSON, NOTE):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(cs.GUARD_RE.search(fh.read()), path)
        for r in self.rows:
            self.assertTrue(str(r["text_chars"]).isdigit(), r["host"])


class NoteTests(unittest.TestCase):
    """Every figure in NHS-STOCK-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.info = load_json(FRAME_JSON)
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.rows = load_rows()
        cls.found = [r for r in cls.rows if cs.ok(r)]
        cls.dated = [r for r in cls.found if r["statement_date"]]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def share(self, key):
        s = self.m[key]
        return s["k"], s["n"], pct(s["k"], s["n"])

    def test_status_and_headline(self):
        c, t = self.result["crawl"], self.result["table"]
        self.has("the %d hosts were read from %s to %s UTC on %s."
                 % (t["rows"], c["started_utc"][11:19], c["finished_utc"][11:19],
                    c["started_utc"][:10]))
        self.assertEqual(self.info["retrieved_utc"][:10], c["started_utc"][:10])
        self.assertLess(self.info["retrieved_utc"], c["started_utc"])
        self.has("The job built its frame from NHS England's ODS API on %s, after the plan was on main"
                 % self.info["retrieved_utc"][:10])
        self.assertEqual(self.result["predictions"], EXPECTED)
        self.has("**All four predictions held (T1, T2, T3, T4).**")
        k, total, p = self.share("T4_stale_of_dated")
        self.has("**%d of the %d dated statements (%s%%) carry a date before 1 November 2025**"
                 % (k, total, p))
        self.has("against 105 of 271 (38.75%) for the UK's principal councils")
        self.has("and 81 of 191 (42.41%) for UK government organisations with their own website")
        old = sum(1 for r in self.dated if r["statement_date"] < "2024-01-01")
        self.has("%d of the %d dated statements (%s%%) carry a date before 2024."
                 % (old, len(self.dated), pct(old, len(self.dated))))
        k1, n1, p1 = self.share("T1_found")
        k3, n3, p3 = self.share("T3_wcag22_of_found")
        self.has("a statement was found on %d of the %d hosts (%s%%), and %d of the %d (%s%%) name "
                 "WCAG 2.2 as the highest version." % (k1, n1, p1, k3, n3, p3))
        self.assertGreater(Decimal(p1), Decimal("74.93"))
        self.assertGreater(Decimal(p3), Decimal("68.81"))

    def test_frame(self):
        i, f = self.info, self.result["frame"]
        bk = i["by_kind"]
        self.assertEqual(i["list_entries"], i["organisations"])
        self.has("NHS England's ODS API listed %d active organisations with the primary role RO197 "
                 "(\"NHS TRUST\") on %s (SHA-256 of the list `%s`): %d foundation trusts and %d "
                 "trusts." % (i["organisations"], i["retrieved_utc"][:10],
                              i["organisations_sha256"][:12], bk["foundation_trust"], bk["trust"]))
        self.assertEqual(i["rows"], i["organisations"])
        self.has("All %d records were read (%d could not be read); %d give no website and are counted "
                 "in the frame file but not read, and %d rows were dropped by the publishing tool's "
                 "blocked word." % (i["rows"], len(i["fetch_failed"]), len(i["without_url"]),
                                    f["dropped"]))
        self.assertEqual(i["with_url"], f["hosts"])
        self.assertEqual(i["hosts_shared"], {})
        self.has("The other %d trusts make %d distinct hosts; no host is shared by two trusts."
                 % (i["with_url"], f["hosts"]))
        self.has("`nhs-frame.csv` (`%s`, %s bytes)" % (f["sha256"][:12], n(f["bytes"])))
        welsh = sorted(r["host"] for r in self.rows if "wales" in r["host"])
        self.assertEqual(welsh, WELSH)
        self.assertEqual(len(welsh), 3)
        self.has("Three of the hosts read belong to Welsh trusts (%s, %s, %s)" % tuple(welsh))
        g = self.m["G1_answered"]
        self.has("F1 held (%d trusts read from the list, %d records unread, %d rows dropped, %d "
                 "hosts); G1 held: %d of the %d hosts answered (%s%%)."
                 % (f["organisations"], f["fetch_failed"], f["dropped"], f["hosts"], g["k"],
                    g["n"], pct(g["k"], g["n"])))

    def test_prediction_table(self):
        for key in ("T1_found", "T3_wcag22_of_found", "T4_stale_of_dated"):
            k, total, p = self.share(key)
            self.has("| %s of %s (%s%%) | yes |" % (n(k), n(total), p))
        self.assertEqual(self.m["T2_placeholder_hosts"], len(self.d["placeholder_hosts"]))
        self.has("| %d (%s) | yes |" % (self.m["T2_placeholder_hosts"],
                                        ", ".join(self.d["placeholder_hosts"])))

    def test_not_found(self):
        st = self.d["status"]
        missing = [r for r in self.rows if not cs.ok(r)]
        self.assertEqual(len(missing), sum(v for k, v in st.items() if k != "ok"))
        self.assertEqual(set(st), {"ok", "not_found", "robots", "http_0"})
        self.has("The reader found no statement on %d hosts. %d refused it through robots.txt and "
                 "%d did not answer at all. The other %d answered, but no statement was found"
                 % (len(missing), st["robots"], st["http_0"], st["not_found"]))
        nf = [r for r in self.rows if r["status"] == "not_found"]
        h403 = [r for r in nf if r["home_status"] == "403"]
        self.assertEqual({r["home_status"] for r in nf}, {"200", "403"})
        self.assertEqual(len(h403), self.d["home_status"]["403"])   # no 403 home page had one
        self.has("%d of those %d home pages answered 403 (Forbidden)" % (len(h403), len(nf)))
        blocked = st["robots"] + st["http_0"] + len(h403)
        rest = len(self.rows) - blocked
        self.has("Leaving out the %d hosts that refused or blocked the reader (robots.txt, no "
                 "answer, or a 403 home page), a statement was found on %d of %d (%s%%)."
                 % (blocked, len(self.found), rest, pct(len(self.found), rest)))

    def test_statements_found(self):
        d = self.d
        hi, src, by = d["found_highest"], d["date_source"], d["found_by"]
        self.assertEqual(set(hi), {"2.2", "2.1", ""})
        self.has("The %d statements cover %d trusts. %d use GOV.UK's compliance sentence."
                 % (len(self.found), d["found_organisations"], d["found_gov_uk_wording"]))
        self.has("%d name WCAG 2.2 as the highest version, %d name 2.1 and %d give no WCAG version "
                 "the reader could take." % (hi["2.2"], hi["2.1"], hi[""]))
        self.has("%d give no date the reader could take; of the %d dated, %d take their date from a "
                 "\"last reviewed\" or \"updated\" line and %d from a \"prepared\" or \"published\" "
                 "line." % (d["found_no_date"], len(self.dated), src["reviewed"], src["prepared"]))
        mse = sorted(r["org_id"] for r in self.found
                     if urlsplit(r["statement_url"]).hostname == "www.mse.nhs.uk"
                     and r["other_host"])
        self.assertEqual(mse, ["RDD", "RQ8"])
        names = {r["org_id"]: r["name"] for r in self.found}
        self.assertIn("BASILDON AND THURROCK", names["RDD"])
        self.assertIn("MID ESSEX", names["RQ8"])
        self.has("%d statements are served on another host than the one ODS names; for example, the "
                 "hosts of both Basildon and Thurrock and Mid Essex lead to one statement on "
                 "mse.nhs.uk." % d["found_other_host"])
        self.has("The %d pages hold %d distinct texts." % (len(self.found), d["distinct_texts"]))
        self.assertEqual(set(by), {"link", "probe1", "probe2"})
        self.has("%d were found through the home page's link, %d one hop further, and %d at a fixed "
                 "address (%d at /accessibility-statement, %d at /accessibility)."
                 % (by["link"], by.get("hub", 0), by["probe1"] + by["probe2"], by["probe1"],
                    by["probe2"]))
        years = ", ".join("%s (%d)" % kv for kv in sorted(d["statement_year"].items()))
        self.has("By year of the statement's date: %s." % years)
        self.assertEqual(d["placeholder_hosts"],
                         ["hpft.nhs.uk", "lincolnshirecommunityhealthservices.nhs.uk"])
        ph = {r["host"]: r["placeholder_ids"] for r in self.found if r["placeholder"]}
        self.assertEqual(ph, {"hpft.nhs.uk": "gov-uk/example_document",
                              "lincolnshirecommunityhealthservices.nhs.uk": "gov-uk/insert_one_of"})
        self.has("hpft.nhs.uk (rule gov-uk/example_document, the sample's \"[example of "
                 "non-essential document]\")")
        self.has("lincolnshirecommunityhealthservices.nhs.uk (rule gov-uk/insert_one_of, the "
                 "sample's \"[insert one of the following ...]\")")

    def test_by_kind(self):
        kinds = self.d["by_kind"]
        self.assertEqual(set(kinds), {"foundation_trust", "trust"})
        for k in sorted(kinds):
            v = kinds[k]
            self.has("| %s | %d | %d | %d | %d | %d |"
                     % (k, v["hosts"], v["found"], v["wcag22"], v["dated"], v["stale"]))
        self.assertEqual(sum(v["hosts"] for v in kinds.values()), len(self.rows))
        ft, t = kinds["foundation_trust"], kinds["trust"]
        self.has("Among foundation trusts, %d of %d dated statements (%s%%) carry a date before 1 "
                 "November 2025; among other trusts, %d of %d (%s%%)."
                 % (ft["stale"], ft["dated"], pct(ft["stale"], ft["dated"]),
                    t["stale"], t["dated"], pct(t["stale"], t["dated"])))

    def test_found_after_the_run(self):
        groups = collections.defaultdict(list)
        for r in self.found:
            groups[r["text_sha256"]].append(r["host"])
        dups = [hs for hs in groups.values() if len(hs) > 1]
        self.assertEqual(sorted(len(hs) for hs in dups), [2, 2, 2, 2, 2])
        self.has("Five statements are each served for two listed trusts.")
        texts = {}
        for r in self.dated:
            texts[r["text_sha256"]] = r["statement_date"]
        old = sum(1 for v in texts.values() if v < STALE_BEFORE)
        self.has("Counted once per distinct text, %d of %d dated texts (%s%%) carry a date before 1 "
                 "November 2025." % (old, len(texts), pct(old, len(texts))))
        census_day = self.result["crawl"]["started_utc"][:10]
        later = sorted((r for r in self.dated if r["statement_date"] > census_day),
                       key=lambda r: r["host"])
        self.assertEqual([(r["host"], r["statement_date"]) for r in later],
                         [("phw.nhs.wales", "2027-03-31"), ("whittington.nhs.uk", "2026-11-30")])
        self.assertTrue(all(r["review_date"] == r["statement_date"] for r in later))
        self.has("%d statement dates are later than the census (phw.nhs.wales: 2027-03-31; "
                 "whittington.nhs.uk: 2026-11-30)." % len(later))
        kept = [r for r in self.dated if r["statement_date"] <= census_day]
        k = sum(1 for r in kept if cs.stale(r))
        self.assertEqual(k, self.m["T4_stale_of_dated"]["k"])
        self.has("counted as undated, the two would leave %d of %d (%s%%)."
                 % (k, len(kept), pct(k, len(kept))))

    def test_comparison(self):
        for k, total, p in COUNCILS + CENTRAL:
            self.assertEqual(pct(k, total), p)
        rows = (("Statement found", "T1_found", " hosts"),
                ("WCAG 2.2 the highest version", "T3_wcag22_of_found", ""),
                ("Dated before 1 November 2025", "T4_stale_of_dated", ""))
        for (label, key, unit), a, b in zip(rows, COUNCILS, CENTRAL):
            k, total, p = self.share(key)
            self.has("| %s | %d of %d%s (%s%%) | %d of %d%s (%s%%) | %d of %d%s (%s%%) |"
                     % (label, a[0], a[1], unit, a[2], b[0], b[1], unit, b[2], k, total, unit, p))
        self.has("| Template placeholder | 1 host | 1 host | %d hosts |"
                 % self.m["T2_placeholder_hosts"])

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(cs.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
