#!/bin/sh
# Setup for tagtree-reach (v1 job): pypdf (the census's own PDF checks), pdfminer.six (marked
# content and the structure tree), and the census crawler exactly as released at v0.2.2, hashed
# so the results name their code.
set -u
cd "$(dirname "$0")"
pip install -q "pypdf[crypto]>=5" "pdfminer.six>=20231228" || exit 1
python -c "import pypdf, pdfminer; print('pypdf', pypdf.__version__, 'pdfminer.six', pdfminer.__version__)"
python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" \
  "https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/v0.2.2/census.py" census.py \
  || { echo "could not fetch census.py" >&2; exit 1; }
sha256sum census.py tagtree.py test_tagtree.py
