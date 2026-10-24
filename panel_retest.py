# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
"""Same-day re-crawl check: do two crawls of the same governments see the same PDFs, and agree on them?

Usage: python panel_retest.py first.jsonl second.jsonl [out.json]

Reads two row files (one JSON row per PDF tried; the URL replaced by `url_sha256`), matches files
across the two crawls by (`qid`, `url_sha256`), and measures how many readable files of the first
crawl are read again by the second, whether the machine checks agree on the files read twice, and
whether a file's basic4 result predicts being read again (it should not, a few hours apart).
Standard library only. See docs/panel-retest-prereg.md.
"""
import json
import math
import sys

Z = 1.959964
NAN = float("nan")

CHECKS = ("tagged", "lang", "title", "image_only", "basic4")


def key(row):
    return (row.get("qid"), row.get("url_sha256"))


def ok_rows(rows):
    """{(qid, url_sha256): row} for readable rows."""
    return {key(r): r for r in rows if r.get("result") == "ok"}


def ok_sites(rows):
    return {r.get("qid") for r in rows if r.get("result") == "ok"}


def share(k, n):
    return k / n if n else NAN


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


def sign_test(up, down):
    """Exact two-sided sign test p-value (ties already dropped)."""
    n = up + down
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(up, down) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def base_href_sites(rows):
    """Sites where the first crawl got a 404 on a link with a space: the sign of the <base href> gap."""
    return {r.get("qid") for r in rows if r.get("url_has_space") and r.get("status") == 404}


def paired_basic4(first_ok, seen, sites):
    """Per site: share of failing files read again minus share of passing files read again."""
    by_site = {}
    for k, r in first_ok.items():
        if k[0] not in sites:
            continue
        cell = by_site.setdefault(k[0], {True: [0, 0], False: [0, 0]})
        cell[bool(r.get("basic4"))][0] += k in seen
        cell[bool(r.get("basic4"))][1] += 1
    diffs = [share(*c[False]) - share(*c[True])
             for _, c in sorted(by_site.items()) if c[False][1] and c[True][1]]
    up = sum(d > 0 for d in diffs)
    down = sum(d < 0 for d in diffs)
    out = {"sites": len(diffs), "up": up, "down": down, "same": len(diffs) - up - down,
           "sign_p": sign_test(up, down)}
    out["mean"], out["low"], out["high"] = mean_ci(diffs)
    return out


def analyse(first, second):
    a_ok, b_ok = ok_rows(first), ok_rows(second)
    b_any = {key(r) for r in second}
    both_sites = ok_sites(first) & ok_sites(second)
    seen = set(a_ok) & set(b_ok)
    on_both = [k for k in a_ok if k[0] in both_sites]
    pairs = sorted(seen)
    disagree = {c: sum(bool(a_ok[k].get(c)) != bool(b_ok[k].get(c)) for k in pairs) for c in CHECKS}
    checks_same = sum(all(bool(a_ok[k].get(c)) == bool(b_ok[k].get(c)) for c in CHECKS)
                      for k in pairs)
    bytes_same = sum(a_ok[k].get("bytes") == b_ok[k].get("bytes") for k in pairs)
    created_same = sum(a_ok[k].get("created") == b_ok[k].get("created") for k in pairs)
    basic4 = {}
    for label, want in (("fail", False), ("pass", True)):
        ks = [k for k, r in a_ok.items() if bool(r.get("basic4")) == want]
        basic4[label] = {"seen": sum(k in seen for k in ks), "files": len(ks)}
    basic4_diff = (share(basic4["fail"]["seen"], basic4["fail"]["files"])
                   - share(basic4["pass"]["seen"], basic4["pass"]["files"]))
    paired = paired_basic4(a_ok, seen, both_sites)
    proxy = base_href_sites(first) & both_sites
    split = {}
    for label, sites in (("base_href", proxy), ("other", both_sites - proxy)):
        ks = [k for k in on_both if k[0] in sites]
        split[label] = {"sites": len(sites), "seen": sum(k in seen for k in ks), "files": len(ks)}
    seen_all = share(len(seen), len(a_ok))
    seen_both = share(sum(k in seen for k in on_both), len(on_both))
    # NaN compares False, so a measure with nothing to count never counts as held
    predictions = {
        "R1": seen_all >= 0.80,
        "R2": seen_both >= 0.90,
        "R3": share(checks_same, len(pairs)) >= 0.99,
        "R4": share(bytes_same, len(pairs)) >= 0.98,
        "R5": abs(basic4_diff) < 0.05,
        "R6": abs(paired["mean"]) < 0.05,
    }
    return {
        "first": {"ok": len(a_ok), "sites": len(ok_sites(first))},
        "second": {"ok": len(b_ok), "sites": len(ok_sites(second))},
        "sites_in_both": len(both_sites),
        "seen": {"files": len(seen), "of": len(a_ok), "share": seen_all},
        "seen_on_sites_in_both": {"files": sum(k in seen for k in on_both), "of": len(on_both),
                                  "share": seen_both},
        "seen_any_result": {"files": sum(k in b_any for k in a_ok), "of": len(a_ok)},
        "agree": {"pairs": len(pairs), "checks_same": checks_same, "bytes_same": bytes_same,
                  "created_same": created_same, "disagreements": disagree},
        "basic4": dict(basic4, diff=basic4_diff),
        "paired_basic4": paired,
        "base_href_split": split,
        "predictions": predictions,
    }


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    result = analyse(load(argv[1]), load(argv[2]))
    if len(argv) > 3:
        with open(argv[3], "w", encoding="utf-8") as f:
            f.write(json.dumps(result, indent=1, sort_keys=True) + "\n")
    r = result
    print("ROWS first ok=%d sites=%d second ok=%d sites=%d sites_in_both=%d" % (
        r["first"]["ok"], r["first"]["sites"], r["second"]["ok"], r["second"]["sites"],
        r["sites_in_both"]))
    s, sb, sa = r["seen"], r["seen_on_sites_in_both"], r["seen_any_result"]
    print("SEEN all=%d/%d (%.4f) sites_in_both=%d/%d (%.4f) any_result=%d/%d" % (
        s["files"], s["of"], s["share"], sb["files"], sb["of"], sb["share"], sa["files"], sa["of"]))
    a = r["agree"]
    print("AGREE pairs=%d checks=%d bytes=%d created=%d" % (
        a["pairs"], a["checks_same"], a["bytes_same"], a["created_same"]))
    print("DISAGREE " + " ".join("%s=%d" % (c, a["disagreements"][c]) for c in CHECKS))
    b = r["basic4"]
    print("BASIC4 fail=%d/%d pass=%d/%d diff=%.4f" % (
        b["fail"]["seen"], b["fail"]["files"], b["pass"]["seen"], b["pass"]["files"], b["diff"]))
    q = r["paired_basic4"]
    print("PAIRED sites=%d up=%d down=%d same=%d sign_p=%.4f mean=%.4f (%.4f..%.4f)" % (
        q["sites"], q["up"], q["down"], q["same"], q["sign_p"], q["mean"], q["low"], q["high"]))
    h, o = r["base_href_split"]["base_href"], r["base_href_split"]["other"]
    print("SPLIT base_href sites=%d seen=%d/%d other sites=%d seen=%d/%d" % (
        h["sites"], h["seen"], h["files"], o["sites"], o["seen"], o["files"]))
    print("predictions held: %d of 6" % sum(r["predictions"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
