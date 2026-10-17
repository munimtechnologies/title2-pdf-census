#!/bin/sh
# Setup for tagtree-orphans (v1 job): the same PDF libraries as tagtree-reach-v1, and tagtree.py
# exactly as committed for that study (title2-pdf-census 90fe0ec), hashed so the results name their code.
set -u
cd "$(dirname "$0")"
pip install -q "pypdf[crypto]>=5" "pdfminer.six>=20231228" || exit 1
python -c "import pypdf, pdfminer; print('pypdf', pypdf.__version__, 'pdfminer.six', pdfminer.__version__)"
python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" \
  "https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/90fe0eccc65d918f8458af7e20a7508f54ee6265/tagtree/tagtree.py" tagtree.py \
  || { echo "could not fetch tagtree.py" >&2; exit 1; }
python tagtree.py --version
sha256sum tagtree.py orphans.py test_orphans.py
