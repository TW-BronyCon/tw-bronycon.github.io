#!/usr/bin/env bash
set -euo pipefail

source_2026=$1
source_2027=$2
output=$3

for source in "$source_2026" "$source_2027"; do
  test -s "$source/index.html"
  test -s "$source/en/index.html"
done

mkdir -p "$output/2026" "$output/2027"
cp -R "$source_2026/." "$output/2026/"
cp -R "$source_2027/." "$output/2027/"
cp -R site/. "$output/"
touch "$output/.nojekyll"
python3 scripts/sitemap.py "$output"
