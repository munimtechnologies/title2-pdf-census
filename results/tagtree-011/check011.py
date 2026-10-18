"""tagtree 0.1.1 on the two PDFs that tagtree 0.1.0 misread (tagtree-xcheck-v1, tagtree-diag-v2).

Fetches each file again (public pages only, robots.txt honoured) and runs tagtree's own child
process twice: as released in 0.1.1 (object-stream members found by header number) and with
--xref-index (as 0.1.0 read). Writes the full public record of each (the fields of
tagtree.PUBLIC_FIELDS that analyze returns, so page order and upward jumps too) to
/out/check011.json. Stores no document text and no URL: only counts and hashes.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import hashlib
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
import urllib.robotparser

import tagtree

__version__ = "0.1.0"

UA = tagtree.UA
MAX_BYTES = 60_000_000


def allowed(url):
    parts = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url("%s://%s/robots.txt" % (parts.scheme, parts.netloc))
    try:
        req = urllib.request.Request(rp.url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            rp.parse(r.read(500_000).decode("utf-8", "replace").splitlines())
    except Exception:
        return True  # no readable robots.txt: crawling is not disallowed
    return rp.can_fetch(UA, url)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(MAX_BYTES + 1)


def public(rec):
    return {k: rec.get(k) for k in tagtree.PUBLIC_FIELDS if k in rec}


def check(data):
    row = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(data)
    try:
        row["tagtree_0_1_1"] = public(tagtree.analyze_file(f.name))
        row["xref_index"] = public(tagtree.analyze_file(f.name, xref_index=True))
    finally:
        os.unlink(f.name)
    return row


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    urls_path, out_dir = argv[0], argv[1]
    import pdfminer
    result = {"version": __version__, "tagtree": tagtree.__version__, "pdfminer": pdfminer.__version__,
              "files": []}
    with open(urls_path, encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip()]
    for url in urls:
        row = {"url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest()}
        try:
            if not allowed(url):
                row["fetch"] = "robots_disallow"
            else:
                data = fetch(url)
                if len(data) > MAX_BYTES or b"%PDF" not in data[:1024]:
                    row["fetch"] = "not_a_pdf_or_too_big"
                else:
                    row["fetch"] = "ok"
                    row.update(check(data))
        except Exception as e:
            row["fetch"] = "error %s: %s" % (type(e).__name__, str(e)[:160])
        result["files"].append(row)
        print(json.dumps(row), flush=True)
    with open(os.path.join(out_dir, "check011.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
