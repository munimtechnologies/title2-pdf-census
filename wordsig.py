"""wordsig: is the "Word signature" real? A pre-registered test on Canadian municipalities.

The lang-census found, after looking (docs/lang-word-note.md, exploratory), that most Word-made
non-English PDFs whose document language (/Lang) names English already mark the real language
inside, on structure elements or marked content, while Adobe-made ones rarely do. A pattern found
by looking cannot be confirmed on the same rows. This tests it on PDFs the lang-census never read:
those of Canadian municipalities, which publish in French and English, so both directions (French
text declared English, English text declared French) are covered by one rule.

Nothing in the crawl or the checks is new: it runs title2-pdf-census 0.2.2's crawl (public pages
only, robots.txt honoured, 1 s between requests to a site) and lang.py 0.1.1's checks unchanged,
with a Canadian cohort query and its own seed, and scores the predictions in
docs/wordsig-prereg.md. Stores no document text.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import collections
import importlib.util
import json
import math
import os
import sys
import time

__version__ = "0.1.0"

UA = "MV2-wordsig/%s (Munim, Inc.; mv2@munimtech.com; reads public pages only)" % __version__
SEED = "wordsig-v1"
CENSUS_VERSION = "0.2.2"
LANG_VERSION = "0.1.1"
# Fixed in docs/wordsig-prereg.md before any PDF is read.
COHORT_CLASS = "municipality"
MIN_POPULATION = 10000
CLASSES = {
    # municipality (Q15284), and anything under it
    "municipality": "?type wdt:P279* wd:Q15284 .",
    # city (Q515) or town (Q3957), and anything under them
    "city-town": "?type wdt:P279* ?root . VALUES ?root { wd:Q515 wd:Q3957 }",
}
ALPHA = 0.05
MIN_GROUP = 8       # Word and Adobe mismatched PDFs each needed to score W1 and W2
W2_WORD_MIN = 0.60
W2_ADOBE_MAX = 0.40
W3_MIN = 3          # Word and Adobe mismatched PDFs each needed in a direction for W3
W4_MIN_SITES = 5
POWER_NS = (8, 10, 15)
POWER_SHARES = ((0.8, 0.2), (0.7, 0.3))


def cohort_query(cls=COHORT_CLASS, min_population=MIN_POPULATION):
    """A query in the shape census.fetch_cohort expects: the province comes out as ?stateLabel
    and its OPTIONAL clause is one line, so census's fallback (without provinces) still works."""
    return """
SELECT ?item ?itemLabel ?typeLabel ?stateLabel (MAX(?pop) AS ?population) (SAMPLE(?site) AS ?website) WHERE {
  ?item wdt:P17 wd:Q16 ;
        wdt:P1082 ?pop ;
        wdt:P856 ?site ;
        wdt:P31 ?type .
  %s
  FILTER(?pop >= %d)
  OPTIONAL { ?item wdt:P131* ?state . ?state wdt:P31 ?st . VALUES ?st { wd:Q11828004 wd:Q9357527 } }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
}
GROUP BY ?item ?itemLabel ?typeLabel ?stateLabel
""" % (CLASSES[cls], min_population)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def setup(census_path, lang_path, cls=COHORT_CLASS, min_population=MIN_POPULATION):
    """census.py and lang.py as released, pointed at the Canadian cohort and this study's seed."""
    census, lang = load(census_path, "census"), load(lang_path, "lang")
    if census.__version__ != CENSUS_VERSION or lang.__version__ != LANG_VERSION:
        raise RuntimeError("need census %s and lang %s, got %s and %s" % (
            CENSUS_VERSION, LANG_VERSION, census.__version__, lang.__version__))
    census.COHORT_QUERY = cohort_query(cls, min_population)
    census.UA = UA  # robots.txt is checked for this agent
    lang.SITE_SEED = SEED
    return census, lang


def fetch(census, waits=(60, 180, 300, 0)):
    for wait in waits:
        try:
            return census.fetch_cohort()
        except Exception as e:
            print("cohort failed (%s), waiting %d s" % (e, wait), file=sys.stderr)
            time.sleep(wait)
    return None


