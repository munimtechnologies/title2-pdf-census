#!/bin/sh
# Setup for title2-pdf-census: pypdf (with AES support for encrypted-but-openable PDFs).
set -u
pip install -q "pypdf[crypto]>=5" || exit 1
python -c "import pypdf; print('pypdf', pypdf.__version__)"
