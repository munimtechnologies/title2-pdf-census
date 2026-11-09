# Copyright 2026 Munim, Inc. Licensed under the Apache License, Version 2.0 (Apache-2.0).
"""school_stock 0.1.0: how many school websites in England serve an unfinished accessibility statement template at /accessibility-statement/?

Pre-registered in results/uk-schools/PREREG.md. The frame is the one built by uk_frame.py 0.1.0
from the Department for Education's GIAS file of 2026-11-09 (Open Government Licence v3.0): every
open establishment that lists a website, 24,659 establishments on 23,802 distinct hosts, committed
as results/uk-schools/frame-part1..3.csv before any school website was read. Each host is asked
once for /accessibility-statement/ (robots.txt first, one request at a time per host, a pause after
each request) and the page is read with the rules of MV2's free checker a11y-statement-check
(statement_template_check.py 0.3.0, byte-identical to its release v0.3.0), plus the fields of one
vendor's school template that 0.3.0 does not know, which are described and never graded.

Schools are exempt from the UK accessibility regulations (SI 2018/952, regulation 4(1)(c)) except
for content needed for essential online administrative functions, so a school statement is mostly
voluntary: this counts what schools that publish one left in it. A placeholder says nothing about
whether a website is accessible; it says the statement was never finished. No page text is stored,
only a hash, rule ids and counts. Made by MV2 of Munim, Inc. with AI agents; not yet checked by a
person. Standard library only.
"""

import argparse
import collections
import concurrent.futures
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
import urllib.robotparser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statement_template_check as stc  # noqa: E402  (a11y-statement-check 0.3.0, unchanged)

__version__ = "0.1.0"

PREREG_PATH = "results/uk-schools/PREREG.md"
FRAME_DIR = "results/uk-schools"
CHECKER_VERSION = "0.3.0"
CHECKER_RELEASE_URL = ("https://raw.githubusercontent.com/munimtechnologies/a11y-statement-check/"
                       "v0.3.0/skills/accessibility-statement-check/statement_template_check.py")
# frame-partN.csv as written by uk_frame.py 0.1.0 (sealed job uk-frame-v1, GIAS file of 20261109).
FRAME_PARTS = (
    ("frame-part1.csv", 9891, "fe6568ec3ee71a41c7254bb6210445ee4c074b85f0776a94eb8321bf48b0d920"),
    ("frame-part2.csv", 10088, "fbb89b0c61a9e02a390b3f53f0d16023812ad9431fd70486327f56f71e4fe51d"),
    ("frame-part3.csv", 4680, "e0b1e8ddc949d640649a195b9ffd36b819cde30c993603c4fd9edbed443c3969"),
)
FRAME_ROWS = 24659
FRAME_HOSTS = 23802
MAX_DROPPED = 5
PROBE_PATH = "/accessibility-statement/"
CRAWL_SEED = "school-stock-2026-11"
RETRY_STATUSES = (429, 503)
RETRY_PAUSE = 30
# A word that MV2's publishing tool blocks (it is in some place names). Rows whose name or website
# contain it are dropped before anything is read; none were in the frame when it was built.
GUARD_RE = re.compile(r"s[a]ybr[o]ok", re.I)

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
G1_MIN_ANSWERED = 0.80          # G1: share of hosts whose server answered
J1_MIN_HOSTS = 400              # J1: hosts serving a page with a 0.3.0 placeholder at the address
J2_MIN_CREDIT = 0.80            # J2: share of those pages carrying the Juniper Websites credit
J2_MIN_PAGES = 50
J3_MIN_KEPT = 0.40              # J3: share of Juniper-template pages that keep a 0.3.0 placeholder
J3_MIN_PAGES = 100
J4_MIN_22 = 0.50                # J4: share of GOV.UK-wording pages naming WCAG 2.2 as the highest
J4_MIN_PAGES = 200

