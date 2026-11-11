# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered council-agree result from its saved tables.

Reads results/uk-councils/agree/ (agree.csv, accessibility-build-councils.csv, result.json and
result.txt: the output of sealed job council-agree-v1, unchanged) and MV2's November council table
results/uk-councils/hosts.csv. It rebuilds the council-by-council join from the two tables with
the pinned council_agree.py 0.1.0, re-grades every measure, gate, prediction and described count,
and checks every figure in results/uk-councils/AGREE-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_council_agree_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import json
import os
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import council_agree as ca  # noqa: E402
import council_stock as cs  # noqa: E402

RES = os.path.join(ROOT, "results", "uk-councils")
OUT = os.path.join(RES, "agree")
NOTE = os.path.join(RES, "AGREE-RESULT.md")
TABLE = os.path.join(OUT, "agree.csv")
A_COPY = os.path.join(OUT, ca.A_FILE)
B_TABLE = os.path.join(RES, "hosts.csv")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED = {"H1": True, "H2": True, "H3": True, "H4": True}
REREAD_COLS = ("reread", "reread_status", "robots_blocked", "retried", "answered_html",
               "final_is_ours", "is_statement", "links_to_ours", "reread_chars",
               "reread_highest", "reread_statement_date")
MEASURED = "2026-09-02"            # Accessibility.build's measurement date
STALE_BEFORE = "2025-11-01"        # council-stock's N4 line


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
        return list(reader.fieldnames), ca.typed(list(reader))


def norm(x):
    """The value as it reads back from result.json."""
    return json.loads(json.dumps(x))


def n(k):
    return format(k, ",")


