# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered uk-planned result from its saved tables.

Reads results/uk-planned/ (rows.csv, planned.csv, result.json and result.txt: the output of sealed
job uk-planned-v1, unchanged). It rebuilds the frame from the two census tables with the pinned
planned_dates.py 0.1.0, re-grades every measure, gate and prediction from rows.csv, replays the
planned-date rule on every kept snippet, applies the Q4 reading and the "last" exception, and
checks every figure in results/uk-planned/UK-PLANNED-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_uk_planned_result.py
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import csv
import hashlib
import json
import os
import re
import sys
import unittest
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import planned_dates as pd  # noqa: E402

cs = pd.cs
RES = os.path.join(ROOT, "results", "uk-planned")
NOTE = os.path.join(RES, "UK-PLANNED-RESULT.md")
ROWS = os.path.join(RES, "rows.csv")
PLANNED = os.path.join(RES, "planned.csv")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED = {"Q1": True, "Q2": True, "Q3": True, "Q4": None}   # Q4 is graded by reading, below
WESTMINSTER = "https://www.westminster.gov.uk/accessibility"
RE_READ_DAY = "2026-11-13"
# Q4: every kept snippet, read by eye by AI agents working in MV2's name (not by a person).
READING = [
    ("https://phw.nhs.wales/accessibility-statement/", "2027-03-31",
     "ement was prepared in March 2026. It will be reviewed in March 2027", "planned review"),
    ("https://www.bolton.gov.uk/policies-strategies-procedures/accessibilty/2", "2025-07-23",
     "was prepared on 30 June 2025. It was will be reviewed on 23 July 2025", "planned review"),
    ("https://www.gedling.gov.uk/accessibility-statement", "2026-11-18",
     "ement was prepared on 18/11/2025. It will be reviewed on 18/11/2026", "planned review"),
    ("https://www.malvernhills.gov.uk/accessibility", "2023-10-31",
     "wed on 23 March 2022. This statement will be reviewed in full again by 31 October 2023",
     "planned review"),
    ("https://www.redbridge.gov.uk/accessibility-statement/", "2022-09-21",
     "ent was updated on 23 March 2022. It will be reviewed on 21 September 2022", "planned review"),
    ("https://www.redbridge.gov.uk/accessibility-statement/", "2022-09-21",
     "as last updated on 23 March 2022 and will be reviewed on 21 September 2022", "planned review"),
    (WESTMINSTER, "2026-10-01",
     "y Advisory and Support Service (EASS) . Next Last updated: 1 October 2026",
     "not planned: a \"Next\" link, then the page's last update"),
]
LAST_RE = re.compile(r"last\b", re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def shas(data):
    return (sha(data), sha(data.replace(b"\r\n", b"\n")))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def norm(x):
    return json.loads(json.dumps(x))


def pct(k, total):
    """k of total as a percentage with two decimals, e.g. 6, 470 -> '1.28'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def refined_planned(flat, m):
    """The 0.7.0 rule with one exception: a phrase starting with 'last' is never planned."""
    return pd.planned(flat, m) and not LAST_RE.match(m.group(0))


def snippet_dates(snippet, rule):
    flat = " ".join(snippet.split())
    out = []
    for rx in (cs.REVIEW_RE, cs.PREPARED_RE):
        for m in rx.finditer(flat):
            d = cs._date(m)
            if d and rule(flat, m):
                out.append(d.isoformat())
    return out


def not_planned():
    return [r for r in READING if not r[3].startswith("planned")]


def refined_rows(rows):
    """Rows with the new reading as the 'last' exception would give it: where every planned date
    of a row is one the exception keeps, the row keeps its old date."""
    kept = {r[0] for r in not_planned()}
    true_urls = {r[0] for r in READING if r[3].startswith("planned")}
    assert not kept & true_urls
    out = []
    for r in rows:
        r = dict(r)
        if r["url"] in kept:
            r["new_date"], r["new_source"] = r["old_date"], r["old_source"]
        out.append(r)
    return out


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.header, cls.rows = load_csv(ROWS)
        cls.sheader, cls.snips = load_csv(PLANNED)

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual((r["version"], r["reader_version"], r["checker_version"]),
                         (pd.__version__, cs.__version__, pd.stc.__version__))
        self.assertEqual((pd.__version__, cs.__version__, pd.stc.__version__),
                         ("0.1.0", "0.1.0", "0.3.0"))
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]),
                         {"P0_prereg", "P0_reader", "P0_planned_rule", "F1_frame", "G1_read"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED)

    def test_input_files_are_the_ones_that_ran(self):
        self.assertEqual(set(self.result["files"]),
                         {pd.PREREG_PATH} | {p for _, p in pd.TABLES})
        for name, want in self.result["files"].items():
            with open(os.path.join(ROOT, *name.split("/")), "rb") as fh:
                self.assertIn(want, shas(fh.read()), name)

    def test_tables_match_result_json(self):
        t = self.result["tables"]
        self.assertEqual(set(t), {"rows.csv", "planned.csv"})
        for name, path, n in (("rows.csv", ROWS, len(self.rows)),
                              ("planned.csv", PLANNED, len(self.snips))):
            with open(path, "rb") as fh:
                data = fh.read()
            self.assertLess(len(data), LIMIT)
            self.assertIn(t[name]["sha256"], shas(data), name)
            self.assertEqual(len(data.replace(b"\r\n", b"\n")), t[name]["bytes"], name)
            self.assertEqual(n, t[name]["rows"], name)
        self.assertEqual(self.header, pd.COLUMNS)
        self.assertEqual(self.sheader, pd.SNIPPET_COLUMNS)

    def test_frame_rebuilds_from_the_census_tables(self):
        tables = [(src, pd.read_table(os.path.join(ROOT, *path.split("/")))[0])
                  for src, path in pd.TABLES]
        items, counts = pd.build_frame(tables)
        self.assertTrue(pd.frame_ok(items, counts))
        f = self.result["frame"]
        self.assertEqual(counts["ok_rows"], f["ok_rows"])
        self.assertEqual((len(items), counts["withheld"]), (f["urls"], f["withheld"]))
        self.assertEqual(sum(1 for it in items if ";" in it["sources"]), f["both"])
        by_url = {r["url"]: r for r in self.rows}
        self.assertEqual(len(by_url), len(self.rows))
        self.assertEqual(set(by_url), {it["url"] for it in items})
        for it in items:
            for c in ("sources", "census_date", "census_sha256"):
                self.assertEqual(by_url[it["url"]][c], it[c], (it["url"], c))

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = pd.grade(self.rows, True)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual((pd.G1_MIN_READ, pd.Q1_MAX_PLANNED, pd.Q2_MAX_FLIPPED, pd.Q3_MAX_PP,
                          pd.Q4_MAX_NOT_PLANNED), (0.80, 0.05, 0.01, 1.5, 1))
        self.assertEqual((pd.Q2_MIN_PAGES, pd.Q3_MIN_PAGES, pd.STALE_BEFORE),
                         (100, 100, "2025-11-01"))

    def test_described_counts(self):
        self.assertEqual(norm(pd.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), pd.result_text(self.result) + "\n")

    def test_q4_reading_covers_every_snippet_and_holds(self):
        got = [(s["url"], s["date"], s["snippet"]) for s in self.snips]
        self.assertEqual(got, [r[:3] for r in READING])
        self.assertLessEqual(len(not_planned()), pd.Q4_MAX_NOT_PLANNED)
        self.assertEqual([r[0] for r in not_planned()], [WESTMINSTER])

    def test_rule_replays_on_every_snippet(self):
        for url, date, snip, _ in READING:
            self.assertIn(date, snippet_dates(snip, pd.planned), url)

    def test_westminster_is_the_one_flip(self):
        snip = READING[-1][2]
        self.assertEqual(cs.statement_dates(snip)[2], "2026-10-01")
        self.assertEqual(pd.new_dates(snip)[2], "")
        read = [r for r in self.rows if r["status"] == "ok"]
        flipped = [r["url"] for r in read if r["old_date"] and r["old_date"] >= pd.STALE_BEFORE
                   and (not r["new_date"] or r["new_date"] < pd.STALE_BEFORE)]
        self.assertEqual(flipped, [WESTMINSTER])
        w = [r for r in self.rows if r["url"] == WESTMINSTER][0]
        self.assertEqual((w["old_date"], w["new_date"], w["planned_n"], w["future_phrases"]),
                         ("2026-10-01", "", "1", "0"))

    def test_last_exception(self):
        for url, date, snip, reading in READING:
            kept_out = date in snippet_dates(snip, refined_planned)
            self.assertEqual(kept_out, reading.startswith("planned"), url)
        self.assertEqual(pd.new_dates(READING[0][2])[2], "2026-03-31")

    def test_no_page_text_and_no_blocked_word(self):
        for path in (ROWS, PLANNED, NOTE):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(cs.GUARD_RE.search(fh.read()), path)
        for s in self.snips:
            self.assertLessEqual(len(s["snippet"]), pd.SNIPPET_CHARS)


class NoteTests(unittest.TestCase):
    """Every figure in UK-PLANNED-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.rows = load_csv(ROWS)
        cls.read = [r for r in cls.rows if r["status"] == "ok"]
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def share(self, key):
        s = self.m[key]
        return s["k"], s["n"], pct(s["k"], s["n"])

    def test_headline(self):
        c = self.result["crawl"]
        self.has("the %d addresses were read from %s to %s UTC on %s."
                 % (self.m["F1_urls"], c["started_utc"][11:19], c["finished_utc"][11:19],
                    c["started_utc"][:10]))
        self.assertEqual(c["started_utc"][:10], RE_READ_DAY)
        self.has("**All four predictions held (Q1, Q2, Q3, Q4); Q4 held at its limit.**")
        self.assertEqual(len(not_planned()), pd.Q4_MAX_NOT_PLANNED)
        k, n, p = self.share("Q1_planned_of_read")
        self.has("%d of the %d statements read again (%s%%) give a planned date" % (k, n, p))
        k, n, p = self.share("Q2_flipped_of_dated")
        self.has("%d of the %d dated statements (%s%%) goes from current to undated" % (k, n, p))
        q3 = self.m["Q3_by_census"]
        co, gv = q3["council"], q3["govuk"]
        self.has("moves by %.2f points for councils (%d of %d, %s%%, to %d of %d, %s%%) and by %.2f "
                 "points for organisations (%d of %d, %s%%)."
                 % (co["diff_pp"], co["old_stale"], co["old_dated"],
                    pct(co["old_stale"], co["old_dated"]), co["new_stale"], co["new_dated"],
                    pct(co["new_stale"], co["new_dated"]), gv["diff_pp"], gv["old_stale"],
                    gv["old_dated"], pct(gv["old_stale"], gv["old_dated"])))
        self.assertEqual((gv["old_stale"], gv["old_dated"]), (gv["new_stale"], gv["new_dated"]))
        changed = [r for r in self.read if r["old_date"] != r["new_date"]]
        crossed = [r["url"] for r in changed
                   if (r["old_date"] >= pd.STALE_BEFORE) != (bool(r["new_date"])
                                                             and r["new_date"] >= pd.STALE_BEFORE)]
        self.assertEqual(crossed, [WESTMINSTER])

    def test_frame_and_gates(self):
        f = self.result["frame"]
        ok = f["ok_rows"]
        self.has("The %d rows with status ok (%d in the councils' table, %d in the organisations' "
                 "table) give %d distinct addresses; no address is in both tables, and no address "
                 "was withheld. F1 held." % (ok["council"] + ok["govuk"], ok["council"],
                                             ok["govuk"], f["urls"]))
        self.assertEqual((f["both"], f["withheld"]), (0, 0))
        st = self.d["status"]
        self.assertEqual(set(st), {"ok", "http_0", "not_statement"})
        ns = [r["url"] for r in self.rows if r["status"] == "not_statement"]
        self.assertEqual(len(ns), 1)
        self.assertIn("wirral.gov.uk", ns[0])
        k, n, p = self.share("G1_read")
        self.has("G1 held: %d of the %d addresses (%s%%) were read again as a statement; %d did not "
                 "answer and %d (wirral.gov.uk) no longer reads as a statement."
                 % (k, n, p, st["http_0"], st["not_statement"]))

    def test_prediction_table(self):
        for key in ("Q1_planned_of_read", "Q2_flipped_of_dated"):
            k, n, p = self.share(key)
            self.has("| %d of %d (%s%%) | yes |" % (k, n, p))
        q3 = self.m["Q3_by_census"]
        self.has("| councils %.2f points, organisations %.2f points | yes |"
                 % (q3["council"]["diff_pp"], q3["govuk"]["diff_pp"]))
        self.has("| %d of %d (westminster.gov.uk) | yes |" % (len(not_planned()), len(READING)))

    def test_snippet_table(self):
        for url, date, snip, reading in READING:
            self.has("| %s | %s | `%s` | %s |" % (url, date, snip, reading))

    def test_described(self):
        fp = self.d["future_phrase_pages"]
        both = [r for r in self.read if int(r["planned_n"]) > 0 and int(r["future_phrases"]) > 0]
        self.assertEqual(len(both), 5)
        self.has("%d of the %d statements (%s%%) use a future-review phrase" % (
            fp, len(self.read), pct(fp, len(self.read))))
        self.has("but the census reader took a planned date from only %d of them." % len(both))
        true = {r[0]: r[1] for r in READING if r[3].startswith("planned")}
        self.assertEqual(len(true), 5)
        past = sorted(u for u, dd in true.items() if dd < RE_READ_DAY)
        self.assertEqual(len(past), 3)
        self.assertEqual([true[u] for u in past], ["2025-07-23", "2023-10-31", "2022-09-21"])
        self.has("Three of the five statements with a true planned date promise a review by a day "
                 "that had already passed when they were read: Redbridge (21 September 2022), "
                 "Malvern Hills (31 October 2023) and Bolton (23 July 2025).")
        later = sorted((r for r in self.rows if r["census_date"] > RE_READ_DAY),
                       key=lambda r: r["census_date"], reverse=True)
        self.assertEqual([(r["url"], r["census_date"]) for r in later],
                         [(READING[0][0], "2027-03-31"), (READING[2][0], "2026-11-18")])
        self.has("Exactly %d statements in the frame carry a census date later than the day of this "
                 "re-read (phw.nhs.wales: 2027-03-31; gedling.gov.uk: 2026-11-18)" % len(later))
        same, dsame = self.d["text_same_as_census"], self.d["old_date_same_as_census"]
        n = len(self.read)
        self.has("%d of the %d texts (%s%%) are byte for byte the text the census read, and the "
                 "census reader gives the same date as in the census for %d (%s%%)."
                 % (same, n, pct(same, n), dsame, pct(dsame, n)))
        o, w = self.d["old_source"], self.d["new_source"]
        self.has("Old reading: %d undated, %d dated from a \"reviewed / updated\" line and %d from a "
                 "\"prepared / published\" line. New reading: %d undated, %d and %d."
                 % (self.d["old_undated"], o["reviewed"], o["prepared"], self.d["new_undated"],
                    w["reviewed"], w["prepared"]))

    def test_last_exception_figures(self):
        rows = [r for r in refined_rows(self.rows) if r["status"] == "ok"]
        flipped = [r for r in rows if r["old_date"] and r["old_date"] >= pd.STALE_BEFORE
                   and (not r["new_date"] or r["new_date"] < pd.STALE_BEFORE)]
        council = [r for r in rows if "council" in r["sources"].split(";")]
        k, n = pd.stale_share(council, "new_date")
        self.assertEqual((k, n), pd.stale_share(council, "old_date"))
        self.has("the six true planned snippets are still left out, the Westminster date is kept, "
                 "%d dated statements change side of the line, and the councils' share stays %d of "
                 "%d (%s%%)." % (len(flipped), k, n, pct(k, n)))
        self.assertEqual(len(flipped), 0)
        self.assertEqual(sum(1 for r in READING if r[3].startswith("planned")), 6)

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(cs.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
