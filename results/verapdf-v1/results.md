# tagtree-reach vs the veraPDF PDF/UA-1 corpus (validate 0.1.0, tagtree 0.1.0)

veraPDF corpus veraPDF/veraPDF-corpus at commit bb75f4f (CC BY 4.0), 296 PDF/UA-1 files (list from git tree API). Machine checks only.

- Results: {"ok": 295, "no_struct_tree": 1}

## Pre-registered checks

| Check | Measured | Met |
|---|---|---|
| V1: every 7.1-t03 fail file has unreachable text | 1 of 2 analysed (2 files) | False |
| V2: no 7.1-t03 pass file has unreachable text | 0 of 2 analysed (2 files) | True |
| V3: 90%+ of pass files with text have none unreachable | 130 of 130 (1.0) | True |

## Every file

| File | Result | Reach | Untag | Dangl | Artif | XObj | Named | Outline |
|---|---|---|---|---|---|---|---|---|
| 5-t01-fail-a.pdf | ok | 718 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / PDF/UA Identifier is not present / Expected result: fail |
| 5-t01-pass-a.pdf | ok | 718 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / PDF/UA Identifier is present / Expected result: pass |
| 5-t02-fail-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / <pdfuaid:part>2</pdfuaid:part> is present / Actual result: fail |
| 5-t02-pass-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / <pdfuaid:part>1</pdfuaid:part> is present / Actual result: pass |
| 5-t03-fail-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / Property 'part' of the PDF/UA Identification Schema has namespace 'pdfuaia' prefix / Actua... |
| 5-t03-pass-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / Property 'part' of the PDF/UA Identification Schema has namespace 'pdfuaid' prefix / Actua... |
| 5-t04-fail-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / Property 'amd' of the PDF/UA Identification Schema has namespace 'pdfuaia' prefix / Actual... |
| 5-t04-pass-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / Property 'amd' of the PDF/UA Identification Schema has namespace 'pdfuaid' prefix / Actual... |
| 5-t05-fail-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / Property 'corr' of the PDF/UA Identification Schema has namespace 'pdfuaia' prefix / Actua... |
| 5-t05-pass-a.pdf | ok | 416 | 0 | 0 | 0 | 0 | 0 | 5 Version identification / Property 'corr' of the PDF/UA Identification Schema has namespace 'pdfuaid' prefix / Actua... |
| 7.1-t01-fail-a.pdf | ok | 536 | 0 | 0 | 0 | 0 | 0 | 7.1-1 General / All real content is tagged / Artifact is present in real content / Expected result: fail |
| 7.1-t01-pass-a.pdf | ok | 536 | 0 | 0 | 0 | 0 | 0 | 7.1-1 General / All real content is tagged / Artifact is not tagged in the structure tree / Expected result: pass |
| 7.1-t01-pass-b.pdf | ok | 0 | 0 | 0 | 58 | 0 | 0 | 7.1-1 General / Artifact is present in P / P has not MCID / Expected result: pass |
| 7.1-t02-fail-a.pdf | ok | 340 | 0 | 0 | 196 | 0 | 0 | 7.1-1 General / Note is real content / Note is present in Artifact / Expected result: fail |
| 7.1-t02-pass-a.pdf | ok | 536 | 0 | 0 | 0 | 0 | 0 | 7.1-1 General / Note is real content / Note is not present in Artifact / Expected result: pass |
| 7.1-t02-pass-b.pdf | ok | 38 | 0 | 0 | 0 | 0 | 0 | 7.1-1 General / junk is present in Artifact / junk has not MCID / Expected result: pass |
| 7.1-t03-fail-a.pdf | ok | 20 | 0 | 0 | 13 | 0 | 0 | 7.1-2 General / Image is not marked as Artifact or real content / Expected result: fail |
| 7.1-t03-fail-b.pdf | ok | 8 | 12 | 0 | 0 | 0 | 0 | 7.1-3 General / Content stream doesn't contain an "Artifact" tag / Expected result: fail |
| 7.1-t03-pass-a.pdf | ok | 20 | 0 | 0 | 13 | 0 | 0 | 7.1-2 General / Content is marked as Artifact / Real content is tagged / Expected result: pass |
| 7.1-t03-pass-b.pdf | ok | 8 | 0 | 0 | 12 | 0 | 0 | 7.1-3 General / Content stream explicitly distinguished with the "Artifact" tag / Expected result: pass |
| 7.1-t04-fail-a.pdf | ok | 546 | 0 | 0 | 0 | 0 | 0 | 7.1-11 General / Suspect entry is present with value of true in MarkInfo dictionary / Expected result: fail |
| 7.1-t04-pass-a.pdf | ok | 546 | 0 | 0 | 0 | 0 | 0 | 7.1-11 General / Suspect entry is present with value of false in MarkInfo dictionary / Expected result: pass |
| 7.1-t05-fail-a.pdf | ok | 1651 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / RoleMap entry is present with value : "Standard - > p" / p is not standard type; standard type is P(c... |
| 7.1-t05-fail-b.pdf | ok | 23 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / RoleMap entry is present with next values: / Standard -> Text body / Text body -> p(case sensitive) /... |
| 7.1-t05-fail-c.pdf | ok | 31 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / Standard structure element is remapped to empty string / Standard -> "" / Expected result: fail |
| 7.1-t05-fail-d.pdf | ok | 23 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / Non-standard structure elements "Text body" and "Standard" are rolemapped to each other / Expected re... |
| 7.1-t05-pass-a.pdf | ok | 1651 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / RoleMap entry is present with value : "Standard - > P" / Expected result: pass |
| 7.1-t05-pass-b.pdf | ok | 23 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / RoleMap entry is present with next values: / Standard -> Text body / Text body -> P / Expected result... |
| 7.1-t06-fail-a.pdf | ok | 1651 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / Rolemap entry is present / LI rolemapped to LI / Expected result: fail |
| 7.1-t06-pass-a.pdf | ok | 1651 | 0 | 0 | 0 | 0 | 0 | 7.1-3 General / All structure elements in document have Standard type / Expected result: pass |
| 7.1-t07-fail-a.pdf | ok | 65 | 0 | 0 | 0 | 0 | 0 | 7.1-4 General / Document is remapped to Book / Expected result: fail |
| 7.1-t07-pass-a.pdf | ok | 65 | 0 | 0 | 0 | 0 | 0 | 7.1-4 General / All structure elements are standard / Expected result: pass |
| 7.1-t08-fail-a.pdf | ok | 718 | 0 | 0 | 0 | 0 | 0 | 7.1 General / Metadata stream is not present / Expected result: fail |
| 7.1-t08-pass-a.pdf | ok | 718 | 0 | 0 | 0 | 0 | 0 | 7.1-8 General / Metadata stream is present / Expected result: pass |
| 7.1-t09-fail-a.pdf | ok | 46 | 0 | 0 | 0 | 0 | 0 | 7.1-8 General / dc:title is not present in metadata stream / Expected result: fail |
| 7.1-t09-pass-a.pdf | ok | 46 | 0 | 0 | 0 | 0 | 0 | 7.1-8 General / dc:title "title" is present in metadata stream / Expected result: pass |
| 7.1-t10-fail-a.pdf | ok | 288 | 0 | 0 | 0 | 0 | 0 | 7.1-9 General / DisplayDocTitle entry is not present in ViewerPreferences dictionary / Expected result: fail |
| 7.1-t10-fail-b.pdf | ok | 288 | 0 | 0 | 0 | 0 | 0 | 7.1-9 General / "DisplayDocTitle: False" is present in ViewerPreferences dictionary / Expected result: fail |
| 7.1-t10-pass-a.pdf | ok | 288 | 0 | 0 | 0 | 0 | 0 | 7.1-9 General / "DisplayDocTitle: True" is present in ViewerPreferences dictionary / Expected result: pass |
| 7.1-t11-fail-a.pdf | no_struct_tree |  |  |  |  |  |  | 7.1-11 General / StructTreeRoot entry of the document catalog dictionary is not present / Expected result: fail |
| 7.10-t01-fail-a.pdf | ok | 15 | 0 | 0 | 0 | 0 | 0 | 7.10 Optional content / Name entry is present in D dictionary and it is empty string / Expected result: fail |
| 7.10-t01-fail-b.pdf | ok | 15 | 0 | 0 | 0 | 0 | 0 | 7.10 Optional content / Name entry is not present in D dictionary / Expected result: fail |
| 7.10-t01-pass-a.pdf | ok | 15 | 0 | 0 | 0 | 0 | 0 | 7.10 Optional content / Name entry is present in D dictionary and it is not empty string / Expected result: pass |
| 7.10-t02-fail-a.pdf | ok | 15 | 0 | 0 | 0 | 0 | 0 | 7.10-2 Optional content / The AS key appears in an Optional Content Configuration Dictionary / Expected result: fail |
| 7.10-t02-pass-a.pdf | ok | 15 | 0 | 0 | 0 | 0 | 0 | 7.10-2 Optional content / The AS key doesn't appear in an Optional Content Configuration Dictionary / Expected result... |
| 7.11-t01-fail-a.pdf | ok | 57 | 0 | 0 | 0 | 0 | 0 | 7.11-1 Embedded files / F entry is not present in Embedded files dictionary / Expected result: fail |
| 7.11-t01-fail-b.pdf | ok | 57 | 0 | 0 | 0 | 0 | 0 | 7.11-1 Embedded files / UF entry is not present in Embedded files dictionary / Expected result: fail |
| 7.11-t01-pass-a.pdf | ok | 57 | 0 | 0 | 0 | 0 | 0 | 7.11-1 Embedded files / UF and F entries are present in Embedded files dictionary / Expected result: pass |
| 7.15-t01-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.15-1 XFA / File contains the dynamicRender element with value “required”. / <dynamicRender >required</dynamicRender... |
| 7.16-t01-fail-a.pdf | ok | 72 | 0 | 0 | 0 | 0 | 0 | 7.16-1 Security / 10th bit is not present / Password is "password" / Expected result: fail |
| 7.16-t01-pass-a.pdf | ok | 72 | 0 | 0 | 0 | 0 | 0 | 7.16-1 Security / 10th bit is present / Expected result: pass |
| 7.18.1-t01-fail-a.pdf | ok | 99 | 0 | 0 | 0 | 0 | 0 | 7.18.1-2 General / Highlight annotation is not included in Annot structure element / Expected result: fail |
| 7.18.1-t01-pass-a.pdf | ok | 4 | 0 | 0 | 0 | 0 | 0 | 7.18.1-2 General / Link annotation is present in Link structure element instead Annot / Expected result: pass |
| 7.18.1-t01-pass-b.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-2 General / Widget annotation is present in Form structure element instead Annot / Expected result: pass |
| 7.18.1-t01-pass-c.pdf | ok | 27 | 0 | 0 | 0 | 0 | 0 | 7.18.2-1 Annotation types / Annotation of the subtype "FREETEXT" (in upper case) is not standard. / FREETEXT annot is... |
| 7.18.1-t02-fail-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Contents key is not present in OBJR / Al... |
| 7.18.1-t02-fail-b.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Contents key is not present in OBJR / Al... |
| 7.18.1-t02-fail-c.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Alt entry is not present in Annot struct... |
| 7.18.1-t02-pass-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Contents key is not present in OBJR / Al... |
| 7.18.1-t02-pass-b.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Alt entry is not present in Annot struct... |
| 7.18.1-t02-pass-c.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Contents key is not present in Annot dic... |
| 7.18.1-t02-pass-d.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Annotation of subtype Highlight is present in Annot tag / Contents key is not present in Annot dic... |
| 7.18.1-t02-pass-e.pdf | ok | 27 | 0 | 0 | 0 | 0 | 0 | 7.18.2-1 Annotation types / Annotation of the subtype "FREETEXT" (in upper case) is not standard / FREETEXT annot is ... |
| 7.18.1-t02-pass-f.pdf | ok | 27 | 0 | 0 | 0 | 0 | 0 | 7.18.2-1 Annotation types / Annotation of the subtype "FREETEXT" (in upper case) is not standard / FREETEXT annot is ... |
| 7.18.1-t02-pass-g.pdf | ok | 27 | 0 | 0 | 0 | 0 | 0 | 7.18.2-1 Annotation types / Annotation of the subtype "FREETEXT" (in upper case) is not standard / FREETEXT annot is ... |
| 7.18.1-t02-pass-h.pdf | ok | 27 | 0 | 0 | 0 | 0 | 0 | 7.18.2-1 Annotation types / Annotation of the subtype "FREETEXT" (in upper case) is not standard / FREETEXT annot is ... |
| 7.18.1-t03-fail-a.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Hidden flag for form field is not set / Rectangle of CropBox is not outside / TU key is not presen... |
| 7.18.1-t03-fail-b.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Hidden flag for form field is not set / Rectangle of CropBox is not outside / Alt key is not prese... |
| 7.18.1-t03-fail-c.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Hidden flag for form field is not set / Rectangle of CropBox is not outside / Alt key is present /... |
| 7.18.1-t03-fail-d.pdf | ok | 4 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / TU key is not present in Fields entry / Kids array is present in Fields entry / Kids key have 2 wi... |
| 7.18.1-t03-pass-a.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Hidden flag for form field is not set / Rectangle of CropBox is not outside / TU key is present / ... |
| 7.18.1-t03-pass-b.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Hidden flag for form field is not set / Rectangle of CropBox is not outside / Alt key is present /... |
| 7.18.1-t03-pass-c.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Rectangle of CropBox is not outside / TU key is not present / Alt key is not present / Hidden flag... |
| 7.18.1-t03-pass-d.pdf | ok | 217 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / Hidden flag is set / TU key is not present / Alt key is not present / Rectangle of CropBox is outs... |
| 7.18.1-t03-pass-e.pdf | ok | 4 | 0 | 0 | 0 | 0 | 0 | 7.18.1-4 General / TU key is present in Fields entry / Expected result: pass |
| 7.18.1-t03-pass-f.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.18.1-3 General / For Widget annotations there is a value of the TU entry / Expected result: pass |
| 7.18.2-t01-fail-a.pdf | ok | 7 | 0 | 0 | 0 | 0 | 0 | 7.18.2-1 Annotation types / Subtype entry is present / Value of Subtype entry is TrapNet / Expected result: fail |
| 7.18.3-t01-fail-a.pdf | ok | 146 | 0 | 0 | 0 | 0 | 0 | 7.18.3-1 Tab order / Page1 dictionary is not contain Tabs entry / Page2 dictionary is not contain Tabs entry / Expect... |
| 7.18.3-t01-fail-b.pdf | ok | 146 | 0 | 0 | 0 | 0 | 0 | 7.18.3-1 Tab order / Page1 dictionary contains Tabs entry with value = "C" / Page2 dictionary contains Tabs entry wit... |
| 7.18.4-t01-fail-a.pdf | ok | 66 | 0 | 0 | 0 | 0 | 0 | 7.18.4-1 Forms / Widget annotation is nested within Document / Expected result: fail |
| 7.18.4-t01-pass-a.pdf | ok | 66 | 0 | 0 | 0 | 0 | 0 | 7.18.4-1 Forms / Widget annot is nested within Form / Expected result: pass |
| 7.18.5-t01-fail-a.pdf | ok | 86 | 0 | 0 | 0 | 0 | 0 | 7.18.5-1 Links / Link annotation is nested within a Paragraph tag. / Expected result: fail |
| 7.18.5-t01-pass-a.pdf | ok | 86 | 0 | 0 | 0 | 0 | 0 | 7.18.5-1 Links / Link annotation is nested within a Link tag. / Expected result: pass |
| 7.18.5-t01-pass-b.pdf | ok | 45 | 0 | 0 | 0 | 0 | 0 | 7.18.5-1 Links / Link annotation is nested within the non-standard structure tag 'Link1' which is role mapped to the ... |
| 7.18.5-t02-fail-a.pdf | ok | 86 | 0 | 0 | 0 | 0 | 0 | 7.18.5-2 Links / Contents key is not present in Link annotation / Expected result: fail |
| 7.18.5-t02-fail-b.pdf | ok | 86 | 0 | 0 | 0 | 0 | 0 | 7.18.5-2 Links / Contents key is present in Link annotation / Value of Contents is empty / Expected result: fail |
| 7.18.5-t02-pass-a.pdf | ok | 86 | 0 | 0 | 0 | 0 | 0 | 7.18.5-2 Links / Contents key is present in Link annotation / Expected result: pass |
| 7.18.6.2-t01-fail-a.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.18.6.2-1 Media clip data / Alt array is present / CT entry is not present / Expected result: fail |
| 7.18.6.2-t01-pass-a.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.18.6.2-1 Media clip data / Alt array is present / CT entry is present / Value of CT is empty / Expected result: pass |
| 7.18.6.2-t02-fail-a.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.18.6.2-2 Media clip data / CT entry is present / Alt array is not present / Expected result: fail |
| 7.18.6.2-t02-fail-b.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.18.6.2-2 Media clip data / CT entry is present / Alt array is present / Value of Alt is empty / Expected result: fail |
| 7.18.6.2-t02-pass-a.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.18.6.2-2 Media clip data / CT entry is present / Alt array is present / Expected result: pass |
| 7.18.7-t01-fail-a.pdf | ok | 54 | 0 | 0 | 0 | 0 | 0 | 7.18.7-1 File Attachments / F entry is not present / Expected result: fail |
| 7.18.7-t01-fail-b.pdf | ok | 54 | 0 | 0 | 0 | 0 | 0 | 7.18.7-1 File Attachments / UF entry is not present / Expected result: fail |
| 7.18.7-t01-fail-c.pdf | ok | 54 | 0 | 0 | 0 | 0 | 0 | 7.18.7-1 File Attachments / F and UF entries are present / Value of F entry is empty string / Expected result: fail |
| 7.18.7-t01-fail-d.pdf | ok | 54 | 0 | 0 | 0 | 0 | 0 | 7.18.7-1 File Attachments / F and UF entries are present / Value of UF entry is empty string / Expected result: fail |
| 7.18.7-t01-pass-a.pdf | ok | 54 | 0 | 0 | 0 | 0 | 0 | 7.18.7-1 File Attachments / F and UF entries are present / Expected result: pass |
| 7.18.8-t01-fail-a.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.18.8-1 PrinterMark / Annot is present in structure tree root / Subtype of annotation is PrinterMark / Expected resu... |
| 7.2-t02-fail-a.pdf | ok | 398 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is not present in Document Catalog for determine language of "Outlines" / Expected result: fail |
| 7.2-t02-pass-a.pdf | ok | 398 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Expected result: pass |
| 7.2-t03-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / P is enclosed in Table structure element / Expected result: fail / because only THead, TBody, TFoot, TR,... |
| 7.2-t03-fail-b.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / More than one Caption is present in Table / Expected result: fail |
| 7.2-t03-fail-c.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is not a first or last child of Table / Expected result: fail |
| 7.2-t03-pass-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is a last child of Table / THead may be present and shall be only one / "THead" shall be followe... |
| 7.2-t03-pass-b.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is a first child of Table / THead may be present and shall be only one / "THead" shall be follow... |
| 7.2-t03-pass-c.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is a last child of Table / Each TH and TD shall be enclosed in TR / Each TR shall be enclosed in... |
| 7.2-t04-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / TR is not enclosed in Table, THead, TBody or TFoot / Expected result: fail |
| 7.2-t05-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / THead is not enclosed in Table / Expected result: fail |
| 7.2-t06-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / TBody is not enclosed in Table / Expected result: fail |
| 7.2-t07-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / TFoot is not enclosed in Table / Expected result: fail |
| 7.2-t08-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / TH is not enclosed in TR / Expected result: fail |
| 7.2-t09-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / TD is not enclosed in TR / Expected result: fail |
| 7.2-t10-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / THead-TR contains Span / Expected result: fail |
| 7.2-t11-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / More than one THead is present / Expected result: fail |
| 7.2-t12-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / More than one TFoot is present / Expected result: fail |
| 7.2-t13-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / TFoot is present without TBody / Expected result: fail |
| 7.2-t14-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / THead is present without TBody / Expected result: fail |
| 7.2-t15-pass-a.pdf | ok | 45 | 0 | 0 | 0 | 0 | 0 | 7.2-15 Table / Attribute RowSpan with value 2 is present in empty cell / Attribute ColSpan with value 3 is present in... |
| 7.2-t15-pass-b.pdf | ok | 116 | 0 | 0 | 0 | 0 | 0 | 7.2-15 Table / Reading order of Table is good / Expected result: pass |
| 7.2-t17-fail-a.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Each List items are not enclosed in List structure element / Expected result: fail |
| 7.2-t17-pass-a.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is a first child of List / Each LI is present in L / Each Lbl and LBody is present in LI / LBody... |
| 7.2-t17-pass-b.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is a first child of List / Each LI is present in L / Lbl and LBody are not present in LI / Expec... |
| 7.2-t17-pass-c.pdf | ok | 6 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Lbl is present in L / LBody is not present in L / Expected result: pass |
| 7.2-t17-pass-d.pdf | ok | 6 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Lbl is not present in L / LBody is present in L / Expected result: pass |
| 7.2-t17-pass-e.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is not a child of List / Each LI is present in L / Each Lbl and LBody is present in LI / LBody c... |
| 7.2-t17-pass-f.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Lbl is not enclosed in LI / Expected result: pass |
| 7.2-t17-pass-g.pdf | ok | 114 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / List is present in List / Expected result: pass |
| 7.2-t18-fail-a.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / LBody is not enclosed in LI / Expected result: fail |
| 7.2-t19-fail-a.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Caption is not a first child of List / Expected result: fail |
| 7.2-t19-fail-b.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Span is a child of L / Expected result: fail |
| 7.2-t19-fail-c.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / More than one Caption is present in List / Expected result: fail |
| 7.2-t20-fail-a.pdf | ok | 622 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Span is present in first LI / Expected result: fail |
| 7.2-t20-fail-b.pdf | ok | 38 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / L is present in List item / Expected result: fail |
| 7.2-t21-fail-a.pdf | ok | 82 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / ActualText entry is present in H1 structure element / Lang entry is not present in Document Catalog, str... |
| 7.2-t21-pass-a.pdf | ok | 82 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / ActualText entry is present in H1 structure element / Lang entry is present in Document Catalog / Expect... |
| 7.2-t21-pass-b.pdf | ok | 160 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t21-pass-c.pdf | ok | 203 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t22-fail-a.pdf | ok | 38 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Alt entry is present in Figure / Lang entry is not present in Document Catalog, structure element dictio... |
| 7.2-t22-pass-a.pdf | ok | 38 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Alt entry is present in Figure / Lang entry is present in Document Catalog / Expected result: pass |
| 7.2-t22-pass-b.pdf | ok | 113 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t22-pass-c.pdf | ok | 170 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t23-fail-a.pdf | ok | 36 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / E entry is present in P structure element / Lang entry is not present in Document Catalog, structure ele... |
| 7.2-t23-pass-a.pdf | ok | 36 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / E entry is present in Paragraph / Lang entry is present in Document Catalog / Expected result: pass |
| 7.2-t23-pass-b.pdf | ok | 112 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t23-pass-c.pdf | ok | 174 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t24-fail-a.pdf | ok | 50 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is not present in Document Catalog, structure element dictionary / Expected result: fail |
| 7.2-t24-pass-a.pdf | ok | 50 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Expected result: pass |
| 7.2-t24-pass-b.pdf | ok | 128 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t25-fail-a.pdf | ok | 14 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang is not present in Form or Document Catalog / Expected result: fail |
| 7.2-t25-pass-a.pdf | ok | 14 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang is present in Document Catalog / Expected result: pass |
| 7.2-t25-pass-b.pdf | ok | 86 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t26-fail-a.pdf | ok | 84 | 0 | 0 | 558 | 0 | 0 | 7.2-1 Text / TOCI is not contained in TOC / Expected result: fail |
| 7.2-t26-pass-a.pdf | ok | 84 | 0 | 0 | 558 | 0 | 0 | 7.2-1 Text / TOCI is contained in TOC / Expected result: pass |
| 7.2-t27-fail-a.pdf | ok | 84 | 0 | 0 | 558 | 0 | 0 | 7.2-1 Text / TOCI and TOC are immediately children of TOC / Caption is a last child of TOC / Expected result: fail |
| 7.2-t27-fail-b.pdf | ok | 84 | 0 | 0 | 558 | 0 | 0 | 7.2-1 Text / TOCI and TOC are immediately children of TOC / More than one Caption is present as a child of TOC / Expe... |
| 7.2-t27-fail-c.pdf | ok | 84 | 0 | 0 | 558 | 0 | 0 | 7.2-1 Text / P is a children of TOC / Expected result: fail |
| 7.2-t27-pass-a.pdf | ok | 84 | 0 | 0 | 558 | 0 | 0 | 7.2-1 Text / TOCI and TOC are immediately children of TOC / Caption is a first child of TOC / Expected result: pass |
| 7.2-t29-fail-a.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Primary-subtag of Lang is "portugues" / Expected result: fail |
| 7.2-t29-fail-b.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Primary-subtag of Lang is digit / Expected result: fail |
| 7.2-t29-fail-c.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Primary-subtag of Lang is empty / Expected result: fail |
| 7.2-t29-fail-d.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Primary-subtag of Lang is "portugues" / Expected result: fail |
| 7.2-t29-fail-e.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Primary-subtag of Lang is digit / Expected result: fail |
| 7.2-t29-fail-f.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Primary-subtag of Lang is empty / Expected result: fail |
| 7.2-t29-fail-g.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in property list / Primary-subtag of Lang is empty / Expected result: fail |
| 7.2-t29-fail-h.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in property list / Primary-subtag of Lang is "portugues" / Expected result: fail |
| 7.2-t29-fail-i.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in property list / Primary-subtag of Lang is digit / Expected result: fail |
| 7.2-t29-fail-j.pdf | ok | 16 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Subtag of Lang is "1234abcde" / Expected result: fail |
| 7.2-t29-fail-k.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Subtag of Lang is "пт" / Expected result: fail |
| 7.2-t29-fail-l.pdf | ok | 16 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Subtag of Lang is "1234abcdf" / Expected result: fail |
| 7.2-t29-fail-m.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Subtag of Lang is "ПТ" / Expected result: fail |
| 7.2-t29-fail-n.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Value of Lang is empty / Expected result: fail |
| 7.2-t29-fail-o.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Value of lang is empty / Expected result: fail |
| 7.2-t29-fail-p.pdf | ok | 28 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang is present in marked content sequence / Value of lang is empty / Expected result: fail |
| 7.2-t29-pass-a.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Primary-subtag of Lang is "portugue" / Expected result: pass |
| 7.2-t29-pass-b.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Primary-subtag of Lang is "p" / Expected result: pass |
| 7.2-t29-pass-c.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph structure element / Primary-subtag of Lang is "portugue" / Expected r... |
| 7.2-t29-pass-d.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph structure element / Primary-subtag of Lang is "p" / Expected result: ... |
| 7.2-t29-pass-e.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in property list / Primary-subtag of Lang is "portugue" / Expected result: pass |
| 7.2-t29-pass-f.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in property list / Primary-subtag of Lang is "p" / Expected result: pass |
| 7.2-t29-pass-g.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Subtag of Lang is "PT" / Expected result: pass |
| 7.2-t29-pass-h.pdf | ok | 16 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Subtag of Lang is "1234abcd" / Expected result: pass |
| 7.2-t29-pass-i.pdf | ok | 16 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Subtag of Lang is "1234abcd" / Expected result: pass |
| 7.2-t29-pass-j.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Paragraph / Subtag of Lang is "PT" / Expected result: pass |
| 7.2-t30-fail-a.pdf | ok | 22 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / ActualText is present in marked content sequence / Lang is not present in marked content sequence / Expe... |
| 7.2-t30-pass-a.pdf | ok | 119 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t30-pass-b.pdf | ok | 268 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t31-fail-a.pdf | ok | 15 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Alt is present in marked content sequence / Lang is not present in marked content sequence / Expected re... |
| 7.2-t31-pass-a.pdf | ok | 105 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t31-pass-b.pdf | ok | 242 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t32-fail-a.pdf | ok | 21 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / E is present in marked content sequence / Lang is not present in marked content sequence / Expected resu... |
| 7.2-t32-pass-a.pdf | ok | 109 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t32-pass-b.pdf | ok | 238 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t33-fail-a.pdf | ok | 53 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is not present in Document Catalog for determination "dc:title" / Expected result: fail |
| 7.2-t33-pass-a.pdf | ok | 53 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / "dc:title" is determined through Lang entry in Document Catalog / Expected result: pass |
| 7.2-t33-pass-b.pdf | ok | 125 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t34-fail-a.pdf | ok | 398 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is not present in Document Catalog, structure element dictionary and property list / Expected... |
| 7.2-t34-pass-a.pdf | ok | 398 | 0 | 0 | 0 | 0 | 0 | 7.2-3 Text / Lang entry is present in Document Catalog / Expected result: pass |
| 7.2-t34-pass-b.pdf | ok | 480 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t34-pass-c.pdf | ok | 82 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t34-pass-d.pdf | ok | 167 | 0 | 0 | 0 | 0 | 0 |  |
| 7.2-t36-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Span is contained in THead / Expected result: fail |
| 7.2-t37-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Span is contained in TBody / Expected result: fail |
| 7.2-t38-fail-a.pdf | ok | 123 | 0 | 0 | 0 | 0 | 0 | 7.2-1 Text / Span is contained in TFoot / Expected result: fail |
| 7.2-t41-fail-a.pdf | ok | 43 | 0 | 0 | 0 | 0 | 0 | 7.2-41 Table / Attribute RowSpan with value 5 is present in Header 1 / Expected result: fail |
| 7.2-t42-fail-a.pdf | ok | 45 | 0 | 0 | 0 | 0 | 0 | 7.2-42 Table / Attribute RowSpan with value 2 is present in empty cell / Attribute ColSpan with value 2 is present in... |
| 7.2-t43-fail-a.pdf | ok | 45 | 0 | 0 | 0 | 0 | 0 | 7.2-43 Table / Attribute RowSpan with value 1 is present in empty cell / Attribute ColSpan with value 3 is present in... |
| 7.2-t43-fail-b.pdf | ok | 116 | 0 | 0 | 0 | 0 | 0 | 7.2-43 Table / THead contains all Table Header Cells / TBody contains all Table Data Cells / Expected result: fail |
| 7.2-t43-fail-c.pdf | ok | 116 | 0 | 0 | 0 | 0 | 0 | 7.2-43 Table / All Table Header Cells are present in TR / Expected result: fail |
| 7.20-t01-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.20-1 XObjects / Ref key is present in XObject dictionary / Expected result: fail |
| 7.20-t01-pass-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.20-1 XObjects / Ref key is not present in XObject dictionary / Expected result: pass |
| 7.20-t02-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.20-2 XObjects / Form XObjects contains MCID and it is referenced three times / Expected result: fail |
| 7.20-t02-pass-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.20-2 XObjects / Form XObjects contains MCID and it is referenced one time / Expected result: pass |
| 7.21.3.1-t01-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Registry values in Encoding and DescendantFonts dictionaries are not the same / Expected result:... |
| 7.21.3.1-t01-fail-b.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Ordering values in Encoding and DescendantFonts dictionaries are not the same / Expected result:... |
| 7.21.3.1-t01-fail-c.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Supplement value in DescendantFonts more than value in Encoding / Expected result: fail |
| 7.21.3.1-t01-pass-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Registry values in Encoding and DescendantFonts dictionaries are the same / Expected result: pass |
| 7.21.3.1-t01-pass-b.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Ordering values in Encoding and DescendantFonts dictionaries are the same / Expected result: pass |
| 7.21.3.1-t01-pass-c.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Supplement value in Encoding and DescendantFonts dictionaries are the same / Expected result: pass |
| 7.21.3.1-t01-pass-d.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.1-1 General / Supplement value in DescendantFonts dictionary less than in Encoding dictionary / Expected resul... |
| 7.21.3.2-t01-fail-a.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.3.2-1 CIDFonts / CIDToGIDMap is name / Value of CIDToGIDMap is NoIdentity / Expected result: fail |
| 7.21.3.2-t01-fail-b.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.3.2-1 CIDFonts / CIDToGIDMap entry is not present / Expected result: fail |
| 7.21.3.2-t01-fail-c.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.3.2-1 CIDFonts / CIDToGIDMap entry is present / Value of CIDToGIDMap is empty / Expected result: fail |
| 7.21.3.2-t01-pass-a.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.3.2-1 CIDFonts / CIDToGIDMap with value "Identity" is present / Expected result: pass |
| 7.21.3.3-t01-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-1 CMaps / Encoding contains "Adobe-Korea1-2" that is not present in Table 118 of ISO 32000-1 / Expected resu... |
| 7.21.3.3-t01-pass-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-1 CMaps / Encoding contains "Identity-H" that is present in Table 118 of ISO 32000-1 / Expected result: pass |
| 7.21.3.3-t02-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-1 CMaps / WMode in Encoding is 1 / WMode in CMap stream is 0 / Expected result: fail |
| 7.21.3.3-t02-fail-b.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-1 CMaps / WMode in Encoding is 0 / WMode in CMap stream is 1 / Expected result: fail |
| 7.21.3.3-t02-pass-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-1 CMaps / WMode in Encoding is 0 / WMode in CMap stream is 0 / Expected result: pass |
| 7.21.3.3-t03-fail-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-2 CMaps / UseCMap contains "Adobe-Korea1-2" that is not present in Table 118 of ISO 32000-1 / Expected resul... |
| 7.21.3.3-t03-pass-a.pdf | ok | 0 | 0 | 0 | 0 | 0 | 0 | 7.21.3.3-2 CMaps / UseCMap contains "H" that is present in Table 118 of ISO 32000-1 / Expected result: pass |
| 7.21.4.1-t01-fail-a.pdf | ok | 12 | 0 | 0 | 0 | 0 | 0 | 7.21.4.1-1 General / Font is not embedded / Expected result: fail |
| 7.21.4.1-t01-pass-a.pdf | ok | 12 | 0 | 0 | 0 | 0 | 0 | 7.21.4.1-1 General / Font is embedded / Expected result: pass |
| 7.21.4.2-t01-fail-a.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.21.4.2 Subset embedding / "a" character is not present in CharSet string / Expected result: fail |
| 7.21.4.2-t01-fail-b.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.21.4.2 Subset embedding / "d" charachter is present in CharSet string / Expected result: fail |
| 7.21.4.2-t01-pass-a.pdf | ok | 13 | 0 | 0 | 0 | 0 | 0 | 7.21.4.2 Subset embedding / Characters in CharSet string are complete / Expected result: pass |
| 7.21.4.2-t02-fail-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.4.2-3 Subset embedding / Embedded CID font contains a CIDSet stream that does not list all character names of al... |
| 7.21.4.2-t02-pass-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.4.2-3 Subset embedding / Embedded CID font contains a CIDSet stream that lists all character names of all glyphs... |
| 7.21.5-t01-fail-a.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.5 Font metrics / First value in Width array is 192 / Expected result: fail |
| 7.21.5-t01-pass-a.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.5 Font metrics / First value in Width array is 250 / Expected result: pass |
| 7.21.6-t02-fail-a.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / BaseEncoding with value "Identity" is present in Encoding Dictionary / Expected result... |
| 7.21.6-t02-fail-b.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / BaseEncoding entry is not present in Encoding Dictionary / Expected result: fail |
| 7.21.6-t02-fail-c.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / Encoding entry is not present in Font Dictionary / Expected result: fail |
| 7.21.6-t02-fail-d.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-3 Character encodings / Differences array contains "gravee" glyph that not present in Adobe Glyph List / Expec... |
| 7.21.6-t02-pass-a.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / BaseEncoding with value "WinAnsiEncoding" is present in Encoding Dictionary / Expected... |
| 7.21.6-t02-pass-b.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / BaseEncoding with value WinAnsiEncoding is present in Encoding Dictionary / Expected r... |
| 7.21.6-t02-pass-c.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / Encoding with value WinAnsiEncoding is present in Font Dictionary / Expected result: pass |
| 7.21.6-t02-pass-d.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-3 Character encodings / Differences array contains "grave" glyph that present in Adobe Glyph List / Expected r... |
| 7.21.6-t03-fail-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.6-4 Character encodings / Encoding entry is present in Font Dictionary for Symbolic TrueType font / Expected res... |
| 7.21.6-t03-pass-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.6-4 Character encodings / Encoding entry is not present in Font Dictionary for Symbolic TrueType font / Expected... |
| 7.21.7-t01-fail-a.pdf | ok | 11 | 0 | 0 | 0 | 0 | 0 | 7.21.7-1 Unicode character maps / A font dictionary does not contain the ToUnicode entry and none of the following is... |
| 7.21.7-t01-pass-a.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.7-1 Unicode character maps / A Type0 font uses the Adobe-Japan1 character collection and does not contain the To... |
| 7.21.7-t01-pass-b.pdf | ok | 10 | 0 | 0 | 0 | 0 | 0 | 7.21.7-1 Unicode character maps / A Font uses the predefined encoding MacRomanEncoding and does not contain the ToUni... |
| 7.21.7-t01-pass-c.pdf | ok | 8 | 0 | 0 | 0 | 0 | 0 | 7.21.6-2 Character encodings / non-symbolic TrueType font is present so ToUnicode entry is not required / Expected re... |
| 7.21.7-t02-fail-a.pdf | ok | 1 | 0 | 0 | 0 | 0 | 0 | 7.21.7-2 Unicode character maps / Unicode value in ToUnicode CMap is <0000> / Expected result: fail |
| 7.21.7-t02-fail-b.pdf | ok | 1 | 0 | 0 | 0 | 0 | 0 | 7.21.7-2 Unicode character maps / Unicode value in ToUnicode CMap is <fffe> / Expected result: fail |
| 7.21.7-t02-fail-c.pdf | ok | 1 | 0 | 0 | 0 | 0 | 0 | 7.21.7-2 Unicode character maps / Unicode value in ToUnicode CMap is <feff> / Expected result: fail |
| 7.21.7-t02-pass-a.pdf | ok | 1 | 0 | 0 | 0 | 0 | 0 | 7.21.7-2 Unicode character maps / Unicode value in ToUnicode CMap is <0075> / Unicode values: <0000>, <fffe>, <feff> ... |
| 7.21.8-t01-fail-a.pdf | ok | 1 | 0 | 0 | 0 | 0 | 0 | 7.21.8 Use of .notdef glyph / One or more characters used in text showing operators reference the .notdef glyph. / Ex... |
| 7.3-t01-fail-a.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.3-3 Graphics / ActualText or Alt entries are not present in Figure structure element / Expected result: fail |
| 7.3-t01-fail-b.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.3-3 Graphics / Alt entry is present in Figure structure element / Value of Alt is empty / Expected result: fail |
| 7.3-t01-pass-a.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.3-3 Graphics / Alt is present in Figure / Expected result: pass |
| 7.3-t01-pass-b.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.3-3 Graphics / ActualText is present in Figure / Expected result: pass |
| 7.3-t01-pass-c.pdf | ok | 26 | 0 | 0 | 0 | 0 | 0 | 7.3-3 Graphics / ActualText is present in Figure / Value of ActualText is empty / Expected result: pass |
| 7.4.2-t01-fail-a.pdf | ok | 55 | 0 | 0 | 0 | 0 | 0 | 7.4.2-1 Numbered headings / The first heading level is H2 / Expected result: fail |
| 7.4.2-t01-fail-b.pdf | ok | 90 | 0 | 0 | 0 | 0 | 0 | 7.4.2-1 Numbered headings / Heading level 4 follows immediately after Heading level 2 in weakly structured document /... |
| 7.4.2-t01-pass-a.pdf | ok | 55 | 0 | 0 | 0 | 0 | 0 | 7.4.2-1 Numbered headings / The first heading level is H1 / Expected result: pass |
| 7.4.2-t01-pass-b.pdf | ok | 52 | 0 | 0 | 0 | 0 | 0 | 7.4.2-1 Numbered headings / Heading level 1 is repeated more than once / Expected result: pass |
| 7.4.2-t01-pass-c.pdf | ok | 181 | 0 | 0 | 0 | 0 | 0 | 7.4.2-1 Numbered headings / Heading levels have next sequence: H1-H2-H3-H4-H3-H4-H3-H4-H2-H3 in weakly structured doc... |
| 7.4.2-t01-pass-d.pdf | ok | 38 | 0 | 0 | 0 | 0 | 0 | 7.4.2-1 Numbered headings / H1 is enclosed in Sect, H2 is enclosed in Sect and H3 is enclosed in Sect / Expected resu... |
| 7.4.4-t01-fail-a.pdf | ok | 65 | 0 | 0 | 0 | 0 | 0 | 7.4.4-1 Unnumbered headings / PDF document is strongly structured / Sect contains two headings H / Expected result: fail |
| 7.4.4-t01-pass-a.pdf | ok | 65 | 0 | 0 | 0 | 0 | 0 | 7.4.4-1 Unnumbered headings / PDF document is strongly structured / Document contains two Sect / Each Sect contains o... |
| 7.4.4-t02-fail-a.pdf | ok | 134 | 0 | 0 | 0 | 0 | 0 | 7.4.4-3 Unnumbered headings / PDF document is strongly structured / First Section contains H / Second Section contain... |
| 7.4.4-t02-fail-b.pdf | ok | 134 | 0 | 0 | 0 | 0 | 0 | 7.4.4-3 Unnumbered headings / PDF document is weakly structured / H and H1 are present in Sect / Expected result: fail |
| 7.4.4-t02-pass-a.pdf | ok | 134 | 0 | 0 | 0 | 0 | 0 | 7.4.4-3 Unnumbered headings / PDF document is strongly structured / Document contains two Sections / Each Sect contai... |
| 7.4.4-t02-pass-b.pdf | ok | 134 | 0 | 0 | 0 | 0 | 0 | 7.4.4-3 Unnumbered headings / PDF document is weakly structured / Document contains two Heading Level 1 / Expected re... |
| 7.4.4-t03-fail-a.pdf | ok | 134 | 0 | 0 | 0 | 0 | 0 | 7.4.4-3 Unnumbered headings / PDF document is strongly structured / First Section contains H / Second Section contain... |
| 7.4.4-t03-fail-b.pdf | ok | 134 | 0 | 0 | 0 | 0 | 0 | 7.4.4-3 Unnumbered headings / PDF document is weakly structured / H and H1 are present in Sect / Expected result: fail |
| 7.5-t01-fail-a.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / ID and Headers are not present for cell (row = 2, column = 2) / Scope attribute is not defined for the... |
| 7.5-t01-fail-b.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / Scope, Associated Headers and ID are not present in standard structure types of Table / Expected resul... |
| 7.5-t01-fail-c.pdf | ok | 40 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / Table has row and column headers but not all TH cells have a Scope attribute / TD cells do not have an... |
| 7.5-t01-pass-a.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / ID and Header are not present in standard structure types of Table / Scope attribute is present for al... |
| 7.5-t01-pass-b.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / Scope attribute is not present in TH cells / ID and Header are present for all corresponding structure... |
| 7.5-t01-pass-c.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / Scope attribute is not present in TH cells / (Index) Table Heading has no associated subcells / Expect... |
| 7.5-t01-pass-d.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / Scope attribute is not present in TH cells / ID and Header are present for all corresponding structure... |
| 7.5-t01-pass-e.pdf | ok | 175 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / Scope attribute is not present in TH cells / Table Heading (Row) / Headers attribute is associated wit... |
| 7.5-t02-fail-a.pdf | ok | 95 | 0 | 0 | 0 | 0 | 0 | 7.5-1 Tables / ID is not present for cell (row = 2, column = 2) / Scope attribute is not defined for the TH cells "15... |
| 7.7-t01-fail-a.pdf | ok | 22 | 0 | 0 | 0 | 0 | 0 | 7.7-1 Mathematical expressions / Alt or Actual entries are not present in Formula / Expected result: fail |
| 7.7-t01-fail-b.pdf | ok | 22 | 0 | 0 | 0 | 0 | 0 | 7.7-1 Mathematical expressions / Alt entry is present in Formula / Value of Alt is empty / Expected result: fail |
| 7.7-t01-pass-a.pdf | ok | 22 | 0 | 0 | 0 | 0 | 0 | 7.7-1 Mathematical expressions / Alt entry is present in Formula / Expected result: pass |
| 7.7-t01-pass-b.pdf | ok | 22 | 0 | 0 | 0 | 0 | 0 | 7.7-1 Mathematical expressions / ActualText entry is present in Formula / Expected result: pass |
| 7.7-t01-pass-c.pdf | ok | 22 | 0 | 0 | 0 | 0 | 0 | 7.7-1 Mathematical expressions / ActualText entry is present in Formula / Value of ActualText is empty / Expected res... |
| 7.9-t01-fail-a.pdf | ok | 297 | 0 | 0 | 0 | 0 | 0 | 7.9-2 Notes and references / ID entry is not present in Note structure element / Expected result: fail |
| 7.9-t01-fail-b.pdf | ok | 297 | 0 | 0 | 0 | 0 | 0 | 7.9-2 Notes and references / ID entry is present in Note structure element / Value of ID is empty / Expected result: ... |
| 7.9-t01-pass-a.pdf | ok | 297 | 0 | 0 | 0 | 0 | 0 | 7.9-2 Notes and references / ID entry is present in Note structure element / Expected result: pass |
| 7.9-t02-fail-a.pdf | ok | 277 | 0 | 0 | 0 | 0 | 0 | 7.9-2 Notes and references / Both Note structure elements are contain the same ID / Expected result: fail |
| 7.9-t02-pass-a.pdf | ok | 277 | 0 | 0 | 0 | 0 | 0 | 7.9-2 Notes and references / ID entry is unique for each Note structure element / Expected result: pass |