def pct(k, total):
    """k of total as a percentage with two decimals, e.g. 13, 17 -> '76.47'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def groups(rows):
    both = [r for r in rows if r["both_found"]]
    out = {}
    for g in ca.GROUPS:
        bs = [r for r in both if r["a_group"] == g]
        diff = [r for r in bs if not r["same_url"]]
        out[g] = {"rows": [r for r in rows if r["a_group"] == g], "both": bs, "diff": diff,
                  "same": [r for r in bs if r["same_url"]],
                  "pages": [r for r in diff if r["answered_html"]]}
    return out


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(OUT, "result.json"))
        cls.header, cls.rows = load_rows()

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual(r["version"], ca.__version__)
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]), {"P0_prereg", "P0_pins", "F1_mv2_table",
                                           "A1_their_table", "G1_both_found"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED)

    def test_pinned_scripts_are_the_ones_that_ran(self):
        for name in ("council_agree.py", "council_stock.py", "statement_template_check.py"):
            with open(os.path.join(ROOT, name), "rb") as fh:
                self.assertIn(self.result["files"][name], shas(fh.read()), name)
        self.assertEqual((cs.__version__, cs.stc.__version__), ("0.1.0", "0.3.0"))

    def test_mv2_table_is_the_registered_one(self):
        _, ok = ca.read_b(B_TABLE)
        self.assertTrue(ok)
        with open(B_TABLE, "rb") as fh:
            self.assertIn(self.result["files"]["results/uk-councils/hosts.csv"], shas(fh.read()))

    def test_table_matches_result_json(self):
        t = self.result["table"]
        self.assertEqual(t["file"], "agree.csv")
        with open(TABLE, "rb") as fh:
            data = fh.read()
        self.assertLess(len(data), LIMIT)
        self.assertIn(t["sha256"], shas(data))
        self.assertEqual(len(data.replace(b"\r\n", b"\n")), t["bytes"])
        self.assertEqual(self.header, ca.COLUMNS)
        self.assertEqual(len(self.rows), t["rows"])

    def test_their_copy_matches_result_json(self):
        a = self.result["a_table"]
        with open(A_COPY, "rb") as fh:
            data = fh.read()
        self.assertIn(a["copy_sha256"], shas(data))
        self.assertEqual(a["dropped"], 0)
        self.assertEqual(a["copy_sha256"], a["sha256"])   # the copy is their table, byte for byte
        rows, ok, dropped = ca.parse_a(data.replace(b"\r\n", b"\n"))
        self.assertTrue(ok)
        self.assertEqual((len(rows), dropped), (a["rows"], 0))

    def test_join_rebuilt_from_the_two_tables(self):
        with open(A_COPY, "rb") as fh:
            a_rows, _, _ = ca.parse_a(fh.read().replace(b"\r\n", b"\n"))
        b_rows, _ = ca.read_b(B_TABLE)
        joined = ca.match(a_rows, b_rows)
        self.assertEqual(len(joined), len(self.rows))
        for want, got in zip(joined, self.rows):
            for c in ca.COLUMNS:
                if c in REREAD_COLS:
                    continue
                self.assertEqual(str(got[c]), str(want[c]), (got["a_host"], c))
            self.assertEqual(got["reread"], want["both_found"] and not want["same_url"],
                             got["a_host"])

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = ca.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED)

    def test_described_counts(self):
        b_rows, _ = ca.read_b(B_TABLE)
        self.assertEqual(norm(ca.described(self.rows, b_rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(OUT, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), ca.result_text(self.result) + "\n")

    def test_no_page_text_and_no_blocked_word(self):
        for path in (TABLE, A_COPY, NOTE):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(cs.GUARD_RE.search(fh.read()), path)
        for r in self.rows:
            self.assertIsInstance(r["reread_chars"], int)


class NoteTests(unittest.TestCase):
    """Every figure in AGREE-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(OUT, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.rows = load_rows()
        cls.g = groups(cls.rows)
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def test_status_and_times(self):
        c, a = self.result["crawl"], self.result["a_table"]
        self.has("(%s to %s UTC on %s)" % (c["started_utc"][11:19], c["finished_utc"][11:19],
                                            c["started_utc"][:10]))
        self.has("**All four predictions held (H1, H2, H3, H4).**")
        self.has("fetched at %s UTC (%s rows, %s bytes, SHA-256 `%s`)"
                 % (a["fetched_utc"][11:19], n(a["rows"]), n(a["bytes"]), a["sha256"][:12]))

    def test_prediction_table(self):
        self.assertEqual((ca.H1_MIN_DIFF, ca.H2_MIN_SAME, ca.H3_MIN_LINK, ca.H4_MIN_DATED),
                         (0.60, 0.80, 0.60, 0.90))
        for key in ("H1_low_diff", "H2_full_same", "H3_low_links_to_ours", "H4_full_same_dated"):
            s = self.m[key]
            self.assertEqual(pct(s["k"], s["n"]), "%.2f" % s["pct"])
            self.has("| %s of %s (%s%%) | yes |" % (n(s["k"]), n(s["n"]), pct(s["k"], s["n"])))

    def test_matching(self):
        mt, st = self.d["match"], self.d["b_status_of_matched"]
        self.has("%d rows matched an MV2 host (%d by host, %d by the scored address's host) and %d "
                 "did not" % (self.m["matched"], mt["host"], mt["url_host"], mt["none"]))
        self.assertEqual(self.m["matched"], mt["host"] + mt["url_host"])
        self.has("Both censuses found a statement for %d councils, above G1's %d."
                 % (self.m["G1_both_found"], ca.G1_MIN_BOTH))
        self.has("For the other %d matched rows MV2's November reader found no statement (%d) or "
                 "was refused by robots.txt (%d)."
                 % (st["not_found"] + st["robots"], st["not_found"], st["robots"]))
        self.has("MV2's census found %d statements on hosts that have no row in Accessibility.build's "
                 "table" % self.d["b_ok_not_in_a"])
        v = self.d["a_via"]
        self.has("%d of Accessibility.build's %d rows were found through a footer link and %d at a "
                 "common path" % (v["footer-link"], self.m["A_rows"], v["common-path"]))

    def test_groups_and_verdicts(self):
        ag, av = self.d["a_group"], self.d["a_verdict"]
        self.assertEqual((ag["low"], ag["partial"], ag["full"]),
                         (av["not-compliant"], av["missing-information"], av["compliant"]))
        for r in self.rows:
            self.assertEqual(r["a_verdict"], {"low": "not-compliant", "partial":
                                              "missing-information", "full": "compliant"}
                             [r["a_group"]], r["a_host"])
        self.has("%d rows score 0 to 3 of 8 (\"not-compliant\"), %d score 4 to 7 "
                 "(\"missing-information\") and %d score 8 of 8 (\"compliant\")"
                 % (ag["low"], ag["partial"], ag["full"]))

    def test_low_group(self):
        g = self.g["low"]
        rows, both, diff, same, pages = g["rows"], g["both"], g["diff"], g["same"], g["pages"]
        others = [r for r in rows if not r["both_found"]]
        self.assertTrue(all(r["b_status"] == "not_found" for r in others))
        linked = [r for r in pages if r["links_to_ours"]]
        self.has("**%d of the %d councils whose pages Accessibility.build scored lowest (%s%%) have "
                 "that page link straight to the statement MV2's reader found.**"
                 % (len(linked), len(rows), pct(len(linked), len(rows))))
        self.has("MV2's reader also found a statement for %d of the %d; for the other %d, MV2's "
                 "November reader found no statement either."
                 % (len(both), len(rows), len(others)))
        self.assertEqual(len(pages), len(diff))
        self.assertEqual(sum(1 for r in pages if r["is_statement"]), 0)
        self.has("All %d of those addresses answered with HTML when read again; none passed the "
                 "statement test of MV2's reader, and %d link straight to the statement MV2's "
                 "reader found." % (len(diff), len(linked)))
        odd = [r for r in pages if not r["links_to_ours"]]
        self.assertEqual(len(odd), self.d["reread_not_statement_no_link"])
        self.has("The one exception (%s) neither passed the statement test nor linked to MV2's "
                 "statement address." % odd[0]["a_host"])
        v22 = sum(1 for r in linked if r["b_highest"] == "2.2")
        v21 = sum(1 for r in linked if r["b_highest"] == "2.1")
        self.assertEqual(v22 + v21, len(linked))
        dated = [r for r in linked if r["b_statement_date"]]
        later = sum(1 for r in dated if r["b_statement_date"] > MEASURED)
        self.has("Read in November, all %d of those statements name a WCAG version (%d name 2.2, %d "
                 "name 2.1) and %d give a date; %d of the dates are later than 2 September 2026"
                 % (len(linked), v22, v21, len(dated), later))
        self.has("On the %d low-score rows at the same address, MV2's reader took a WCAG version "
                 "from %d and a date from %d."
                 % (len(same), sum(1 for r in same if r["b_highest"]),
                    sum(1 for r in same if r["b_statement_date"])))

    def test_full_and_partial(self):
        f, p = self.g["full"], self.g["partial"]
        dated = [r for r in f["both"] if r["b_statement_date"]]
        stale = sum(1 for r in dated if r["b_statement_date"] < STALE_BEFORE)
        v22 = sum(1 for r in f["both"] if r["b_highest"] == "2.2")
        self.has("%d of the %d full-score statements that MV2's reader dated (%s%%) carry a date "
                 "before 1 November 2025, and %d of the %d (%s%%) name WCAG 2.2"
                 % (stale, len(dated), pct(stale, len(dated)), v22, len(f["both"]),
                    pct(v22, len(f["both"]))))
        self.has("%d full-score rows give another address; %d of those pages answered with HTML "
                 "when read again and all %d pass the statement test"
                 % (len(f["diff"]), len(f["pages"]), len(f["pages"])))
        self.assertTrue(all(r["is_statement"] for r in f["pages"]))
        self.has("%d of the %d partial-score rows where both found a statement give the same "
                 "address" % (len(p["same"]), len(p["both"])))
        rs = self.d["reread_status"]
        self.has("Of the %d addresses read again, %d answered 404 in November."
                 % (sum(rs.values()), rs["404"]))
        self.assertEqual(sum(rs.values()), self.result["crawl"]["pages"])

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(cs.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
