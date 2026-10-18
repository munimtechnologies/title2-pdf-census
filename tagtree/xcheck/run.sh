#!/bin/sh
# tagtree-xcheck, first run (pre-registered in docs/tagtree-xcheck-prereg.md): the same 600
# cohort sites and per-site PDF choice as tagtree-reach-v1 (title2-pdf-census 0.2.2: public pages
# only, robots.txt honoured, 1 s between requests to a site); each chosen PDF is read by tagtree
# (pdfminer.six) and by xcheck's pypdf reader from the same bytes. Writes after every site.
set -u
cd "$(dirname "$0")"
mkdir -p /out
[ -f tagtree.py ] || sh setup.sh || exit 1
sha256sum census.py tagtree.py xcheck.py > /out/code-sha256.txt
python -c "import pdfminer, pypdf; print('pdfminer.six', pdfminer.__version__, 'pypdf', pypdf.__version__)" >> /out/code-sha256.txt
date -u +%Y-%m-%dT%H:%M:%SZ > /out/started-at.txt
python xcheck.py run --census census.py --out-dir /out --sites 600 --workers 4 --max-minutes 150 \
  || echo "run stopped early" >&2
python xcheck.py summarize --out-dir /out
