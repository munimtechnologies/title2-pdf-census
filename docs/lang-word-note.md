# Word-made PDFs: the text is marked Spanish, the document says English

Added 2026-10-19 by AI agents working for MV2 of Munim, Inc. **Exploratory, not pre-registered:**
this breakdown was chosen after the [lang-census results](lang-census-results.md) were public, by
looking again at the same public rows, so read it as a pattern worth testing, not a finding scored
in advance. Machine checks only: nothing here is a WCAG conformance judgment about any government,
and no government is named. Code Apache-2.0; this text CC BY 4.0.

`test_lang_word_note.py` in the repository root recomputes every number on this page from the
public rows in [results/lang-v1/](../results/lang-v1/) and checks the totals against `summary.json`.

## What we looked at
The lang-census found 65 PDFs from large US local governments whose text is not English. 38 of
them declare English as their document language, and 16 of those 38 name the text's real language
on at least one structure element or marked-content sequence (prediction L2). The results page
gave, for each producer family, how many of the 65 declare a wrong or missing language. Here the
65 are split by what they declare and by whether the file names the real language anywhere inside.

"Word" is census.py's producer family for files whose Producer or Creator names Microsoft Word.
"Adobe" is Acrobat, Distiller, the Adobe PDF Library, PDFMaker, InDesign and other Adobe tools.
"Everything else" is other, print-to-PDF, unknown and PDF-library output.

| Made with | Non-English PDFs | Right /Lang | No /Lang | Declares English | Of those, real language marked inside |
|---|---|---|---|---|---|
| Word | 15 | 1 | 1 | 13 | 11 |
| Adobe | 34 | 7 | 13 | 14 | 2 |
| Everything else | 16 | 0 | 5 | 11 | 3 |
| All | 65 | 8 | 19 | 38 | 16 |

All 38 declarations of another language name English, and none of the 65 has an unusable value.

## What it shows
- 11 of the 16 PDFs that declare English while marking the real language inside are Word output.
  In 11 of Word's 13 English-declared non-English PDFs, parts of the file already say Spanish (or,
  once, Korean); only the document-level language says English. For Adobe output it is 2 of 14,
  for everything else 3 of 11. A Fisher exact test of Word against Adobe (11 of 13 against 2 of
  14), which we did not plan before looking, gives p = 0.0004 (two-sided).
- Those 11 Word PDFs come from 11 different governments' sites, so this is not one site's habit.
  Public rows carry no site id, so this was checked on the private rows and the test cannot
  recheck it.
- Word output almost always declares some language. Of Word's 15 non-English PDFs, 14 have a
  /Lang, and 13 of those say English. Among English PDFs, 732 of 768 English Word PDFs (95.3%)
  have a /Lang, against 899 of 1261 English Adobe PDFs (71.3%).

## What it suggests (not tested by us)
- Word seems to know the language of the text, writes it on the parts, and still writes English as
  the document language. The document-level value most likely comes from a different setting than
  the language marked on the text. People have reported the same signature in public threads: a
  Dutch Word for Mac document whose tagged PDF says English
  ([Microsoft Q&A, 2022](https://learn.microsoft.com/en-us/answers/questions/5160285/wrong-language-when-exporting-to-pdf)),
  a Dutch document whose PDF says English with all its content wrapped in Span tags
  ([Microsoft Q&A, 2024](https://learn.microsoft.com/en-us/answers/questions/5273700/language-up-pdf-from-word-causes-span-tag)),
  and a Microsoft moderator's answer that Word may leave out the document-level language while
  keeping the language of parts
  ([Microsoft Q&A, 2026](https://learn.microsoft.com/en-us/answers/questions/5890105/issues-with-language-markup-in-word-and-save-to-pd)).
  We found no Microsoft documentation that says where Word's tagged-PDF export takes the document
  language from. A .docx file stores a document default language in its styles (the default run
  properties or the Normal style), which is one candidate.
- If so, the Word advice site_check 0.2.0 gives ("select all the text, Review > Language > Set
  Proofing Language, then save as PDF again") may not fix these files, because their text already
  carries the right language. We have not tested this: there is no copy of Word in our sandbox.
  The fix that does not depend on Word is the one after export: in Acrobat, File > Properties >
  Advanced > Language. The threads above also suggest, untested by us, setting the language of
  Word's Normal style (Modify Style > Format > Language), or exporting through Word for the web.
- A repair tool can propose the document language from the file itself in these cases: when the
  language both text detectors found is also marked on parts of the file, two independent signals
  agree. That covers 16 of the 38 English-declared non-English PDFs, 11 of them Word's.

## Limits
Small numbers (15 Word and 34 Adobe PDFs) from 46 sites; chosen after the results were seen; the
Producer and Creator strings say which tool made a PDF, not its version or settings, and "Word"
includes files whose Creator names Word but whose Producer is another tool; marked-content
/Lang is found only when written inline; only the first 5 pages are read; no copy of Word and no
screen reader was tested. The lang-census results page and its limits still apply.

## What comes next
site_check: when a PDF declares one language and its parts already carry the text's language, say
so, and lead with the Acrobat fix. A pre-registered test on a real Word install (the same Spanish
document exported with different language settings) would settle where the document language
comes from.

Made by MV2 of Munim, Inc. with AI agents.
