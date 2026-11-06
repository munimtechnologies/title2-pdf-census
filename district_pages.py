"""district_pages: what do US school districts' accessibility pages promise?

The pre-registered test in results/district-pages/PREREG.md. MV2's 2026 censuses read the
accessibility pages of US cities, counties and towns (results/a11y-pages, results/small-pages).
Public school districts are Title II entities too, and their two dates turn on the same figure:
the total population of the district's area (April 26, 2027 at 50,000 or more, April 26, 2028
under 50,000, since the Justice Department's interim final rule of April 20, 2026). This script:

  1. waits until results/district-pages/PREREG.md is on the repository's main branch and main's
     copies of the five pinned files are byte for byte these files (gives up after about an
     hour), unless --dry-run;
  2. builds the frame from two public federal files: the NCES Common Core of Data LEA directory
     2024-25 (regular, open districts with a website) and the Census Bureau's SAIPE 2024
     school-district populations (else SAIPE 2023), one row per website host;
  3. takes a fixed sample in a pre-registered hash order: up to 800 districts of 50,000 or more
     people and up to 1,700 of under 50,000. --dry-run stops here and reads no district page;
  4. reads each home page, picks its accessibility page by the census's link rules
     (a11y_pages.candidates), reads it with district_check.check_text, and grades D1-D6.

Reads public pages only, one site at a time with a pause between requests, honouring robots.txt,
under a User-Agent that names Munim, Inc. and an email. Stores no page text beyond short
snippets around a WCAG version, a date or the 50,000 threshold, with email addresses and phone
numbers removed. A statement's wording is not a judgment of whether a website is accessible.

Standard library only. Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import os
import sys
import time
import urllib.parse
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a11y_pages as ap  # noqa: E402  (the census's requests, link rules and statistics)
import district_check as dc  # noqa: E402  (this study's page rules)

__version__ = "0.1.0"

REPO_RAW = ap.REPO_RAW
PREREG_PATH = "results/district-pages/PREREG.md"
PINNED = ("district_pages.py", "district_check.py", "a11y_pages.py", "statement_check.py",
          "template_check.py")
CCD_URLS = ("https://nces.ed.gov/ccd/Data/zip/ccd_lea_029_2425_w_1a_073025.zip",
            "https://nces.ed.gov/ccd/data/zip/ccd_lea_029_2425_w_1a_073025.zip")
SAIPE_URLS = ("https://www2.census.gov/programs-surveys/saipe/datasets/2024/2024-school-districts/"
              "ussd24.txt",
              "https://www2.census.gov/programs-surveys/saipe/datasets/2023/2023-school-districts/"
              "ussd23.txt")

# Pre-registered (PREREG.md). Changing any of these after the crawl voids the test.
REGULAR_TYPES = ("1", "2")                 # CCD LEA_TYPE: regular, regular in a supervisory union
OPEN_STATUSES = ("1", "3", "4", "5", "8")  # CCD SY_STATUS: open, new, added, changed, reopened
BIG = 50000
SEED = "district-pages-2026-11"
N_BIG, N_SMALL = 800, 1700
MIN_FRAME, MAX_FRAME = 8000, 16000          # F1
MIN_BIG_FRAME, MAX_BIG_FRAME = 400, 2500    # F1
MIN_HOMES = 1000                            # G1, both bands together
MIN_PAGES = 400                             # G1, both bands together
MIN_SMALL_VERSIONED = 150                   # D1
MIN_SMALL_PAGES = 300                       # D2, D6
MIN_BAND_VERSIONED = 80                     # D3, each band
MIN_SMALL_HOMES = 600                       # D5
D1_MAX_ONLY_20 = 0.5571   # cities and counties of 50,000+: 283 of 508 versioned pages
D2_MAX_STOCK = 0.10
D3_MIN_GAP = 0.05
D4_MIN_PLACEHOLDER = 0.005
D5_MIN_LINKED = 0.682     # cities and counties of 50,000+: 815 of 1,195 home pages read
D6_MIN_TITLE2 = 0.2215    # cities and counties of 50,000+: 179 of 808 pages read

FRAME_COLUMNS = ["leaid", "name", "state", "lea_type", "population", "band", "website", "host"]
PAGE_KEYS = ["wcag_any", "versions", "highest", "section508", "title2", "old_date", "new_date",
             "date_2028", "stock", "contact", "placeholder", "placeholder_kinds",
             "placeholder_text", "no_wcag", "students_threshold", "ocr", "s504", "vendor_named",
             "finalsite_line", "generator_line", "findings", "version_snippet", "date_snippet",
             "threshold_snippet"]
COLUMNS = (FRAME_COLUMNS + ["home", "platform", "overlay", "candidates", "offsite_links", "tries",
                            "page_status", "page_rank", "page_url", "text_chars", "text_sha256"]
           + PAGE_KEYS)


# ---------------------------------------------------------------- the frame

def first(urls, fetch):
    errors = []
    for url in urls:
        try:
            return url, fetch(url, tries=3, timeout=180)
        except Exception as e:  # the next mirror or year is tried
            errors.append("%s: %s" % (url.rsplit("/", 1)[-1], str(e)[:80]))
    raise RuntimeError("; ".join(errors))


def read_ccd(zbytes):
    """Rows of the one CSV inside the CCD zip."""
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        names = sorted(n for n in z.namelist() if n.lower().endswith(".csv"))
        raw = z.read(names[0])
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))))


def parse_saipe(text):
    """{7-digit LEAID: total population} from the fixed-width SAIPE file (state in columns 1-2,
    district 4-8, total population 83-90)."""
    out = {}
    for line in text.splitlines():
        if len(line) < 90:
            continue
        st, dist, pop = line[0:2], line[3:8], line[82:90].strip()
        if st.isdigit() and dist.isdigit() and pop.isdigit():
            out[st + dist] = int(pop)
    return out


def host_of(website):
    w = (website or "").strip()
    if not w or w.upper() in ("M", "N", "NA", "N/A", "-1", "-2", "-9"):
        return ""
    if "://" not in w:
        w = "http://" + w
    try:
        host = (urllib.parse.urlsplit(w).hostname or "").lower()
    except ValueError:
        return ""
    if "." not in host:
        return ""
    return host[4:] if host.startswith("www.") else host


def band(pop):
    return "50k+" if pop >= BIG else "under50k"


def build_frame(ccd_rows, pops):
    """Regular, open districts with a website host and a SAIPE population; one row per host
    (the largest population kept, then the lowest LEAID)."""
    best = {}
    for r in ccd_rows:
        if str(r.get("LEA_TYPE", "")).strip() not in REGULAR_TYPES:
            continue
        if str(r.get("SY_STATUS", "")).strip() not in OPEN_STATUSES:
            continue
        leaid = str(r.get("LEAID", "")).strip()
        host = host_of(r.get("WEBSITE", ""))
        pop = pops.get(leaid)
        if not host or pop is None:
            continue
        row = {"leaid": leaid, "name": (r.get("LEA_NAME") or "").strip(),
               "state": (r.get("ST") or "").strip(), "lea_type": str(r.get("LEA_TYPE")).strip(),
               "population": pop, "band": band(pop), "website": r.get("WEBSITE", "").strip(),
               "host": host}
        old = best.get(host)
        if old is None or (-pop, leaid) < (-old["population"], old["leaid"]):
            best[host] = row
    return sorted(best.values(), key=lambda x: x["leaid"])


def hash_key(leaid, seed=SEED):
    return hashlib.sha256((seed + leaid).encode("utf-8")).hexdigest()


def sample(frame, n_big=N_BIG, n_small=N_SMALL, seed=SEED):
    """The first n_big districts of 50,000+ and n_small of under 50,000 in the order of
    SHA-256(seed + LEAID): fixed before any page is read."""
    ordered = sorted(frame, key=lambda r: hash_key(r["leaid"], seed))
    big = [r for r in ordered if r["band"] == "50k+"][:n_big]
    small = [r for r in ordered if r["band"] == "under50k"][:n_small]
    return big + small


# ---------------------------------------------------------------- crawling

def crawl_site(row, get=ap.http_get, delay=1.0, sleep=time.sleep, deadline=None):
    """The census's requests, in its order (a11y_pages.crawl_site), read with district_check."""
    out = {k: row.get(k, "") for k in FRAME_COLUMNS}
    out.update(home="", platform="", overlay="", candidates=0, offsite_links=0, tries=0,
               page_status="", page_rank="", page_url="", text_chars=0, text_sha256="")
    if deadline and time.time() > deadline:
        out["home"] = "not_started"
        return out
    start = ap.normalize_site(row["website"])
    allowed = ap.robots_checker(get, delay, sleep)
    if not allowed(start):
        out["home"] = "robots"
        return out
    status, final, ctype, body = get(start)
    sleep(delay)
    if status != 200:
        out["home"] = "http_%d" % status
        return out
    if not ap.is_html(ctype, body):
        out["home"] = "not_html"
        return out
    out["home"] = "ok"
    out["platform"] = dc.platforms(body)
    out["overlay"] = ap.overlays(body)
    cands, off, _ = ap.candidates(ap.parse(body, ctype), final or start)
    out["candidates"], out["offsite_links"] = len(cands), off
    if not cands:
        out["page_status"] = "no_link"
        return out
    for url, rank in cands[:ap.MAX_TRIES]:
        if deadline and time.time() > deadline:
            out["page_status"] = "deadline"
            return out
        out["tries"] += 1
        if not allowed(url):
            out["page_status"] = "robots"
            continue
        status, final2, ctype, body = get(url)
        sleep(delay)
        if status != 200:
            out["page_status"] = "http_%d" % status
            continue
        if not ap.is_html(ctype, body):
            out["page_status"] = "not_html"
            continue
        text = ap.visible_text(ap.parse(body, ctype))
        out.update(page_url=final2 or url, page_rank=rank, text_chars=len(text),
                   text_sha256=ap.sha256(text.encode("utf-8")))
        if len(text) < ap.MIN_TEXT:
            out["page_status"] = "short"
            continue
        out["page_status"] = "ok"
        out.update(dc.check_text(text))
        return out
    return out


