#!/bin/bash
# usage: tools/check.sh <benchdir>  -- re-compare out1.txt of all configs with expected.txt
D=$(realpath "$1"); total=0; ok=0; bad=""
for d in "$D"/.BM_*; do
  total=$((total+1))
  if [ -f "$d/out1.txt" ] && diff -q <(tail -n +3 "$d/out1.txt") "$D/expected.txt" > /dev/null; then ok=$((ok+1)); else bad="$bad $(basename $d)"; fi
done
echo "configs=$total ok=$ok"; [ -n "$bad" ] && echo "BAD:$bad" | head -c 3000; echo