# One vendor's school template (Juniper Websites), read on live pages on 2026-11-09. Described
# only: the graded placeholder measure is the 0.3.0 checker's.
JUNIPER_FIELD_RULES = (
    ("website_link_and_date", r"\[\s*website\s+link\s+and\s+date\s*\]"),
    ("accessibility_email", r"\[\s*accessibility\s+email\s+address\s*\]"),
    ("school_phone", r"\[\s*school\s+phone\s+number\s*\]"),
    ("school_address", r"\[\s*school\s+(?:mailing\s+)?address\s*\]"),
    ("school_name_round", r"\(\s*school\s+name\s*\)"),
    ("sample_notice", r"\[\s*this\s+is\s+a\s+sample\s+accessibility\s+statement\b"),
    ("prior_to_publication", r"\bprior\s+to\s+publication\s*,?\s+please\s+remove\s+this\s+text\b"),
    ("delete_as_appropriate", r"\[\s*delete\s+as\s+appropriate\b"),
    ("examples_only", r"\[\s*the\s+above\s+are\s+examples\s+only\b"),
    ("please_instruction", r"\[\s*please\s+(?:add|refer|use|remove)\b"),
    ("method_note", r"\[\s*set\s+out\s+the\s+method\b"),
    ("review_note", r"\[\s*it\s+is\s+recommended\s+that\s+statements\b"),
)
JUNIPER_FIELD_RES = tuple((i, re.compile(p, re.I)) for i, p in JUNIPER_FIELD_RULES)
# The template's closing sentence, filled in or not ("[School Name] values diversity and inclusion
# and is committed to providing an accessible online experience ...").
JUNIPER_TEMPLATE_RE = re.compile(r"values\s+diversity\s+and\s+inclusion\s+and\s+is\s+committed\s+to\s+"
                                 r"providing\s+an\s+accessible\s+online\s+experience", re.I)
# The longer variant that carries editing instructions.
JUNIPER_SAMPLE_RE = re.compile(r"curate\s+your\s+own\s+accessibility\s+statement", re.I)
# The vendor's footer credit ("School Website by Juniper Websites") or a link to the vendor.
JUNIPER_CREDIT_RE = re.compile(rb"juniper(?:\s|&nbsp;|&#160;|<[^>]{0,200}>)*websites|juniperwebsites\.co\.uk|"
                               rb"junipereducation\.org", re.I)
# A statement that names the vendor's build address instead of the school's own.
STAGING_RE = re.compile(r"\b[a-z0-9-]+\.web\d+\.juniperwebsites\.co\.uk\b", re.I)

BOOLS = ("retried", "juniper_credit", "juniper_template", "juniper_sample", "staging_domain",
         "placeholder", "juniper_field", "gov_uk_sample", "other_host")
COLUMNS = ["host", "urn", "name", "type_group", "phase", "la_name", "region", "establishments",
           "base", "status", "retried", "final_url", "other_host", "text_chars", "text_sha256",
           "juniper_credit", "juniper_template", "juniper_sample", "staging_domain", "placeholder",
           "placeholder_ids", "juniper_field", "juniper_field_ids", "gov_uk_sample", "highest"]
NOT_ANSWERED = ("", "http_0", "crash", "not_started", "bad_url")
PART_LIMIT = 1_900_000


# ---------------------------------------------------------------- the frame

def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalize(data):
    return data.replace(b"\r\n", b"\n")


def base_of(website):
    """scheme://netloc of a GIAS website field (http when no scheme is given), or ''."""
    w = (website or "").strip()
    if not w:
        return ""
    if not re.match(r"https?://", w, re.I):
        w = "http://" + w
    try:
        p = urllib.parse.urlsplit(w)
        netloc = (p.netloc or "").lower().rstrip(".")
    except ValueError:
        return ""
    if not netloc or " " in netloc or "." not in netloc:
        return ""
    return "%s://%s" % (p.scheme.lower(), netloc)


def read_parts(folder):
    """(rows, checks): the frame's rows and, per part, whether its bytes and row count are the
    ones uk_frame.py wrote."""
    rows, checks = [], {}
    for name, n, digest in FRAME_PARTS:
        with open(os.path.join(folder, name), "rb") as f:
            data = f.read()
        part = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
        checks[name] = sha256(data) == digest and len(part) == n
        rows.extend(part)
    return rows, checks


def build_frame(rows):
    """One row per distinct host: the establishment with the lowest URN, with the number of
    establishments that list this host. Returns (hosts, dropped)."""
    groups = collections.OrderedDict()
    dropped = 0
    for r in rows:
        if GUARD_RE.search(r.get("name", "")) or GUARD_RE.search(r.get("website", "")):
            dropped += 1
            continue
        h = r.get("host", "")
        if not h:
            continue
        groups.setdefault(h, []).append(r)
    out = []
    for h, rs in groups.items():
        first = min(rs, key=lambda r: int(r["urn"]) if r["urn"].isdigit() else 10 ** 9)
        out.append({"host": h, "urn": first["urn"], "name": first["name"],
                    "type_group": first["type_group"], "phase": first["phase"],
                    "la_name": first["la_name"], "region": first["region"],
                    "establishments": len(rs), "base": base_of(first.get("website", ""))})
    return out, dropped


