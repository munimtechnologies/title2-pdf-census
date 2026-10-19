"""Counts repeated PDF links in a census rows file (JSON lines with url_sha256, qid, result).

For the rows with result "ok": how many rows, how many distinct url_sha256, how many rows repeat
an earlier row's link, and for each repeated link whether its rows come from one site (qid) or
several. Then, for each boolean field named on the command line, the share of ok rows where it is
true, with every row and with each link counted once (its first row). Prints JSON with counts
only: no URL, hash or site id. Standard library only. Apache-2.0 licensed.

    python -I repeat_links.py ROWS.jsonl [FIELD ...]
"""

import collections
import json
import sys


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    path, fields = argv[1], argv[2:]
    ok = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                if d.get("result") == "ok":
                    ok.append(d)
    sites = collections.defaultdict(list)
    first = {}
    for d in ok:
        sites[d["url_sha256"]].append(d.get("qid"))
        first.setdefault(d["url_sha256"], d)
    repeated = {h: q for h, q in sites.items() if len(q) > 1}
    out = {
        "file": path.replace("\\", "/").split("/")[-1],
        "ok_rows": len(ok),
        "distinct_links": len(first),
        "repeat_rows": len(ok) - len(first),
        "repeated_links": len(repeated),
        "rows_per_repeated_link": dict(collections.Counter(str(len(q)) for q in repeated.values())),
        "repeated_links_all_different_sites": sum(1 for q in repeated.values() if len(set(q)) == len(q)),
        "repeated_links_same_site_twice": sum(1 for q in repeated.values() if len(set(q)) < len(q)),
        "shares": {},
    }
    once = list(first.values())
    for name in fields:
        k_all = sum(1 for d in ok if d.get(name) is True)
        k_once = sum(1 for d in once if d.get(name) is True)
        out["shares"][name] = {
            "all": [k_all, len(ok), round(k_all / len(ok), 4) if ok else None],
            "once": [k_once, len(once), round(k_once / len(once), 4) if once else None]}
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
