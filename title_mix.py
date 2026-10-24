# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
"""Is the post-extension drop in PDF titles a change in software mix or in practice?

Usage: python title_mix.py pdfs-public.jsonl [out.json]

Reads the v0.2.2 row file (one JSON row per PDF), groups readable dated PDFs by the software that
made them (`producer_family`, merged into six groups) and splits each window-to-window change in
the share of PDFs with a document title into a within-group part (same software, different
practice) and a mix part (different software). Standard library only.
See docs/title-mix-prereg.md.
"""
import json
import math
import random
import sys

WINDOWS = {
    "PRE": ("2025-04-20", "2026-04-19"),
    "POST": ("2026-04-20", "2026-10-16"),
    "R3": ("2026-01-20", "2026-04-19"),
    "A3": ("2026-04-20", "2026-07-19"),
    # placebo: the same split one year earlier
    "PRE0": ("2024-04-20", "2025-04-19"),
    "POST0": ("2025-04-20", "2025-10-16"),
}
GROUPS = {"word": "office", "office-other": "office", "adobe": "adobe",
          "print-to-pdf": "print-to-pdf", "scanner": "scanner", "unknown": "unknown"}
GROUP_ORDER = ("office", "adobe", "print-to-pdf", "scanner", "unknown", "rest")
BOOT_REPS = 2000
BOOT_SEED = 20261024
NAN = float("nan")


def in_window(created, window):
    start, end = window
    return bool(created) and start <= created <= end


def group(row):
    """Six groups; libreoffice, google-docs, generator and other go to "rest"."""
    return GROUPS.get(row.get("producer_family"), "rest")


def window_rows(rows, window):
    return [r for r in rows if r.get("result") == "ok" and in_window(r.get("created"), window)]


def group_counts(rows, check="title"):
    """{group: [passing files, files]} for every group in GROUP_ORDER."""
    out = {g: [0, 0] for g in GROUP_ORDER}
    for r in rows:
        k_n = out[group(r)]
        k_n[0] += bool(r.get(check))
        k_n[1] += 1
    return out


def decompose(before, after):
    """Split after-share minus before-share into a within-group part and a mix part.

    within = sum, over groups with files in both windows, of (before weight) x (after share minus
    before share); mix = total change minus within. A group missing from either window adds
    nothing to within, so its effect lands in mix."""
    n1 = sum(n for _, n in before.values())
    n2 = sum(n for _, n in after.values())
    if not n1 or not n2:
        return {"before": NAN, "after": NAN, "diff": NAN, "within": NAN, "mix": NAN}
    s1 = sum(k for k, _ in before.values()) / n1
    s2 = sum(k for k, _ in after.values()) / n2
    within = 0.0
    for g in GROUP_ORDER:
        (k1, m1), (k2, m2) = before[g], after[g]
        if m1 and m2:
            within += m1 / n1 * (k2 / m2 - k1 / m1)
    return {"before": s1, "after": s2, "diff": s2 - s1, "within": within,
            "mix": s2 - s1 - within}


def bootstrap_within(before_rows, after_rows, reps=BOOT_REPS, seed=BOOT_SEED):
    """Percentile 95% interval of the within part, resampling sites (`qid`) with replacement."""
    by_site = {}
    for i, part in enumerate((before_rows, after_rows)):
        for r in part:
            by_site.setdefault(r["qid"], ([], []))[i].append(r)
    sites = sorted(by_site)
    counts = [(group_counts(by_site[q][0]), group_counts(by_site[q][1])) for q in sites]
    rng = random.Random(seed)
    values = []
    for _ in range(reps):
        before = {g: [0, 0] for g in GROUP_ORDER}
        after = {g: [0, 0] for g in GROUP_ORDER}
        for _ in sites:
            b, a = counts[rng.randrange(len(sites))]
            for g in GROUP_ORDER:
                before[g][0] += b[g][0]
                before[g][1] += b[g][1]
                after[g][0] += a[g][0]
                after[g][1] += a[g][1]
        within = decompose(before, after)["within"]
        if not math.isnan(within):
            values.append(within)
    values.sort()
    if not values:
        return {"sites": len(sites), "reps": 0, "low": NAN, "high": NAN}
    last = len(values) - 1
    return {"sites": len(sites), "reps": len(values),
            "low": values[int(0.025 * last + 0.5)], "high": values[int(0.975 * last + 0.5)]}


def share(k_n):
    k, n = k_n
    return k / n if n else NAN


def analyse(rows, reps=BOOT_REPS):
    w = {name: window_rows(rows, win) for name, win in WINDOWS.items()}
    c = {name: group_counts(w[name]) for name in WINDOWS}
    main = decompose(c["PRE"], c["POST"])
    short = decompose(c["R3"], c["A3"])
    placebo = decompose(c["PRE0"], c["POST0"])
    largest = sorted(GROUP_ORDER, key=lambda g: (-c["PRE"][g][1], GROUP_ORDER.index(g)))[:3]
    lower = [g for g in largest if share(c["POST"][g]) < share(c["PRE"][g])]
    boot = bootstrap_within(w["PRE"], w["POST"], reps=reps)
    predictions = {
        "T1": abs(main["mix"]) < 0.02,
        "T2": main["within"] <= -0.03,
        "T3": short["within"] <= -0.03,
        "T4": len(lower) >= 2,
        "T5": placebo["within"] >= -0.02,
        "T6": boot["high"] < 0,
    }
    return {
        "group_counts": c,
        "titled": {name: sum(k for k, _ in c[name].values()) for name in WINDOWS},
        "files": {name: sum(n for _, n in c[name].values()) for name in WINDOWS},
        "PRE_POST": main,
        "R3_A3": short,
        "placebo_PRE0_POST0": placebo,
        "largest_groups": largest,
        "largest_lower": lower,
        "bootstrap_within_PRE_POST": boot,
        "predictions": predictions,
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    result = analyse(rows)
    if len(argv) > 2:
        with open(argv[2], "w", encoding="utf-8") as f:
            f.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    t, fl, c = result["titled"], result["files"], result["group_counts"]
    print("CHECK title " + " ".join("%s=%d/%d" % (name, t[name], fl[name]) for name in WINDOWS))
    for name in ("PRE", "POST"):
        print("GROUPS %s " % name + " ".join("%s=%d/%d" % (g, c[name][g][0], c[name][g][1])
                                             for g in GROUP_ORDER))
    for label, d in (("T1T2 PRE->POST", result["PRE_POST"]), ("T3 R3->A3", result["R3_A3"]),
                     ("T5 placebo PRE0->POST0", result["placebo_PRE0_POST0"])):
        print("%s diff=%.4f within=%.4f mix=%.4f" % (label, d["diff"], d["within"], d["mix"]))
    print("T4 largest=%s lower=%s" % (",".join(result["largest_groups"]),
                                      ",".join(result["largest_lower"]) or "none"))
    b = result["bootstrap_within_PRE_POST"]
    print("T6 bootstrap sites=%d reps=%d within (%.4f..%.4f)" % (b["sites"], b["reps"], b["low"],
                                                                 b["high"]))
    print("predictions held: %d of 6" % sum(result["predictions"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