def crawl_order(hosts):
    """A fixed shuffled order, so one vendor's servers are not asked one host after another."""
    return sorted(hosts, key=lambda r: sha256((CRAWL_SEED + r["host"]).encode("utf-8")))


# ---------------------------------------------------------------- one page

def check_text(text, body=b""):
    """The 0.3.0 checker's reading of one page plus this study's described markers."""
    d = stc.check_text(text)
    flat = " ".join(text.split())
    fields = [i for i, rx in JUNIPER_FIELD_RES if rx.search(flat)]
    return {"placeholder": bool(d["placeholder"]),
            "placeholder_ids": ";".join("%s/%s" % (p["group"], p["id"]) for p in d["placeholders"]),
            "highest": d["highest"],
            "gov_uk_sample": "gov_uk_sample" in d["templates"],
            "juniper_field": bool(fields), "juniper_field_ids": ";".join(fields),
            "juniper_template": bool(JUNIPER_TEMPLATE_RE.search(flat)),
            "juniper_sample": bool(JUNIPER_SAMPLE_RE.search(flat)),
            "staging_domain": bool(STAGING_RE.search(flat)),
            "juniper_credit": bool(JUNIPER_CREDIT_RE.search(body or b""))}


def blank(row):
    out = dict(row)
    out.update(status="", final_url="", text_chars=0, text_sha256="", placeholder_ids="",
               juniper_field_ids="", highest="")
    for k in BOOLS:
        out[k] = False
    return out


def robots_allows(status, body, url):
    rp = urllib.robotparser.RobotFileParser()
    if status == 200 and body:
        rp.parse(body.decode("utf-8", "replace").splitlines())
    elif status in (401, 403):
        rp.disallow_all = True
    else:
        rp.allow_all = True
    return rp.can_fetch(stc.UA, url)


def read_one(row, get=stc.http_get, delay=1.0, sleep=time.sleep):
    """robots.txt first (no answer at all ends the host), then the one address, asked a second
    time after a pause only if the server answered 429 or 503."""
    out = blank(row)
    if not row.get("base"):
        out["status"] = "bad_url"
        return out
    url = row["base"] + PROBE_PATH
    rstatus, _, _, rbody = get(row["base"] + "/robots.txt")
    sleep(delay)
    if rstatus == 0:
        out["status"] = "http_0"
        return out
    if not robots_allows(rstatus, rbody, url):
        out["status"] = "robots"
        return out
    status, final, ctype, body = get(url)
    sleep(delay)
    if status in RETRY_STATUSES:
        out["retried"] = True
        sleep(RETRY_PAUSE)
        status, final, ctype, body = get(url)
        sleep(delay)
    final = final or url
    out["final_url"] = "[withheld]" if GUARD_RE.search(final) else final
    try:
        fp = urllib.parse.urlsplit(final)
        fhost = (fp.hostname or "").lower()
        fpath = fp.path
    except ValueError:
        fhost, fpath = "", ""
    if fhost.startswith("www."):
        fhost = fhost[4:]
    out["other_host"] = bool(fhost) and fhost != row["host"]
    if status != 200:
        out["status"] = "http_%d" % status
        return out
    if not stc.is_html(ctype, body):
        out["status"] = "not_html"
        return out
    if fpath in ("", "/"):
        out["status"] = "redirect_home"
        return out
    text = stc.visible_text(body, ctype)
    out.update(text_chars=len(text), text_sha256=sha256(text.encode("utf-8")))
    if len(text) < stc.MIN_TEXT:
        out["status"] = "short"
        return out
    if "accessib" not in text.lower():
        out["status"] = "not_statement"
        return out
    out["status"] = "ok"
    out.update(check_text(text, body))
    return out


def _read_or_skip(row, deadline, kw):
    if deadline and time.time() > deadline:
        r = blank(row)
        r["status"] = "not_started"
        return r
    return read_one(row, **kw)


def crawl(rows, workers=8, deadline=None, **kw):
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_read_or_skip, r, deadline, kw) for r in rows]
        for i, fut in enumerate(futures, 1):
            try:
                out.append(fut.result())
            except Exception as e:  # one host's crash is recorded, never fatal
                r = blank(rows[i - 1])
                r.update(status="crash", final_url=str(e)[:80])
                out.append(r)
            if i % 1000 == 0:
                print("%d/%d hosts" % (i, len(futures)), flush=True)
    return out


