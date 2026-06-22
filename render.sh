#!/usr/bin/env bash
# Render a resume profile and publish it as a GitHub release.
#
#   bash render.sh            # render base.yaml
#   bash render.sh research   # merge base + profiles/research.yaml, then render
#
# Source (base.yaml + profiles/) lives in git; rendered artifacts are
# distributed as releases tagged <profile>-vYYYY.MM.DD and are not committed.
set -euo pipefail

PROFILE="${1:-base}"

# 1. Resolve the source YAML (merge an overlay if a profile was named).
if [ "$PROFILE" = "base" ]; then
  SRC="base.yaml"
else
  OVERLAY="profiles/${PROFILE}.yaml"
  [ -f "$OVERLAY" ] || { echo "No such profile: $OVERLAY" >&2; exit 1; }
  mkdir -p .build
  SRC=".build/${PROFILE}.yaml"
  python merge.py base.yaml "$OVERLAY" > "$SRC"
fi

# 2. Render the chosen assets straight into out/<profile>/ (absolute paths so
#    they land here regardless of where $SRC lives). PNG gets a _N page suffix.
ASSETS="out/${PROFILE}"
rm -rf "$ASSETS"; mkdir -p "$ASSETS"
A="${PWD}/${ASSETS}/Arnav_Rastogi_${PROFILE}"
rendercv render "$SRC" \
  -pdf "${A}.pdf" -html "${A}.html" -md "${A}.md" -png "${A}.png"
cp "$SRC" "${ASSETS}/Arnav_Rastogi_${PROFILE}.source.yaml"
# rendercv still drops a rendercv_output/ (typst intermediates) next to $SRC.
rm -rf rendercv_output "$(dirname "$SRC")/rendercv_output"
echo "Assets:"; ls "$ASSETS"

# 4. Commit any source changes so the release snapshots the real source.
git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "render ${PROFILE} ($(date +%Y-%m-%d))"
fi
git push -q

# 5. Cut a dated release (uniquified by time if the day's tag already exists).
DATE="$(date +%Y.%m.%d)"
TAG="${PROFILE}-v${DATE}"
if gh release view "$TAG" >/dev/null 2>&1; then
  TAG="${PROFILE}-v${DATE}-$(date +%H%M)"
fi
gh release create "$TAG" \
  --title "${PROFILE} resume — ${DATE}" \
  --notes "Rendered from ${SRC} on ${DATE}." \
  "$ASSETS"/*

echo "-> released ${TAG}"
