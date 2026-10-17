#!/bin/sh
# tagtree-reach, first run (pre-registered in docs/tagtree-reach-prereg.md): 600 cohort sites
# chosen by hash, crawled with title2-pdf-census 0.2.2 (public pages only, robots.txt honoured,
# 1 s between requests to a site), then up to 3 tagged, text-bearing PDFs per site analysed for
# structure-tree reachability. Writes after every site, so a run cut short still summarizes.
set -u
cd "$(dirname "$0")"
mkdir -p /out
[ -f census.py ] || sh setup.sh || exit 1
sha256sum census.py tagtree.py > /out/code-sha256.txt
python -c "import pdfminer, pypdf; print('pdfminer.six', pdfminer.__version__, 'pypdf', pypdf.__version__)" >> /out/code-sha256.txt
date -u +%Y-%m-%dT%H:%M:%SZ > /out/started-at.txt
python tagtree.py run --census census.py --out-dir /out --sites 600 --workers 6 --pages 8 --pdfs 8 \
  --per-site 3 --delay 1.0 --max-minutes 120 || echo "run stopped early" >&2
python tagtree.py summarize --out-dir /out
