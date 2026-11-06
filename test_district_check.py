"""Offline tests for district_check.py. Apache-2.0. Made by MV2 of Munim, Inc. with AI agents."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import district_check as dc  # noqa: E402

FILLER = (" This page explains how the district works to make its website usable for everyone, "
          "including people who use screen readers, keyboards and other assistive technology. ")

TEMPLATE = ("[Your School] is committed to ensuring digital accessibility for people with "
            "disabilities. [Your School] is built with WCAG 2.1 AA guidelines in mind. "
            "We try to respond to feedback within # business days." + FILLER)

GENERATOR = ("We've been using the Web Content Accessibility Guidelines (WCAG) 2.0 and chose "
             "Level AA as the target for the Your School website. Email accessibility@yourschool.com"
             " or call 555-555-5555. This accessibility statement was generated on 16th May 2017 "
             "using the Accessibility Statement Generator." + FILLER)

EDITED = ("Springfield Public Schools is committed to WCAG 2.1 Level AA under Title II of the ADA "
          "and Section 504. Districts with a total population of 50,000 or more must comply by "
          "April 26, 2027. Contact the Office for Civil Rights or our coordinator at "
          "help@example.org. Our website runs on Finalsite." + FILLER)

STUDENTS = ("Under the new rule, districts with 50,000 or more students must conform to WCAG 2.1 "
            "AA by April 26, 2027, and smaller districts by April 26, 2028." + FILLER)


class CheckTextTests(unittest.TestCase):
    def test_finalsite_template_is_flagged(self):
        r = dc.check_text(TEMPLATE)
        self.assertTrue(r["placeholder"])
        self.assertIn("school_bracket", r["placeholder_kinds"])
        self.assertIn("hash_days", r["placeholder_kinds"])
        self.assertEqual(r["placeholder_text"], "[Your School]")
        self.assertTrue(r["finalsite_line"])
        self.assertEqual(r["highest"], "2.1")
        self.assertFalse(r["students_threshold"])

    def test_generator_template_is_flagged(self):
        r = dc.check_text(GENERATOR)
        kinds = r["placeholder_kinds"].split("+")
        for k in ("your_school", "your_domain", "fake_phone"):
            self.assertIn(k, kinds)
        self.assertTrue(r["generator_line"])
        self.assertEqual(r["highest"], "2.0")
        self.assertIn("wcag-2.0", r["findings"])

    def test_edited_page_is_not_flagged(self):
        r = dc.check_text(EDITED)
        self.assertFalse(r["placeholder"])
        self.assertEqual(r["placeholder_kinds"], "")
        self.assertTrue(r["title2"])
        self.assertTrue(r["s504"])
        self.assertTrue(r["ocr"])
        self.assertTrue(r["new_date"])
        self.assertFalse(r["date_2028"])
        self.assertTrue(r["contact"])
        self.assertEqual(r["vendor_named"], "finalsite")
        self.assertFalse(r["students_threshold"])
        self.assertNotIn("help@example.org", r["date_snippet"])

    def test_students_threshold(self):
        r = dc.check_text(STUDENTS)
        self.assertTrue(r["students_threshold"])
        self.assertIn("50,000 or more students", r["threshold_snippet"])
        self.assertTrue(r["date_2028"])
        self.assertTrue(dc.check_text("Enrollment of 50,000 is not the test." + FILLER)
                        ["students_threshold"])
        self.assertFalse(dc.check_text("A population of 50,000 or more people." + FILLER)
                         ["students_threshold"])

    def test_government_template_flags_still_count(self):
        r = dc.check_text("The YOURMUNICIPALITY website. NAME TITLE EMAIL PHONE" + FILLER)
        self.assertTrue(r["placeholder"])
        self.assertIn("muni", r["placeholder_kinds"])
        self.assertIn("contact_block", r["placeholder_kinds"])

    def test_ordinary_brackets_are_not_placeholders(self):
        r = dc.check_text("See the board policy [PDF] and the calendar [updated]." + FILLER)
        self.assertFalse(r["placeholder"])
        self.assertTrue(dc.check_text("Call [Insert phone] today." + FILLER)["placeholder"])

    def test_platforms(self):
        body = b'<html><link href="https://resources.finalsite.net/x.css"><div id="wp-content">'
        self.assertEqual(dc.platforms(body), "finalsite+wordpress")
        self.assertEqual(dc.platforms(b"<html><p>plain</p></html>"), "")

    def test_flags_keep_template_check_order(self):
        self.assertEqual(dc.FLAGS[:4], ("muni", "template_note", "contact_block", "bracket"))
        self.assertEqual(len(set(dc.FLAGS)), len(dc.FLAGS))


if __name__ == "__main__":
    unittest.main()
