# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
"""Does the post-extension drop in PDF titles hold within the same governments?

Usage: python title_pairs.py pdfs-public.jsonl [out.json]

Reads the v0.2.2 row file (one JSON row per PDF), groups readable dated PDFs by site (`qid`,
one per city, county or town government) and compares the share of PDFs with a document title
before and after the Title II extension with each site counted once: site-weighted shares over
all sites, and per-site changes for sites with files in both windows. Standard library only.
See docs/title-pairs-prereg.md.
"""
import json
import math
import sys

Z = 1.959964
NAN = float("nan")

WINDOWS = {
    "PRE": ("2025-04-20", "2026-04-19"),
    "POST": ("2026-04-20", "2026-10-16"),
    "R3": ("2026-01-20", "2026-04-19"),
    "A3": ("2026-04-20", "2026-07-19"),
    # placebo: the same split one year earlier
    "PRE0": ("2024-04-20", "2025-04-19"),
    "POST0": ("2025-04-20", "2025-10-16"),
}
COMPARISONS = (("PRE", "POST"), ("R3", "A3"), ("PRE0", "POST0"))
MIN_FILES = 3


def in_window(created, window):
    start, end = window
    return bool(created) and start <= created <= end


def site_counts(rows, window, check="title"):
    """{qid: [passing files, files]} for readable rows created inside the window."""
    out = {}
    for row in rows:
        if row.get("result") != "ok" or not in_window(row.get("created"), window):
            continue
        k_n = out.setdefault(row["qid"], [0, 0])
        k_n[0] += bool(row.get(check))
        k_n[1] += 1
    return out


def mean_ci(values, z=Z):
    """Mean with a normal-approximation 95% interval (sample sd); (mean, low, high)."""
    n = len(values)
    if n == 0:
        return (NAN, NAN, NAN)
    m = sum(values) / n
    if n < 2:
        return (m, NAN, NAN)
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))
    half = z * sd / math.sqrt(n)
    return (m, m - half, m + half)


def unpaired_diff(first, second, z=Z):
    """Mean of `second` minus mean of `first`, Welch normal-approximation 95% interval."""
    if len(first) < 2 or len(second) < 2:
        return (NAN, NAN, NAN)

    def mean_var(values):
        m = sum(values) / len(values)
        return m, sum((v - m) ** 2 for v in values) / (len(values) - 1)
    m1, v1 = mean_var(first)
    m2, v2 = mean_var(second)
    d = m2 - m1
    half = z * math.sqrt(v1 / len(first) + v2 / len(second))
    return (d, d - half, d + half)


def sign_test(up, down):
    """Exact two-sided sign test p-value (ties already dropped)."""
    n = up + down
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(up, down) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def shares(counts):
    return [k / n for k, n in counts.values()]


def paired(before, after, min_files=1):
    """Per-site change in share for sites with at least `min_files` files in both windows."""
    both = sorted(q for q in set(before) & set(after)
                  if before[q][1] >= min_files and after[q][1] >= min_files)
    diffs = [after[q][0] / after[q][1] - before[q][0] / before[q][1] for q in both]
    up = sum(d > 0 for d in diffs)
    down = sum(d < 0 for d in diffs)
    out = {"sites": len(both), "up": up, "down": down, "same": len(both) - up - down,
           "sign_p": sign_test(up, down)}
    out["mean"], out["low"], out["high"] = mean_ci(diffs)
    return out


def analyse(rows):
    c = {name: site_counts(rows, w) for name, w in WINDOWS.items()}
    site_weighted = {}
    pairs = {}
    for before, after in COMPARISONS:
        key = before + "_" + after
        d, low, high = unpaired_diff(shares(c[before]), shares(c[after]))
        site_weighted[key] = {"diff": d, "low": low, "high": high}
        pairs[key] = paired(c[before], c[after])
    dense = paired(c["PRE"], c["POST"], MIN_FILES)
    main_pair = pairs["PRE_POST"]
    # NaN compares False, so a comparison with too few sites never counts as held
    predictions = {
        "U1": site_weighted["PRE_POST"]["diff"] <= -0.03,
        "U2": main_pair["mean"] > -0.03,
        "U3": main_pair["sign_p"] >= 0.05,
        "U4": pairs["R3_A3"]["mean"] > -0.03,
        "U5": dense["mean"] > -0.03,
        "U6": site_weighted["PRE0_POST0"]["diff"] > -0.03,
    }
    return {
        "sites": {name: len(c[name]) for name in WINDOWS},
        "files": {name: sum(n for _, n in c[name].values()) for name in WINDOWS},
        "titled": {name: sum(k for k, _ in c[name].values()) for name in WINDOWS},
        "site_weighted": site_weighted,
        "paired": pairs,
        "paired_min_files": dict(dense, min_files=MIN_FILES),
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
    t, fl, s = result["titled"], result["files"], result["sites"]
    print("CHECK title " + " ".join("%s=%d/%d" % (name, t[name], fl[name]) for name in WINDOWS))
    print("SITES " + " ".join("%s=%d" % (name, s[name]) for name in WINDOWS))
    for before, after in COMPARISONS:
        d = result["site_weighted"][before + "_" + after]
        print("SW %s->%s diff=%.4f (%.4f..%.4f)" % (before, after, d["diff"], d["low"], d["high"]))
    lines = [("PAIRED %s->%s" % pair, result["paired"]["_".join(pair)]) for pair in COMPARISONS]
    lines.append(("PAIRED%d PRE->POST" % MIN_FILES, result["paired_min_files"]))
    for label, q in lines:
        print("%s sites=%d up=%d down=%d same=%d sign_p=%.4f mean=%.4f (%.4f..%.4f)" % (
            label, q["sites"], q["up"], q["down"], q["same"], q["sign_p"], q["mean"], q["low"],
            q["high"]))
    print("predictions held: %d of 6" % sum(result["predictions"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
