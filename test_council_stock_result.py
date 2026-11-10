# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Re-grades the pre-registered council-stock result from its saved table.

Reads results/uk-councils/result.json, result.txt and hosts.csv (the run's output of sealed job
council-stock-v1, unchanged), re-grades every measure, gate, prediction and described count with
the pinned council_stock.py 0.1.0 (unchanged; it imports statement_template_check.py 0.3.0),
checks the table against the registered frame (council-frame.csv), and checks every figure in
results/uk-councils/COUNCIL-STOCK-RESULT.md against the data.

Standard library only: python -m unittest discover -p test_council_stock_result.py
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
import council_stock as cs  # noqa: E402

RES = os.path.join(ROOT, "results", "uk-councils")
NOTE = os.path.join(RES, "COUNCIL-STOCK-RESULT.md")
TABLE = os.path.join(RES, "hosts.csv")
FRAME = os.path.join(RES, "council-frame.csv")
LIMIT = 2000000                    # the publishing tool's limit per file
EXPECTED_PREDICTIONS = {"N1": False, "N2": True, "N3": True, "N4": True}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
AB_FOUND, AB_TOTAL = 206, 303      # accessibility.build, "State of accessibility statements, 2026"
KIND_LABELS = (("england_county", "English counties"),
               ("england_district", "English districts"),
               ("england_metropolitan", "Metropolitan boroughs"),
               ("england_unitary", "English unitaries"),
               ("london_borough", "London boroughs"),
               ("northern_ireland_district", "Northern Irish districts"),
               ("scotland_council", "Scottish councils"),
               ("wales_unitary", "Welsh unitaries"))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def norm(x):
    """The value as it reads back from result.json."""
    return json.loads(json.dumps(x))


def n(k):
    return format(k, ",")


def pct(k, total):
    """k of total as a percentage with two decimals, e.g. 284, 379 -> '74.93'."""
    return str((Decimal(k) * 100 / Decimal(total)).quantize(Decimal("0.01")))


def load_rows():
    _, raw = load_csv(TABLE)
    return raw, cs.typed(raw)


class TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.raw, cls.rows = load_rows()

    def test_version_status_gates(self):
        r = self.result
        self.assertEqual(r["version"], cs.__version__)
        self.assertEqual(r["checker_version"], cs.CHECKER_VERSION)
        self.assertEqual(r["status"], "graded")
        self.assertEqual(set(r["gates"]), {"P0_prereg", "P0_checker", "F1_frame", "G1_answered"})
        self.assertTrue(all(r["gates"].values()))
        self.assertEqual(r["predictions"], EXPECTED_PREDICTIONS)
        f = r["frame"]
        self.assertEqual((f["rows"], f["hosts"], f["dropped"], f["bytes_ok"]),
                         (cs.FRAME_ROWS, cs.FRAME_HOSTS, 0, True))

    def test_table_matches_result_json(self):
        t = self.result["table"]
        self.assertEqual(t["file"], "hosts.csv")
        with open(TABLE, "rb") as fh:
            data = fh.read()
        self.assertEqual(len(data), t["bytes"])
        self.assertEqual(hashlib.sha256(data).hexdigest(), t["sha256"])
        self.assertLess(len(data), LIMIT)
        header, rows = load_csv(TABLE)
        self.assertEqual(header, cs.COLUMNS)
        self.assertEqual(len(rows), t["rows"])

    def test_pinned_script_is_the_one_that_ran(self):
        with open(os.path.join(ROOT, "council_stock.py"), "rb") as fh:
            data = fh.read()
        ran = self.result["files"]["council_stock.py"]
        self.assertIn(ran, (hashlib.sha256(data).hexdigest(),
                            hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()))

    def test_table_is_the_registered_frame(self):
        frame_rows, ok = cs.read_frame(FRAME)
        self.assertTrue(ok)
        hosts, dropped = cs.build_frame(frame_rows)
        self.assertEqual(dropped, 0)
        want = sorted((h["host"], h["kind"], str(h["authorities"])) for h in hosts)
        got = [(r["host"], r["kind"], r["authorities"]) for r in self.raw]
        self.assertEqual(got, want)
        self.assertEqual(sum(int(r["authorities"]) for r in self.raw), cs.FRAME_ROWS)

    def test_no_page_text_and_no_blocked_word(self):
        for r in self.raw:
            self.assertTrue(r["text_sha256"] == "" or HEX64.match(r["text_sha256"]))
            int(r["text_chars"])
        with open(TABLE, encoding="utf-8") as fh:
            self.assertIsNone(cs.GUARD_RE.search(fh.read()))

    def test_regrade_measures_gates_and_predictions(self):
        measures, gates, preds = cs.grade(self.rows)
        self.assertEqual(norm(measures), self.result["measures"])
        for k, v in gates.items():
            self.assertEqual(v, self.result["gates"][k], k)
        self.assertEqual(norm(preds), self.result["predictions"])
        self.assertEqual(preds, EXPECTED_PREDICTIONS)

    def test_described_counts(self):
        self.assertEqual(norm(cs.described(self.rows)), self.result["described"])

    def test_result_txt_matches_result_json(self):
        with open(os.path.join(RES, "result.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), cs.result_text(self.result) + "\n")

    def test_flags_only_on_read_pages(self):
        for r in self.rows:
            if r["status"] != "ok":
                for k in ("placeholder", "gov_uk_sample", "wcag_named", "other_host"):
                    self.assertFalse(r[k], (r["host"], k))
                for k in ("placeholder_ids", "highest", "statement_date", "statement_url"):
                    self.assertEqual(r[k], "", (r["host"], k))
            else:
                self.assertEqual(r["home_status"], "200", r["host"])

    def test_statement_date_is_the_later_of_the_two(self):
        for r in self.rows:
            rv, pr = r["review_date"], r["prepared_date"]
            if rv and (not pr or rv >= pr):
                want = (rv, "reviewed")
            elif pr:
                want = (pr, "prepared")
            else:
                want = ("", "")
            self.assertEqual((r["statement_date"], r["date_source"]), want, r["host"])


class NoteTests(unittest.TestCase):
    """Every figure in COUNCIL-STOCK-RESULT.md, checked against the data."""

    @classmethod
    def setUpClass(cls):
        cls.result = load_json(os.path.join(RES, "result.json"))
        cls.m = cls.result["measures"]
        cls.d = cls.result["described"]
        _, cls.rows = load_rows()
        cls.found = [r for r in cls.rows if r["status"] == "ok"]
        cls.k = len(cls.found)
        with open(NOTE, encoding="utf-8") as f:
            cls.note = " ".join(f.read().split())

    def has(self, phrase):
        self.assertIn(" ".join(phrase.split()), self.note)

    def test_status_and_crawl_times(self):
        c = self.result["crawl"]
        self.has("(%s to %s UTC on %s)" % (c["started_utc"][11:16], c["finished_utc"][11:16],
                                            c["started_utc"][:10]))
        self.has("**Three of the four predictions held (N2, N3, N4) and one failed (N1).**")

    def test_headline(self):
        s, d = self.m["N1_found"], self.d
        self.assertEqual(s["k"], self.k)
        self.has("**%s of the %s principal-council website hosts (%s%%) serve an accessibility "
                 "statement that this method found and read**, covering %s of the %s councils "
                 "(%s%%)." % (n(s["k"]), n(s["n"]), pct(s["k"], s["n"]), n(d["found_councils"]),
                             n(cs.FRAME_ROWS), pct(d["found_councils"], cs.FRAME_ROWS)))

    def test_prediction_table(self):
        m = self.m
        self.assertEqual((cs.N1_MIN_FOUND, cs.N2_MAX_PLACEHOLDER, cs.N3_MIN_22, cs.N4_MIN_STALE),
                         (0.85, 5, 0.60, 0.25))
        for key, held in (("N1_found", "no"), ("N3_wcag22_of_found", "yes"),
                          ("N4_stale_of_dated", "yes")):
            s = m[key]
            self.assertEqual(pct(s["k"], s["n"]), "%.2f" % s["pct"])
            self.has("| %s of %s (%s%%) | %s |" % (n(s["k"]), n(s["n"]), pct(s["k"], s["n"]), held))
        self.assertEqual(m["N2_placeholder_hosts"], 1)
        self.has("| 1 host | yes |")

    def test_gates(self):
        f, g = self.result["frame"], self.m["G1_answered"]
        self.has("The frame is the %s councils on %s hosts" % (n(f["rows"]), n(f["hosts"])))
        self.has("%s of %s hosts (%s%%) answered, above G1's 90%%"
                 % (n(g["k"]), n(g["n"]), pct(g["k"], g["n"])))

    def test_statuses(self):
        st, rows = self.d["status"], self.rows
        home200 = sum(1 for r in rows if r["home_status"] == "200")
        nf = [r for r in rows if r["status"] == "not_found"]
        nf200 = sum(1 for r in nf if r["home_status"] == "200")
        nf_other = [r for r in nf if r["home_status"] != "200"]
        nf403 = sum(1 for r in nf_other if r["home_status"] == "403")
        self.assertEqual(home200, self.k + nf200)
        self.assertEqual(len(nf), st["not_found"])
        self.has("%d hosts did not answer at all, and for %d the home page was not requested because "
                 "robots.txt disallowed it or answered 401 or 403, which the reader takes as a "
                 "refusal." % (st["http_0"], st["robots"]))
        self.has("%d answered the home page with another status (%d of them 403) and no statement "
                 "was found" % (len(nf_other), nf403))
        self.has("Of the %d hosts whose home page answered 200, %d (%s%%) led to a statement; on the "
                 "other %d, none was found this way." % (home200, self.k, pct(self.k, home200),
                                                         nf200))
        let_in = sum(1 for r in rows if r["status"] not in ("http_0", "robots"))
        self.has("Of the %d hosts that answered and did not refuse the reader by robots.txt, %d "
                 "(%s%%) led to a statement, just above N1's 85%%"
                 % (let_in, self.k, pct(self.k, let_in)))

    def test_found_by(self):
        fb, d = self.d["found_by"], self.d
        self.assertEqual(d["distinct_texts"], self.k)
        self.has("%d were found through the home page's own link, %d one hop further on, and %d at "
                 "a fixed address" % (fb["link"], fb["hub"],
                                      fb.get("probe1", 0) + fb.get("probe2", 0)))
        self.has("%d statements were served from another host and every one of the %d texts is "
                 "different." % (d["found_other_host"], d["distinct_texts"]))
        self.assertEqual((d["offsite_link"], d["retried"]), (0, 0))
        self.has("No statement link pointed to another site and no host answered 429 or 503.")

    def test_wcag(self):
        h, k, d = self.d["found_highest"], self.k, self.d
        self.assertEqual(sum(h.values()), k)
        self.has("%d of the %d statements (%s%%) name WCAG 2.2 as the highest version, %d (%s%%) "
                 "name 2.1 and %d name no version" % (h["2.2"], k, pct(h["2.2"], k), h["2.1"],
                                                      pct(h["2.1"], k), h[""]))
        g = d["found_gov_uk_wording"]
        self.has("%d (%s%%) carry GOV.UK's compliance sentence" % (g, pct(g, k)))

    def test_dates(self):
        d, k = self.d, self.k
        dated = [r for r in self.found if r["statement_date"]]
        ds, y = d["date_source"], d["statement_year"]
        self.has("%d of the %d statements give a date that the reader could take (%d dated by their "
                 "last review or update, %d by their preparation) and %d give none."
                 % (len(dated), k, ds["reviewed"], ds["prepared"], d["found_no_date"]))
        s = self.m["N4_stale_of_dated"]
        self.assertEqual(s["n"], len(dated))
        self.has("**%d of the %d dated statements (%s%%) carry a date before 1 November 2025**"
                 % (s["k"], s["n"], pct(s["k"], s["n"])))
        old = sum(v for yr, v in y.items() if yr <= "2024")
        self.assertLessEqual(old, s["k"])
        self.has("%d of them (%s%% of the dated) are dated 2024 or earlier"
                 % (old, pct(old, len(dated))))
        self.has("%d (%s%%) are dated in 2026" % (y["2026"], pct(y["2026"], len(dated))))
        v21 = sum(1 for r in dated if r["statement_date"][:4] == "2026" and r["highest"] == "2.1")
        self.has("%d of those %d dated in 2026 still name WCAG 2.1 as the highest version"
                 % (v21, y["2026"]))

    def test_by_kind(self):
        bk = self.d["by_kind"]
        self.assertEqual(sorted(bk), sorted(k for k, _ in KIND_LABELS))
        for key, label in KIND_LABELS:
            b = bk[key]
            self.has("| %s | %d | %d | %d | %d | %d (%s%%) |"
                     % (label, b["hosts"], b["found"], b["wcag22"], b["dated"], b["stale"],
                        pct(b["stale"], b["dated"])))
        worst = max(bk, key=lambda kk: Decimal(bk[kk]["stale"]) / Decimal(bk[kk]["dated"]))
        self.assertEqual(worst, "london_borough")
        b = bk[worst]
        self.has("London boroughs have the largest share of statements dated before 1 November 2025 "
                 "(%d of %d, %s%%)" % (b["stale"], b["dated"], pct(b["stale"], b["dated"])))
        low = min(bk, key=lambda kk: Decimal(bk[kk]["found"]) / Decimal(bk[kk]["hosts"]))
        self.assertEqual(low, "wales_unitary")
        b = bk[low]
        self.has("Welsh unitary councils have the lowest share found (%d of %d hosts, %s%%)"
                 % (b["found"], b["hosts"], pct(b["found"], b["hosts"])))

    def test_placeholder(self):
        d = self.d
        self.assertEqual(d["placeholder_ids"], {"gov-uk/example_document": 1})
        self.assertEqual(len(d["placeholder_hosts"]), 1)
        self.has("One statement (%s) keeps one field of GOV.UK's sample statement, \"[example of "
                 "non-essential document]\"" % d["placeholder_hosts"][0])

    def test_comparison(self):
        self.has("found a statement for %d of %d local authorities (%s%%)"
                 % (AB_FOUND, AB_TOTAL, pct(AB_FOUND, AB_TOTAL)))

    def test_no_blocked_word_in_note(self):
        self.assertIsNone(cs.GUARD_RE.search(self.note))


if __name__ == "__main__":
    unittest.main()
