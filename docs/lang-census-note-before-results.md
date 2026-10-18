# lang-census: a note written before the results

Written 2026-10-18 around 20:50 UTC by AI agents working for MV2 of Munim, Inc. The study's job
(lang-census-v2) started on the shared compute machine at 20:31 UTC and was still running; we
had seen none of its output. CC BY 4.0.

This note is a separate file on purpose. The job records the SHA-256 of
`docs/lang-census-prereg.md` as it was when the job started (with Amendment 1), and that file
stays byte for byte as it was. Nothing below changes the crawl, the detectors, the thresholds,
the rules, predictions L1 to L4 or check K.

## What we found while the job ran
While the job waited and ran, we read the source of the two pinned language detectors again
(py3langid 0.4.0 at its tag, and langdetect 1.0.9), looking for anything that could make check K
fail for a reason that has nothing to do with the documents' languages. We found two:

1. **A class for text with no language.** py3langid 0.4.0's model has 139 languages "plus
   `zxx`" (its changelog), the code for no linguistic content. langdetect has no such class:
   it turns digits and punctuation into word breaks and skips words written in capitals, and if
   a chunk then has no letter n-grams it raises "No features in text", which lang.py records as
   no language. So a chunk made mostly of numbers or capitalised headings (budget tables,
   agenda headings) could be one py3langid is sure of (`zxx`, or another code) while langdetect
   names nothing. K counts that chunk as a disagreement.
2. **A stricter bar than we assumed.** py3langid 0.4.0's normalized probabilities are
   "length-calibrated" (its changelog): the scores are divided by the square root of the text's
   length in bytes before they are turned into probabilities. That flattens them, so fewer
   200-character chunks reach 0.9 than with the older langid.py. This mainly changes how many
   PDFs get a text language (more "undetermined"), not which language they get.

We have not measured either effect. lang.py keeps only how many chunks py3langid was sure of and
how many of those langdetect agreed with, per PDF; it does not keep which languages disagreed, or
any text. So the finished run cannot tell us why K is what it is.

## What we commit to now
- K is scored exactly as pre-registered: at least 90% of the chunks py3langid gives 0.9 or more
  must get the same language from langdetect.
- If K holds, this note changes nothing.
- If K fails, we report it as failed and, as the pre-registration says, do not score L1 to L3 as
  findings. We will not say that the two effects above caused the failure, because this run
  cannot show it; we will list them only as untested possibilities.
- Any study that records which languages disagree, or that leaves out chunks without linguistic
  content, is a new study. It gets its own pre-registration, published before its job runs, on a
  fresh crawl, and it does not rescore this run.
- We will report how many PDFs came out "undetermined" either way.

Made by MV2 of Munim, Inc. with AI agents. Apache-2.0 (code), CC BY 4.0 (this text).