def cohort_counts(cohort):
    return {"sites": len(cohort),
            "provinces": dict(collections.Counter(r["state"] or "(none)" for r in cohort).most_common()),
            "kinds": dict(collections.Counter(r["kind"] for r in cohort).most_common())}


def run(census_path, lang_path, out_dir, workers, minutes):
    census, lang = setup(census_path, lang_path)
    cohort = fetch(census)
    if not cohort:
        return 1
    with open(os.path.join(out_dir, "cohort.json"), "w", encoding="utf-8") as f:
        json.dump(cohort, f, ensure_ascii=False, indent=0)
    print("%d municipalities in the cohort" % len(cohort), flush=True)
    lang.crawl(census, cohort, len(cohort), out_dir, workers, minutes)
    return 0


# ---------------------------------------------------------------- statistics

def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that row 1's share is the higher, for [[a, b], [c, d]]: the
    tables with these margins and at least a in the first cell."""
    r1, c1, n = a + b, a + c, a + b + c + d
    return sum(math.comb(r1, k) * math.comb(n - r1, c1 - k)
               for k in range(a, min(r1, c1) + 1)) / math.comb(n, c1)


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact p for [[a, b], [c, d]]: the tables with these margins that are no
    more likely than this one."""
    r1, c1, n = a + b, a + c, a + b + c + d
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)

    def ways(k):
        return math.comb(r1, k) * math.comb(n - r1, c1 - k)

    obs = ways(a)
    return sum(ways(k) for k in range(lo, hi + 1) if ways(k) <= obs) / math.comb(n, c1)


def held_w1(a, n1, c, n0, alpha=ALPHA):
    return a * n0 > c * n1 and fisher_greater(a, n1 - a, c, n0 - c) < alpha


def power(n1, n0, p1, p0, alpha=ALPHA):
    """Chance that W1 holds with n1 Word and n0 Adobe mismatched PDFs whose true shares are p1
    and p0: every outcome enumerated, no simulation."""
    def pmf(n, p):
        return [math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)]

    f1, f0 = pmf(n1, p1), pmf(n0, p0)
    return sum(f1[a] * f0[c] for a in range(n1 + 1) for c in range(n0 + 1)
               if held_w1(a, n1, c, n0, alpha))


def power_table():
    return [{"n_word": n, "n_adobe": n, "word_share": p1, "adobe_share": p0,
             "power": round(power(n, n, p1, p0), 4)}
            for p1, p0 in POWER_SHARES for n in POWER_NS]


# ---------------------------------------------------------------- scoring

def direction(d):
    t, p = d.get("text_lang"), d.get("lang_primary")
    return "fr-as-en" if (t, p) == ("fr", "en") else "en-as-fr" if (t, p) == ("en", "fr") else "other"


def tally(rows, lang):
    k = sum(1 for d in rows if lang.local_match(d))
    return {"k": k, "n": len(rows), "share": round(k / len(rows), 4) if rows else None}


