"""Tests for lang.py: the language check on small PDFs built here (known declared, element,
marked-content and text languages), the child process, and the summary's pre-registered counts
on made-up records. Needs pypdf, py3langid and langdetect; no network.
Apache-2.0 licensed."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lang  # noqa: E402

SPANISH = [
    "El ayuntamiento de la ciudad invita a todos los residentes a la reunion publica",
    "que se celebrara el martes por la noche en la biblioteca central del distrito.",
    "Durante la reunion se presentara el nuevo plan de transporte y los vecinos",
    "podran hacer preguntas sobre las rutas de autobus, las paradas y los horarios.",
    "Tambien habra informacion sobre los programas de asistencia para el pago del agua",
    "y de la electricidad para las familias con ingresos bajos y las personas mayores.",
    "Si necesita un interprete o una adaptacion por discapacidad, llame a la oficina",
    "del secretario municipal por lo menos tres dias antes de la fecha de la reunion.",
]
ENGLISH = [
    "The city council invites all residents to a public meeting on Tuesday evening",
    "at the central branch of the public library to discuss the new transit plan.",
    "During the meeting staff will present the proposed bus routes, stops and schedules,",
    "and residents will be able to ask questions and leave written comments for the board.",
    "Information will also be available about assistance programs that help families",
    "with low incomes and older adults pay their water and electricity bills each month.",
    "If you need an interpreter or a disability accommodation, please call the office",
    "of the city clerk at least three days before the date of the meeting. Thank you.",
]


def make_pdf(lines, lang_token=None, elem_lang=None, mc_lang=None):
    """A one-page PDF in Helvetica. lang_token is the catalog's /Lang as written, e.g. "(en-US)"
    or "/en-US"; elem_lang gives one structure element that /Lang; mc_lang wraps the page's
    text in a /Span marked-content sequence with that /Lang."""
    ops = ["BT", "/F1 10 Tf", "72 720 Td"]
    for i, line in enumerate(lines):
        if i:
            ops.append("0 -14 Td")
        ops.append("(%s) Tj" % line)
    ops.append("ET")
    content = "\n".join(ops)
    if mc_lang:
        content = "/Span <</Lang (%s)>> BDC\n%s\nEMC" % (mc_lang, content)
    content = content.encode("latin-1")
    cat = "<< /Type /Catalog /Pages 2 0 R"
    if lang_token is not None:
        cat += " /Lang %s" % lang_token
    if elem_lang is not None:
        cat += " /StructTreeRoot 6 0 R /MarkInfo << /Marked true >>"
    cat += " >>"
    objs = [cat, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            None]
    if elem_lang is not None:
        objs += ["<< /Type /StructTreeRoot /K 7 0 R >>",
                 "<< /Type /StructElem /S /P /P 6 0 R /Pg 3 0 R /Lang (%s) /K 0 >>" % elem_lang]
    out = bytearray(b"%PDF-1.7\n")
    offsets = []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        if o is None:
            out += b"%d 0 obj\n<< /Length %d >>\nstream\n" % (i, len(content))
            out += content + b"\nendstream\nendobj\n"
        else:
            out += ("%d 0 obj\n%s\nendobj\n" % (i, o)).encode("latin-1")
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


class Codes(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(lang.norm("en-US"), "en")
        self.assertEqual(lang.norm("EN_us"), "en")
        self.assertEqual(lang.norm("zh-cn"), "zh")
        self.assertEqual(lang.norm("iw"), "he")
        self.assertEqual(lang.norm("spa"), "es")
        self.assertIsNone(lang.norm("x-none"))
        self.assertIsNone(lang.norm("English"))
        self.assertIsNone(lang.norm("/en-US"))
        self.assertIsNone(lang.norm(""))
        self.assertIsNone(lang.norm(None))

    def test_well_formed(self):
        for v in ("en-US", "es", "zh-Hant-TW", "x-none", "EN-us"):
            self.assertTrue(lang.WELL_FORMED.fullmatch(v), v)
        for v in ("en_US", "English", "/en-US", "en-", "e", "en US"):
            self.assertFalse(lang.WELL_FORMED.fullmatch(v), v)

    def test_chunks(self):
        c = lang.chunks_of("a" * 150 + "\n" + "b" * 60 + "\n\n" + "c" * 120)
        self.assertEqual(len(c), 2)
        self.assertEqual(len(c[0]), 211)
        self.assertEqual(c[1], "c" * 120)
        self.assertEqual(lang.chunks_of("x" * 99), [])
        self.assertEqual(lang.chunks_of("  two   words  \n"), [])


class Check(unittest.TestCase):
    """Known answers: every PDF here has a declared and a text language we chose."""

    @classmethod
    def setUpClass(cls):
        cls.det = lang.Detectors()

    def check(self, *args, **kw):
        return lang.check_bytes(make_pdf(*args, **kw), self.det)

    def test_model_from_any_directory(self):
        # 0.1.0 passed py3langid's relative MODEL_FILE to from_modelpath, which looked for it
        # under the working directory
        self.assertTrue(lang.model_path().is_absolute())
        self.assertTrue(lang.model_path().is_file())
        here = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            os.chdir(d)
            try:
                det = lang.Detectors()
            finally:
                os.chdir(here)
        a, pa, b, pb = det.detect(" ".join(SPANISH[:3]))
        self.assertEqual((a, b), ("es", "es"))
        self.assertGreaterEqual(pa, lang.MIN_PROB)

    def test_spanish_declared_english(self):
        r = self.check(SPANISH, "(en-US)", elem_lang="es-ES")
        self.assertEqual((r["result"], r["text_lang"], r["lang_primary"], r["lang_well_formed"]),
                         ("ok", "es", "en", True))
        self.assertEqual((r["element_lang"], r["element_langs"], r["mc_lang"]), (1, {"es": 1}, 0))
        self.assertEqual(lang.declared(r), "other")
        self.assertTrue(lang.local_match(r))
        self.assertGreaterEqual(r["determined_chars"], lang.MIN_DETERMINED)

    def test_english(self):
        r = self.check(ENGLISH, "(en-US)")
        self.assertEqual((r["text_lang"], r["lang_primary"], r["lang_raw"]), ("en", "en", "en-US"))
        self.assertEqual((r["element_lang"], r["element_langs"], r["mc_lang"], r["mc_langs"]),
                         (0, {}, 0, {}))
        self.assertEqual(lang.declared(r), "match")
        self.assertGreater(r["chunks_confident"], 0)
        self.assertEqual(r["chunks_agree"], r["chunks_confident"])

    def test_missing(self):
        r = self.check(SPANISH)
        self.assertEqual((r["text_lang"], r["lang_present"], r["lang_well_formed"]), ("es", False, None))
        self.assertEqual(lang.declared(r), "none")

    def test_name_not_string(self):
        r = self.check(ENGLISH, "/en-US")
        self.assertEqual((r["lang_present"], r["lang_is_name"], r["lang_well_formed"], r["lang_primary"]),
                         (True, True, False, None))
        self.assertEqual(lang.declared(r), "unusable")

    def test_marked_content(self):
        r = self.check(SPANISH, "(en-US)", mc_lang="es-MX")
        self.assertEqual((r["mc_lang"], r["mc_langs"], r["element_lang"]), (1, {"es": 1}, 0))
        self.assertTrue(lang.local_match(r))

    def test_too_little_text(self):
        r = self.check(ENGLISH[:2], "(en-US)")
        self.assertEqual(r["text_lang"], "undetermined")

    def test_child_process(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(make_pdf(SPANISH, "(es-US)"))
        try:
            r = lang.check_file(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual((r["result"], r["text_lang"], r["lang_primary"]), ("ok", "es", "es"))

    def test_not_a_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"not a pdf")
        try:
            r = lang.check_file(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(r["result"], "error")


def doc(h, text_lang, primary, raw, well=True, el=None, mc=None, qid="Q1", fam="word",
        conf=3, agree=3):
    present = bool(raw)
    return {"qid": qid, "kind": "city", "state": "TX", "url": "https://example.org/%s.pdf" % h,
            "url_sha256": h, "producer_family": fam, "created": "2025-03-01", "tagged": True,
            "result": "ok", "lang_raw": raw, "lang_present": present,
            "lang_well_formed": well if present else None, "lang_primary": primary,
            "lang_is_name": False, "text_chars": 600, "chunks": 3, "chunks_confident": conf,
            "chunks_agree": agree, "determined_chars": 600,
            "text_langs": {text_lang: 600} if lang.is_language(text_lang) else {},
            "text_lang": text_lang, "element_lang": len(el or {}), "element_langs": el or {},
            "struct_capped": False, "mc_lang": len(mc or {}), "mc_langs": mc or {}}


class Summary(unittest.TestCase):
    def setUp(self):
        self.docs = [
            doc("a", "es", "en", "en-US", el={"es": 4}),         # declared English, Spanish locally
            doc("b", "es", None, ""),                            # no /Lang
            doc("c", "es", "es", "es-MX", qid="Q2"),             # right
            doc("d", "vi", "en", "en-US", qid="Q3", conf=4, agree=2),
            doc("e", "en", "en", "en-US"),
            doc("f", "en", None, "English", well=False),         # present but unusable
            doc("g", "en", "fr", "fr-FR", fam="adobe"),          # English text declared French
            doc("h", "en", "en", "en_US", well=False),           # usable but malformed
            doc("i", "mixed", "en", "en-US"),
            doc("j", "undetermined", None, ""),
            {"qid": "Q9", "url_sha256": "k", "result": "error", "error": "x"},
        ]

    def test_counts(self):
        s = lang.summarize(self.docs)
        self.assertEqual(s["version"], lang.__version__)
        self.assertEqual((s["pdfs"], s["ok"], s["determined"], s["english"], s["non_english"],
                          s["non_english_sites"]), (11, 10, 8, 4, 4, 3))
        self.assertEqual(s["check_results"], {"ok": 10, "error": 1})
        self.assertEqual(s["text_lang_counts"], {"en": 4, "es": 3, "vi": 1, "mixed": 1, "undetermined": 1})
        l1 = s["L1_non_english_wrong"]
        self.assertEqual((l1["k"], l1["n"], l1["share"], l1["met"]), (3, 4, 0.75, True))
        lo, hi = l1["cluster_ci95"]
        self.assertTrue(lo <= 0.75 <= hi)
        l2 = s["L2_local_match"]
        self.assertEqual((l2["k"], l2["n"], l2["share"], l2["met"]), (1, 2, 0.5, True))
        l3 = s["L3_english_other"]
        self.assertEqual((l3["k"], l3["n"], l3["share"], l3["met"]), (1, 4, 0.25, False))
        l4 = s["L4_malformed"]
        self.assertEqual((l4["k"], l4["n"], l4["share"], l4["met"]), (2, 8, 0.25, False))
        k = s["K_detector_agreement"]
        self.assertEqual((k["k"], k["n"], k["share"], k["met"]), (29, 31, 0.9355, True))
        self.assertEqual(s["explore_non_english_declared"],
                         {"es:match": 1, "es:none": 1, "es:other": 1, "vi:other": 1})
        self.assertEqual(s["explore_non_english_declared_as"], {"en": 2})
        self.assertEqual(s["explore_english_declared"], {"match": 2, "other": 1, "unusable": 1})
        self.assertEqual(s["explore_non_english_by_family"], {"word": [4, 3]})
        self.assertEqual(s["explore_non_english_by_tagged"], {"tagged": [4, 3]})
        self.assertEqual(s["explore_mixed_declared"], {"en": 1})
        self.assertEqual(s["explore_malformed_values"], {"English": 1, "en_US": 1})
        self.assertEqual(s["explore_lang_is_name"], 0)
        self.assertEqual((s["explore_lang_present_all"]["k"], s["explore_lang_present_all"]["n"]), (8, 10))
        text = lang.report(s)
        self.assertIn("| L1: 50%+ of non-English PDFs have a missing, unusable or other /Lang | 3 of 4, 75.0% (",
                      text)
        self.assertIn("| L3: under 2% of English PDFs declare another language | 1 of 4, 25.0% (", text)
        self.assertIn("**no**", text)
        self.assertNotIn("not testable", text)

    def test_nothing_non_english(self):
        s = lang.summarize([self.docs[4]])
        self.assertIsNone(s["L1_non_english_wrong"]["met"])
        self.assertIsNone(s["L1_non_english_wrong"]["cluster_ci95"])
        self.assertIsNone(s["L2_local_match"]["met"])
        self.assertTrue(s["L3_english_other"]["met"])
        self.assertIn("not testable", lang.report(s))

    def test_public(self):
        row = lang.public(self.docs[0])
        for key in ("url", "qid", "lang_raw"):
            self.assertNotIn(key, row)
        self.assertEqual((row["text_lang"], row["lang_primary"], row["element_langs"]), ("es", "en", {"es": 4}))
        self.assertNotIn("http", str(row))


if __name__ == "__main__":
    unittest.main()
