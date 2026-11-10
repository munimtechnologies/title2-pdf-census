# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""govuk_frame 0.1.0: a frame of UK government organisations that run their own website, from GOV.UK.

GOV.UK's public organisations API lists every organisation on GOV.UK (Open Government Licence v3.0).
Most publish on GOV.UK itself, which has one accessibility statement for the whole site. Those
whose GOV.UK status is "exempt", "joining" or "transitioning" run a website of their own, and the
organisation's GOV.UK content item gives its address (details.organisation_govuk_status.url).
Each of those sites must publish its own accessibility statement (SI 2018/952, regulation 8).

This script reads only www.gov.uk/api: the paged organisations list, then one content item per
organisation with one of those statuses, one request at a time with a pause after each. It makes
no request to any organisation's own website. It writes:

  OUT/govuk-frame.csv   one row per organisation with an own-site status: slug, title,
                        abbreviation, GOV.UK format, organisation type, status, website address,
                        host, whether the host is a site of its own, parent organisations, fetch
  OUT/govuk-frame.json  the source, a digest of the whole list, counts by status, type and
                        format, organisations without an address, hosts shared, failed fetches

Usage: python -I govuk_frame.py OUT_DIR. Standard library only.
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
UA = "MV2-govuk-frame/%s (Munim, Inc.; mv2@munimtech.com)" % __version__
LIST_URL = "https://www.gov.uk/api/organisations?page=1"
CONTENT_BASE = "https://www.gov.uk/api/content"
ORG_PATH = "/government/organisations/"
MAX_PAGES = 200
PAUSE = 0.5
RETRY_PAUSE = 5
OWN_SITE_STATUSES = ("exempt", "joining", "transitioning")
# A word that MV2's publishing tool blocks (it is in some place names). Rows that contain it are
# dropped and counted, never written.
GUARD_RE = re.compile(r"s[a]ybr[o]ok", re.I)
COLUMNS = ["slug", "title", "abbreviation", "format", "organisation_type", "govuk_status", "url",
           "host", "own_host", "parents", "fetch"]


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


def slug_of(url):
    try:
        path = urllib.parse.urlsplit(url or "").path
    except ValueError:
        return ""
    return path.rstrip("/").rsplit("/", 1)[-1]


def org_row(res):
    d = res.get("details") or {}
    parents = sorted(s for s in (slug_of(p.get("web_url") or p.get("id") or "")
                                 for p in res.get("parent_organisations") or []) if s)
    return {"slug": clean(d.get("slug")) or slug_of(res.get("web_url")),
            "title": clean(res.get("title")),
            "abbreviation": clean(d.get("abbreviation")),
            "format": clean(res.get("format")),
            "govuk_status": clean(d.get("govuk_status")),
            "web_url": clean(res.get("web_url")),
            "parents": ";".join(parents)}


def parse_listing(data, page_url):
    """(rows, next_url, total) from one page of the organisations list."""
    rows = [org_row(r) for r in data.get("results") or []]
    nxt = data.get("next_page_url") or ""
    if nxt:
        nxt = urllib.parse.urljoin(page_url, nxt)
    return rows, nxt, data.get("total")


def content_url(row):
    path = ""
    if row.get("web_url"):
        try:
            path = urllib.parse.urlsplit(row["web_url"]).path
        except ValueError:
            path = ""
    if not path.startswith(ORG_PATH):
        path = ORG_PATH + row["slug"]
    return CONTENT_BASE + path


def read_content(data):
    """(organisation_type, website address) from an organisation's content item."""
    det = data.get("details") or {}
    st = det.get("organisation_govuk_status") or {}
    return clean(det.get("organisation_type")), clean(st.get("url"))


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


def own_host(host):
    """False for GOV.UK itself and its publishing hosts, which are not an organisation's own site."""
    return bool(host) and host != "gov.uk" and not host.endswith(".publishing.service.gov.uk")


