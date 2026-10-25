#!/usr/bin/env bash
# Copy the shared LaTeX files into the overview and every project's docs/ folder,
# then build all PDFs. Run from anywhere:  bash docs/build_all.sh
set -euo pipefail
cd "$(dirname "$0")"                      # -> qml_portal/docs
SHARED="shared/qmlproject.sty shared/harvardqml.bst shared/references.bib"
mkdir -p pdf

build() {   # build <folder> <pdf name>
  cp $SHARED "$1/"
  if (cd "$1" && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex >/dev/null 2>&1); then
    cp "$1/main.pdf" "pdf/$2.pdf"
    (cd "$1" && latexmk -c >/dev/null 2>&1 && rm -f main.bbl)
    echo "built   $2"
  else
    echo "FAILED  $2  (see $1/main.log)"; exit 1
  fi
}

build overview 00-overview-four-quadrants
for dir in ../qml_projects/*/docs; do
  [ -f "$dir/main.tex" ] || continue
  slug=$(basename "$(dirname "$dir")")
  number=$(grep -m1 '^number' "$dir/../project.toml" 2>/dev/null | grep -o '[0-9]\+' || true)
  build "$dir" "$(printf '%02d' "${number:-0}")-$slug"
done
