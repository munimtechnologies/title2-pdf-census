"""qcfr_page: the qcfr scoring's outputs, turned into the public results.

From qcfr.py's out folder it copies summary.json, results.md and sites-public.json into
results/qcfr-v1/, writes run-facts.json (the day it was scored and the SHA-256 of the code and of
the rows it read; no URL and no site name), then writes docs/qcfr-results.md from those files alone
and adds one bullet to the README after the wordsig one. No number on the page is typed in:
test_qcfr_results.py checks that the page and the bullet are exactly what this writes.
Standard library only.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import qcfr  # noqa: E402

__version__ = "0.1.0"

OUT_FILES = ("summary.json", "results.md", "sites-public.json")
README_ANCHOR = "- **Confirmatory test of the Word pattern (wordsig"
SIGN = "Made by MV2 of Munim, Inc. with AI agents."
BANNED = ("an ai", "by hand", "hand check", "http", "://")
LIMITS = ("Groups follow the province label Wikidata gave each municipality when the crawl ran. "
          "Quebec's municipalities differ from the others in more than language: size, software, "
          "staff and how many French documents they publish, so a gap says where wrong document "
          "languages are, not why. Text is read from the first 5 pages, and a PDF counts as "
          "French only when two detectors agree on enough of its text. The cohort is the "
          "municipalities of 10,000+ people that Wikidata lists with a website, and the PDFs the "
          "crawl reached. No screen reader was used. The private rows, which have URLs and site "
          "ids, are not published.")


# ---------------------------------------------------------------- files

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def lf_sha256(path):
    """SHA-256 of a file with CRLF read as LF, so a checkout's line endings do not change it."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# ---------------------------------------------------------------- wording

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


def q1_parts(s):
    q1 = s["Q1_rest_wrong_more_than_quebec"]
    return q1, q1["rest"], q1["quebec"]


def outcome(s):
    q1 = s["Q1_rest_wrong_more_than_quebec"]
    if q1["status"] != "scored":
        return "inconclusive"
    return "held" if q1["met"] else "not held"


def group_text(c):
    return "%d of %d (%s, %d sites)" % (c["k"], c["n"], pct(c["share"]), c["sites"])


def verdict_text(s):
    q1, r, q = q1_parts(s)
    o = outcome(s)
    if o == "inconclusive":
        return ("**Inconclusive: too few.** Outside Quebec the crawl has %d French-text PDFs from %d "
                "sites, Quebec %d from %d sites. The pre-registered minimum was %d PDFs and %d sites "
                "in each group, so Q1 is not scored and nothing is claimed." % (
                    r["n"], r["sites"], q["n"], q["sites"], qcfr.MIN_PDFS, qcfr.MIN_SITES))
    measured = ("Outside Quebec, %s of the French-text PDFs have a document language that is "
                "missing, unusable or names another language; in Quebec, %s. The gap is %.1f "
                "percentage points, and the site-level permutation test gives one-sided p = %s." % (
                    group_text(r), group_text(q), 100 * q1["gap"], pval(q1["p_permutation"])))
    if o == "held":
        return ("**Q1 held.** %s In this cohort, wrong document languages on French PDFs are more "
                "common where French is not the language of municipal administration. The test "
                "does not show why." % measured)
    text = "**Q1 did not hold.** %s" % measured
    if q1["gap"] <= 0:
        text += " The gap is not in the predicted direction."
    return text + (" In this cohort, a wrong document language on a French PDF is not clearly rarer "
                   "where French is the language of municipal administration.")


def page(s, f):
    q1, r, q = q1_parts(s)
    e = s["explore_by_group"]
    lines = [
        "# qcfr results: French PDFs in Quebec and in the rest of Canada", "",
        wrap("Scored %s by AI agents working for MV2 of Munim, Inc., as fixed in the "
             "[pre-registration](qcfr-prereg.md) before the split by province was computed. It "
             "re-reads the rows of the wordsig crawl ([wordsig-results.md](wordsig-results.md)) "
             "with `results/lang-v1/lang.py` %s unchanged; no new crawl was made. Machine checks "
             "only: nothing here is a WCAG conformance judgment about any government, and no "
             "government is named. Code Apache-2.0; this text and the data CC BY 4.0." % (
                 f["scored_on"], s["lang_version"])), "",
        wrap("`test_qcfr_results.py` in the repository root runs the site-level permutation test "
             "again on [results/qcfr-v1/sites-public.json](../results/qcfr-v1/sites-public.json) "
             "with `qcfr.score_sites`, counts the PDF-level numbers again from the public wordsig "
             "rows, and checks that this page is exactly what `qcfr_page.py` writes from those "
             "files. The site table has one `[group, French-text PDFs, wrong]` row per site and no "
             "site name, URL or Wikidata id; the site-resampled intervals need the private site "
             "ids and are not rechecked."), "",
        "## Verdict", "", wrap(verdict_text(s)), "",
        "## Pre-registered prediction", "",
        "| Prediction | Measured | Result |", "|---|---|---|",
        "| Q1: French-text PDFs of municipalities outside Quebec have a missing, unusable or other "
        "/Lang more often than Quebec's (site-level permutation, one-sided, p < 0.05; scored with at "
        "least %d PDFs and %d sites in each group) | outside Quebec %s; Quebec %s; gap %s; p = %s "
        "| %s |" % (qcfr.MIN_PDFS, qcfr.MIN_SITES, group_text(r), group_text(q),
                    "n/a" if q1["gap"] is None else "%.1f points" % (100 * q1["gap"]),
                    pval(q1["p_permutation"]), qcfr.verdict(q1["met"])), "",
        wrap("Site-resampled 95%% intervals: outside Quebec %s, Quebec %s." % (
            ci(e["rest"]["cluster_ci95"]), ci(e["quebec"]["cluster_ci95"]))), "",
        "## Rows", "",
        bullet("PDFs in the wordsig crawl %d; read without error %d; French text %d." % (
            s["pdfs"], s["ok"], s["french_text"])),
        bullet("Left out: French-text PDFs with no province %d; sites whose rows carry two groups "
               "%d." % (s["french_text_no_province"], s["sites_with_two_groups"])),
        bullet("Permutations %d, seed `%s`; qcfr.py %s." % (q1["permutations"], q1["seed"],
                                                          s["version"])),
        "", "## Exploratory (no prediction)", "",
        bullet("Declared /Lang of French-text PDFs outside Quebec: %s." % listing(e["rest"]["declared"])),
        bullet("Declared /Lang of French-text PDFs in Quebec: %s." % listing(e["quebec"]["declared"])),
        bullet("Language named when it is not French: outside Quebec %s; Quebec %s." % (
            listing(e["rest"]["declared_other_primary"]),
            listing(e["quebec"]["declared_other_primary"]))),
        bullet("PDF-level one-sided Fisher exact p, which ignores that PDFs of one site are alike: "
               "%s." % pval(s["explore_pdf_level_fisher_p"])),
        "", "## Limits", "", wrap(LIMITS), "", SIGN,
    ]
    return "\n".join(lines) + "\n"


