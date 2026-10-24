#!/bin/bash
# usage: tools/classify.sh <benchdir> -- prints, per configuration, the variant of each source file
# (classes: T typed, U untyped, S structural (records/lambdas); interfaces: I typed, J untyped, K removed)
# followed by the exit code and the result status (ok/BAD) of out1.txt.
D=$(realpath "$1")
files=$(grep -o 'file name="[^"]*"' "$D"/*.mnp | sed 's/file name="//;s/"//' | grep -v -f <(grep -o '<libraryfiles>.*' "$D"/*.mnp | grep -o 'name="[^"]*"' | sed 's/name="//;s/"//') )
for d in "$D"/.BM_*; do
  line=""
  for f in $files; do
    src="$D/$f"; gen="$d/$f"
    v=""
    if grep -q '^\s*\(public \)\?\(class\|interface\)\|^class\|^interface' "$src"; then
      nc=$(grep -c '^class' "$src"); ni=$(grep -c '^interface' "$src")
      gc=$(grep -c '^class' "$gen"); gi=$(grep -c '^interface' "$gen")
      hasdyn=$(grep -c '\bdyn\b' "$gen")
      if [ "$nc" -gt 0 ]; then
        if [ "$gc" -lt "$nc" ]; then v="${v}S"; elif [ "$hasdyn" -gt 0 ] && grep -q '^class' "$gen" && ! grep -q 'interface' "$gen" && [ "$(grep -c ': dyn' "$gen")" -gt 0 ]; then v="${v}U"; else v="${v}T"; fi
      fi
      if [ "$ni" -gt 0 ]; then
        if [ "$gi" -eq 0 ]; then v="${v}K"; elif grep -q ': dyn\|(dyn' "$gen"; then v="${v}J"; else v="${v}I"; fi
      fi
    fi
    line="$line $f=$v"
  done
  ok=BAD; [ -f "$d/out1.txt" ] && diff -q <(tail -n +3 "$d/out1.txt") "$D/expected.txt" > /dev/null && ok=ok
  echo "$(basename $d)$line exit=$(cat $d/exit1.txt 2>/dev/null) $ok"
done
