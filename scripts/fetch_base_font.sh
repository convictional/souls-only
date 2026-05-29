#!/usr/bin/env bash
# Fetch the OFL base font (Jost, geometric single-story) and instance it to a
# static Regular. The variable font is gitignored; build reads
# base/Jost-Regular.ttf. Run from the repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv/bin"
URL="https://github.com/google/fonts/raw/main/ofl/jost/Jost%5Bwght%5D.ttf"

mkdir -p "$ROOT/base"
echo "downloading Jost (OFL) ..."
curl -sL -o "$ROOT/base/Jost-Variable.ttf" "$URL"

echo "instancing to static Regular ..."
"$VENV/fonttools" varLib.instancer "$ROOT/base/Jost-Variable.ttf" \
  wght=400 -o "$ROOT/base/Jost-Regular.ttf"

echo "done: base/Jost-Regular.ttf"
