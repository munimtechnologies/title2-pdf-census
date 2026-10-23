# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
"""Split the census row file at the Title II extension (2026-04-20) and compare windows.

Usage: python deadline_split.py pdfs-public.jsonl [out.json]

Reads the v0.2.2 row file (one JSON row per PDF) and counts, per creation-date window,
how many readable PDFs pass each basic check. Standard library only.
See docs/deadline-split-prereg.md and docs/deadline-split-results.md.
"""
import json
import math
import sys

Z = 1.959964

WINDOWS = {
    "PRE": ("2025-04-20", "2026-04-19"),
    "POST": ("2026-04-20", "2026-10-16"),
    "R3": ("2026-01-20", "2026-04-19"),
    "A3": ("2026-04-20", "2026-07-19"),
    "PRE0": ("2024-04-20", "2025-04-19"),
    "POST0": ("2025-04-20", "2025-10-16"),
    # exploratory, added after the pre-registered windows were counted
    "R3_2025": ("2025-01-20", "2025-04-19"),
    "A3_2025": ("2025-04-20", "2025-07-19"),
    "APR01_19_2026": ("2026-04-01", "2026-04-19"),
    "APR01_19_2025": ("2025-04-01", "2025-04-19"),
}
CRAWL_DAY = "2026-10-16"
CHECKS = ("tagged", "lang", "title", "image_only", "basic4")


def wilson(k, n, z=Z):
    """95% Wilson score interval for k of n, as (low, high)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


def newcombe(k1, n1, k2, n2, z=Z):
    """Newcombe hybrid score interval for p2 - p1 (second group minus first)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    d = p2 - p1
    low = d - math.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2)
    high = d + math.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)
    return (d, low, high)


def in_window(created, window):
    start, end = window
    return bool(created) and start <= created <= end


def count(rows):
    out = {name: {"n": 0, "figure_files": 0, "figure_files_zero_alt": 0,
                  **{c: 0 for c in CHECKS}} for name in WINDOWS}
    out["_excluded_after_crawl_day"] = 0
    out["_readable"] = 0
    out["_dated"] = 0
    for row in rows:
        if row.get("result") != "ok":
            continue
        out["_readable"] += 1
        created = row.get("created")
        if not created:
            continue
        out["_dated"] += 1
        if created > CRAWL_DAY:
            out["_excluded_after_crawl_day"] += 1
        for name, window in WINDOWS.items():
            if not in_window(created, window):
                continue
            w = out[name]
            w["n"] += 1
            for c in CHECKS:
                w[c] += bool(row.get(c))
            if (row.get("figures") or 0) >= 1:
                w["figure_files"] += 1
                w["figure_files_zero_alt"] += (row.get("figures_alt") or 0) == 0
    return out


def compare(counts, first, second, key, denom_key="n"):
    a, b = counts[first], counts[second]
    d, low, high = newcombe(a[key], a[denom_key], b[key], b[denom_key])
    return {"first": first, "second": second, "check": key,
            "first_share": a[key] / a[denom_key], "second_share": b[key] / b[denom_key],
            "diff": d, "diff_low": low, "diff_high": high}


def predictions(counts):
    """The six pre-registered predictions; point estimates decide."""
    p1 = compare(counts, "PRE", "POST", "tagged")
    p2 = compare(counts, "PRE", "POST", "lang")
    p3 = compare(counts, "PRE", "POST", "title")
    p4 = compare(counts, "R3", "A3", "tagged")
    p5 = compare(counts, "PRE0", "POST0", "tagged")
    p6 = compare(counts, "PRE", "POST", "figure_files_zero_alt", "figure_files")
    return {
        "P1": dict(p1, held=p1["diff"] >= 0),
        "P2": dict(p2, held=p2["diff"] >= 0.02),
        "P3": dict(p3, held=abs(p3["diff"]) < 0.04),
        "P4": dict(p4, held=p4["diff"] >= -0.03),
        "P5": dict(p5, held=abs(p5["diff"]) <= 0.04),
        "P6": dict(p6, held=p6["diff"] <= 0.03),
    }


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    counts = count(rows)
    result = {"counts": counts, "predictions": predictions(counts)}
    text = json.dumps(result, indent=1, sort_keys=True)
    if len(argv) > 2:
        with open(argv[2], "w", encoding="utf-8") as f:
            f.write(text + "\n")
    held = sum(p["held"] for p in result["predictions"].values())
    for name in ("PRE", "POST", "R3", "A3", "PRE0", "POST0"):
        w = counts[name]
        print("%s n=%d tagged=%d lang=%d title=%d image_only=%d basic4=%d figs=%d figs_zero_alt=%d"
              % (name, w["n"], w["tagged"], w["lang"], w["title"], w["image_only"], w["basic4"],
                 w["figure_files"], w["figure_files_zero_alt"]))
    print("predictions held: %d of 6" % held)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
