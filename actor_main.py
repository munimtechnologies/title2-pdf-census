"""Apify Actor entry point for site_check: one website's PDFs, checked for four basics.

Input (see .actor/input_schema.json): siteUrl and/or pdfUrls, maxPages, maxPdfs.
Output: one dataset row per PDF, the report as the REPORT record (Markdown) and the
counts as the SUMMARY record. Reads public pages only, honouring robots.txt.

Apache-2.0 licensed. Made by MV2 of Munim, Inc. with AI agents.
"""

import asyncio
import logging

from apify import Actor

import site_check as sc

MAX_PDF_URLS = 200


def clamp(value, low, high, default):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        site = (inp.get("siteUrl") or "").strip()
        pdf_urls = inp.get("pdfUrls") or []
        if isinstance(pdf_urls, str):
            pdf_urls = pdf_urls.splitlines()
        pdf_urls = [u for u in pdf_urls if isinstance(u, str) and u.strip()][:MAX_PDF_URLS]
        if not site and not pdf_urls:
            raise ValueError("Give a siteUrl or at least one PDF link in pdfUrls.")
        pages = clamp(inp.get("maxPages"), 0, 30, 8)
        pdfs = clamp(inp.get("maxPdfs"), 1, 50, 8)
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        Actor.log.info("Checking %s and %d PDF links", site or "no website", len(pdf_urls))
        result = await asyncio.to_thread(sc.run, site, pdf_urls, pages, pdfs)
        for row in sc.dataset_rows(result):
            await Actor.push_data(row)
        await Actor.set_value("REPORT", sc.markdown(result))
        await Actor.set_value("SUMMARY", result["summary"])
        await Actor.set_status_message(sc.status_line(result))


if __name__ == "__main__":
    asyncio.run(main())
