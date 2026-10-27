#!/bin/bash
# usage: bugs/run_test.sh [TestName] [-- NOM_FLAGS...]
# Runs every test of GtpBugs.mn in its own process (or only TestName), so
# a crash cannot hide other results. Each run keeps only that test's
# # BEGIN/# END block and its call in Main.
# NOM selects the runtime binary (default: nom from setpath.sh), e.g.
#   NOM=$PWD/nom-snapshot/nom-500c674c-20261027 bugs/run_test.sh
# NOMC selects the compiler. Default flag: -o3.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
NAME=""
if [ $# -gt 0 ] && [ "$1" != "--" ]; then NAME=$1; shift; fi
[ "$1" = "--" ] && shift
FLAGS=("$@")
[ ${#FLAGS[@]} -eq 0 ] && FLAGS=(-o3)

cd "$ROOT" && . ./setpath.sh > /dev/null 2>&1
NOM=${NOM:-nom}
if [ -n "$NAME" ]; then
  if ! grep -q "Main.$NAME();" "$HERE/GtpBugs.mn"; then
    echo "unknown test $NAME"; exit 2
  fi
  TESTS=$NAME
else
  TESTS=$(grep -o 'Main\.Test_[A-Za-z0-9_]*();' "$HERE/GtpBugs.mn" | sed 's/Main\.//; s/();//')
fi

pass=0; total=0
for T in $TESTS; do
  total=$((total+1))
  W=$(mktemp -d)
  cp "$HERE/GtpBugs.mnp" "$W/"
  awk -v name="$T" -v keep="Main.$T();" '
    /# BEGIN Test_/ { skip = ($3 != name) }
    skip { if ($0 ~ /# END Test_/) skip = 0; next }
    /# TESTS-BEGIN/ {inside=1; print; next}
    /# TESTS-END/ {inside=0}
    inside && index($0, "Main.Test_") && !index($0, keep) {next}
    {print}' "$HERE/GtpBugs.mn" > "$W/GtpBugs.mn"
  if ! ${NOMC:-nomc} -p "$W" --project GtpBugs > "$W/compile.txt" 2>&1 ||
     ! grep -q "Done!" "$W/compile.txt"; then
    echo "$T: FAIL (compiler) $(grep -m1 -o '[A-Za-z.]*Exception[^.]*' "$W/compile.txt")"
    rm -rf "$W"; continue
  fi
  OUT=$(cd "$W" && timeout 120 $NOM -p "$W" "${FLAGS[@]}" GtpBugs 2>&1)
  STATUS=$?
  if echo "$OUT" | grep -q "^$T: PASS"; then
    echo "$T: PASS"; pass=$((pass+1))
  elif echo "$OUT" | grep -q "^$T: FAIL"; then
    echo "$OUT" | grep -m1 "^$T: FAIL"
  else
    MSG=$(echo "$OUT" | grep -v '^\s*$' | grep -v -- '---' |
          grep -E 'rror|Abort|UNIMPL|dumped|Assert|not found|invokable|Cast' |
          tail -2 | tr '\n' ' ')
    echo "$T: FAIL (exit $STATUS) $MSG"
  fi
  rm -rf "$W"
done
echo "passed $pass of $total"