# ---------------------------------------------------------------- grading

def share(k, n):
    return {"k": k, "n": n, "pct": round(100.0 * k / n, 2) if n else None}


def typed(rows):
    """Rows read back from the hosts tables, with the flag columns as booleans again."""
    return [dict(r, **{k: r.get(k) in (True, "True") for k in BOOLS}) for r in rows]


def answered(r):
    return r.get("status") not in NOT_ANSWERED


def ok(r):
    return r.get("status") == "ok"


def flagged(r):
    return ok(r) and bool(r.get("placeholder"))


def grade(rows, frame_ok=True):
    n = len(rows)
    ans = [r for r in rows if answered(r)]
    ph = [r for r in rows if flagged(r)]
    credit = [r for r in ph if r.get("juniper_credit")]
    tmpl = [r for r in rows if ok(r) and r.get("juniper_template")]
    kept = [r for r in tmpl if r.get("placeholder")]
    uk = [r for r in rows if ok(r) and r.get("gov_uk_sample")]
    v22 = [r for r in uk if r.get("highest") == "2.2"]
    measures = {"F1_hosts": n,
                "G1_answered": share(len(ans), n),
                "J1_placeholder_hosts": len(ph),
                "J2_credit_of_placeholder": share(len(credit), len(ph)),
                "J3_kept_of_juniper_template": share(len(kept), len(tmpl)),
                "J4_wcag22_of_gov_uk_wording": share(len(v22), len(uk))}
    gates = {"F1_frame": bool(frame_ok),
             "G1_answered": bool(n) and len(ans) / n >= G1_MIN_ANSWERED}
    if not all(gates.values()):
        return measures, gates, {k: None for k in ("J1", "J2", "J3", "J4")}
    preds = {"J1": len(ph) >= J1_MIN_HOSTS,
             "J2": (len(credit) / len(ph) >= J2_MIN_CREDIT) if len(ph) >= J2_MIN_PAGES else None,
             "J3": (len(kept) / len(tmpl) >= J3_MIN_KEPT) if len(tmpl) >= J3_MIN_PAGES else None,
             "J4": (len(v22) / len(uk) >= J4_MIN_22) if len(uk) >= J4_MIN_PAGES else None}
    return measures, gates, preds


def tally(rows, key):
    c = collections.Counter(str(r.get(key, "")) for r in rows)
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def tally_ids(rows, key):
    c = collections.Counter()
    for r in rows:
        for i in (r.get(key) or "").split(";"):
            if i:
                c[i] += 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def described(rows):
    """Reported, not graded."""
    oks = [r for r in rows if ok(r)]
    ph = [r for r in rows if flagged(r)]
    jf = [r for r in oks if r.get("juniper_field")]
    either = [r for r in oks if r.get("placeholder") or r.get("juniper_field")]
    groups = {}
    for g in sorted(set(r.get("type_group", "") for r in rows)):
        rs = [r for r in rows if r.get("type_group", "") == g]
        groups[g] = {"hosts": len(rs), "ok": sum(1 for r in rs if ok(r)),
                     "placeholder": sum(1 for r in rs if flagged(r))}
    return {
        "status": tally(rows, "status"),
        "ok_pages": len(oks),
        "ok_juniper_credit": sum(1 for r in oks if r.get("juniper_credit")),
        "ok_juniper_template": sum(1 for r in oks if r.get("juniper_template")),
        "ok_juniper_sample": sum(1 for r in oks if r.get("juniper_sample")),
        "ok_gov_uk_wording": sum(1 for r in oks if r.get("gov_uk_sample")),
        "ok_highest": tally(oks, "highest"),
        "placeholder_ids": tally_ids(ph, "placeholder_ids"),
        "placeholder_highest": tally(ph, "highest"),
        "placeholder_distinct_texts": len(set(r.get("text_sha256") for r in ph)),
        "placeholder_other_host": sum(1 for r in ph if r.get("other_host")),
        "placeholder_establishments": sum(int(r.get("establishments") or 0) for r in ph),
        "placeholder_by_region": tally(ph, "region"),
        "placeholder_by_phase": tally(ph, "phase"),
        "by_type_group": groups,
        "juniper_field_pages": len(jf),
        "juniper_field_without_placeholder": sum(1 for r in jf if not r.get("placeholder")),
        "juniper_field_ids": tally_ids(jf, "juniper_field_ids"),
        "placeholder_or_juniper_field": len(either),
        "staging_domain_pages": sum(1 for r in oks if r.get("staging_domain")),
        "retried": sum(1 for r in rows if r.get("retried")),
    }


