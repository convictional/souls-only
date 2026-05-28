#!/usr/bin/env bash
# Fetch the OFL base font (Inter, variable) and instance it to a static Regular.
# The variable font is gitignored; the instanced base/Inter-Regular.ttf is what
# build_font.py reads. Run from the repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv/bin"
URL="https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"

mkdir -p "$ROOT/base"
echo "downloading Inter (OFL) ..."
curl -sL -o "$ROOT/base/Inter-Variable.ttf" "$URL"

echo "instancing to static Regular ..."
"$VENV/fonttools" varLib.instancer "$ROOT/base/Inter-Variable.ttf" \
  wght=400 opsz=14 -o "$ROOT/base/Inter-Regular.ttf"

echo "done: base/Inter-Regular.ttf"
