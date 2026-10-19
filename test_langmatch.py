"""Offline tests for langmatch and site_check 0.2.0's /Lang-against-text check (no network).
The PDF tests need pypdf and the detector tests py3langid and langdetect; each is skipped if
its package is missing. Apache-2.0 licensed."""

import importlib.util
import inspect
import json
import os
import sys
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import langmatch as lm  # noqa: E402
import site_check as sc  # noqa: E402

HAVE_PYPDF = importlib.util.find_spec("pypdf") is not None
HAVE_DETECTORS = all(importlib.util.find_spec(m) is not None for m in ("py3langid", "langdetect"))
LANG_PY = os.path.join(HERE, "results", "lang-v1", "lang.py")
COPIED = ("norm", "resolve", "text_of", "chunks_of", "model_path", "Detectors", "detect_doc",
          "element_langs", "raw_contents", "content_langs")
CONSTANTS = ("TEXT_PAGES", "MAX_TEXT", "CHUNK", "MAX_CHUNKS", "MIN_PROB", "MIN_DETERMINED",
             "MAJORITY", "NODE_CAP", "ALIASES", "MC_LANG")
SPANISH = ("Aviso público sobre la reunión del concejo municipal. La ciudad invita a todos los "
           "residentes a participar en la audiencia pública sobre el presupuesto anual. Los documentos "
           "estarán disponibles en la biblioteca y en el sitio web de la ciudad. Si necesita servicios de "
           "interpretación o adaptaciones por discapacidad, comuníquese con la oficina del secretario "
           "municipal al menos tres días antes de la reunión. Las personas que deseen hablar deberán "
           "inscribirse antes del comienzo de la sesión. El concejo también considerará cambios en las "
           "tarifas de agua y alcantarillado, así como nuevos proyectos de mantenimiento de calles y "
           "parques. Todos los comentarios por escrito deben enviarse antes del viernes a mediodía.")


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return f.read()