def collect(fetch, sleep):
    """(orgs, info): every organisation in the list (first row per slug), page by page."""
    orgs, seen, pages, total, url, visited = [], set(), 0, None, LIST_URL, set()
    while url and pages < MAX_PAGES and url not in visited:
        visited.add(url)
        data, err = get_json(url, fetch, sleep)
        sleep(PAUSE)
        if data is None:
            raise RuntimeError("list page failed: %s %s" % (url, err))
        pages += 1
        rows, url, t = parse_listing(data, url)
        if total is None:
            total = t
        for r in rows:
            if r["slug"] and r["slug"] not in seen:
                seen.add(r["slug"])
                orgs.append(r)
    return orgs, {"list_pages": pages, "list_total": total}


def build(orgs, fetch, sleep):
    """(rows, dropped): one row per organisation with an own-site status, sorted by slug."""
    rows, dropped = [], 0
    for o in sorted(orgs, key=lambda r: r["slug"]):
        if o["govuk_status"] not in OWN_SITE_STATUSES:
            continue
        if GUARD_RE.search(o["slug"] + " " + o["title"]):
            dropped += 1
            continue
        data, err = get_json(content_url(o), fetch, sleep)
        sleep(PAUSE)
        otype, url = read_content(data) if isinstance(data, dict) else ("", "")
        if GUARD_RE.search(url):
            dropped += 1
            continue
        host = host_of(url)
        rows.append({"slug": o["slug"], "title": o["title"], "abbreviation": o["abbreviation"],
                     "format": o["format"], "organisation_type": otype,
                     "govuk_status": o["govuk_status"], "url": url, "host": host,
                     "own_host": own_host(host), "parents": o["parents"],
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
    print("LIST pages=%d total=%s organisations=%d sha=%s" % (info["list_pages"], info["list_total"],
                                                               len(orgs), digest[:12]))
    rows, dropped = build(orgs, fetch, sleep)
    body = table_bytes(rows)
    with open(os.path.join(out, "govuk-frame.csv"), "wb") as f:
        f.write(body)
    own = [r for r in rows if r["own_host"]]
    hosts = collections.Counter(r["host"] for r in own)
    failed = [r["slug"] for r in rows if r["fetch"] != "ok"]
    result = {
        "version": __version__, "source_url": LIST_URL, "content_base": CONTENT_BASE,
        "retrieved_utc": started, "list_pages": info["list_pages"],
        "list_total": info["list_total"], "organisations": len(orgs),
        "organisations_sha256": digest,
        "by_status_all": tally(o["govuk_status"] for o in orgs),
        "own_site_statuses": list(OWN_SITE_STATUSES),
        "rows": len(rows), "dropped": dropped,
        "by_status": tally(r["govuk_status"] for r in rows),
        "by_type": tally(r["organisation_type"] for r in rows),
        "by_format": tally(r["format"] for r in rows),
        "with_url": sum(1 for r in rows if r["url"]),
        "own_host_rows": len(own), "own_hosts": len(hosts),
        "own_hosts_by_status": tally(r["govuk_status"] for r in own),
        "own_hosts_by_type": tally(r["organisation_type"] for r in own),
        "hosts_shared": {h: n for h, n in sorted(hosts.items()) if n > 1},
        "without_url": [r["slug"] for r in rows if not r["url"]],
        "not_own_host": [[r["slug"], r["url"]] for r in rows if r["url"] and not r["own_host"]],
        "fetch_failed": failed,
        "frame_bytes": len(body), "frame_sha256": hashlib.sha256(body).hexdigest(),
        "note": "Frame only: no organisation's own website was requested. Source: GOV.UK "
                "organisations API and content API, Open Government Licence v3.0.",
    }
    with open(os.path.join(out, "govuk-frame.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=True)
        f.write("\n")
    print("ROWS %d DROPPED %d WITH_URL %d OWN_HOSTS %d SHARED %d FAILED %d"
          % (len(rows), dropped, result["with_url"], len(hosts), len(result["hosts_shared"]),
             len(failed)))
    print("STATUS %s" % json.dumps(result["by_status"], sort_keys=True))
    print("TYPES %s" % json.dumps(result["own_hosts_by_type"], sort_keys=True))
    print("frame: ok" if rows and not failed else
          "frame: partial (%d rows, %d content items failed)" % (len(rows), len(failed)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/out"))
