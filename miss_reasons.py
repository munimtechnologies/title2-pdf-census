# Copyright 2026 MV2, Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
# Made by MV2 of Munim, Inc. with AI agents.
"""Why did the re-crawl miss a file? A follow-up to the panel retest's placebo gap.

Usage: python miss_reasons.py first.jsonl second.jsonl [out.json]

The panel retest found that, within sites, PDFs failing the four basics were read again slightly less
often than passing ones (70 sites down, 29 up), six hours apart. This splits each readable first-crawl
file on a site read in both crawls into: read again ("seen"), tried again but not readable ("notok"),
or no row at all in the second crawl ("norow"); then asks which part carries the gap, whether file
size explains it, and whether it is confined to sites with the `<base href>` sign.
Standard library only. Matching and statistics are copied unchanged from panel_retest.py, so this
file runs on its own (`python -I` does not put the script's folder on the import path). See
docs/miss-reasons-prereg.md.
"""
import collections
import json
import math
import statistics
import sys

Z = 1.959964
NAN = float("nan")
OUTCOMES = ("seen", "notok", "norow")


# --- copied from panel_retest.py ---
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


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
# --- end of copy ---


def classify(first, second):
    """{(qid, url_sha256): (first row, outcome, second row or None)} for readable first-crawl files
    on sites readable in both crawls."""
    a_ok, b_ok = ok_rows(first), ok_rows(second)
    b_any = {}
    for r in second:
        b_any.setdefault(key(r), r)
    both = ok_sites(first) & ok_sites(second)
    files = {}
    for k, r in a_ok.items():
        if k[0] not in both:
            continue
        if k in b_ok:
            files[k] = (r, "seen", b_ok[k])
        elif k in b_any:
            files[k] = (r, "notok", b_any[k])
        else:
            files[k] = (r, "norow", None)
    return files, both


def paired_sites(files):
    """{qid: {True: [outcomes of passing files], False: [... failing]}} for sites with both kinds."""
    sites = {}
    for k, (r, o, _) in files.items():
        sites.setdefault(k[0], {True: [], False: []})[bool(r.get("basic4"))].append(o)
    return {q: c for q, c in sites.items() if c[True] and c[False]}


def gap(cell, outcome):
    """On one site: share of failing files with this outcome minus the same share of passing files."""
    return (cell[False].count(outcome) / len(cell[False])
            - cell[True].count(outcome) / len(cell[True]))


def summarise(diffs):
    up = sum(d > 0 for d in diffs)
    down = sum(d < 0 for d in diffs)
    out = {"sites": len(diffs), "up": up, "down": down, "same": len(diffs) - up - down,
           "sign_p": sign_test(up, down)}
    out["mean"], out["low"], out["high"] = mean_ci(diffs)
    return out