def crawl(cohort, workers=24, deadline=None, **kw):
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(crawl_site, r, deadline=deadline, **kw) for r in cohort]
        for i, fut in enumerate(futures, 1):
            try:
                rows.append(fut.result())
            except Exception as e:  # one site's crash is recorded, never fatal
                r = {k: cohort[i - 1].get(k, "") for k in FRAME_COLUMNS}
                r.update(home="crash", page_status=str(e)[:80])
                rows.append(r)
            if i % 100 == 0:
                print("%d/%d sites" % (i, len(futures)), flush=True)
    return rows


# ---------------------------------------------------------------- grading

def truthy(v):
    return v is True or str(v) == "True"


def band_stats(rows):
    homes = [r for r in rows if r.get("home") == "ok"]
    pages = [r for r in rows if r.get("page_status") == "ok"]
    versioned = [r for r in pages if r.get("highest")]
    return {"homes": homes, "pages": pages, "versioned": versioned,
            "linked": sum(1 for r in homes if int(r.get("candidates") or 0) > 0),
            "only20": sum(1 for r in versioned if r["highest"] == "2.0"),
            "newer": sum(1 for r in versioned if r["highest"] in ("2.1", "2.2")),
            "stock": sum(1 for r in pages if truthy(r.get("stock"))),
            "title2": sum(1 for r in pages if truthy(r.get("title2"))),
            "placeholder": sum(1 for r in pages if truthy(r.get("placeholder")))}


