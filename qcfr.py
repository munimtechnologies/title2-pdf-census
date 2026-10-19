"""qcfr: do Quebec municipalities' French PDFs declare French more often than other provinces'?

The wordsig crawl (docs/wordsig-results.md) read 1,616 PDFs from Canadian municipal websites and
found, as an exploratory count, that 43.9% of the French-text PDFs have a document language
(/Lang) that is missing, unusable or names another language. This tests, as pre-registered in
docs/qcfr-prereg.md, whether that share is lower for municipalities in Quebec, where French is
the working language and office software is most often set up in French, than for those in the
other provinces and territories, where French versions are often made from English originals.

No new crawl: it re-reads the wordsig crawl's rows with lang.py 0.1.1's rules unchanged. PDFs of
one site are not independent, so the main test permutes the province label across sites, not
PDFs. Writes counts only; the public site table has no site names, URLs or Wikidata ids.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import importlib.util
import json
import math
import os
import random
import sys

__version__ = "0.1.0"

LANG_VERSION = "0.1.1"
# Fixed in docs/qcfr-prereg.md before the split is computed.
QUEBEC = "Quebec"     # the province label in the wordsig cohort (Wikidata's English label)
ALPHA = 0.05
MIN_PDFS = 20         # French-text PDFs each group needs for Q1 to be scored
MIN_SITES = 4         # sites with a French-text PDF each group needs
PERMUTATIONS = 20000
SEED = "qcfr-v1"
EPS = 1e-12


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_lang(path):
    lang = load(path, "lang")
    if lang.__version__ != LANG_VERSION:
        raise RuntimeError("need lang %s, got %s" % (LANG_VERSION, lang.__version__))
    return lang


def group_of(state):
    if not state:
        return None
    return "quebec" if state == QUEBEC else "rest"


# ---------------------------------------------------------------- statistics

def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that row 1's share is the higher, for [[a, b], [c, d]]."""
    r1, c1, n = a + b, a + c, a + b + c + d
    return sum(math.comb(r1, k) * math.comb(n - r1, c1 - k)
               for k in range(a, min(r1, c1) + 1)) / math.comb(n, c1)


def gap(sites, labels):
    """Pooled wrong share of the 'rest' sites minus that of the 'quebec' sites."""
    k = {"quebec": 0, "rest": 0}
    n = {"quebec": 0, "rest": 0}
    for (_, sn, sk), g in zip(sites, labels):
        k[g] += sk
        n[g] += sn
    return k["rest"] / n["rest"] - k["quebec"] / n["quebec"]


def permutation_p(sites, reps=PERMUTATIONS, seed=SEED):
    """One-sided p for gap() > 0: the province labels are shuffled across sites, each site keeping
    all its PDFs; p = (1 + permutations at least as large as the observed gap) / (1 + reps)."""
    labels = [g for g, _, _ in sites]
    observed = gap(sites, labels)
    rng = random.Random(seed)
    hits = 0
    for _ in range(reps):
        rng.shuffle(labels)
        if gap(sites, labels) >= observed - EPS:
            hits += 1
    return (1 + hits) / (1 + reps)


def score_sites(sites, reps=PERMUTATIONS):
    """Q1 from the site table [[group, French-text PDFs, of which wrong], ...]."""
    out = {}
    for g in ("quebec", "rest"):
        rows = [s for s in sites if s[0] == g]
        n, k = sum(s[1] for s in rows), sum(s[2] for s in rows)
        out[g] = {"sites": len(rows), "k": k, "n": n, "share": round(k / n, 4) if n else None}
    enough = all(out[g]["n"] >= MIN_PDFS and out[g]["sites"] >= MIN_SITES for g in out)
    q1 = {"quebec": out["quebec"], "rest": out["rest"], "gap": None, "p_permutation": None,
          "permutations": reps, "seed": SEED,
          "status": "scored" if enough else "inconclusive: too few", "met": None}
    if enough:
        g = gap(sites, [s[0] for s in sites])
        p = permutation_p(sites, reps)
        q1.update(gap=round(g, 4), p_permutation=round(p, 6), met=g > 0 and p < ALPHA)
    return q1


# ---------------------------------------------------------------- scoring

def french_rows(docs, lang):
    """ok PDFs whose text language is French, with their group; rows with no province dropped."""
    out = []
    for d in docs:
        if d.get("result") != "ok" or d.get("text_lang") != "fr":
            continue
        g = group_of(d.get("state"))
        if g:
            out.append((g, d))
    return out


