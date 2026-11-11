# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered govuk-stock result from its saved tables.

Reads results/govuk-orgs/ (hosts.csv, govuk-frame.csv, govuk-frame.json, result.json and
result.txt: the output of sealed job govuk-stock-v1, unchanged). It rebuilds the frame's hosts
from govuk-frame.csv with the pinned govuk_stock.py 0.1.0, re-grades every measure, gate,
prediction and described count from hosts.csv, and checks every figure in
results/govuk-orgs/GOVUK-STOCK-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_govuk_stock_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import collections
import csv
import hashlib
import io
import json
import os
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import govuk_stock as gs  # noqa: E402

cs = gs.cs
RES = os.path.join(ROOT, "results", "govuk-orgs")
NOTE = os.path.join(RES, "GOVUK-STOCK-RESULT.md")
TABLE = os.path.join(RES, "hosts.csv")
FRAME_CSV = os.path.join(RES, "govuk-frame.csv")
FRAME_JSON = os.path.join(RES, "govuk-frame.json")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED = {"O1": False, "O2": True, "O3": False, "O4": True}
STALE_BEFORE = "2025-11-01"


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
        return list(reader.fieldnames), gs.typed(list(reader))


def norm(x):
    """The value as it reads back from result.json."""
    return json.loads(json.dumps(x))


def n(k):
    return format(k, ",")