def grade(rows):
    s = band_stats([r for r in rows if r.get("band") == "under50k"])
    b = band_stats([r for r in rows if r.get("band") == "50k+"])
    a = band_stats(rows)
    nv_s, nv_b = len(s["versioned"]), len(b["versioned"])
    measures = {"D1_only_2.0_of_versioned_under50k": ap.share(s["only20"], nv_s),
                "D2_stock_of_pages_under50k": ap.share(s["stock"], len(s["pages"])),
                "D3_newer_of_versioned_50k+": ap.share(b["newer"], nv_b),
                "D3_newer_of_versioned_under50k": ap.share(s["newer"], nv_s),
                "D4_placeholder_of_pages_all": ap.share(a["placeholder"], len(a["pages"])),
                "D5_linked_of_homes_under50k": ap.share(s["linked"], len(s["homes"])),
                "D6_title2_of_pages_under50k": ap.share(s["title2"], len(s["pages"]))}
    small_pages = len(s["pages"])
    preds = {
        "D1": (s["only20"] / nv_s < D1_MAX_ONLY_20) if nv_s >= MIN_SMALL_VERSIONED else None,
        "D2": (s["stock"] / small_pages < D2_MAX_STOCK) if small_pages >= MIN_SMALL_PAGES else None,
        "D3": (b["newer"] / nv_b - s["newer"] / nv_s >= D3_MIN_GAP)
              if min(nv_s, nv_b) >= MIN_BAND_VERSIONED else None,
        "D4": (a["placeholder"] / len(a["pages"]) >= D4_MIN_PLACEHOLDER)
              if len(a["pages"]) >= MIN_PAGES else None,
        "D5": (s["linked"] / len(s["homes"]) >= D5_MIN_LINKED)
              if len(s["homes"]) >= MIN_SMALL_HOMES else None,
        "D6": (s["title2"] / small_pages >= D6_MIN_TITLE2) if small_pages >= MIN_SMALL_PAGES
              else None}
    return measures, preds


