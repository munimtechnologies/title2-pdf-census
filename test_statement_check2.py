"""Offline tests for statement_check2.py (no network). Apache-2.0.

Made by MV2 of Munim, Inc. with AI agents.
"""

import io
import json
import unittest

import statement_check2 as s2
import template_check as tc

FILLER = (" The City is committed to making its website usable by everyone, including people who "
          "use screen readers, keyboard navigation or magnification software.")
STOCK_NO_WCAG = ("We work to comply with Section 508 as well as 2.0 A and AA referring to website "
                 "accessibility standards.")


def ids(r):
    return [f["id"] for f in r["findings"]]


def run(html, *extra):
    out = io.StringIO()
    code = s2.main(["-"] + list(extra), out=out, stdin=io.BytesIO(html.encode("utf-8")))
    return code, out.getvalue()


class CheckText(unittest.TestCase):
    def test_clean_page_has_no_template_findings(self):
        text = ("This website aims to conform to WCAG 2.1 Level AA. To report a barrier, contact "
                "your municipality clerk at ada@example.gov or 555-123-4567. See note [1]."
                + FILLER)
        r = s2.check_text(text)
        self.assertFalse(r["placeholder"])
        self.assertFalse(r["stock_no_wcag"])
        self.assertNotIn("template-placeholder", ids(r))
        self.assertNotIn("stock-no-wcag", ids(r))

    def test_yourmunicipality(self):
        r = s2.check_text("YOURMUNICIPALITY is committed to accessibility." + FILLER)
        self.assertEqual(r["placeholder_kinds"], ["muni"])
        self.assertIn("template-placeholder", ids(r))
        self.assertIn("YOURMUNICIPALITY", r["findings"][ids(r).index("template-placeholder")]["text"])

    def test_bracket_placeholder_is_quoted(self):
        r = s2.check_text("Please email [INSERT CITY NAME] staff about problems." + FILLER)
        self.assertEqual(r["placeholder_kinds"], ["bracket"])
        self.assertEqual(r["placeholder_text"], "[INSERT CITY NAME]")
        text = r["findings"][ids(r).index("template-placeholder")]["text"]
        self.assertIn("([INSERT CITY NAME])", text)

    def test_url_of_website_bracket(self):
        r = s2.check_text("This statement covers [URL OF WEBSITE] only." + FILLER)
        self.assertTrue(r["placeholder"])
        self.assertEqual(r["placeholder_text"], "[URL OF WEBSITE]")

    def test_contact_block_and_template_note(self):
        r = s2.check_text("Coordinator: NAME TITLE EMAIL PHONE. This page is only meant as a "
                          "template." + FILLER)
        self.assertEqual(r["placeholder_kinds"], ["template_note", "contact_block"])
        self.assertEqual(ids(r).count("template-placeholder"), 1)

    def test_lowercase_words_are_not_placeholders(self):
        r = s2.check_text("Ask your municipality; name, title, email and phone are below. "
                          "[Updated 2026]" + FILLER)
        self.assertFalse(r["placeholder"])

    def test_stock_sentence_without_wcag(self):
        r = s2.check_text(STOCK_NO_WCAG + FILLER)
        self.assertTrue(r["stock_no_wcag"])
        self.assertIn("stock-no-wcag", ids(r))
        self.assertTrue(r["stock_sentence"])  # statement_check's own stock check still fires

    def test_stock_sentence_with_wcag_is_not_no_wcag(self):
        r = s2.check_text("We work to comply with Section 508 as well as WCAG 2.0 A and AA "
                          "referring to website accessibility standards." + FILLER)
        self.assertFalse(r["stock_no_wcag"])
        self.assertNotIn("stock-no-wcag", ids(r))

    def test_every_flag_has_words(self):
        self.assertEqual(sorted(s2.KIND_WORDS), sorted(tc.FLAGS))


class Main(unittest.TestCase):
    def test_json_from_stdin(self):
        code, out = run("<html><body><p>YOURMUNICIPALITY Accessibility</p><p>"
                        + STOCK_NO_WCAG + FILLER + "</p></body></html>", "--json")
        r = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(r["version"], s2.__version__)
        self.assertIn("template-placeholder", ids(r))
        self.assertIn("stock-no-wcag", ids(r))

    def test_text_report(self):
        code, out = run("<html><body><p>YOURMUNICIPALITY Accessibility. " + FILLER
                        + "</p></body></html>")
        lines = out.splitlines()
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("statement_check2 %s" % s2.__version__))
        self.assertIn("template placeholder: muni", lines)
        self.assertIn("stock sentence without the word WCAG: no", lines)
        self.assertTrue(lines[-1].startswith("statement_check2: "))
        at = lines.index("template placeholder: muni")
        self.assertTrue(lines[at - 1].startswith("email or phone on the page:"))

    def test_find_with_file_is_not_checked(self):
        code, out = run("<html></html>", "--find")
        self.assertEqual(code, 2)
        self.assertEqual(out.splitlines()[-1], "statement_check2: not checked")


if __name__ == "__main__":
    unittest.main()
