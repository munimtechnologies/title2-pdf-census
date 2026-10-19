"""wordsig_page: the wordsig crawl's outputs, turned into the public results.

From the job's out folder it copies summary.json and results.md, splits wordsig-public.jsonl into
parts under 1.9 MB, writes run-facts.json (counts only: the cohort's size and provinces, the sites'
crawl results, the run's times and the SHA-256 of the code it ran; no URL and no site name), then
writes docs/wordsig-results.md from those files alone and adds a dated section to
docs/lang-word-note.md. No number on the page is typed in: test_wordsig_results.py checks that the
page is exactly what this writes. W3 is scored as the pre-registration's text and its Amendment 1
say. Standard library only.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wordsig as ws  # noqa: E402

__version__ = "0.1.0"

MAX_PART = 1_900_000  # bytes per public-rows file (the publish lane takes files under 2 MB)
STUDY_FILES = ("wordsig.py", "test_wordsig.py", "census.py", "results/lang-v1/lang.py")
HEX = re.compile(r"[0-9a-f]{64}")
STATUS = re.compile(r"[a-z_-]{1,30}")
PART = re.compile(r"wordsig-public-(\d+)\.jsonl")
NOTE_HEAD = "## Confirmatory test"
SIGN = "Made by MV2 of Munim, Inc. with AI agents."
BANNED = ("an ai", "by hand", "hand check", "http", "://")
LIMITS = ("Producer strings name the tool, not its version or settings, and Word includes files "
          "whose Creator names Word but whose Producer is another tool. Canada is not the US. "
          "Wikidata lists only some municipalities' websites, so the cohort is the municipalities "
          "Wikidata lists, not all of them. Text is read from the first 5 pages, and marked-content "
          "/Lang is found only when written inline. No copy of Word and no screen reader was used. "
          "The private rows, which have URLs, are not published.")


# ---------------------------------------------------------------- files

def read_text(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_jsonl(path):
    text = read_text(path) or ""
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def load_public(res_dir):
    """The public rows, from wordsig-public-1.jsonl, wordsig-public-2.jsonl, ..."""
    names = sorted((n for n in os.listdir(res_dir) if PART.fullmatch(n)),
                   key=lambda n: int(PART.fullmatch(n).group(1)))
    rows = []
    for name in names:
        rows += read_jsonl(os.path.join(res_dir, name))
    return rows


def split_public(src, dest):
    """wordsig-public.jsonl as numbered parts under MAX_PART bytes, cut only between rows."""
    with open(src, "rb") as f:
        data = f.read()
    parts, cur, size = [], [], 0
    for line in data.splitlines(keepends=True):
        if len(line) > MAX_PART:
            raise RuntimeError("one row is bigger than a part")
        if cur and size + len(line) > MAX_PART:
            parts.append(b"".join(cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line)
    parts.append(b"".join(cur))
    if b"".join(parts) != data:
        raise RuntimeError("the parts do not join back to the rows")
    names = []
    for i, part in enumerate(parts, 1):
        name = "wordsig-public-%d.jsonl" % i
        with open(os.path.join(dest, name), "wb") as f:
            f.write(part)
        names.append(name)
    return names


def facts(out_dir, prereg, setup_log=None):
    """Counts and hashes from the job's own files, with no URL or site name in them."""
    cohort_text = read_text(os.path.join(out_dir, "cohort.json"))
    cohort = json.loads(cohort_text) if cohort_text else []
    sites = read_jsonl(os.path.join(out_dir, "sites-private.jsonl"))
    status = collections.Counter(s.get("status") if STATUS.fullmatch(str(s.get("status"))) else "other"
                                 for s in sites)
    hashes, versions = {}, None
    for line in (read_text(os.path.join(out_dir, "code-sha256.txt")) or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and HEX.fullmatch(parts[0]):
            hashes[parts[1].lstrip("*")] = parts[0]
        elif line.strip() and "://" not in line:
            versions = line.strip()

    def stamp(name):
        return (read_text(os.path.join(out_dir, name)) or "").strip() or None

    m = re.search(r"([0-9a-f]{64})\s+\*?census-tag\.py", read_text(setup_log) or "")
    tag = m.group(1) if m else None
    return {
        "version": __version__,
        "cohort_sites": len(cohort),
        "cohort_provinces": dict(collections.Counter(r.get("state") or "(none)" for r in cohort).most_common()),
        "sites_crawled": len(sites),
        "site_results": dict(sorted(status.items())),
        "pdfs_from_sites": sum(int(s.get("pdfs_checked") or 0) for s in sites),
        "started_at": stamp("started-at.txt"),
        "finished_at": stamp("finished-at.txt"),
        "code_sha256": {k: hashes.get(k) for k in STUDY_FILES + ("wordsig-prereg.md",)},
        "code_matches_prereg": all(bool(hashes.get(k)) and hashes[k] in prereg for k in STUDY_FILES),
        "package_versions": versions,
        "census_tag_sha256": tag,
        "census_tag_equals_census": None if tag is None else tag == hashes.get("census.py"),
    }


# ---------------------------------------------------------------- scoring as the text says

def w1_parts(s):
    w1 = s["W1_word_marks_inside_more_than_adobe"]
    return w1, w1["word"], w1["adobe"]


def outcome(s):
    w1 = s["W1_word_marks_inside_more_than_adobe"]
    if w1["status"] != "scored":
        return "inconclusive"
    return "held" if w1["met"] else "not held"


def w3_prereg(s):
    """W3 as the pre-registration's text scores it (Amendment 1): judged when each direction has
    W3_MIN Word and Adobe mismatched PDFs, held if Word's share is higher in each."""
    dirs = s["W3_same_sign_each_direction"]["directions"]
    if not all(v["testable"] for v in dirs.values()):
        return None
    # exact shares, k/n, compared without rounding
    return all(v["word"]["k"] * v["adobe"]["n"] > v["adobe"]["k"] * v["word"]["n"]
               for v in dirs.values())


# ---------------------------------------------------------------- page

def wrap(text, first="", rest=""):
    return textwrap.fill(text, width=100, initial_indent=first, subsequent_indent=rest,
                         break_long_words=False, break_on_hyphens=False)


def bullet(text):
    return wrap(text, "- ", "  ")


def pct(share):
    return "n/a" if share is None else "%.1f%%" % (100 * share)


def ci(c):
    return "n/a" if not c else "%.1f-%.1f%%" % (100 * c[0], 100 * c[1])


def pval(p):
    if p is None:
        return "n/a"
    return "< 0.000001" if p < 0.000001 else "%.6f" % p


def listing(d):
    return ", ".join("%s %s" % (k, v) for k, v in d.items()) or "none"


def day(f):
    return (f.get("finished_at") or "")[:10] or "an unrecorded date"


def counts(s):
    w1, w, a = w1_parts(s)
    return "Word %d of %d against Adobe %d of %d, one-sided p = %s" % (
        w["k"], w["n"], a["k"], a["n"], pval(w1["p_one_sided"]))


def verdict_text(s):
    w1, w, a = w1_parts(s)
    o = outcome(s)
    measured = ("Among mismatched PDFs (the document language names a different language from the "
                "text), %d of %d Word-made ones mark the real language inside the file, against %d "
                "of %d Adobe-made ones (one-sided Fisher exact p = %s)." % (
                    w["k"], w["n"], a["k"], a["n"], pval(w1["p_one_sided"])))
    if o == "inconclusive":
        text = ("**Inconclusive: too few.** The crawl found %d Word-made and %d Adobe-made "
                "mismatched PDFs (the document language names a different language from the text). "
                "The pre-registered minimum was %d of each, so W1 and W2 are not scored and nothing "
                "is claimed; the counts are published below. As pre-registered, there is no second "
                "crawl unless an amendment is published first." % (w["n"], a["n"], ws.MIN_GROUP))
    elif o == "held":
        text = ("**W1 held.** %s The pattern the [Word note](lang-word-note.md) found after looking "
                "at the lang-census appeared again on PDFs that census never read, from another "
                "country." % measured)
    else:
        text = ("**W1 did not hold.** %s The pattern the [Word note](lang-word-note.md) found after "
                "looking at the lang-census did not clearly appear again here." % measured)
        if min(w["n"], a["n"]) < max(ws.POWER_NS):
            text += (" With groups this small W1 had limited power (see the power line under "
                     "Exploratory), so, as the pre-registration says, this is weak evidence against "
                     "the pattern, not proof that it is absent.")
    return text + (" site_check 0.2.1 leads with the Acrobat fix only for a file whose parts already "
                   "carry the text's language, so its advice for any one file does not depend on "
                   "this result; what this result bears on is how often Word output looks like that.")


def table(s):
    w1, w, a = w1_parts(s)
    dirs = s["W3_same_sign_each_direction"]["directions"]

    def pair(name):
        x = dirs[name]
        return "Word %d of %d, Adobe %d of %d" % (x["word"]["k"], x["word"]["n"],
                                                  x["adobe"]["k"], x["adobe"]["n"])

    return [
        "| Prediction | Measured | Result |", "|---|---|---|",
        "| W1 (primary): Word's share that marks the real language inside is higher than Adobe's "
        "(one-sided Fisher exact, p < 0.05; scored with at least %d of each) | Word %d of %d, "
        "Adobe %d of %d; p = %s | %s |" % (ws.MIN_GROUP, w["k"], w["n"], a["k"], a["n"],
                                          pval(w1["p_one_sided"]), ws.verdict(w1["met"])),
        "| W2: Word's share at least 60%%, Adobe's at most 40%% | Word %s, Adobe %s | %s |" % (
            pct(w["share"]), pct(a["share"]), ws.verdict(s["W2_word_60_adobe_40"]["met"])),
        "| W3: Word's share is higher in both directions (judged with at least %d of each in each) "
        "| French declared English: %s; English declared French: %s | %s |" % (
            ws.W3_MIN, pair("fr-as-en"), pair("en-as-fr"), ws.verdict(w3_prereg(s))),
        "| W4: the Word PDFs that mark the real language inside come from at least %d sites | %d "
        "sites | %s |" % (ws.W4_MIN_SITES, s["W4_word_sites"]["sites"],
                          ws.verdict(s["W4_word_sites"]["met"])),
    ]


def families(d):
    return ", ".join("%s %d (%d marked inside)" % (k, v[0], v[1]) for k, v in d.items()) or "none"


def share_text(c):
    return "%d of %d (%s)" % (c["k"], c["n"], pct(c["share"]))


def page(s, f):
    w1, w, a = w1_parts(s)
    w3_code = s["W3_same_sign_each_direction"]["met"]
    fr = s["explore_french_wrong"]
    tag = {True: "is the same file as", False: "**differs from**", None: "was not compared with"}
    code = ("the four study files had the SHA-256 values the pre-registration lists"
            if f["code_matches_prereg"] else
            "**at least one study file had a SHA-256 the pre-registration does not list**")
    lines = [
        "# wordsig results: the Word signature on PDFs nobody had looked at", "",
        wrap("Scored %s by AI agents working for MV2 of Munim, Inc., from the crawl described in the "
             "[pre-registration](wordsig-prereg.md), which fixed the predictions, the minimum "
             "sample and the code before any PDF was read. Machine checks only: nothing here is a "
             "WCAG conformance judgment about any government, and no government is named. Code "
             "Apache-2.0; this text and the data CC BY 4.0." % day(f)), "",
        wrap("`test_wordsig_results.py` in the repository root scores the public rows in "
             "[results/wordsig-v1/](../results/wordsig-v1/) again with `wordsig.py`, checks that "
             "every count, share and p-value agrees with `summary.json`, and checks that this page "
             "is exactly what `wordsig_page.py` writes from those files. Public rows carry no site "
             "id, so the site counts and the site-resampled intervals come from `summary.json` and "
             "are not rechecked."), "",
        "## Verdict", "", wrap(verdict_text(s)), "",
        "## Pre-registered predictions", "",
    ] + table(s) + [""]
    if w3_prereg(s) != w3_code:
        lines += [wrap("W3 is scored by the pre-registration's text, as its Amendment 1 says. The W3 "
                       "value that `wordsig.py` 0.1.0 itself computes is %s here (it also requires "
                       "W1's minimum sample and compares each direction with the overall sign)."
                       % ws.verdict(w3_code)), ""]
    lines += [
        wrap("Site-resampled 95%% intervals for W1's shares: Word %s, Adobe %s." % (
            ci(w["cluster_ci95"]), ci(a["cluster_ci95"]))), "",
        "## The crawl", "",
        bullet("Cohort: %d municipal website hosts listed on Wikidata, fetched again when the crawl "
               "ran. By province: %s." % (f["cohort_sites"], listing(f["cohort_provinces"]))),
        bullet("Sites crawled: %d (%s)." % (f["sites_crawled"], listing(f["site_results"]))),
        bullet("Ran from %s to %s (UTC)." % (f["started_at"] or "an unrecorded time",
                                             f["finished_at"] or "an unrecorded time")),
        bullet("PDFs checked %d; read without error %d; text language determined %d; mismatched "
               "%d." % (s["pdfs"], s["ok"], s["determined"], s["mismatched"])),
        bullet("Code: %s. census.py on main %s the file at tag v0.2.2. Packages: %s." % (
            code, tag[f["census_tag_equals_census"]], f["package_versions"] or "not recorded")),
        "", "## Exploratory (no prediction)", "",
        bullet("Text languages of the PDFs read without error: %s." % listing(s["text_lang_counts"])),
        bullet("French-text PDFs whose /Lang is missing, unusable or another language: %d of %d (%s; "
               "site-resampled 95%% interval %s)." % (fr["k"], fr["n"], pct(fr["share"]),
                                                      ci(fr["cluster_ci95"]))),
        bullet("Text language and what the document declares: %s." % listing(
            s["explore_declared_by_text_lang"])),
        bullet("Mismatched PDFs by producer family and direction: %s." % families(
            s["explore_mismatched_by_family_direction"])),
        bullet("Word's share of non-English-text PDFs: %s." % share_text(
            s["explore_word_share_non_english"])),
    ]
    if w1["status"] == "scored":
        lines.append(bullet(
            "Not pre-registered: with %d Word and %d Adobe mismatched PDFs, W1 had a %s chance of "
            "holding if the true shares were 80%% and 20%%, and %s if they were 70%% and 30%% "
            "(`wordsig.power`, every outcome enumerated)." % (
                w["n"], a["n"], pct(round(ws.power(w["n"], a["n"], 0.8, 0.2), 4)),
                pct(round(ws.power(w["n"], a["n"], 0.7, 0.3), 4)))))
    lines += ["", "## Limits", "", wrap(LIMITS), "", SIGN]
    return "\n".join(lines) + "\n"


def note_section(s, f):
    o = outcome(s)
    if o == "inconclusive":
        w1, w, a = w1_parts(s)
        short = ("inconclusive, too few mismatched PDFs (Word %d, Adobe %d; %d of each were needed), "
                 "so nothing is claimed" % (w["n"], a["n"], ws.MIN_GROUP))
    else:
        short = "W1 %s (%s)" % ("held" if o == "held" else "did not hold", counts(s))
    return "%s (added %s)\n%s\n" % (NOTE_HEAD, day(f), wrap(
        "The pre-registered test of this pattern on PDFs of Canadian municipalities is scored in "
        "[wordsig-results.md](wordsig-results.md): %s." % short))


def add_note(note, section):
    if NOTE_HEAD in note:
        raise RuntimeError("the note already has a confirmatory section")
    i = note.rindex(SIGN)
    return note[:i] + section + "\n" + note[i:]


# ---------------------------------------------------------------- main

def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build(out_dir, repo, setup_log=None):
    res = os.path.join(repo, "results", "wordsig-v1")
    os.makedirs(res, exist_ok=True)
    if any(PART.fullmatch(n) for n in os.listdir(res)):
        raise RuntimeError("results/wordsig-v1 already has public rows")
    prereg = read_text(os.path.join(repo, "docs", "wordsig-prereg.md"))
    note = read_text(os.path.join(repo, "docs", "lang-word-note.md"))
    if prereg is None or note is None:
        raise RuntimeError("docs/wordsig-prereg.md and docs/lang-word-note.md must be in the tree")
    for name in ("summary.json", "results.md"):
        shutil.copyfile(os.path.join(out_dir, name), os.path.join(res, name))
    parts = split_public(os.path.join(out_dir, "wordsig-public.jsonl"), res)
    f = facts(out_dir, prereg, setup_log)
    write(os.path.join(res, "run-facts.json"), json.dumps(f, indent=1) + "\n")
    s = json.loads(read_text(os.path.join(res, "summary.json")))
    write(os.path.join(repo, "docs", "wordsig-results.md"), page(s, f))
    write(os.path.join(repo, "docs", "lang-word-note.md"), add_note(note, note_section(s, f)))
    files = []
    for rel in ["results/wordsig-v1/%s" % n for n in ["summary.json", "results.md", "run-facts.json"] + parts] \
            + ["docs/wordsig-results.md", "docs/lang-word-note.md"]:
        with open(os.path.join(repo, *rel.split("/")), "rb") as fh:
            data = fh.read()
        files.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return {"outcome": outcome(s), "w3_text": w3_prereg(s),
            "w3_code": s["W3_same_sign_each_direction"]["met"], "note": note_section(s, f),
            "files": files}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write the results files into a copy of the repository")
    b.add_argument("--out-dir", required=True, help="the crawl job's out folder")
    b.add_argument("--repo", required=True, help="a folder laid out like the repository")
    b.add_argument("--setup-log", default="", help="the setup step's stdout (census-tag.py hash)")
    args = ap.parse_args(argv)
    print(json.dumps(build(args.out_dir, args.repo, args.setup_log or None), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
