"""district_check 0.1.0: what does a US school district's accessibility page say?

The page-reading rules of MV2's pre-registered district-pages study (results/district-pages/
PREREG.md). Everything statement_check.py reports (which WCAG version a page promises, the stock
"We work to comply with Section 508 as well as ..." sentence, the Title II dates, contact
details) and template_check.py's placeholder flags, both unchanged, plus what school-website
templates leave behind and what district pages say about the rule:

  * school placeholders: a bracketed "[Your School]", "[School Name]", "[District Name]" or
    "[Insert ...]"; "the Your School website"; a "yourschool.com"-style address; the dummy
    phone number 555-555-5555; "within # business days";
  * the 50,000 threshold given in students: the ADA Title II rule (28 CFR 35.200) splits its
    two dates by the total population of the district's area, not by enrollment;
  * the Office for Civil Rights, Section 504, a school-website vendor named on the page, the
    Finalsite template's line "built with WCAG 2.1 AA guidelines in mind", and a statement-
    generator credit line.

It reads what a page says, not whether the site meets WCAG, and it is not legal advice.
Needs a11y_pages.py, statement_check.py and template_check.py from this repository next to it.
Standard library only. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (pinned: parser, snippets, scrubbing)
import statement_check as sc  # noqa: E402  (pinned: versions, stock sentence, dates, contact)
import template_check as tc  # noqa: E402  (pinned: the four government-template flags)

__version__ = "0.1.0"

SCHOOL_BRACKET_RE = re.compile(
    r"\[\s*(?:(?:your|the|insert|name\s+of(?:\s+the)?)\s+)?(?:school|district|school\s+district|"
    r"organi[sz]ation|campus)(?:\s+(?:name|district|website|url))?\s*\]|\[\s*insert\b[^\[\]]{0,60}\]",
    re.I)
YOUR_SCHOOL_RE = re.compile(r"\bthe Your (?:School|District)\b")
YOUR_DOMAIN_RE = re.compile(r"\byour(?:school|district|website|domain|site|organi[sz]ation)"
                            r"\.(?:com|org|net|edu|us)\b", re.I)
FAKE_PHONE_RE = re.compile(r"\b555[\s.-]555[\s.-]5555\b")
HASH_DAYS_RE = re.compile(r"\bwithin\s+#\s+(?:business\s+|working\s+)?days\b", re.I)
SCHOOL_FLAGS = ("school_bracket", "your_school", "your_domain", "fake_phone", "hash_days")
FLAGS = tc.FLAGS + SCHOOL_FLAGS

STUDENTS_RE = re.compile(
    r"\b50,?000\s+(?:or\s+more\s+|\+\s*|plus\s+)?(?:students|pupils)\b|"
    r"\b(?:students|pupils|enrollment|enrolment)\s+(?:of\s+)?(?:over\s+|under\s+|fewer\s+than\s+|"
    r"less\s+than\s+|more\s+than\s+|at\s+least\s+)?50,?000\b", re.I)
OCR_RE = re.compile(r"\bOffice\s+for\s+Civil\s+Rights\b|\bOCR\b")
S504_RE = re.compile(r"\bSection\s+504\b", re.I)
FINALSITE_LINE_RE = re.compile(r"\bbuilt\s+with\s+WCAG\s+2\.1\s+AA\s+guidelines\s+in\s+mind\b",
                               re.I)
GENERATOR_RE = re.compile(r"\bAccessibility\s+Statement\s+Generator\b", re.I)
VENDORS = (("apptegy", r"\bApptegy\b|\bThrillshare\b"), ("blackboard", r"\bBlackboard\b"),
           ("catapult", r"\bCatapult\s?K12\b|\bCatapultCMS\b"), ("civicplus", r"\bCivicPlus\b"),
           ("edlio", r"\bEdlio\b"), ("finalsite", r"\bFinalsite\b"),
           ("schoolblocks", r"\bSchoolBlocks\b"), ("schoolmessenger", r"\bSchoolMessenger\b"),
           ("schoolpointe", r"\bSchoolPointe\b"), ("sharpschool", r"\bSharpSchool\b"))
VENDOR_RES = tuple((name, re.compile(rx, re.I)) for name, rx in VENDORS)

# Home-page markup of school-website platforms (lower-case bytes); reported, never graded.
PLATFORMS = (("apptegy", b"apptegy"), ("apptegy", b"thrillshare"), ("blackboard", b"blackboard"),
             ("catapult", b"catapultk12"), ("catapult", b"catapultcms"),
             ("civicplus", b"civicplus"), ("edlio", b"edlio"), ("finalsite", b"finalsite"),
             ("schoolblocks", b"schoolblocks"), ("schoolmessenger", b"schoolmessenger"),
             ("schoolpointe", b"schoolpointe"), ("sharpschool", b"sharpschool"),
             ("wordpress", b"wp-content"))


def check_text(text):
    """The district study's reading of one accessibility page's visible text."""
    text = " ".join(text.replace("\xa0", " ").split())
    r = sc.check_text(text, small=False)
    t = tc.check_text(text)
    flags = {k: t[k] for k in tc.FLAGS}
    b = SCHOOL_BRACKET_RE.search(text)
    flags.update(school_bracket=bool(b), your_school=bool(YOUR_SCHOOL_RE.search(text)),
                 your_domain=bool(YOUR_DOMAIN_RE.search(text)),
                 fake_phone=bool(FAKE_PHONE_RE.search(text)),
                 hash_days=bool(HASH_DAYS_RE.search(text)))
    kinds = [k for k in FLAGS if flags[k]]
    placeholder_text = t["bracket_text"] or (ap.scrub(b.group(0))[:100] if b else "")
    m = STUDENTS_RE.search(text)
    out = {"wcag_any": r["wcag_any"], "versions": r["versions"], "highest": r["highest"],
           "section508": r["section508"], "title2": r["title2"],
           "old_date": r["date_2026_04_24"], "new_date": r["date_2027_04_26"],
           "date_2028": r["date_2028_04_26"], "stock": r["stock_sentence"],
           "contact": r["contact"], "findings": "+".join(f["id"] for f in r["findings"]),
           "version_snippet": r["version_snippet"],
           "placeholder": bool(kinds), "placeholder_kinds": "+".join(kinds),
           "placeholder_text": placeholder_text,
           "no_wcag": t["no_wcag"],
           "students_threshold": bool(m),
           "threshold_snippet": ap.snippet(text, m) if m else "",
           "ocr": bool(OCR_RE.search(text)), "s504": bool(S504_RE.search(text)),
           "vendor_named": "+".join(sorted({n for n, rx in VENDOR_RES if rx.search(text)})),
           "finalsite_line": bool(FINALSITE_LINE_RE.search(text)),
           "generator_line": bool(GENERATOR_RE.search(text))}
    c = ap.classify(text)
    out["date_snippet"] = c["date_snippet"]
    return out


def platforms(body):
    """School-website platforms whose markup appears on a home page (reported only)."""
    low = body.lower()
    return "+".join(sorted({name for name, mark in PLATFORMS if mark in low}))
