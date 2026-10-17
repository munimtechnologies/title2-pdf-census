#!/bin/sh
# tagtree-orphans, first run (pre-registered in docs/tagtree-orphans-prereg.md): tagtree 0.1.0 on the
# PDF attached to veraPDF issue #1629 (structure elements unreachable from StructTreeRoot).
set -u
cd "$(dirname "$0")"
mkdir -p /out /data/orphans
[ -f tagtree.py ] || sh setup.sh || exit 1
sha256sum tagtree.py orphans.py > /out/code-sha256.txt
python -c "import pdfminer, pypdf; print('pdfminer.six', pdfminer.__version__, 'pypdf', pypdf.__version__)" >> /out/code-sha256.txt
python orphans.py --data-dir /data/orphans --out-dir /out