def site_table(rows, lang):
    """[[group, PDFs, wrong], ...] per site, sorted, without ids. A site whose rows carry two
    groups is left out and counted."""
    by_site = collections.defaultdict(list)
    for g, d in rows:
        by_site[d["qid"]].append((g, d))
    table, split = [], 0
    for items in by_site.values():
        groups = {g for g, _ in items}
        if len(groups) > 1:
            split += 1
            continue
        table.append([groups.pop(), len(items), sum(1 for _, d in items if lang.wrong(d))])
    return sorted(table), split


def score(docs, lang, reps=PERMUTATIONS):
    ok = [d for d in docs if d.get("result") == "ok"]
    rows = french_rows(docs, lang)
    sites, split = site_table(rows, lang)
    q1 = score_sites(sites, reps)
    explore = {}
    for g in ("quebec", "rest"):
        docs_g = [d for gg, d in rows if gg == g]
        explore[g] = {
            "declared": dict(sorted(collections.Counter(lang.declared(d) for d in docs_g).items())),
            "declared_other_primary": dict(collections.Counter(
                d.get("lang_primary") for d in docs_g if lang.declared(d) == "other").most_common()),
            "cluster_ci95": lang.cluster_ci(docs_g, lang.wrong),
        }
    qk, qn, rk, rn = q1["quebec"]["k"], q1["quebec"]["n"], q1["rest"]["k"], q1["rest"]["n"]
    pdf_p = fisher_greater(rk, rn - rk, qk, qn - qk) if qn and rn else None
    return {
        "version": __version__,
        "lang_version": LANG_VERSION,
        "pdfs": len(docs),
        "ok": len(ok),
        "french_text": sum(1 for d in ok if d.get("text_lang") == "fr"),
        "french_text_no_province": sum(1 for d in ok if d.get("text_lang") == "fr"
                                       and not group_of(d.get("state"))),
        "sites_with_two_groups": split,
        "Q1_rest_wrong_more_than_quebec": q1,
        "explore_by_group": explore,
        "explore_pdf_level_fisher_p": None if pdf_p is None else round(pdf_p, 6),
    }


def verdict(met):
    return {True: "held", False: "**not held**", None: "not testable"}[met]


def report(s):
    q1 = s["Q1_rest_wrong_more_than_quebec"]
    q, r = q1["quebec"], q1["rest"]
    e = s["explore_by_group"]
    lines = ["# qcfr results (machine summary)", "",
             "PDFs in the wordsig crawl %d; ok %d; French text %d (no province: %d); sites with "
             "rows in two groups (left out): %d." % (
                 s["pdfs"], s["ok"], s["french_text"], s["french_text_no_province"],
                 s["sites_with_two_groups"]), "",
             "## Pre-registered prediction", "",
             "| Prediction | Measured | Result |", "|---|---|---|",
             "| Q1: French-text PDFs of municipalities outside Quebec have a missing, unusable or "
             "other /Lang more often than Quebec's (site permutation, one-sided, p < 0.05) | "
             "outside Quebec %d of %d (%d sites), Quebec %d of %d (%d sites), gap %s, p = %s (%s) "
             "| %s |" % (r["k"], r["n"], r["sites"], q["k"], q["n"], q["sites"], q1["gap"],
                         q1["p_permutation"], q1["status"], verdict(q1["met"])), "",
             "Site-resampled 95%% intervals: outside Quebec %s, Quebec %s" % (
                 json.dumps(e["rest"]["cluster_ci95"]), json.dumps(e["quebec"]["cluster_ci95"])), "",
             "## Exploratory (no prediction)", "",
             "- Declared /Lang of French-text PDFs, outside Quebec: %s" % json.dumps(
                 e["rest"]["declared"]),
             "- Declared /Lang of French-text PDFs, Quebec: %s" % json.dumps(e["quebec"]["declared"]),
             "- Language named when it is not French, outside Quebec: %s; Quebec: %s" % (
                 json.dumps(e["rest"]["declared_other_primary"]),
                 json.dumps(e["quebec"]["declared_other_primary"])),
             "- PDF-level one-sided Fisher p (ignores that PDFs of one site are alike): %s" % (
                 s["explore_pdf_level_fisher_p"]),
             ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--lang", required=True, help="results/lang-v1/lang.py")
    ap.add_argument("--docs", required=True, help="the wordsig crawl's docs-private.jsonl")
    ap.add_argument("--out-dir", required=True, help="a new folder for the results")
    args = ap.parse_args(argv)

    if os.path.exists(args.out_dir) and os.listdir(args.out_dir):
        print("refused: %s is not empty" % args.out_dir)
        return 2
    lang = load_lang(args.lang)
    with open(args.docs, encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]
    s = score(docs, lang)
    sites, _ = site_table(french_rows(docs, lang), lang)
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(s, f, indent=1)
    with open(os.path.join(args.out_dir, "sites-public.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(sites, f)
    text = report(s)
    with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