def score(docs, lang):
    """The pre-registered predictions W1-W4 and the exploratory counts, from the private rows."""
    ok = [d for d in docs if d.get("result") == "ok"]
    det = [d for d in ok if lang.is_language(d.get("text_lang"))]
    mis = [d for d in det if lang.declared(d) == "other"]
    word = [d for d in mis if d.get("producer_family") == "word"]
    adobe = [d for d in mis if d.get("producer_family") == "adobe"]
    w, a = tally(word, lang), tally(adobe, lang)
    enough = w["n"] >= MIN_GROUP and a["n"] >= MIN_GROUP
    p = fisher_greater(w["k"], w["n"] - w["k"], a["k"], a["n"] - a["k"]) if word and adobe else None
    w1 = {"word": dict(w, cluster_ci95=lang.cluster_ci(word, lang.local_match)),
          "adobe": dict(a, cluster_ci95=lang.cluster_ci(adobe, lang.local_match)),
          "p_one_sided": None if p is None else round(p, 6),
          "status": "scored" if enough else "inconclusive: too few",
          "met": held_w1(w["k"], w["n"], a["k"], a["n"]) if enough else None}
    w2 = {"met": (w["share"] >= W2_WORD_MIN and a["share"] <= W2_ADOBE_MAX) if enough else None}
    dirs = {}
    for name in ("fr-as-en", "en-as-fr"):
        dw = tally([d for d in word if direction(d) == name], lang)
        da = tally([d for d in adobe if direction(d) == name], lang)
        dirs[name] = {"word": dw, "adobe": da,
                      "testable": dw["n"] >= W3_MIN and da["n"] >= W3_MIN}
    if all(v["testable"] for v in dirs.values()) and enough and w["share"] != a["share"]:
        sign = w["share"] > a["share"]
        w3 = all((v["word"]["share"] > v["adobe"]["share"]) == sign
                 and v["word"]["share"] != v["adobe"]["share"] for v in dirs.values())
    else:
        w3 = None
    sites = len({d["qid"] for d in word if lang.local_match(d)})
    french = [d for d in det if d["text_lang"] == "fr"]
    non_english = [d for d in det if d["text_lang"] != "en"]
    by_family = collections.defaultdict(lambda: [0, 0])
    for d in mis:
        key = "%s|%s" % (d.get("producer_family"), direction(d))
        by_family[key][0] += 1
        by_family[key][1] += int(lang.local_match(d))
    return {
        "version": __version__,
        "seed": SEED,
        "pdfs": len(docs),
        "ok": len(ok),
        "determined": len(det),
        "text_lang_counts": dict(collections.Counter(d.get("text_lang") for d in ok).most_common()),
        "mismatched": len(mis),
        "W1_word_marks_inside_more_than_adobe": w1,
        "W2_word_60_adobe_40": w2,
        "W3_same_sign_each_direction": {"directions": dirs, "met": w3},
        "W4_word_sites": {"sites": sites, "met": sites >= W4_MIN_SITES if word else None},
        "explore_french_wrong": dict(lang.share(sum(1 for d in french if lang.wrong(d)), len(french)),
                                     cluster_ci95=lang.cluster_ci(french, lang.wrong)),
        "explore_declared_by_text_lang": dict(sorted(collections.Counter(
            "%s:%s" % (d["text_lang"], lang.declared(d)) for d in det).items())),
        "explore_mismatched_by_family_direction": dict(sorted(by_family.items())),
        "explore_word_share_non_english": lang.share(
            sum(1 for d in non_english if d.get("producer_family") == "word"), len(non_english)),
    }


def verdict(met):
    return {True: "held", False: "**not held**", None: "not testable"}[met]


