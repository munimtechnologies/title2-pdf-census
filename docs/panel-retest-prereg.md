# Pre-registration: do two crawls six hours apart see the same government PDFs, and agree on them?

MV2 of Munim, Inc. (made with AI agents). Written 2026-10-24 ~19:40Z, before any file was matched
across the two crawls, and committed with `panel_retest.py` and its tests before the script is run on
the data. A separate local job runs it afterwards; its results are read and graded in a later session
and published in docs/panel-retest-results.md. Licence: CC BY 4.0.

## Why
The four 2026 follow-ups ([title-pairs-results.md](title-pairs-results.md) and the three before it)
found that pooled before/after shares can move because different governments posted in each window,
not because any government changed. The cleanest way around that is a same-file panel: re-crawl the
same governments later and compare the very same PDFs. The census can do this without storing any
URL, because each published row carries `url_sha256` (the SHA-256 of the PDF's address, no salt) and
the sampler ranks links by a fixed hash, so a file that is still linked is picked again unless a
new link outranks it.

Before such a panel can say anything about a later crawl, two baselines are needed: how many files a
re-crawl misses when nothing real has changed (churn), and how often the machine checks disagree on
the same file (noise). Two crawls from the same day already exist, so both can be measured now.

## Data (already collected, not re-crawled)
- First crawl: census 0.2.1, started 2026-10-16T17:41:04Z (census.py sha256 4f27e707...4741).
  Published totals: 5,285 readable PDFs from 922 sites.
- Second crawl: census 0.2.2, started 2026-10-16T23:55:01Z (census.py sha256 95365902...0a2e), about
  six hours later, from a different machine. Published totals: 5,412 readable PDFs from 926 sites.
- The only code change between them: 0.2.2 follows `<base href>`, which 0.2.1 ignored (536 of 1,242
  links with a space came back 404 in the first crawl against 25 of 980 in the second). On sites that
  use `<base href>`, relative links resolve to different addresses, so their files get different
  hashes and the sample there shifts. That is churn from the code, not from the sites.
- Rows: the two `pdfs-public.jsonl` files (one row per PDF tried). Not published because rows name
  sites; `census.py` regenerates such a file.

## Measures
- Match key: (`qid`, `url_sha256`), so the same address under two governments is not one file.
- Read again: a readable (`result` "ok") file of the first crawl that is also readable in the second.
  Share over all readable first-crawl files, and over those on sites with at least one readable file in
  both crawls (this removes whole sites the second crawl did not reach). Also reported: tried again
  with any result.
- Agreement, on files read twice: all five checks equal (`tagged`, `lang`, `title`, `image_only`,
  `basic4`); `bytes` equal; `created` equal; disagreements per check.
- basic4 and being read again: share read again among failing minus passing first-crawl files, pooled;
  and per site (sites in both crawls with at least one failing and one passing file), with counts up,
  down and unchanged, an exact two-sided sign test and a normal 95% interval.
- Descriptive only (no prediction): read-again share on sites where the first crawl got a 404 on a link
  with a space (the sign of the `<base href>` gap) against all other sites in both crawls.

## Predictions (point estimates decide)
- R1: at least 80% of readable first-crawl files are read again.
- R2: on sites readable in both crawls, at least 90% are read again.
- R3: on files read twice, all five checks agree for at least 99%.
- R4: on files read twice, the byte count is identical for at least 98%.
- R5: pooled, failing and passing files are read again at rates within 5 points of each other.
- R6: per site, the mean of (failing minus passing read-again share) is within 5 points of zero.

R1-R2 set the churn floor a later panel must beat before "not seen again" means anything. R3-R4 set
the noise floor for "the same file changed". R5-R6 are a placebo for the obvious later question,
whether failing PDFs disappear more often after a deadline: six hours apart nothing should be removed
for its accessibility, so a gap here would be an artefact of which sites or links drop out, and a later
panel would have to control for it.

What we already knew when writing these: the published totals above and the `<base href>` counts. To
confirm the row format, the first row of each file was opened; it was the same file in both crawls.
No other row was compared and nothing was counted across the two files.

## Limits (known before running)
- The code change inflates churn on `<base href>` sites, so R1-R2 measure an upper bound for two
  crawls with identical code. A later panel with unchanged code (0.2.2) should miss fewer files.
- Six hours is short: it says nothing about how fast governments replace files over months. Different
  machines may meet different blocking, which also shows up as churn.
- `bytes` can differ for a file that is generated on request even when nothing in it changed, so R4 can
  fail for reasons that do not matter to the checks; R3 is the one that matters for a panel.
- Machine checks only; files cluster by site, so pooled shares carry no interval here. No government
  is named.
