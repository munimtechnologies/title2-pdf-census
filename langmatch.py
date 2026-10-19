"""langmatch: does a PDF's declared document language match the language of its text?

site_check's /Lang-against-text check (0.2.0). Screen readers pick a voice and pronunciation
rules from the PDF's document language (the catalog's /Lang), so a Spanish notice declared
English is read aloud with English rules. In the pre-registered lang-census
(docs/lang-census-results.md), 57 of 65 local-government PDFs whose text is not English had a
missing or wrong /Lang.

The detection rules are lang-census's own: the functions below from norm() to content_langs()
are copied unchanged from results/lang-v1/lang.py 0.1.1 (test_langmatch.py checks that they
still match), so a site_check report reads a PDF exactly as the census did. The text of the
first 5 pages is split into chunks of about 200 characters, each read by two independent
detectors (py3langid and langdetect); a chunk counts only where both name the same language with
probability 0.9 or more. Both detectors are optional: without them, check() says "not checked".

Since 0.1.1 (site_check 0.2.1), when a PDF declares one language while parts of it are already
marked with the text's language, the note leads with the Acrobat fix and says that re-applying
Word's proofing language may not help: in the census, 11 of the 13 Word-made non-English PDFs
declared English looked like this (docs/lang-word-note.md, exploratory).

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import collections
import io
import re

__version__ = "0.1.1"
LANG_VERSION = "0.1.1"  # the lang.py these rules are copied from

TEXT_PAGES = 5            # pages whose text, element and marked-content languages are read
MAX_TEXT = 20_000         # characters of text kept per PDF
CHUNK = 200               # characters per chunk given to the detectors
MAX_CHUNKS = 60
MIN_PROB = 0.9            # both detectors must reach this on a chunk
MIN_DETERMINED = 400      # characters of agreed chunks a PDF needs for a text language
MAJORITY = 0.8            # share of agreed characters the top language needs, else "mixed"
NODE_CAP = 20_000
# Deprecated or alternative codes, so declared and detected languages compare like for like.
ALIASES = {"iw": "he", "in": "id", "ji": "yi", "nb": "no", "nn": "no", "fil": "tl",
           "eng": "en", "spa": "es", "zho": "zh", "chi": "zh", "vie": "vi", "kor": "ko"}
MC_LANG = re.compile(rb"/Lang\s*\(([^)]{0,35})\)")
# Where the note on Word-made PDFs with the right language inside and the wrong one outside lives.
WORD_NOTE = "https://github.com/munimtechnologies/title2-pdf-census/blob/main/docs/lang-word-note.md"

# English names for the report; any other code is shown as it is.
NAMES = {"en": "English", "es": "Spanish", "zh": "Chinese", "vi": "Vietnamese", "ko": "Korean",
         "ru": "Russian", "fr": "French", "pt": "Portuguese", "tl": "Tagalog", "ar": "Arabic",
         "ht": "Haitian Creole", "de": "German", "it": "Italian", "ja": "Japanese", "pl": "Polish",
         "hi": "Hindi", "fa": "Persian", "uk": "Ukrainian", "so": "Somali", "hy": "Armenian",
         "km": "Khmer", "lo": "Lao", "th": "Thai", "ur": "Urdu", "bn": "Bengali", "pa": "Punjabi",
         "el": "Greek", "he": "Hebrew", "nl": "Dutch", "tr": "Turkish", "am": "Amharic"}


def name(code):
    return NAMES.get(code, code)


def is_language(t):
    return t not in (None, "undetermined", "mixed")


# ---------------------------------------------------------------- copied from lang.py 0.1.1

def norm(code):
    """'en-US' -> 'en', 'zh-cn' -> 'zh'; None if there is no 2-3 letter primary subtag."""
    if not code:
        return None
    first = re.split(r"[-_\s]", str(code).strip().lower(), maxsplit=1)[0]
    if not re.fullmatch(r"[a-z]{2,3}", first):
        return None
    return ALIASES.get(first, first)


def resolve(obj):
    return obj.get_object() if hasattr(obj, "get_object") else obj


def text_of(v):
    if isinstance(v, bytes):
        return v.decode("latin-1").strip()
    return str(v).strip()


def chunks_of(text, size=CHUNK):
    """Whole lines joined into chunks of at least size characters; a short tail is kept only
    if it has half that."""
    out, cur, n = [], [], 0
    for line in text.splitlines():
        line = " ".join(line.split())
        if not line:
            continue
        cur.append(line)
        n += len(line)
        if n >= size:
            out.append(" ".join(cur))
            cur, n = [], 0
    if cur and n >= size // 2:
        out.append(" ".join(cur))
    return out


def model_path():
    """py3langid's bundled model as an absolute path. In py3langid 0.4.0 MODEL_FILE is
    'data/model.npz.xz', relative to the package, and from_modelpath resolves a relative path
    against the working directory, so passing MODEL_FILE as it is fails outside the package."""
    import pathlib
    from py3langid import langid
    path = pathlib.Path(langid.MODEL_FILE)
    if not path.is_absolute():
        path = pathlib.Path(langid.__file__).resolve().parent / path
    return path


class Detectors:
    """py3langid (normalized probabilities) and langdetect (seeded), loaded once per process."""

    def __init__(self):
        from py3langid.langid import LanguageIdentifier
        from langdetect import DetectorFactory
        self.langid = LanguageIdentifier.from_modelpath(model_path(), norm_probs=True)
        DetectorFactory.seed = 0

    def detect(self, text):
        """(py3langid language, probability, langdetect language, probability)"""
        from langdetect import detect_langs
        from langdetect.lang_detect_exception import LangDetectException
        a, pa = self.langid.classify(text)
        try:
            top = detect_langs(text)[0]
            b, pb = top.lang, top.prob
        except LangDetectException:
            b, pb = None, 0.0
        return norm(a), float(pa), norm(b), float(pb)


def detect_doc(chunks, det):
    """The text language of one PDF from its chunks: a language, "mixed" or "undetermined"."""
    by, total, confident, agree = collections.Counter(), 0, 0, 0
    for c in chunks:
        a, pa, b, pb = det.detect(c)
        total += len(c)
        if pa >= MIN_PROB:
            confident += 1
            agree += int(a == b)
        if a and a == b and pa >= MIN_PROB and pb >= MIN_PROB:
            by[a] += len(c)
    determined = sum(by.values())
    if determined < MIN_DETERMINED or determined < 0.5 * total:
        text_lang = "undetermined"
    else:
        top, n = by.most_common(1)[0]
        text_lang = top if n >= MAJORITY * determined else "mixed"
    return {"chunks": len(chunks), "chunks_confident": confident, "chunks_agree": agree,
            "determined_chars": determined, "text_langs": dict(by), "text_lang": text_lang}


def element_langs(root, cap=NODE_CAP):
    """(structure elements with /Lang, {language: count}, stopped at cap)"""
    tree = resolve(root.get("/StructTreeRoot"))
    if not isinstance(tree, dict):
        return 0, {}, False
    stack, seen, n, langs = [tree.get("/K")], 0, 0, collections.Counter()
    while stack and seen < cap:
        node = resolve(stack.pop())
        seen += 1
        if isinstance(node, list):
            stack.extend(node)
            continue
        if not isinstance(node, dict):
            continue
        if "/Lang" in node:
            n += 1
            langs[norm(text_of(resolve(node["/Lang"]))) or "none"] += 1
        kids = node.get("/K")
        if kids is not None:
            stack.append(kids)
    return n, dict(langs), seen >= cap


def raw_contents(page):
    c = resolve(page.get("/Contents"))
    parts = c if isinstance(c, list) else [c]
    out = b""
    for p in parts:
        p = resolve(p)
        if hasattr(p, "get_data"):
            out += p.get_data() + b"\n"
    return out


def content_langs(pages):
    """(marked-content /Lang entries written inline in the pages' content, {language: count})"""
    n, langs = 0, collections.Counter()
    for page in pages:
        try:
            data = raw_contents(page)
        except Exception:
            continue
        for m in MC_LANG.finditer(data):
            n += 1
            langs[norm(m.group(1).decode("latin-1")) or "none"] += 1
    return n, dict(langs)


# ---------------------------------------------------------------- site_check's use

def detectors():
    """Detectors(), or None if py3langid or langdetect is not installed."""
    try:
        return Detectors()
    except ImportError:
        return None


def verdict(declared, text_lang):
    """How the declared language relates to the text's: "match", "other", "none" (no usable
    /Lang) or None when the text's language could not be told."""
    if not is_language(text_lang):
        return None
    if declared is None:
        return "none"
    return "match" if declared == text_lang else "other"


def check(data, det):
    """The /Lang-against-text record of one PDF (bytes), read as lang-census's check_bytes
    reads it; {"checked": False} if det is None."""
    if det is None:
        return {"checked": False}
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")
    root = resolve(reader.trailer["/Root"])
    value = resolve(root.get("/Lang"))
    raw = "" if value is None else text_of(value)
    pages = [reader.pages[i] for i in range(min(TEXT_PAGES, len(reader.pages)))]
    parts, size = [], 0
    for page in pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        parts.append(t)
        size += len(t)
        if size >= MAX_TEXT:
            break
    text = "\n".join(parts)[:MAX_TEXT]
    doc = detect_doc(chunks_of(text)[:MAX_CHUNKS], det)
    _, el, _ = element_langs(root)
    _, mc = content_langs(pages)
    declared, text_lang = norm(raw), doc["text_lang"]
    return {"checked": True, "declared": declared, "declared_raw": raw[:40], "text_lang": text_lang,
            "text_langs": doc["text_langs"], "local_langs": sorted((set(el) | set(mc)) - {"none"}),
            "local_match": text_lang in el or text_lang in mc,
            "verdict": verdict(declared, text_lang)}


def note(lc, lang_set=False):
    """A plain-words note on one PDF's record from check(), or None if there is nothing to say.
    lang_set: the census's "lang" basic (a non-empty /Lang)."""
    if not lc or not lc.get("checked"):
        return None
    v, text_lang = lc.get("verdict"), lc.get("text_lang")
    if v in (None, "match"):
        return None
    lang = name(text_lang)
    if v == "other" and lc.get("local_match"):
        # The Word signature (docs/lang-word-note.md): the text already carries its language, so
        # setting Word's proofing language again may leave the document language as it was.
        declared = name(lc["declared"])
        return ("Its text looks like %s, but its document language says %s, so a screen reader will "
                "read it with %s pronunciation. Parts of the file are already marked as %s, so only "
                "the document language is wrong. Set it to %s in Acrobat: File > Properties > "
                "Advanced > Language. If the file was made in Word, choosing %s again as the proofing "
                "language may not change the document language when you save as PDF again, because "
                "the text already has it (%s). Setting the language of Word's Normal style (Modify "
                "Style > Format > Language) has been reported to help; site_check has not tested it."
                % (lang, declared, declared, lang, lang, lang, WORD_NOTE))
    if v == "other":
        out = ("Its text looks like %s, but its document language says %s, so a screen reader will "
               "read it with %s pronunciation. Set the document language to %s (Acrobat: File > "
               "Properties > Advanced > Language; Word: select all the text, Review > Language > "
               "Set Proofing Language, then save as PDF again)." % (
                   lang, name(lc["declared"]), name(lc["declared"]), lang))
    elif lang_set:
        out = ("Its document language (%s) is not a language code a screen reader can use, and its "
               "text looks like %s: set it to %s." % (lc.get("declared_raw") or "?", lang, lang))
    else:
        out = "Its text looks like %s: when you set the document language, choose %s." % (lang, lang)
    if lc.get("local_match"):
        out += (" Some parts are already tagged as %s, which helps screen readers that honour such "
                "tags; the document language still decides the rest." % lang)
    return out