# ---------------------------------------------------------------- the run

def fetch_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": stc.UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def checker_matches_release(here, fetch=fetch_bytes):
    """True when the local checker is byte-identical (line endings aside) to release v0.3.0."""
    with open(os.path.join(here, "statement_template_check.py"), "rb") as f:
        local = normalize(f.read())
    try:
        remote = normalize(fetch(CHECKER_RELEASE_URL))
    except Exception:
        return False
    return local == remote


def write_tables(out_dir, rows):
    """hosts-partN.csv, sorted by host, each part under PART_LIMIT bytes."""
    rows = sorted(rows, key=lambda r: r["host"])
    header = ",".join(COLUMNS) + "\n"
    parts, buf, size, n = [], [header], len(header.encode("utf-8")), 0

    def flush():
        data = "".join(buf).encode("utf-8")
        name = "hosts-part%d.csv" % (len(parts) + 1)
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)
        parts.append({"file": name, "rows": n, "bytes": len(data), "sha256": sha256(data)})

    for r in rows:
        line = io.StringIO()
        csv.writer(line, lineterminator="\n").writerow([r.get(c, "") for c in COLUMNS])
        enc = line.getvalue()
        b = len(enc.encode("utf-8"))
        if size + b > PART_LIMIT and n:
            flush()
            buf, size, n = [header], len(header.encode("utf-8")), 0
        buf.append(enc)
        size += b
        n += 1
    flush()
    return parts


def result_text(result):
    lines = ["school_stock %s" % result["version"],
             "status: %s" % result["status"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("frame", "crawl", "tables"):
        if k in result:
            lines.append("%s: %s" % (k, json.dumps(result[k], sort_keys=True)))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, json.dumps(v, sort_keys=True)))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        for k in sorted(d):
            lines.append("%s: %s" % (k, json.dumps(d[k], sort_keys=True)))
    return "\n".join(lines)


def main(argv=None, fetch=fetch_bytes, get=stc.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-minutes", type=float, default=270)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "checker_version": stc.__version__, "gates": {}, "files": {}}
    for name in ("school_stock.py", "statement_template_check.py", PREREG_PATH):
        with open(os.path.join(here, *name.split("/")), "rb") as f:
            result["files"][name] = sha256(f.read())

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1, sort_keys=True)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("school_stock: %s" % status)
        return 0

    with open(os.path.join(here, *PREREG_PATH.split("/")), "rb") as f:
        prereg = f.read()
    result["gates"]["P0_prereg"] = b"J4" in prereg
    result["gates"]["P0_checker"] = (stc.__version__ == CHECKER_VERSION
                                     and checker_matches_release(here, fetch))
    if not (result["gates"]["P0_prereg"] and result["gates"]["P0_checker"]):
        return finish("not_run")  # no school website was read
    rows, checks = read_parts(os.path.join(here, *FRAME_DIR.split("/")))
    hosts, dropped = build_frame(rows)
    frame_ok = (all(checks.values()) and len(rows) == FRAME_ROWS and dropped <= MAX_DROPPED
                and len(hosts) + MAX_DROPPED >= FRAME_HOSTS and len(hosts) <= FRAME_HOSTS)
    result["frame"] = {"rows": len(rows), "hosts": len(hosts), "dropped": dropped,
                       "parts_ok": checks, "bad_base": sum(1 for h in hosts if not h["base"])}
    if not frame_ok:
        result["gates"]["F1_frame"] = False
        return finish("not_run")  # nothing was read
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    deadline = time.time() + 60 * args.max_minutes
    read = crawl(crawl_order(hosts), workers=args.workers, deadline=deadline, get=get, sleep=sleep)
    result["crawl"] = {"started_utc": started,
                       "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "workers": args.workers}
    result["tables"] = write_tables(args.out_dir, read)
    measures, gates, preds = grade(read, frame_ok)
    result["gates"].update(gates)
    result.update(measures=measures, predictions=preds, described=described(read))
    return finish("graded" if all(gates.values()) else "ungraded")


if __name__ == "__main__":
    sys.exit(main())
