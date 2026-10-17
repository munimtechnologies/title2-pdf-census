#!/bin/sh
# tagtree-verapdf, first run (pre-registered in docs/tagtree-verapdf-prereg.md): tagtree 0.1.0's
# reachability analysis on every PDF/UA-1 file of the veraPDF corpus at commit bb75f4f.
set -u
cd "$(dirname "$0")"
mkdir -p /out /data/verapdf
[ -f tagtree.py ] || sh setup.sh || exit 1
sha256sum tagtree.py validate.py > /out/code-sha256.txt
python -c "import pdfminer, pypdf; print('pdfminer.six', pdfminer.__version__, 'pypdf', pypdf.__version__)" >> /out/code-sha256.txt
python validate.py --data-dir /data/verapdf --out-dir /out
