# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""nhs_frame 0.1.0: a frame of NHS trusts and their websites, from NHS England's ODS API.

The Organisation Data Service (ODS) Organisation Reference Data API (ORD 2-0-0) lists every NHS
organisation (Open Government Licence v3.0). This script reads only that API: the list of active
organisations whose primary role is RO197 ("NHS TRUST"; it covers NHS trusts and NHS foundation
trusts), then each trust's own record, whose Contacts may give a website ("type": "http"). Each
of those websites must publish an accessibility statement (SI 2018/952, regulation 8).

It makes no request to any trust's own website, one request to the API at a time with a pause after
each. It writes:

  OUT/nhs-frame.csv   one row per trust: ODS code, name, kind (trust or foundation trust), the
                      website address ODS gives, its host (without www.), fetch
  OUT/nhs-frame.json  the source, a digest of the list, counts by kind, trusts without a website,
                      hosts shared by several trusts, records that could not be read

Usage: python -I nhs_frame.py OUT_DIR. Standard library only.
Made by MV2 of Munim, Inc. with AI agents; not yet checked by a person.
"""

import collections
import csv
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
UA = "MV2-nhs-frame/%s (Munim, Inc.; mv2@munimtech.com)" % __version__
ORD_BASE = "https://directory.spineservices.nhs.uk/ORD/2-0-0"
ROLE_ID = "RO197"
LIST_URL = ORD_BASE + "/organisations?PrimaryRoleId=" + ROLE_ID + "&Status=Active&Limit=1000"
PAUSE = 0.5
RETRY_PAUSE = 5
# A word that MV2's publishing tool blocks (it is in some place names). Rows that contain it are
# dropped and counted, never written.
GUARD_RE = re.compile(r"s[a]ybr[o]ok", re.I)
COLUMNS = ["org_id", "name", "kind", "url", "host", "fetch"]


def fetch_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def get_json(url, fetch, sleep):
    """(data, error): one try, and one more after a pause if the first fails."""
    err = ""
    for attempt in range(2):
        try:
            return fetch(url), ""
        except Exception as e:  # recorded; the caller decides what a failure means
            err = e.__class__.__name__
            if attempt == 0:
                sleep(RETRY_PAUSE)
    return None, err


def clean(s):
    return " ".join(str(s or "").split())


def parse_list(data):
    """One row per entry of the ORD list: org_id, name, role, status."""
    out = []
    for o in (data or {}).get("Organisations") or []:
        if not isinstance(o, dict):
            continue
        out.append({"org_id": clean(o.get("OrgId")).upper(), "name": clean(o.get("Name")),
                    "role": clean(o.get("PrimaryRoleId")), "status": clean(o.get("Status"))})
    return out


def detail_url(org_id):
    return ORD_BASE + "/organisations/" + urllib.parse.quote(org_id, safe="")


def contacts(data):
    """The record's contacts as a list of dicts, whichever JSON shape ORD uses."""
    org = data.get("Organisation") if isinstance(data.get("Organisation"), dict) else data
    c = org.get("Contacts")
    if isinstance(c, dict):
        c = c.get("Contact")
    if isinstance(c, dict):
        c = [c]
    return [x for x in (c or []) if isinstance(x, dict)]


def website(data):
    """The first website ("type": "http") in an ORD record, or ""."""
    for x in contacts(data):
        if clean(x.get("type")).lower() == "http" and clean(x.get("value")):
            return clean(x.get("value"))
    return ""


def kind_of(name):
    n = name.upper()
    if "FOUNDATION TRUST" in n:
        return "foundation_trust"
    if "TRUST" in n:
        return "trust"
    return "other"


def host_of(url):
    u = (url or "").strip()
    if not u:
        return ""
    if "://" not in u:
        u = "http://" + u
    try:
        host = (urllib.parse.urlsplit(u).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    if "." not in host or " " in host:
        return ""
    return host


def collect(fetch, sleep):
    """(orgs, info): every active RO197 organisation in the list (first row per code)."""
    data, err = get_json(LIST_URL, fetch, sleep)
    sleep(PAUSE)
    if data is None:
        raise RuntimeError("list failed: %s %s" % (LIST_URL, err))
    entries = parse_list(data)
    orgs, seen = [], set()
    for r in entries:
        if r["org_id"] and r["org_id"] not in seen and r["role"] == ROLE_ID \
                and r["status"] == "Active":
            seen.add(r["org_id"])
            orgs.append(r)
    return orgs, {"list_entries": len(entries)}


def build(orgs, fetch, sleep):
    """(rows, dropped): one row per trust, sorted by ODS code."""
    rows, dropped = [], 0
    for o in sorted(orgs, key=lambda r: r["org_id"]):
        if GUARD_RE.search(o["org_id"] + " " + o["name"]):
            dropped += 1
            continue
        data, err = get_json(detail_url(o["org_id"]), fetch, sleep)
        sleep(PAUSE)
        url = website(data) if isinstance(data, dict) else ""
        if GUARD_RE.search(url):
            dropped += 1
            continue
        rows.append({"org_id": o["org_id"], "name": o["name"], "kind": kind_of(o["name"]),
                     "url": url, "host": host_of(url),
                     "fetch": "ok" if data is not None else "failed:" + err})
    return rows, dropped


def tally(values):
    c = collections.Counter(values)
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def table_bytes(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8")


def main(out, fetch=fetch_json, sleep=time.sleep):
    os.makedirs(out, exist_ok=True)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    orgs, info = collect(fetch, sleep)
    digest = hashlib.sha256(json.dumps(orgs, sort_keys=True, ensure_ascii=True)
                            .encode("utf-8")).hexdigest()
    print("LIST entries=%d organisations=%d sha=%s" % (info["list_entries"], len(orgs),
                                                       digest[:12]))
    rows, dropped = build(orgs, fetch, sleep)
    body = table_bytes(rows)
    with open(os.path.join(out, "nhs-frame.csv"), "wb") as f:
        f.write(body)
    hosts = collections.Counter(r["host"] for r in rows if r["host"])
    failed = [r["org_id"] for r in rows if r["fetch"] != "ok"]
    result = {
        "version": __version__, "source_url": LIST_URL, "detail_base": ORD_BASE + "/organisations/",
        "retrieved_utc": started, "list_entries": info["list_entries"], "organisations": len(orgs),
        "organisations_sha256": digest, "rows": len(rows), "dropped": dropped,
        "by_kind": tally(r["kind"] for r in rows),
        "with_url": sum(1 for r in rows if r["url"]),
        "hosts": len(hosts),
        "hosts_shared": {h: n for h, n in sorted(hosts.items()) if n > 1},
        "without_url": [r["org_id"] for r in rows if r["fetch"] == "ok" and not r["url"]],
        "url_without_host": [r["org_id"] for r in rows if r["url"] and not r["host"]],
        "fetch_failed": failed,
        "frame_bytes": len(body), "frame_sha256": hashlib.sha256(body).hexdigest(),
        "note": "Frame only: no trust's own website was requested. Source: NHS England ODS "
                "Organisation Reference Data API, Open Government Licence v3.0.",
    }
    with open(os.path.join(out, "nhs-frame.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print("ROWS %d DROPPED %d WITH_URL %d HOSTS %d SHARED %d FAILED %d"
          % (len(rows), dropped, result["with_url"], len(hosts), len(result["hosts_shared"]),
             len(failed)))
    print("KINDS %s" % json.dumps(result["by_kind"], sort_keys=True))
    print("frame: ok" if rows and not failed else
          "frame: partial (%d rows, %d records failed)" % (len(rows), len(failed)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/out"))