def make_pdf(lines, lang="en-US"):
    """A one-page PDF with the given lines of text (Helvetica, WinAnsi) and catalog /Lang."""
    stream = b"BT /F1 10 Tf 12 TL 40 760 Td " + b"".join(
        b"(" + line.encode("cp1252") + b") Tj T* " for line in lines) + b"ET"
    catalog = b"<< /Type /Catalog /Pages 2 0 R" + (b" /Lang (" + lang.encode() + b")" if lang else b"") + b" >>"
    objs = [catalog, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >>"
            b" /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % off for off in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out


class Always:
    """A stand-in for lm.Detectors: both detectors always name `code` with probability 0.99."""

    def __init__(self, code):
        self.code = code

    def detect(self, text):
        return self.code, 0.99, self.code, 0.99


class SameRulesAsLangCensus(unittest.TestCase):
    """langmatch's detection code is lang-census's, unchanged."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("lang_census_lang", LANG_PY)
        cls.lang = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.lang  # inspect.getsource needs it for the class
        spec.loader.exec_module(cls.lang)

    def test_version(self):
        self.assertEqual(self.lang.__version__, lm.LANG_VERSION)

    def test_functions_are_copies(self):
        for name in COPIED:
            self.assertEqual(inspect.getsource(getattr(lm, name)), inspect.getsource(getattr(self.lang, name)),
                             name)

    def test_constants_are_the_same(self):
        for name in CONSTANTS:
            self.assertEqual(getattr(lm, name), getattr(self.lang, name), name)

    def test_verdict_is_lang_declared(self):
        for declared, text in (("en", "es"), ("es", "es"), (None, "es"), ("en", "mixed"), (None, "undetermined")):
            d = {"lang_present": declared is not None, "lang_primary": declared, "text_lang": text}
            want = self.lang.declared(d) if lm.is_language(text) else None
            self.assertEqual(lm.verdict(declared, text), want, (declared, text))


class NoteTests(unittest.TestCase):
    def test_declares_another_language(self):
        lc = {"checked": True, "declared": "en", "declared_raw": "en-US", "text_lang": "es",
              "local_match": False, "verdict": "other"}
        note = lm.note(lc, True)
        for text in ("Its text looks like Spanish, but its document language says English",
                     "read it with English pronunciation", "Set the document language to Spanish",
                     "File > Properties > Advanced > Language", "Set Proofing Language"):
            self.assertIn(text, note)
        self.assertNotIn("already tagged", note)
        self.assertIn("Some parts are already tagged as Spanish", lm.note(dict(lc, local_match=True), True))

    def test_no_or_unusable_language(self):
        lc = {"checked": True, "declared": None, "declared_raw": "", "text_lang": "vi",
              "local_match": False, "verdict": "none"}
        self.assertEqual(lm.note(lc, False),
                         "Its text looks like Vietnamese: when you set the document language, choose Vietnamese.")
        self.assertIn("(/en-US) is not a language code", lm.note(dict(lc, declared_raw="/en-US"), True))

    def test_nothing_to_say(self):
        for lc in (None, {}, {"checked": False}, {"checked": True, "verdict": "match", "text_lang": "es"},
                   {"checked": True, "verdict": None, "text_lang": "mixed"}):
            self.assertIsNone(lm.note(lc, True), lc)

    def test_names(self):
        self.assertEqual((lm.name("es"), lm.name("tl"), lm.name("xx")), ("Spanish", "Tagalog", "xx"))

    def test_not_checked_without_detectors(self):
        self.assertEqual(lm.check(b"%PDF-1.4", None), {"checked": False})


class SiteCheckTests(unittest.TestCase):
    OTHER = {"checked": True, "declared": "en", "declared_raw": "en-US", "text_lang": "es",
             "local_match": False, "verdict": "other"}

    def result(self, lang_checks, on=True):
        rows = []
        for i, lc in enumerate(lang_checks):
            rec = {"url": "https://a.gov/%d.pdf" % i, "result": "ok", "tagged": True, "lang": True, "title": True,
                   "image_only": False, "display_doc_title": True, "producer_family": "word"}
            if lc is not None:
                rec["lang_check"] = lc
            rows.append(dict(rec, fails=sc.failures(rec), notes=sc.notes(rec)))
        return {"version": sc.__version__, "census_version": "0.2.2", "checked": "2026-10-19", "site": None,
                "pdfs": rows, "summary": {"pdfs_checked": len(rows), "pdfs_not_read": 0,
                                          "pass_all_four": len(rows), "fail": {}},
                "lang_check": sc.lang_summary(rows, on)}

    def test_version(self):
        self.assertEqual(sc.__version__, "0.2.0")

    def test_mismatch_is_a_note_not_a_fifth_basic(self):
        r = self.result([self.OTHER])
        row = r["pdfs"][0]
        self.assertEqual(row["fails"], [])
        self.assertTrue(row["notes"][0].startswith("Its text looks like Spanish"))
        md = sc.markdown(r)
        self.assertIn("## Also worth fixing", md)
        self.assertIn("- 0.pdf: Its text looks like Spanish", md)
        self.assertIn("- 1 PDFs checked; 1 pass all four basics; 0 could not be read.", md)

    def test_summary_and_line(self):
        match = dict(self.OTHER, declared="es", verdict="match")
        none = dict(self.OTHER, declared=None, verdict="none")
        unclear = dict(self.OTHER, text_lang="undetermined", verdict=None)
        r = self.result([self.OTHER, match, none, unclear, {"checked": False, "error": "x"}])
        self.assertEqual(r["lang_check"], {"on": True, "checked": 4, "text_language_found": 3,
                                           "declares_other": 1, "declares_none": 1})
        md = sc.markdown(r)
        self.assertIn("- Document language against the text: the text's language was clear in 3 of 4 PDFs; "
                      "1 of those declare a different language and 1 declare none.", md)
        self.assertIn(sc.LANG_FINDING, md)

    def test_line_when_not_checked(self):
        md = sc.markdown(self.result([None]))
        self.assertIn("- Document language against the text: " + sc.LANG_MISSING, md)
        self.assertNotIn(sc.LANG_FINDING, md)
        self.assertIn("not checked (turned off)", sc.markdown(self.result([None], on=False)))
        empty = self.result([])
        self.assertIsNone(sc.lang_line(empty))

    def test_dataset_rows(self):
        rows = sc.dataset_rows(self.result([self.OTHER, None]))
        self.assertEqual((rows[0]["declared_lang"], rows[0]["text_lang"], rows[0]["lang_matches_text"]),
                         ("en", "es", False))
        self.assertEqual((rows[1]["declared_lang"], rows[1]["text_lang"], rows[1]["lang_matches_text"]),
                         (None, None, None))

    def test_cli_flag(self):
        self.assertTrue(sc.parser().parse_args(["https://a.gov/", "--no-lang-check"]).no_lang_check)
        self.assertFalse(sc.parser().parse_args(["https://a.gov/"]).no_lang_check)

    def test_quoted_lang_census_numbers(self):
        s = json.loads(read("results", "lang-v1", "summary.json"))["L1_non_english_wrong"]
        self.assertIn("%d of %d PDFs whose text is not English (%.1f%%)" % (s["k"], s["n"], 100 * s["share"]),
                      sc.LANG_FINDING)

    def test_actor_files(self):
        self.assertIn("langmatch.py", read(".actor", "Dockerfile"))
        req = read("requirements-actor.txt").split()
        for pin in ("py3langid==0.4.0", "langdetect==1.0.9"):
            self.assertIn(pin, req)
        self.assertIn("pypdf 6.21.1 py3langid 0.4.0 langdetect 1.0.9",
                      read("results", "lang-v1", "code-sha256.txt"))


@unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
class PdfTests(unittest.TestCase):
    def test_check_with_a_stand_in(self):
        pdf = make_pdf(textwrap.wrap(SPANISH, 70), lang="en-US")
        lc = lm.check(pdf, Always("es"))
        self.assertEqual((lc["checked"], lc["declared"], lc["declared_raw"], lc["text_lang"], lc["verdict"]),
                         (True, "en", "en-US", "es", "other"))
        self.assertEqual((lc["local_langs"], lc["local_match"]), ([], False))
        self.assertEqual(lm.check(make_pdf(textwrap.wrap(SPANISH, 70), lang=None), Always("es"))["verdict"], "none")
        self.assertEqual(lm.check(make_pdf(["Too short."], lang="es"), Always("es"))["verdict"], None)

    def test_pdf_record_keeps_the_basics_if_the_check_fails(self):
        class Broken:
            def detect(self, text):
                raise RuntimeError("boom")

        class Resp:
            status, truncated, body = 200, False, make_pdf(textwrap.wrap(SPANISH, 70))

        sc._DETECTORS[:] = [Broken()]
        try:
            rec = sc.pdf_record("https://a.gov/x.pdf", Resp())
        finally:
            sc._DETECTORS[:] = []
        self.assertEqual(rec["result"], "ok")
        self.assertEqual(rec["lang_check"]["checked"], False)
        self.assertIn("RuntimeError: boom", rec["lang_check"]["error"])
        self.assertNotIn("lang_check", sc.pdf_record("https://a.gov/x.pdf", Resp(), lang=False))


@unittest.skipUnless(HAVE_PYPDF and HAVE_DETECTORS, "pypdf, py3langid or langdetect not installed")
class RealDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.det = lm.detectors()

    def test_spanish_declared_english(self):
        lc = lm.check(make_pdf(textwrap.wrap(SPANISH, 70), lang="en-US"), self.det)
        self.assertEqual((lc["text_lang"], lc["verdict"]), ("es", "other"), lc)
        self.assertIn("Its text looks like Spanish, but its document language says English", lm.note(lc, True))

    def test_spanish_declared_spanish(self):
        lc = lm.check(make_pdf(textwrap.wrap(SPANISH, 70), lang="es-MX"), self.det)
        self.assertEqual((lc["declared"], lc["text_lang"], lc["verdict"]), ("es", "es", "match"), lc)
        self.assertIsNone(lm.note(lc, True))


if __name__ == "__main__":
    unittest.main()