def pct(k, total):
    """k of total as a percentage with two decimals, e.g. 202, 283 -> '71.38'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.info = load_json(FRAME_JSON)
        cls.header, cls.rows = load_rows()

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual(r["version"], gs.__version__)
        self.assertEqual((r["checker_version"], r["reader_version"], r["frame_version"]),
                         ("0.3.0", "0.1.0", "0.1.0"))
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]), {"P0_prereg", "P0_checker", "F1_frame", "G1_answered"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED)

    def test_pinned_files_are_the_ones_that_ran(self):
        self.assertEqual(set(self.result["files"]),
                         {"govuk_stock.py", "govuk_frame.py", "council_stock.py",
                          "statement_template_check.py", "results/govuk-orgs/PREREG.md"})
        for name, want in self.result["files"].items():
            with open(os.path.join(ROOT, *name.split("/")), "rb") as fh:
                self.assertIn(want, shas(fh.read()), name)
        self.assertEqual((gs.__version__, gs.gf.__version__, cs.__version__, gs.stc.__version__),
                         ("0.1.0", "0.1.0", "0.1.0", "0.3.0"))

    def test_table_matches_result_json(self):
        t = self.result["table"]
        self.assertEqual(t["file"], "hosts.csv")
        with open(TABLE, "rb") as fh:
            data = fh.read()
        self.assertLess(len(data), LIMIT)
        self.assertIn(t["sha256"], shas(data))
        self.assertEqual(len(data.replace(b"\r\n", b"\n")), t["bytes"])
        self.assertEqual(self.header, gs.COLUMNS)
        self.assertEqual(len(self.rows), t["rows"])

    def test_frame_matches_result_json_and_rebuilds_the_hosts(self):
        f, info = self.result["frame"], self.info
        frame_rows, data = gs.read_frame_csv(FRAME_CSV)
        self.assertIn(f["sha256"], shas(data))
        self.assertEqual(info["frame_sha256"], f["sha256"])
        self.assertEqual(len(data.replace(b"\r\n", b"\n")), f["bytes"])
        self.assertEqual(info["frame_bytes"], f["bytes"])
        self.assertEqual((len(frame_rows), info["rows"]), (f["rows"], f["rows"]))
        self.assertEqual(info["organisations"], f["organisations"])
        self.assertEqual(len(info["fetch_failed"]), f["fetch_failed"])
        hosts, dropped = gs.build_frame(frame_rows)
        self.assertEqual((len(hosts), int(info["dropped"]) + dropped), (f["hosts"], f["dropped"]))
        self.assertTrue(gs.frame_gate(info, hosts, dropped))
        self.assertEqual(len(hosts), info["own_hosts"])
        by_host = {r["host"]: r for r in self.rows}
        self.assertEqual(set(by_host), {h["host"] for h in hosts})
        for h in hosts:
            for c in gs.ID_COLUMNS:
                self.assertEqual(str(by_host[h["host"]][c]), str(h[c]), (h["host"], c))
        self.assertEqual(sum(r["organisations"] for r in self.rows), info["own_host_rows"])
        self.assertEqual(sum(1 for h in hosts if h["organisations"] > 1), len(info["hosts_shared"]))

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = gs.grade(self.rows, True)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED)
        self.assertEqual((gs.O1_MIN_FOUND, gs.O2_MAX_PLACEHOLDER, gs.O3_MIN_22, gs.O4_MIN_STALE),
                         (0.75, 3, 0.70, 0.25))
        self.assertEqual(cs.STALE_BEFORE, STALE_BEFORE)

    def test_described_counts(self):
        self.assertEqual(norm(gs.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), gs.result_text(self.result) + "\n")

    def test_no_page_text_and_no_blocked_word(self):
        for path in (TABLE, FRAME_CSV, FRAME_JSON, NOTE):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(cs.GUARD_RE.search(fh.read()), path)
        for r in self.rows:
            self.assertTrue(str(r["text_chars"]).isdigit(), r["host"])


class NoteTests(unittest.TestCase):
    """Every figure in GOVUK-STOCK-RESULT.md, checked against the data."""

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
        self.assertEqual(self.result["predictions"], EXPECTED)
        self.has("**Two of the four predictions held (O2, O4); O1 and O3 failed.**")
        k, total, p = self.share("O4_stale_of_dated")
        self.has("**%d of the %d dated statements (%s%%) carry a date before 1 November 2025**"
                 % (k, total, p))
        k1, n1, p1 = self.share("O1_found")
        k3, n3, p3 = self.share("O3_wcag22_of_found")
        self.has("A statement was found on %d of the %d own hosts (%s%%), short of the predicted "
                 "75%%, and %d of the %d (%s%%) name WCAG 2.2 as the highest version, just short "
                 "of the predicted 70%%" % (k1, n1, p1, k3, n3, p3))

    def test_frame(self):
        i, f = self.info, self.result["frame"]
        self.has("GOV.UK's organisations API listed %s organisations on %s (SHA-256 of the list "
                 "`%s`)." % (n(i["organisations"]), i["retrieved_utc"][:10],
                             i["organisations_sha256"][:12]))
        bs = i["by_status"]
        self.assertEqual(sum(bs.values()), i["rows"])
        self.has("%d of them have the status exempt (%d), joining (%d) or transitioning (%d); %d of "
                 "those have a website address in their content item, %d content item could not "
                 "be read (%s), and %d rows were dropped by the publishing tool's blocked word."
                 % (i["rows"], bs["exempt"], bs["joining"], bs["transitioning"], i["with_url"],
                    len(i["fetch_failed"]), ", ".join(i["fetch_failed"]), f["dropped"]))
        self.has("The own hosts of %d organisations make %d distinct hosts; %d hosts are shared by "
                 "several organisations." % (i["own_host_rows"], i["own_hosts"],
                                             len(i["hosts_shared"])))
        self.has("`govuk-frame.csv` (`%s`, %s bytes)" % (f["sha256"][:12], n(f["bytes"])))
        g = self.m["G1_answered"]
        self.has("F1 held (%s organisations, %d content item unread, %d rows dropped, %d hosts); G1 "
                 "held: %d of the %d hosts answered (%s%%)."
                 % (n(f["organisations"]), f["fetch_failed"], f["dropped"], f["hosts"], g["k"],
                    g["n"], pct(g["k"], g["n"])))

    def test_prediction_table(self):
        for key, held in (("O1_found", "no"), ("O3_wcag22_of_found", "no"),
                          ("O4_stale_of_dated", "yes")):
            k, total, p = self.share(key)
            self.has("| %s of %s (%s%%) | %s |" % (n(k), n(total), p, held))
        self.assertEqual(self.m["O2_placeholder_hosts"], len(self.d["placeholder_hosts"]))
        self.has("| %d (%s) | yes |" % (self.m["O2_placeholder_hosts"],
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
        others = [r for r in nf if r["home_status"] not in ("200", "403")]
        self.assertEqual({r["home_status"] for r in others}, {"202", "405", "502"})
        self.assertEqual(len(h403), self.d["home_status"]["403"])   # no 403 home page had one
        self.has("%d of those %d home pages answered 403 (Forbidden)" % (len(h403), len(nf)))
        self.has("and %d more answered 202, 405 or 502." % len(others))
        blocked = st["robots"] + st["http_0"] + len(h403)
        rest = len(self.rows) - blocked
        self.has("Leaving out the %d hosts that refused or blocked the reader (robots.txt, no "
                 "answer, or a 403 home page), a statement was found on %d of %d (%s%%)."
                 % (blocked, len(self.found), rest, pct(len(self.found), rest)))

    def test_statements_found(self):
        d = self.d
        hi, src, by = d["found_highest"], d["date_source"], d["found_by"]
        self.assertEqual(set(hi), {"2.2", "2.1", ""})
        self.has("The %d statements cover %d organisations. %d use GOV.UK's compliance sentence."
                 % (len(self.found), d["found_organisations"], d["found_gov_uk_wording"]))
        self.has("%d name WCAG 2.2 as the highest version, %d name 2.1 and %d name no WCAG version."
                 % (hi["2.2"], hi["2.1"], hi[""]))
        self.has("%d give no date the reader could take; of the %d dated, %d take their date from a "
                 "\"last reviewed\" or \"updated\" line and %d from a \"prepared\" or \"published\" "
                 "line." % (d["found_no_date"], len(self.dated), src["reviewed"], src["prepared"]))
        ukri = [r for r in self.found if r["host"] == "ukri.org"][0]
        linked = [r for r in self.found if r["text_sha256"] == ukri["text_sha256"]
                  and r["other_host"]]
        self.has("%d statements are served on another host than the one GOV.UK names; for example, "
                 "%d research council hosts link to UK Research and Innovation's one statement on "
                 "ukri.org." % (d["found_other_host"], len(linked)))
        self.has("The %d pages hold %d distinct texts." % (len(self.found), d["distinct_texts"]))
        self.assertEqual(set(by), {"link", "hub", "probe1", "probe2"})
        self.has("%d were found through the home page's link, %d one hop further, and %d at a fixed "
                 "address (%d at /accessibility-statement, %d at /accessibility)."
                 % (by["link"], by["hub"], by["probe1"] + by["probe2"], by["probe1"], by["probe2"]))
        years = ", ".join("%s (%d)" % kv for kv in sorted(d["statement_year"].items()))
        self.has("By year of the statement's date: %s." % years)
        self.assertEqual(list(d["placeholder_ids"]), ["gov-uk/insert_one_of"])
        self.has("One statement keeps a placeholder: %s still carries" % d["placeholder_hosts"][0])
        self.has("(rule %s)" % list(d["placeholder_ids"])[0])

    def test_by_type(self):
        types = self.d["by_type"]
        for t in sorted(types):
            v = types[t]
            self.has("| %s | %d | %d | %d | %d | %d |"
                     % (t, v["hosts"], v["found"], v["wcag22"], v["dated"], v["stale"]))
        self.assertEqual(sum(v["hosts"] for v in types.values()), len(self.rows))
        e, o = types["executive_ndpb"], types["other"]
        self.has("Among executive non-departmental public bodies, %d of %d dated statements (%s%%) "
                 "carry a date before 1 November 2025; among hosts GOV.UK types as \"other\", %d "
                 "of %d (%s%%)." % (e["stale"], e["dated"], pct(e["stale"], e["dated"]),
                                    o["stale"], o["dated"], pct(o["stale"], o["dated"])))

    def test_found_after_the_run(self):
        groups = collections.defaultdict(list)
        for r in self.found:
            groups[r["text_sha256"]].append(r["host"])
        dups = sorted((hs for hs in groups.values() if len(hs) > 1), key=len, reverse=True)
        self.assertEqual([len(hs) for hs in dups], [7, 3, 2])
        self.assertIn("ukri.org", dups[0])
        self.assertIn("nmrn.org.uk", dups[1])
        self.has("(seven UK Research and Innovation hosts, three Royal Navy museum hosts)")
        texts = {}
        for r in self.dated:
            texts[r["text_sha256"]] = r["statement_date"]
        old = sum(1 for v in texts.values() if v < STALE_BEFORE)
        self.has("Counted once per distinct text, %d of %d dated texts (%s%%) carry a date before 1 "
                 "November 2025." % (old, len(texts), pct(old, len(texts))))
        census_day = self.result["crawl"]["started_utc"][:10]
        later = [r for r in self.dated if r["statement_date"] > census_day]
        self.assertEqual([r["review_date"] == r["statement_date"] for r in later], [True])
        self.has("%d statement date is later than the census: the page says" % len(later))
        kept = [r for r in self.dated if r["statement_date"] <= census_day]
        k = sum(1 for r in kept if cs.stale(r))
        self.assertEqual(k, self.m["O4_stale_of_dated"]["k"])
        self.has("counted as undated, it would be %d of %d (%s%%)." % (k, len(kept),
                                                                       pct(k, len(kept))))

    def test_council_comparison_row(self):
        k, total, p = self.share("O1_found")
        self.has("| %d of %d hosts (%s%%) |" % (k, total, p))

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(cs.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