def report(s):
    w1 = s["W1_word_marks_inside_more_than_adobe"]
    w, a = w1["word"], w1["adobe"]
    dirs = s["W3_same_sign_each_direction"]["directions"]
    lines = ["# wordsig results (machine summary)", "",
             "PDFs checked %d; ok %d; text language determined %d; mismatched (declared language "
             "is another language) %d." % (s["pdfs"], s["ok"], s["determined"], s["mismatched"]), "",
             "## Pre-registered predictions", "",
             "| Prediction | Measured | Result |", "|---|---|---|",
             "| W1: Word marks the real language inside more often than Adobe (one-sided Fisher, "
             "p < 0.05) | Word %d of %d, Adobe %d of %d, p = %s (%s) | %s |" % (
                 w["k"], w["n"], a["k"], a["n"], w1["p_one_sided"], w1["status"], verdict(w1["met"])),
             "| W2: Word share 60%%+ and Adobe share 40%% or less | Word %s, Adobe %s | %s |" % (
                 w["share"], a["share"], verdict(s["W2_word_60_adobe_40"]["met"])),
             "| W3: same sign in both directions | fr-as-en Word %d/%d Adobe %d/%d; en-as-fr Word "
             "%d/%d Adobe %d/%d | %s |" % (
                 dirs["fr-as-en"]["word"]["k"], dirs["fr-as-en"]["word"]["n"],
                 dirs["fr-as-en"]["adobe"]["k"], dirs["fr-as-en"]["adobe"]["n"],
                 dirs["en-as-fr"]["word"]["k"], dirs["en-as-fr"]["word"]["n"],
                 dirs["en-as-fr"]["adobe"]["k"], dirs["en-as-fr"]["adobe"]["n"],
                 verdict(s["W3_same_sign_each_direction"]["met"])),
             "| W4: Word PDFs that mark the real language come from 5+ sites | %d sites | %s |" % (
                 s["W4_word_sites"]["sites"], verdict(s["W4_word_sites"]["met"])), "",
             "Site-resampled 95%% intervals: Word %s, Adobe %s" % (
                 json.dumps(w["cluster_ci95"]), json.dumps(a["cluster_ci95"])), "",
             "## Exploratory (no prediction)", "",
             "- Text languages: %s" % json.dumps(s["text_lang_counts"]),
             "- French-text PDFs with a missing, unusable or other /Lang: %s" % json.dumps(
                 s["explore_french_wrong"]),
             "- Text language:declared: %s" % json.dumps(s["explore_declared_by_text_lang"]),
             "- Mismatched by producer family|direction [PDFs, marked inside]: %s" % json.dumps(
                 s["explore_mismatched_by_family_direction"]),
             "- Word share of non-English-text PDFs: %s" % json.dumps(s["explore_word_share_non_english"]),
             ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="fetch the cohort, crawl it and check every readable PDF")
    r.add_argument("--census", required=True)
    r.add_argument("--lang", required=True)
    r.add_argument("--out-dir", required=True)
    r.add_argument("--workers", type=int, default=8)
    r.add_argument("--max-minutes", type=float, default=150)
    c = sub.add_parser("cohort", help="fetch the cohort only (Wikidata; no municipal site is read)")
    c.add_argument("--census", required=True)
    c.add_argument("--lang", required=True)
    c.add_argument("--out-dir", required=True)
    c.add_argument("--cls", choices=sorted(CLASSES), default=COHORT_CLASS)
    c.add_argument("--min-population", type=int, default=MIN_POPULATION)
    s = sub.add_parser("summarize", help="score the predictions from docs-private.jsonl")
    s.add_argument("--lang", required=True)
    s.add_argument("--out-dir", required=True)
    p = sub.add_parser("power", help="print the power of W1 at the pre-registered sizes")
    p.add_argument("--out", default="")
    args = ap.parse_args(argv)

    if args.cmd == "power":
        table = power_table()
        text = json.dumps({"version": __version__, "alpha": ALPHA, "power": table}, indent=1)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        print(text)
        return 0
    os.makedirs(args.out_dir, exist_ok=True)
    if args.cmd == "run":
        return run(args.census, args.lang, args.out_dir, args.workers, args.max_minutes)
    if args.cmd == "cohort":
        census, _ = setup(args.census, args.lang, args.cls, args.min_population)
        cohort = fetch(census, waits=(60, 0))
        if not cohort:
            return 1
        counts = dict(cohort_counts(cohort), cls=args.cls, min_population=args.min_population)
        name = "cohort-%s-%d.json" % (args.cls, args.min_population)
        with open(os.path.join(args.out_dir, name), "w", encoding="utf-8") as f:
            json.dump(counts, f, ensure_ascii=False, indent=1)
        print(json.dumps(counts, ensure_ascii=False))
        return 0
    lang = load(args.lang, "lang")
    with open(os.path.join(args.out_dir, "docs-private.jsonl"), encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]
    summary = score(docs, lang)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(args.out_dir, "wordsig-public.jsonl"), "w", encoding="utf-8") as f:
        for d in docs:
            if d.get("result") == "ok":
                f.write(json.dumps(lang.public(d)) + "\n")
    text = report(summary)
    with open(os.path.join(args.out_dir, "results.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
