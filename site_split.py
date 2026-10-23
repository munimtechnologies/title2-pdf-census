# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
"""Site-weighted follow-up to the deadline split: one vote per government, not per PDF.

Usage: python site_split.py pdfs-public.jsonl [out.json]

Reads the v0.2.2 row file (one JSON row per PDF), groups readable dated PDFs by site (`qid`,
one per city, county or town government) and compares the tagged share in the 3 months before
the Title II extension (R3) with the 3 months after (A3), with each site counted once.
Standard library only. See docs/site-split-prereg.md.
"""
import json
import math
import sys

Z = 1.959964

WINDOWS = {
    "R3": ("2026-01-20", "2026-04-19"),
    "A3": ("2026-04-20", "2026-07-19"),
    # placebo: the same calendar months one year earlier
    "R3_2025": ("2025-01-20", "2025-04-19"),
    "A3_2025": ("2025-04-20", "2025-07-19"),
}
TOP_SITES_DROPPED = 10


def in_window(created, window):
    start, end = window
    return bool(created) and start <= created <= end


def site_counts(rows, window, check="tagged"):
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
        return (float("nan"), float("nan"), float("nan"))
    m = sum(values) / n
    if n < 2:
        return (m, float("nan"), float("nan"))
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))
    half = z * sd / math.sqrt(n)
    return (m, m - half, m + half)


def unpaired_diff(first, second, z=Z):
    """Mean of `second` minus mean of `first`, Welch normal-approximation 95% interval."""
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


def paired(before, after):
    """Per-site change in share for sites with files in both windows, sorted by qid."""
    both = sorted(set(before) & set(after))
    diffs = [after[q][0] / after[q][1] - before[q][0] / before[q][1] for q in both]
    up = sum(d > 0 for d in diffs)
    down = sum(d < 0 for d in diffs)
    out = {"sites": len(both), "up": up, "down": down, "same": len(both) - up - down,
           "sign_p": sign_test(up, down)}
    if len(diffs) >= 2:
        out["mean"], out["low"], out["high"] = mean_ci(diffs)
    return out


def pooled_without_top(before, after, drop=TOP_SITES_DROPPED):
    """Pooled file-level shares after removing the `drop` sites with the most files in both
    windows together (ties broken by qid)."""
    total = {}
    for counts in (before, after):
        for q, (_, n) in counts.items():
            total[q] = total.get(q, 0) + n
    top = set(sorted(total, key=lambda q: (-total[q], q))[:drop])

    def pool(counts):
        k = sum(v[0] for q, v in counts.items() if q not in top)
        n = sum(v[1] for q, v in counts.items() if q not in top)
        return k, n
    k1, n1 = pool(before)
    k2, n2 = pool(after)
    diff = k2 / n2 - k1 / n1 if n1 and n2 else float("nan")
    return {"dropped_sites": len(top), "dropped_files": sum(total[q] for q in top),
            "before_k": k1, "before_n": n1, "after_k": k2, "after_n": n2, "diff": diff}


def analyse(rows):
    c = {name: site_counts(rows, w) for name, w in WINDOWS.items()}
    files = {name: sum(n for _, n in c[name].values()) for name in WINDOWS}
    tagged = {name: sum(k for k, _ in c[name].values()) for name in WINDOWS}
    sw = {name: mean_ci(shares(c[name])) for name in WINDOWS}
    d, low, high = unpaired_diff(shares(c["R3"]), shares(c["A3"]))
    pair = paired(c["R3"], c["A3"])
    placebo = paired(c["R3_2025"], c["A3_2025"])
    top = pooled_without_top(c["R3"], c["A3"])
    predictions = {
        "S1": d < 0,
        "S2": d <= -0.03,
        "S3": pair["down"] > pair["up"],
        "S4": pair.get("mean", 0.0) <= -0.03,
        "S5": placebo.get("mean", -1.0) >= -0.01,
        "S6": top["diff"] <= -0.03,
    }
    return {
        "sites": {name: len(c[name]) for name in WINDOWS},
        "files": files,
        "tagged": tagged,
        "site_weighted": {name: {"mean": m, "low": lo, "high": hi}
                          for name, (m, lo, hi) in sw.items()},
        "site_weighted_diff": {"diff": d, "low": low, "high": high},
        "paired": pair,
        "placebo_paired": placebo,
        "without_top_sites": top,
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
    s, fl, t = result["sites"], result["files"], result["tagged"]
    sw, sd = result["site_weighted"], result["site_weighted_diff"]
    p, pp, top = result["paired"], result["placebo_paired"], result["without_top_sites"]
    print("FILES R3=%d/%d A3=%d/%d R3_2025=%d/%d A3_2025=%d/%d" % (
        t["R3"], fl["R3"], t["A3"], fl["A3"], t["R3_2025"], fl["R3_2025"],
        t["A3_2025"], fl["A3_2025"]))
    print("SITES R3=%d A3=%d paired=%d R3_2025=%d A3_2025=%d paired_2025=%d" % (
        s["R3"], s["A3"], p["sites"], s["R3_2025"], s["A3_2025"], pp["sites"]))
    print("S1S2 site-weighted R3=%.4f A3=%.4f diff=%.4f (%.4f..%.4f)" % (
        sw["R3"]["mean"], sw["A3"]["mean"], sd["diff"], sd["low"], sd["high"]))
    for label, q in (("S3S4 paired", p), ("S5 placebo", pp)):
        print("%s up=%d down=%d same=%d sign_p=%.4f mean=%.4f (%.4f..%.4f)" % (
            label, q["up"], q["down"], q["same"], q["sign_p"], q.get("mean", float("nan")),
            q.get("low", float("nan")), q.get("high", float("nan"))))
    print("S6 without top %d sites (%d files) R3=%d/%d A3=%d/%d diff=%.4f" % (
        top["dropped_sites"], top["dropped_files"], top["before_k"], top["before_n"],
        top["after_k"], top["after_n"], top["diff"]))
    print("predictions held: %d of 6" % sum(result["predictions"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
