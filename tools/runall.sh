#!/bin/bash
# usage: tools/runall.sh <outdir> [bench...]
# Generates (nombench --byfile) and runs every configuration of the given
# benchmarks (default: all) once, in base mode (nom -o3, no --trans/--sync),
# with the runtime binary $NOM (default: nom from setpath.sh). Then reruns
# every failing configuration with GC_DONT_GC=1: a configuration that passes
# then fails only because of the record allocation bug (bugs/BUGS.md, B1).
# Writes <outdir>/summary.txt (configs/ok per benchmark), nogc_summary.txt,
# <bench>.bad.txt (failing configurations) and <bench>.nogc.txt (failing
# configurations that still fail with GC off, with their last error line).
# Environment: NOM, J (parallel runs, default 16), TO (timeout, default 300).
OUT=$(realpath -m "$1"); shift
T=$(dirname "$(realpath "$0")"); G=$(dirname "$T")
BENCHES=${*:-$(cd "$G" && ls -d */ | tr -d / | grep -v -x -e tools -e bugs)}
mkdir -p "$OUT"
cd /data/workspace/monnom && . ./setpath.sh > /dev/null 2>&1
export NOM=${NOM:-$(command -v nom)} TO=${TO:-300}
J=${J:-16}
for b in $BENCHES; do
  D=$G/$b; P=$(basename "$D"/*.mnp .mnp); export P D
  rm -rf "$D"/.BM_*
  nombench --path "$D" --project "$P" --byfile > "$OUT/$b.gen.txt" 2>&1
  ls -d "$D"/.BM_* | xargs -P "$J" -I{} bash -c 'cd "{}" && timeout $TO $NOM -p "{}" -o3 $P > out1.txt 2> err1.txt; echo $? > exit1.txt'
  : > "$OUT/$b.bad.txt"; total=0; ok=0
  for d in "$D"/.BM_*; do
    total=$((total+1))
    if diff -q <(tail -n +3 "$d/out1.txt") "$D/expected.txt" > /dev/null; then ok=$((ok+1))
    else echo "$(basename "$d") exit=$(cat "$d/exit1.txt")" >> "$OUT/$b.bad.txt"; fi
  done
  echo "$b configs=$total ok=$ok" | tee -a "$OUT/summary.txt"
  [ -s "$OUT/$b.bad.txt" ] || continue
  awk '{print $1}' "$OUT/$b.bad.txt" | xargs -P $((J / 4 + 1)) -I{} bash -c 'cd "$D/{}" && GC_DONT_GC=1 timeout $TO $NOM -p "$D/{}" -o3 $P > out_nogc.txt 2> err_nogc.txt; echo $? > exit_nogc.txt'
  : > "$OUT/$b.nogc.txt"; n=0; fixed=0
  for c in $(awk '{print $1}' "$OUT/$b.bad.txt"); do
    n=$((n+1)); d=$D/$c
    if diff -q <(tail -n +3 "$d/out_nogc.txt") "$D/expected.txt" > /dev/null; then fixed=$((fixed+1))
    else echo "$c exit=$(cat "$d/exit_nogc.txt") $(cat "$d/out_nogc.txt" "$d/err_nogc.txt" | grep -v '^\s*$' | grep -v -- --- | tail -2 | tr '\n' ' ' | cut -c1-160)" >> "$OUT/$b.nogc.txt"; fi
  done
  echo "$b failing=$n pass_without_gc=$fixed still_fail=$((n-fixed))" | tee -a "$OUT/nogc_summary.txt"
done
awk '{split($2,a,"=");split($3,c,"=");t+=a[2];o+=c[2]} END{print "TOTAL configs="t" ok="o}' "$OUT/summary.txt"
