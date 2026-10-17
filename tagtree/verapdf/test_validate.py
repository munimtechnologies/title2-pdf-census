"""Tests for tagtree-verapdf's pure parts. Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import unittest

import validate


def row(name, result="ok", untagged=0, dangling=0, content=10):
    r = {"file": name, **validate.parse(name), "result": result}
    if result == "ok":
        r.update(reachable=content - untagged - dangling, untagged=untagged, dangling=dangling,
                 content_chars=content)
    return r


class Parse(unittest.TestCase):
    def test_names(self):
        self.assertEqual(validate.parse("PDF_UA-1/7.1 General/7.1-t03-fail-b.pdf"),
                         {"clause": "7.1", "test": 3, "verdict": "fail", "variant": "b"})
        self.assertEqual(validate.parse("7.21.4.1-t01-pass-a.pdf")["clause"], "7.21.4.1")
        self.assertIsNone(validate.parse("PDF_UA-1/README.md"))
        self.assertIsNone(validate.parse("7.1-t03-maybe-a.pdf"))

    def test_fallback_names_all_parse(self):
        self.assertEqual(len(validate.FALLBACK), 30)
        self.assertTrue(all(validate.parse(p) for p in validate.FALLBACK))

    def test_ua_paths(self):
        tree = {"tree": [
            {"path": "PDF_UA-1/7.1 General/7.1-t03-pass-a.pdf", "type": "blob"},
            {"path": "PDF_UA-1/7.1 General", "type": "tree"},
            {"path": "PDF_A-1b/6.1 File structure/6.1.2-t01-fail-a.pdf", "type": "blob"},
            {"path": "PDF_UA-1/5 Version identification/5-t01-fail-a.pdf", "type": "blob"},
            {"path": "PDF_UA-1/notes.txt", "type": "blob"}]}
        self.assertEqual(validate.ua_paths(tree), [
            "PDF_UA-1/5 Version identification/5-t01-fail-a.pdf",
            "PDF_UA-1/7.1 General/7.1-t03-pass-a.pdf"])


class Judge(unittest.TestCase):
    def test_all_met(self):
        rows = [row("7.1-t03-fail-a.pdf", untagged=4), row("7.1-t03-fail-b.pdf", dangling=2),
                row("7.1-t03-pass-a.pdf"), row("7.1-t03-pass-b.pdf"),
                row("7.2-t01-pass-a.pdf"), row("7.2-t01-fail-a.pdf", untagged=9),
                row("7.16-t01-pass-a.pdf", result="parse_error")]
        v = validate.judge(rows)
        self.assertTrue(v["V1_t03_fail"]["met"])
        self.assertEqual(v["V1_t03_fail"]["with_unreachable"], 2)
        self.assertTrue(v["V2_t03_pass"]["met"])
        self.assertEqual(v["V3_pass_specificity"]["analysed_with_text"], 3)
        self.assertEqual(v["V3_pass_specificity"]["share"], 1.0)
        self.assertTrue(v["V3_pass_specificity"]["met"])

    def test_misses(self):
        rows = [row("7.1-t03-fail-a.pdf", untagged=4), row("7.1-t03-fail-b.pdf"),
                row("7.1-t03-pass-a.pdf", untagged=1), row("7.1-t03-pass-b.pdf")]
        v = validate.judge(rows)
        self.assertFalse(v["V1_t03_fail"]["met"])
        self.assertFalse(v["V2_t03_pass"]["met"])
        self.assertEqual(v["V3_pass_specificity"]["share"], 0.5)
        self.assertFalse(v["V3_pass_specificity"]["met"])
        self.assertEqual(v["V3_pass_specificity"]["leaky_files"], ["7.1-t03-pass-a.pdf"])

    def test_unanalysed_fail_file_is_not_a_pass(self):
        rows = [row("7.1-t03-fail-a.pdf", untagged=4),
                dict(row("7.1-t03-fail-b.pdf", result="timeout"))]
        self.assertFalse(validate.judge(rows)["V1_t03_fail"]["met"])

    def test_nothing_analysed_is_untestable(self):
        v = validate.judge([row("7.1-t03-fail-a.pdf", result="no_struct_tree")])
        self.assertIsNone(v["V1_t03_fail"]["met"])
        self.assertIsNone(v["V2_t03_pass"]["met"])
        self.assertIsNone(v["V3_pass_specificity"]["met"])

    def test_report(self):
        rows = [dict(row("7.1-t03-fail-a.pdf", untagged=4), outline="Content | not tagged")]
        s = {"version": validate.__version__, "tagtree_version": "0.1.0", "files": 1,
             "list_source": "test", "results": {"ok": 1}, "verdicts": validate.judge(rows)}
        text = validate.report(s, rows)
        self.assertIn("V1", text)
        self.assertIn("Content / not tagged", text)


if __name__ == "__main__":
    unittest.main()
