"""Split a JSON-lines file into numbered parts that each stay under a byte limit.

Made for title2-pdf-census results/lang-v1: lang-public.jsonl (4339 rows) is over the
2,000,000-byte file limit of the tool that publishes the repository. Rows are not changed,
reordered or re-encoded: parts are cut only at line ends, every row must parse as JSON, and the
parts joined in order must equal the original byte for byte, all checked before anything is
written and again after. Existing files are never overwritten. Apache-2.0 licensed.

    python -I split_rows.py SRC OUT_DIR [--max-bytes 1900000]
"""

import argparse
import hashlib
import io
import json
import os
import sys


def split(data, max_bytes):
    """Cut data at line ends into parts of at most max_bytes each."""
    parts, cur, size = [], [], 0
    for line in io.BytesIO(data).readlines():
        if len(line) > max_bytes:
            raise ValueError("a single line is longer than %d bytes" % max_bytes)
        if cur and size + len(line) > max_bytes:
            parts.append(b"".join(cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line)
    if cur:
        parts.append(b"".join(cur))
    return parts


def rows(part):
    n = 0
    for line in part.splitlines():
        if line.strip():
            json.loads(line.decode("utf-8"))
            n += 1
    return n


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("--max-bytes", type=int, default=1_900_000)
    a = ap.parse_args(argv)

    with open(a.src, "rb") as f:
        data = f.read()
    parts = split(data, a.max_bytes)
    if b"".join(parts) != data:
        sys.exit("refused: the parts do not join back to the original")
    counts = [rows(p) for p in parts]
    if sum(counts) != rows(data):
        sys.exit("refused: the parts do not hold the same number of rows as the original")

    stem = os.path.splitext(os.path.basename(a.src))[0]
    names = ["%s-%d.jsonl" % (stem, i + 1) for i in range(len(parts))]
    os.makedirs(a.out_dir, exist_ok=True)
    for name in names:
        if os.path.exists(os.path.join(a.out_dir, name)):
            sys.exit("refused: %s already exists in %s" % (name, a.out_dir))
    for name, part in zip(names, parts):
        with open(os.path.join(a.out_dir, name), "xb") as f:
            f.write(part)

    back = b""
    for name in names:
        with open(os.path.join(a.out_dir, name), "rb") as f:
            back += f.read()
    report = {
        "src": os.path.basename(a.src), "src_bytes": len(data), "src_sha256": sha(data),
        "src_rows": rows(data), "max_bytes": a.max_bytes,
        "parts": [{"name": n, "bytes": len(p), "rows": c, "sha256": sha(p)}
                  for n, p, c in zip(names, parts, counts)],
        "joined_equals_src": back == data,
    }
    print(json.dumps(report, indent=1))
    return 0 if back == data else 1


if __name__ == "__main__":
    sys.exit(main())
