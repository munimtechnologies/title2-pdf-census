#!/bin/sh
# Setup for tagtree-xcheck (v1 job): the same pypdf and pdfminer.six versions as tagtree-reach-v1,
# tagtree.py exactly as committed for tagtree-reach (90fe0ec, SHA-256 checked) and the census
# crawler exactly as released at v0.2.2.
set -u
cd "$(dirname "$0")"
pip install -q "pypdf[crypto]==6.21.1" "pdfminer.six==20260107" || exit 1
python -c "import pypdf, pdfminer; print('pypdf', pypdf.__version__, 'pdfminer.six', pdfminer.__version__)"
get() {
  python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])" "$1" "$2" \
    || { echo "could not fetch $1" >&2; exit 1; }
}
get "https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/90fe0eccc65d918f8458af7e20a7508f54ee6265/tagtree/tagtree.py" tagtree.py
get "https://raw.githubusercontent.com/munimtechnologies/title2-pdf-census/v0.2.2/census.py" census.py
echo "d49fbe0b7eb62dbdac182fe972ea5e27489fbacf22f8732bd5f0cda0e3c94fab  tagtree.py" | sha256sum -c - || exit 1
sha256sum census.py tagtree.py xcheck.py test_xcheck.py