def readme_bullet(s, f):
    q1, r, q = q1_parts(s)
    o = outcome(s)
    short = {"held": "Q1 held", "not held": "Q1 did not hold",
             "inconclusive": "inconclusive, too few"}[o]
    text = ("**French PDFs in Quebec and elsewhere (qcfr, pre-registered, scored %s): %s.** Of the "
            "wordsig crawl's French-text PDFs, %d of %d outside Quebec (%d sites) and %d of %d in "
            "Quebec (%d sites) have a `/Lang` that is missing, unusable or names another language" % (
                f["scored_on"], short, r["k"], r["n"], r["sites"], q["k"], q["n"], q["sites"]))
    if q1["p_permutation"] is not None:
        text += " (site-level permutation, one-sided p = %s)" % pval(q1["p_permutation"])
    return "- " + text + (". No new crawl was made ([docs/qcfr-prereg.md](docs/qcfr-prereg.md), "
                          "[docs/qcfr-results.md](docs/qcfr-results.md); `test_qcfr_results.py` "
                          "runs the test again from the public site table).")


def add_readme(readme, line):
    """The README with one line added right after the wordsig bullet; nothing else changes."""
    if "docs/qcfr-results.md" in readme:
        raise RuntimeError("the README already has the qcfr bullet")
    lines = readme.splitlines(keepends=True)
    hits = [i for i, l in enumerate(lines) if l.startswith(README_ANCHOR)]
    if len(hits) != 1:
        raise RuntimeError("the wordsig bullet is in the README %d times" % len(hits))
    i = hits[0]
    end = "\r\n" if lines[i].endswith("\r\n") else "\n"
    return "".join(lines[:i + 1] + [line + end] + lines[i + 1:])


# ---------------------------------------------------------------- main

def build(out_dir, repo, docs):
    res = os.path.join(repo, "results", "qcfr-v1")
    if os.path.exists(res) and os.listdir(res):
        raise RuntimeError("results/qcfr-v1 is not empty")
    readme_path = os.path.join(repo, "README.md")
    with open(readme_path, encoding="utf-8", newline="") as fh:
        readme = fh.read()
    os.makedirs(res, exist_ok=True)
    os.makedirs(os.path.join(repo, "docs"), exist_ok=True)
    for name in OUT_FILES:
        shutil.copyfile(os.path.join(out_dir, name), os.path.join(res, name))
    s = json.loads(read_text(os.path.join(res, "summary.json")))
    f = {
        "version": __version__,
        "scored_on": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        "qcfr_sha256": lf_sha256(os.path.join(repo, "qcfr.py")),
        "lang_sha256": lf_sha256(os.path.join(repo, "results", "lang-v1", "lang.py")),
        "docs_rows_sha256": lf_sha256(docs),
    }
    write(os.path.join(res, "run-facts.json"), json.dumps(f, indent=1) + "\n")
    write(os.path.join(repo, "docs", "qcfr-results.md"), page(s, f))
    with open(readme_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(add_readme(readme, readme_bullet(s, f)))
    files = []
    for rel in ["results/qcfr-v1/%s" % n for n in OUT_FILES + ("run-facts.json",)] \
            + ["docs/qcfr-results.md", "README.md"]:
        with open(os.path.join(repo, *rel.split("/")), "rb") as fh:
            data = fh.read()
        files.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return {"outcome": outcome(s), "bullet": readme_bullet(s, f), "files": files}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write the results files into a copy of the repository")
    b.add_argument("--out-dir", required=True, help="qcfr.py's out folder")
    b.add_argument("--repo", required=True, help="a folder laid out like the repository")
    b.add_argument("--docs", required=True, help="the docs-private.jsonl qcfr.py read")
    args = ap.parse_args(argv)
    print(json.dumps(build(args.out_dir, args.repo, args.docs), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