def described(rows):
    """Reported, not graded."""
    out = {"home": ap._tally(rows, "home"), "page_status": ap._tally(rows, "page_status"),
           "by_band": {}}
    for name in ("50k+", "under50k"):
        rs = [r for r in rows if r.get("band") == name]
        pages = [r for r in rs if r.get("page_status") == "ok"]
        homes = [r for r in rs if r.get("home") == "ok"]

        def n(key, pages=pages):
            return sum(1 for r in pages if truthy(r.get(key)))
        out["by_band"][name] = {
            "sampled": len(rs), "homes_ok": len(homes), "pages_ok": len(pages),
            "highest": ap._tally([r for r in pages if r.get("highest")], "highest"),
            "wcag_any": n("wcag_any"), "section508": n("section508"), "title2": n("title2"),
            "s504": n("s504"), "ocr": n("ocr"), "stock": n("stock"), "no_wcag": n("no_wcag"),
            "placeholder": n("placeholder"),
            "placeholder_kinds": ap._tally([r for r in pages if truthy(r.get("placeholder"))],
                                           "placeholder_kinds"),
            "students_threshold": n("students_threshold"),
            "finalsite_line": n("finalsite_line"), "generator_line": n("generator_line"),
            "contact": n("contact"),
            "date_2026_04_24": n("old_date"), "date_2027_04_26": n("new_date"),
            "date_2028_04_26": n("date_2028"),
            "vendor_named": ap._tally([r for r in pages if r.get("vendor_named")],
                                      "vendor_named"),
            "platform_on_home": ap._tally(homes, "platform"),
            "overlay_on_home": ap._tally(homes, "overlay"),
            "no_link_but_offsite": sum(1 for r in homes if r.get("page_status") == "no_link"
                                       and int(r.get("offsite_links") or 0) > 0)}
    return out


def wait_for_prereg(here, fetch=ap.fetch_bytes, sleep=time.sleep, tries=ap.TRIES, pause=ap.PAUSE):
    """(True, attempts) once main holds PREREG.md and the pinned files, else (False, tries)."""
    local = {}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            local[name] = ap.normalize(f.read())
    for i in range(tries):
        try:
            prereg = fetch(REPO_RAW + PREREG_PATH + "?n=%d" % i)
            same = all(ap.normalize(fetch(REPO_RAW + name + "?n=%d" % i)) == local[name]
                       for name in PINNED)
            if b"D6" in prereg and same:
                return True, i + 1
        except Exception:  # not committed yet (404) or a network hiccup: wait and try again
            pass
        if i + 1 < tries:
            sleep(pause)
    return False, tries


# ---------------------------------------------------------------- output

def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r.get("leaid", "")):
            w.writerow({c: r.get(c, "") for c in columns})


