# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""uk_frame 0.1.0: build the frame of England's school websites from GIAS, reading no website.

Downloads one day's public "all establishment data" file of Get Information about Schools (GIAS,
Department for Education, Open Government Licence v3.0), keeps establishment-level fields only
(no person's name, email or phone), and writes:

  OUT/frame-partN.csv  one row per open establishment that lists a website, sorted by URN, in parts
                       under 1,900,000 bytes each
  OUT/frame.json       the source file's URL, date, bytes and SHA-256; counts by establishment
                       type group, phase, country and status; distinct website hosts; hosts shared
                       by several establishments; the most common host suffixes; part sizes

It makes no request to any school's website. Usage: python -I uk_frame.py OUT_DIR
Standard library only. Made by MV2 of Munim, Inc. with AI agents.
"""

import collections
import csv
import datetime
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

__version__ = "0.1.0"
UA = "MV2-uk-frame/%s (Munim, Inc.; mv2@munimtech.com)" % __version__
BASES = ("https://ea-edubase-api-prod.azurewebsites.net/edubase/downloads/public/edubasealldata%s.csv",
         "https://ea-edubase-api-prod.azurewebsites.net/edubase/edubasealldata%s.csv")
PART_LIMIT = 1_900_000
# GIAS column -> frame column. Establishment-level fields only.
KEEP = (("URN", "urn"), ("EstablishmentName", "name"),
        ("EstablishmentTypeGroup (name)", "type_group"), ("TypeOfEstablishment (name)", "type"),
        ("PhaseOfEducation (name)", "phase"), ("LA (code)", "la_code"), ("LA (name)", "la_name"),
        ("GOR (name)", "region"), ("Country (name)", "country"), ("NumberOfPupils", "pupils"),
        ("Trusts (name)", "trust"), ("SchoolWebsite", "website"))
STATUS = "EstablishmentStatus (name)"
COLUMNS = [c for _, c in KEEP] + ["host"]


def fetch(url, timeout=300):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download(today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    errors = []
    for back in range(0, 4):
        day = (today - datetime.timedelta(days=back)).strftime("%Y%m%d")
        for base in BASES:
            url = base % day
            for attempt in range(2):
                try:
                    data = fetch(url)
                    if len(data) > 1_000_000:
                        return url, day, data
                    errors.append("%s short %d" % (url, len(data)))
                    break
                except Exception as e:  # 404 for a day not yet published, or a network error
                    errors.append("%s %s" % (url, e.__class__.__name__))
                    if "404" in str(e):
                        break
                    time.sleep(5)
    raise RuntimeError("no GIAS file: " + "; ".join(errors[-6:]))


def decode(data):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError("undecodable")


def host_of(website):
    w = (website or "").strip()
    if not w:
        return ""
    if not re.match(r"https?://", w, re.I):
        w = "http://" + w
    try:
        host = (urllib.parse.urlsplit(w).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    if "." not in host or " " in host:
        return ""
    return host


def suffix(host, n):
    labels = host.split(".")
    return ".".join(labels[-n:]) if len(labels) >= n else host


def build(text):
    reader = csv.DictReader(io.StringIO(text))
    missing = [k for k, _ in KEEP if k not in reader.fieldnames] + (
        [STATUS] if STATUS not in reader.fieldnames else [])
    required = [k for k in ("URN", "EstablishmentName", "SchoolWebsite", STATUS) if k in missing]
    if required:
        raise ValueError("GIAS columns missing: %s; have: %s" % (missing, reader.fieldnames[:80]))
    build.missing = missing
    status = collections.Counter()
    rows = []
    total = 0
    for rec in reader:
        total += 1
        st = (rec.get(STATUS) or "").strip()
        status[st] += 1
        if not st.startswith("Open"):
            continue
        row = {c: " ".join((rec.get(k) or "").split()) for k, c in KEEP}
        row["host"] = host_of(row["website"])
        rows.append(row)
    rows.sort(key=lambda r: int(r["urn"]) if r["urn"].isdigit() else 10 ** 9)
    return total, status, rows


def tally(rows, key, top=None):
    c = collections.Counter(r[key] for r in rows)
    return dict(c.most_common(top))


def write_parts(rows, out):
    parts, buf, n = [], io.StringIO(), 0
    header = ",".join(COLUMNS) + "\n"

    def flush():
        data = buf.getvalue().encode("utf-8")
        name = "frame-part%d.csv" % (len(parts) + 1)
        with open(os.path.join(out, name), "wb") as f:
            f.write(data)
        parts.append({"file": name, "rows": n, "bytes": len(data),
                      "sha256": hashlib.sha256(data).hexdigest()})

    buf.write(header)
    size = len(header.encode("utf-8"))
    for r in rows:
        line = io.StringIO()
        csv.writer(line, lineterminator="\n").writerow([r[c] for c in COLUMNS])
        enc = line.getvalue()
        b = len(enc.encode("utf-8"))
        if size + b > PART_LIMIT and n:
            flush()
            buf, n = io.StringIO(), 0
            buf.write(header)
            size = len(header.encode("utf-8"))
        buf.write(enc)
        size += b
        n += 1
    flush()
    return parts


def main(out):
    os.makedirs(out, exist_ok=True)
    url, day, data = download()
    text, enc = decode(data)
    print("SRC %s bytes=%d sha=%s enc=%s" % (url, len(data), hashlib.sha256(data).hexdigest()[:12], enc))
    total, status, open_rows = build(text)
    with_site = [r for r in open_rows if r["host"]]
    eng = [r for r in with_site if r["country"] in ("", "England", "United Kingdom")]
    hosts = collections.Counter(r["host"] for r in with_site)
    shared = {h: n for h, n in hosts.items() if n > 1}
    parts = write_parts(with_site, out)
    result = {
        "version": __version__, "source_url": url, "source_date": day, "source_bytes": len(data),
        "source_sha256": hashlib.sha256(data).hexdigest(), "encoding": enc,
        "establishments": total, "by_status": dict(status.most_common()),
        "open": len(open_rows), "open_with_website": len(with_site),
        "open_website_unparseable": sum(1 for r in open_rows if r["website"] and not r["host"]),
        "open_no_website": sum(1 for r in open_rows if not r["website"]),
        "open_with_website_england_or_blank_country": len(eng),
        "distinct_hosts": len(hosts), "hosts_shared": len(shared),
        "establishments_on_shared_hosts": sum(shared.values()),
        "top_shared_hosts": dict(collections.Counter(shared).most_common(25)),
        "by_type_group_open": tally(open_rows, "type_group"),
        "by_type_group_with_website": tally(with_site, "type_group"),
        "by_phase_with_website": tally(with_site, "phase"),
        "by_country_with_website": tally(with_site, "country"),
        "by_region_with_website": tally(with_site, "region"),
        "top_suffix2": dict(collections.Counter(suffix(h, 2) for h in hosts).most_common(30)),
        "top_suffix3": dict(collections.Counter(suffix(h, 3) for h in hosts).most_common(40)),
        "parts": parts,
        "columns": COLUMNS,
        "missing_gias_columns": getattr(build, "missing", []),
        "gias_columns": next(csv.reader(io.StringIO(text.split("\n", 1)[0]))),
        "note": "Frame only: no school website was requested. GIAS data: Department for Education, "
                "Open Government Licence v3.0.",
    }
    with open(os.path.join(out, "frame.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print("OPEN %d WITH_SITE %d HOSTS %d SHARED %d" % (len(open_rows), len(with_site), len(hosts),
                                                       len(shared)))
    for p in parts:
        print("PART %s rows=%d bytes=%d" % (p["file"], p["rows"], p["bytes"]))
    print("frame: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/out"))