def reason(row):
    """Second-crawl reason for a file tried again but not readable."""
    if row.get("result") != "http_error":
        return row.get("result") or "unknown"
    status = row.get("status") or 0
    return "no_response" if status == 0 else "http_%dxx" % (status // 100)


def seen_counts(rows):
    """{True: [seen, files] for passing, False: [...] for failing}."""
    out = {True: [0, 0], False: [0, 0]}
    for r, o, _ in rows:
        cell = out[bool(r.get("basic4"))]
        cell[0] += o == "seen"
        cell[1] += 1
    return out


def seen_gap(counts):
    return share(*counts[False]) - share(*counts[True])


def size_bands(rows):
    """Tertiles of first-crawl bytes; read-again counts per band, and the failing-minus-passing gap
    pooled (unadjusted) and averaged over bands weighted by their file counts (adjusted)."""
    sizes = sorted(r.get("bytes") or 0 for r, _, _ in rows)
    if not sizes:
        return {"cuts": [NAN, NAN], "bands": [], "unadjusted": NAN, "adjusted": NAN}
    cuts = [sizes[len(sizes) // 3], sizes[2 * len(sizes) // 3]]
    groups = [[], [], []]
    for item in rows:
        b = item[0].get("bytes") or 0
        groups[0 if b < cuts[0] else 1 if b < cuts[1] else 2].append(item)
    bands = [seen_counts(g) for g in groups]
    num = den = 0
    for c in bands:
        if c[True][1] and c[False][1]:
            n = c[True][1] + c[False][1]
            num += n * seen_gap(c)
            den += n
    return {"cuts": cuts,
            "bands": [{"fail": c[False], "pass": c[True]} for c in bands],
            "unadjusted": seen_gap(seen_counts(rows)),
            "adjusted": num / den if den else NAN}


def median(values):
    return statistics.median(values) if values else NAN


def analyse(first, second):
    files, both = classify(first, second)
    sites = paired_sites(files)
    rows = [v for k, v in files.items() if k[0] in sites]
    outcome = {label: collections.Counter(o for r, o, _ in rows if bool(r.get("basic4")) == want)
               for label, want in (("fail", False), ("pass", True))}
    gaps = {o: summarise([gap(c, o) for _, c in sorted(sites.items())]) for o in OUTCOMES}
    notok = {label: collections.Counter(reason(b) for r, o, b in rows
                                        if o == "notok" and bool(r.get("basic4")) == want)
             for label, want in (("fail", False), ("pass", True))}
    size = size_bands(rows)
    size["median_fail"] = median([r.get("bytes") or 0 for r, _, _ in rows if not r.get("basic4")])
    size["median_pass"] = median([r.get("bytes") or 0 for r, _, _ in rows if r.get("basic4")])
    proxy = base_href_sites(first)
    split = {label: summarise([gap(c, "seen") for q, c in sorted(sites.items())
                               if (q in proxy) == inside])
             for label, inside in (("base_href", True), ("other", False))}
    place = {}
    for label, want in (("onsite", True), ("offsite", False)):
        c = seen_counts([v for v in rows if bool(v[0].get("same_site")) == want])
        place[label] = {"fail": c[False], "pass": c[True]}
    g = gaps
    total = g["notok"]["mean"] + g["norow"]["mean"]
    # NaN compares False, so a measure with nothing to count never counts as held
    predictions = {
        "M1": total > 0 and g["notok"]["mean"] >= 0.5 * total,
        "M2": size["median_fail"] > size["median_pass"],
        "M3": abs(size["adjusted"]) <= (2 / 3) * abs(size["unadjusted"]),
        "M4": split["other"]["mean"] < 0,
    }
    return {
        "files": {"sites_in_both": len(both), "paired_sites": len(sites), "files": len(rows),
                  "fail": sum(outcome["fail"].values()), "pass": sum(outcome["pass"].values())},
        "outcomes": {label: {o: outcome[label][o] for o in OUTCOMES} for label in outcome},
        "gaps": gaps,
        "notok_reasons": {label: dict(sorted(c.items())) for label, c in notok.items()},
        "size": size,
        "base_href_split": split,
        "same_site_split": place,
        "predictions": predictions,
    }


def reasons_text(counter):
    return ",".join("%s=%d" % kv for kv in sorted(counter.items())) or "none"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    r = analyse(load(argv[1]), load(argv[2]))
    if len(argv) > 3:
        with open(argv[3], "w", encoding="utf-8") as out:
            out.write(json.dumps(r, indent=1, sort_keys=True) + "\n")
    f = r["files"]
    print("FILES sites_in_both=%d paired_sites=%d files=%d fail=%d pass=%d" % (
        f["sites_in_both"], f["paired_sites"], f["files"], f["fail"], f["pass"]))
    o = r["outcomes"]
    print("OUTCOME fail seen=%d notok=%d norow=%d pass seen=%d notok=%d norow=%d" % (
        o["fail"]["seen"], o["fail"]["notok"], o["fail"]["norow"],
        o["pass"]["seen"], o["pass"]["notok"], o["pass"]["norow"]))
    g = r["gaps"]
    print("GAPS seen=%.4f notok=%.4f norow=%.4f sites=%d" % (
        g["seen"]["mean"], g["notok"]["mean"], g["norow"]["mean"], g["seen"]["sites"]))
    for out in ("notok", "norow"):
        q = g[out]
        print("GAP %s up=%d down=%d same=%d sign_p=%.4f mean=%.4f (%.4f..%.4f)" % (
            out, q["up"], q["down"], q["same"], q["sign_p"], q["mean"], q["low"], q["high"]))
    n = r["notok_reasons"]
    print("NOTOK fail %s pass %s" % (reasons_text(n["fail"]), reasons_text(n["pass"])))
    s = r["size"]
    print("SIZE median fail=%.0f pass=%.0f cuts=%.0f,%.0f unadjusted=%.4f adjusted=%.4f" % (
        s["median_fail"], s["median_pass"], s["cuts"][0], s["cuts"][1], s["unadjusted"],
        s["adjusted"]))
    print("BANDS " + " ".join("b%d fail=%d/%d pass=%d/%d" % (
        i, b["fail"][0], b["fail"][1], b["pass"][0], b["pass"][1])
        for i, b in enumerate(s["bands"])))
    h, t = r["base_href_split"]["base_href"], r["base_href_split"]["other"]
    print("SPLIT base_href sites=%d up=%d down=%d mean=%.4f other sites=%d up=%d down=%d "
          "sign_p=%.4f mean=%.4f (%.4f..%.4f)" % (
              h["sites"], h["up"], h["down"], h["mean"], t["sites"], t["up"], t["down"],
              t["sign_p"], t["mean"], t["low"], t["high"]))
    p = r["same_site_split"]
    print("PLACE onsite fail=%d/%d pass=%d/%d offsite fail=%d/%d pass=%d/%d" % (
        p["onsite"]["fail"][0], p["onsite"]["fail"][1], p["onsite"]["pass"][0],
        p["onsite"]["pass"][1], p["offsite"]["fail"][0], p["offsite"]["fail"][1],
        p["offsite"]["pass"][0], p["offsite"]["pass"][1]))
    print("predictions held: %d of 4" % sum(r["predictions"].values()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
