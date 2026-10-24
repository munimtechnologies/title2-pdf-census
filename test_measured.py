# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""Tests for docs/measured.md, the one-page summary of every result in this repository.

Every number on the page must sit inside a phrase checked here: either against
results/wordsig-v1/summary.json and results/qcfr-v1/summary.json, or against the
README or results page it is copied from, whose own tests recompute it from the data.
Standard library only. Made by MV2 of Munim, Inc. with AI agents.
"""
import json
import os
import posixpath
import re
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = "docs/measured.md"
NUM = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*")
LINK = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
BANNED = ("an ai", "by hand", "hand check", "http", "://")

# (phrase on the page, source file, phrase in the source). Every number in the page
# phrase must also be in the source phrase.
FACTS = [
    ("Code Apache-2.0; this text CC BY 4.0", "docs/qcfr-results.md",
     "Code Apache-2.0; this text and the data CC BY 4.0"),
    # Third full run (0.2.2)
    ("(third full run, 0.2.2)", "README.md", "third full run (0.2.2"),
    ("Of 5,412 PDFs read from 926 websites", "README.md",
     "5,412 PDFs were read from 926 sites"),
    ("towns of 50,000+ people", "README.md", "with a population of 50,000+"),
    ("tagged 60.5%, document language (`/Lang`) set 56.6%", "README.md",
     "tagged 60.5% (59.2-61.8); document language set 56.6% (55.2-57.9)"),
    ("all four basics (tagged, `/Lang` set, a title in the metadata, and not image only)",
     "README.md", "**all four basics**: tagged, language and title set, and not image only"),
    ("and not image only) 22.0%", "README.md", "**All four basics: 22.0% (20.9-23.1).**"),
    ("PDFs created on or after the ADA Title II rule (2024-04-24) are tagged more often than "
     "older ones: 66.2% against 56.0%", "README.md",
     "(created on or after 2024-04-24) against before:** tagged 66.2% (64.5-68.0) against "
     "56.0% (54.1-58.0)"),
    # tagtree
    ("Two of the four predictions held.", "README.md", "**Two of the four predictions held.**"),
    ("Of 753 tagged PDFs from 308 sites", "README.md",
     "On 753 tagged PDFs from 308 local-government sites"),
    ("47 (6.2%)", "README.md", "47 leaky PDFs, not 49 (6.2%, not 6.5%)"),
    ("leave 5% or more of the text on their first 3 pages unreachable", "README.md",
     "leave 5% or more of the text on their first 3 pages unreachable"),
    ("The figure first published was 49 (6.5%)", "README.md", "49 (6.5%) leave"),
    ("correction of 2026-10-18", "README.md", "**Correction (2026-10-18):**"),
    # lang-census
    ("All four predictions and the agreement check held.", "README.md",
     "**All four predictions and the agreement check held.**"),
    ("Of 65 PDFs whose text is not English, from 46 sites", "README.md",
     "65, from 46 sites, are in another language"),
    ("57 (87.7%; site-resampled 95% interval 75.7% to 97.0%)", "README.md",
     "57 (87.7%; site-resampled 95% interval 75.7% to 97.0%)"),
    ("Of the 38 that declare English, 16 name the real language", "README.md",
     "Of the 38 declared English, 16 (42.1%) name the real language"),
    ("3 of 2,813 English PDFs declare another language", "README.md",
     "3 of 2,813 English PDFs declare another language"),
    ("no earlier study measures whether PDF `/Lang` values match the text", "README.md",
     "no earlier study measures whether PDF `/Lang` values match the text"),
    # Word note and wordsig
    ("in 11 of Word's 13, against 2 of 14 for Adobe", "README.md",
     "in 11 of Word's 13 English-declared non-English PDFs parts of the file already carry "
     "the real language, against 2 of 14 for Adobe output"),
    ("1,616 PDFs from 367 Canadian municipal websites", "README.md",
     "On 1,616 PDFs from 367 Canadian municipal websites"),
    ("60 declare a language other than their text's", "README.md",
     "60 declare a language other than their text's"),
    ("only 6 are Word-made and 46 Adobe-made", "README.md", "6 Word-made and 46 Adobe-made"),
    ("minimum of 8 of each", "README.md", "pre-registered minimum of 8 of each"),
    # qcfr
    ("The minimum was 20 PDFs and 4 sites in each group", "docs/qcfr-results.md",
     "minimum was 20 PDFs and 4 sites in each group"),
    ("No new crawl was made", "README.md", "No new crawl was made"),
    # Title II extension follow-ups (deadline split, site split, title mix, title pairs)
    ("On 2026-04-20 the US Department of Justice", "docs/deadline-split-results.md",
     "On 2026-04-20, four days before the original date, the US Department of Justice"),
    ("serving 50,000 or more people from 2026-04-24 to 2027-04-26",
     "docs/deadline-split-results.md",
     "serving 50,000 or more people from 2026-04-24 to 2027-04-26"),
    ("Deadline split, 2 of 6 predictions held", "docs/deadline-split-results.md",
     "2 of 6 pre-registered predictions held"),
    ("Pooled over the 12 months on each side, new PDFs were tagged as often after the "
     "extension as before (67.2% vs 67.3%)", "docs/deadline-split-results.md",
     "Pooled over the 12 months on each side of the extension, PDFs that cities and counties "
     "of 50,000+ created after DOJ postponed the Title II compliance date were tagged as "
     "often as before (67.2% vs 67.3%)"),
    ("In the last 3 months before it, 74.4% were tagged; in the first 3 months after, 66.7%",
     "docs/deadline-split-results.md",
     "last 3 months before: 74.4%; first 3 months after: 66.7%"),
    ("The share with a title fell from 45.1% to 39.0%", "docs/deadline-split-results.md",
     "45.1% (488/1,081) | 39.0% (446/1,143)"),
    ("Site split, 4 of 6 held", "docs/site-split-results.md",
     "4 of 6** pre-registered predictions held"),
    ("the site-weighted share fell 5.5 points", "docs/site-split-results.md",
     "the site-weighted share fell 5.5 points"),
    ("among the 102 governments that posted in both windows, slightly more went up (25) "
     "than down (20)", "docs/site-split-results.md",
     "among the 102 governments that posted in **both** windows, slightly more went up (25) "
     "than down (20)"),
    ("sign test gave p = 0.55", "docs/site-split-results.md", "sign test gave p = 0.55"),
    ("Title mix, 6 of 6 held", "docs/title-mix-results.md",
     "6 of 6** pre-registered predictions held"),
    ("is a change in software mix (-0.8 points). It is a change within the same software "
     "groups (-5.3 points", "docs/title-mix-results.md",
     "is a change in software mix (−0.8 points). It is a change **within** the same "
     "software groups (−5.3 points"),
    ("Title pairs, 5 of 6 held", "docs/title-pairs-results.md",
     "5 of 6** pre-registered predictions held"),
    ("Within the 329 governments with files on both sides, the average title share fell 3.7 "
     "points (93 up, 103 down, sign test p = 0.52)", "docs/title-pairs-results.md",
     "Within the 329 governments with files on both sides, the average change is −3.7 "
     "points (−9.5 to +2.1): 93 governments went up, 103 went down and 133 did not "
     "change (sign test p = 0.52)"),
    ("In the three months either side of the extension, the 102 governments with files on "
     "both sides show no drop at all (+0.8 points)", "docs/title-pairs-results.md",
     "In the three months either side of the extension, the 102 governments with files on "
     "both sides show no drop at all (+0.8 points)"),
    # site_check and limits
    ("Since 0.2.0 it also compares", "README.md", "(since 0.2.0)"),
    ("Text languages are read from the first 5 pages", "README.md",
     "text from the first 5 pages only"),
]


def read(path):
    with open(os.path.join(ROOT, *path.split("/")), encoding="utf-8") as f:
        return f.read()


def load(path):
    return json.loads(read(path))


def flat(text):
    return " ".join(text.split())


def nums(text):
    return set(NUM.findall(text))


def summary_facts():
    """(pattern on the page, expected values): ints exact, shares to 0.05 points."""
    ws = load("results/wordsig-v1/summary.json")
    qc = load("results/qcfr-v1/summary.json")
    w1 = ws["W1_word_marks_inside_more_than_adobe"]
    fw = ws["explore_french_wrong"]
    q1 = qc["Q1_rest_wrong_more_than_quebec"]
    rest, que = q1["rest"], q1["quebec"]
    return [
        (r"([\d,]+) PDFs from 367 Canadian", [ws["pdfs"]]),
        (r"(\d+) declare a language other than their text's", [ws["mismatched"]]),
        (r"only (\d+) are Word-made and (\d+) Adobe-made", [w1["word"]["n"], w1["adobe"]["n"]]),
        (r"(\d+) of (\d+) French-text PDFs \(([\d.]+)%; site-resampled 95% interval "
         r"([\d.]+)% to ([\d.]+)%\)",
         [fw["k"], fw["n"], fw["share"], fw["cluster_ci95"][0], fw["cluster_ci95"][1]]),
        (r"Outside Quebec the crawl has (\d+) French-text PDFs from (\d+) sites, and all (\d+)",
         [rest["n"], rest["sites"], rest["k"]]),
        (r"Quebec has (\d+) from (\d+) sites, (\d+) of them \(([\d.]+)%\)",
         [que["n"], que["sites"], que["k"], que["share"]]),
    ]


class MeasuredPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = read(PAGE)
        cls.page = flat(cls.raw)

    def test_facts_match_their_sources(self):
        for page_phrase, source, source_phrase in FACTS:
            with self.subTest(page_phrase=page_phrase):
                self.assertIn(page_phrase, self.page)
                self.assertIn(flat(source_phrase), flat(read(source)))
                self.assertLessEqual(nums(page_phrase), nums(source_phrase))

    def test_numbers_match_summaries(self):
        for pattern, expected in summary_facts():
            with self.subTest(pattern=pattern):
                m = re.search(pattern, self.page)
                self.assertIsNotNone(m)
                for got, want in zip(m.groups(), expected):
                    if isinstance(want, float):
                        self.assertLessEqual(abs(float(got) - 100 * want), 0.05 + 1e-9)
                    else:
                        self.assertEqual(int(got.replace(",", "")), want)

    def test_verdicts_match_summaries(self):
        ws = load("results/wordsig-v1/summary.json")
        qc = load("results/qcfr-v1/summary.json")
        self.assertEqual(ws["W1_word_marks_inside_more_than_adobe"]["status"],
                         "inconclusive: too few")
        self.assertEqual(qc["Q1_rest_wrong_more_than_quebec"]["status"], "inconclusive: too few")
        self.assertIn("367 Canadian municipal websites: inconclusive, too few.", self.page)
        self.assertIn("(qcfr, pre-registered) Inconclusive, too few.", self.page)

    def test_every_number_is_checked(self):
        blanked = LINK.sub(lambda m: " " * len(m.group(0)), self.page)
        covered = [False] * len(self.page)
        spans = []
        for page_phrase, _, _ in FACTS:
            start = self.page.find(page_phrase)
            while start != -1:
                spans.append((start, start + len(page_phrase)))
                start = self.page.find(page_phrase, start + 1)
        for pattern, _ in summary_facts():
            spans.extend(m.span() for m in re.finditer(pattern, self.page))
        for a, b in spans:
            covered[a:b] = [True] * (b - a)
        unchecked = [m.group(0) for m in NUM.finditer(blanked)
                     if not all(covered[m.start():m.end()])]
        self.assertEqual(unchecked, [])

    def test_links_are_pages_the_readme_links(self):
        targets = {t for _, t in LINK.findall(read("README.md"))}
        links = LINK.findall(self.raw)
        self.assertGreaterEqual(len(links), 8)
        for _, target in links:
            with self.subTest(target=target):
                path = posixpath.normpath(posixpath.join("docs", target))
                if target.endswith("/"):
                    path += "/"
                self.assertTrue(path == "README.md" or path in targets, path)

    def test_wording(self):
        lower = self.raw.lower()
        for word in BANNED:
            self.assertNotIn(word, lower)
        self.assertTrue(self.raw.isascii())
        self.assertIsNone(re.search(r"\bMIT\b", self.raw))
        self.assertIn("Apache-2.0", self.raw)
        self.assertTrue(self.raw.endswith("Made by MV2 of Munim, Inc. with AI agents.\n"))


if __name__ == "__main__":
    unittest.main()