def result_text(result):
    lines = ["district_pages %s" % result["version"],
             "gates: %s" % ", ".join("%s=%s" % kv for kv in sorted(result["gates"].items()))]
    for k in ("ccd_file", "ccd_rows", "saipe_file", "saipe_rows", "frame", "frame_by_band",
              "sampled", "sampled_by_band", "homes_ok", "pages_ok"):
        if k in result:
            lines.append("%s: %s" % (k, result[k]))
    for k, v in sorted((result.get("measures") or {}).items()):
        lines.append("  %s: %s" % (k, v))
    p = result.get("predictions")
    lines.append("predictions: %s" % (", ".join("%s=%s" % kv for kv in sorted(p.items()))
                                      if p else "not graded"))
    d = result.get("described")
    if d:
        for k in sorted(d):
            lines.append("%s: %s" % (k, json.dumps(d[k], sort_keys=True)))
    return "\n".join(lines)


def tally_band(rows):
    return {name: sum(1 for r in rows if r["band"] == name) for name in ("50k+", "under50k")}


def main(argv=None, fetch=ap.fetch_bytes, get=ap.http_get, sleep=time.sleep):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--dry-run", action="store_true",
                        help="build the frame and the sample only; read no district page")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--max-minutes", type=float, default=150)
    args = parser.parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(args.out_dir, exist_ok=True)
    result = {"version": __version__, "dry_run": args.dry_run, "gates": {}, "files": {}}
    for name in PINNED:
        with open(os.path.join(here, name), "rb") as f:
            result["files"][name] = ap.sha256(f.read())

    def finish(status):
        result["status"] = status
        with open(os.path.join(args.out_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
            f.write("\n")
        text = result_text(result)
        with open(os.path.join(args.out_dir, "result.txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(text)
        print("district_pages: %s" % status)
        return 0 if status in ("graded", "dry run: frame and sample written") else 1

    if not args.dry_run:
        ok, result["prereg_attempts"] = wait_for_prereg(here, fetch=fetch, sleep=sleep)
        result["gates"]["P0_prereg_public"] = ok
        if not ok:
            return finish("stopped: the pre-registration and pinned files are not on main")
    try:
        ccd_url, zbytes = first(CCD_URLS, fetch)
        ccd_rows = read_ccd(zbytes)
        saipe_url, sbytes = first(SAIPE_URLS, fetch)
        pops = parse_saipe(sbytes.decode("latin-1"))
    except Exception as e:  # recorded; nothing is graded
        result["error"] = str(e)[:200]
        return finish("stopped: federal files not read")
    result.update(ccd_file=ccd_url.rsplit("/", 1)[-1], ccd_sha256=ap.sha256(zbytes),
                  ccd_rows=len(ccd_rows), saipe_file=saipe_url.rsplit("/", 1)[-1],
                  saipe_sha256=ap.sha256(sbytes), saipe_rows=len(pops))
    frame = build_frame(ccd_rows, pops)
    result["frame"] = len(frame)
    result["frame_by_band"] = tally_band(frame)
    write_csv(os.path.join(args.out_dir, "frame.csv"), frame, FRAME_COLUMNS)
    nbig = result["frame_by_band"]["50k+"]
    result["gates"]["F1_frame"] = (MIN_FRAME <= len(frame) <= MAX_FRAME
                                   and MIN_BIG_FRAME <= nbig <= MAX_BIG_FRAME)
    if not result["gates"]["F1_frame"]:
        return finish("stopped: frame size outside the pre-registered range")
    cohort = sample(frame)
    result["sampled"] = len(cohort)
    result["sampled_by_band"] = tally_band(cohort)
    write_csv(os.path.join(args.out_dir, "sample.csv"), cohort, FRAME_COLUMNS)
    if args.dry_run:
        return finish("dry run: frame and sample written")
    deadline = time.time() + args.max_minutes * 60
    rows = crawl(cohort, workers=args.workers, deadline=deadline, get=get, delay=args.delay,
                 sleep=sleep)
    write_csv(os.path.join(args.out_dir, "rows.csv"), rows, COLUMNS)
    result["homes_ok"] = sum(1 for r in rows if r.get("home") == "ok")
    result["pages_ok"] = sum(1 for r in rows if r.get("page_status") == "ok")
    result["gates"]["G1_read"] = (result["homes_ok"] >= MIN_HOMES
                                  and result["pages_ok"] >= MIN_PAGES)
    result["described"] = described(rows)
    if not result["gates"]["G1_read"]:
        return finish("stopped: too few home pages or accessibility pages read")
    result["measures"], result["predictions"] = grade(rows)
    return finish("graded")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    sys.exit(main())
