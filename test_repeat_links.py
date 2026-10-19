"""Tests for repeat_links.py on made-up rows: no network, standard library only. The script is run
as a subprocess, exactly as it was run on the census's own rows (docs/v0.2.2-repeated-links.md).
Apache-2.0 licensed."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "repeat_links.py")


def row(h, qid, result="ok", **fields):
    d = {"url_sha256": h * 64, "qid": qid, "result": result}
    d.update(fields)
    return d


ROWS = [
    row("a", "Q1", tagged=True, lang=True),
    row("b", "Q1", tagged=False, lang=True),
    row("a", "Q2", tagged=True, lang=True),      # link a is posted by Q1 and Q2
    row("c", "Q3", tagged=True, lang=False),
    row("c", "Q4", tagged=True, lang=False),
    row("c", "Q5", tagged=True, lang=False),     # link c is posted by three sites
    row("d", "Q6", tagged=False, lang=False),
    row("d", "Q6", tagged=False, lang=False),    # link d twice on one site (the crawl never does this)
    row("e", "Q7", result="fetch_error", tagged=True),  # not ok: ignored
    row("a", "Q8", result="not_pdf", tagged=True),      # not ok: ignored, even though it is link a
]


def run(rows, *fields):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "rows.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.write("\n")  # a blank line is skipped
        p = subprocess.run([sys.executable, "-I", SCRIPT, path] + list(fields),
                           capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


class RepeatLinksTests(unittest.TestCase):
    def test_counts(self):
        code, out, err = run(ROWS, "tagged", "lang", "marked")
        self.assertEqual(code, 0, err)
        d = json.loads(out)
        self.assertEqual(d["file"], "rows.jsonl")
        self.assertEqual(d["ok_rows"], 8)
        self.assertEqual(d["distinct_links"], 4)
        self.assertEqual(d["repeat_rows"], 4)
        self.assertEqual(d["repeated_links"], 3)
        self.assertEqual(d["rows_per_repeated_link"], {"2": 2, "3": 1})
        self.assertEqual(d["repeated_links_all_different_sites"], 2)
        self.assertEqual(d["repeated_links_same_site_twice"], 1)

    def test_shares_all_and_once(self):
        d = json.loads(run(ROWS, "tagged", "lang", "marked")[1])
        # all: every ok row; once: the first row of each link (a, b, c, d)
        self.assertEqual(d["shares"]["tagged"], {"all": [5, 8, 0.625], "once": [2, 4, 0.5]})
        self.assertEqual(d["shares"]["lang"], {"all": [3, 8, 0.375], "once": [2, 4, 0.5]})
        # a field no row has counts as false everywhere
        self.assertEqual(d["shares"]["marked"], {"all": [0, 8, 0.0], "once": [0, 4, 0.0]})
        self.assertEqual(list(d["shares"]), ["tagged", "lang", "marked"])

    def test_only_a_true_value_counts(self):
        rows = [row("a", "Q1", tagged=1), row("b", "Q2", tagged="yes"), row("c", "Q3", tagged=True)]
        d = json.loads(run(rows, "tagged")[1])
        self.assertEqual(d["shares"]["tagged"]["all"], [1, 3, 0.3333])

    def test_prints_no_hash_url_or_site(self):
        rows = ROWS + [row("f", "Q9", url="https://example.gov/x.pdf", site="example.gov")]
        code, out, err = run(rows, "tagged")
        self.assertEqual(code, 0, err)
        for secret in ("a" * 12, "Q1", "Q9", "example.gov", "http", "url_sha256"):
            self.assertNotIn(secret, out)
        self.assertEqual(sorted(json.loads(out)), sorted([
            "file", "ok_rows", "distinct_links", "repeat_rows", "repeated_links",
            "rows_per_repeated_link", "repeated_links_all_different_sites",
            "repeated_links_same_site_twice", "shares"]))

    def test_no_fields_and_no_rows(self):
        d = json.loads(run(ROWS)[1])
        self.assertEqual(d["shares"], {})
        d = json.loads(run([row("a", "Q1", result="fetch_error")], "tagged")[1])
        self.assertEqual((d["ok_rows"], d["distinct_links"], d["repeat_rows"]), (0, 0, 0))
        self.assertEqual(d["shares"]["tagged"], {"all": [0, 0, None], "once": [0, 0, None]})

    def test_usage_without_a_file(self):
        p = subprocess.run([sys.executable, "-I", SCRIPT], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
        self.assertIn("repeat_links.py ROWS.jsonl [FIELD ...]", p.stderr)
        self.assertEqual(p.stdout, "")


if __name__ == "__main__":
    unittest.main()
