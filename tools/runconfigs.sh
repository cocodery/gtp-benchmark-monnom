#!/bin/bash
# usage: tools/runconfigs.sh <benchdir> <Project> [parallel=8] [timeout=300]
# Runs every .BM_* configuration exactly as nombench -r 1 does
# (nom -p <dir> -o3 <Project>, cwd=<dir>, stdout -> out1.txt), in parallel, with a timeout,
# then compares result lines (all but the timing line) with expected.txt.
D=$(realpath "$1"); P=$2; J=${3:-8}; TO=${4:-300}
cd /data/workspace/monnom && . ./setpath.sh > /dev/null 2>&1
export P TO
ls -d "$D"/.BM_* | xargs -P "$J" -I{} bash -c 'cd "{}" && timeout $TO nom -p "{}" -o3 $P > "{}/out1.txt" 2> "{}/err1.txt"; echo $? > "{}/exit1.txt"'
total=0; ok=0; bad=""
for d in "$D"/.BM_*; do
  total=$((total+1))
  if [ -f "$d/out1.txt" ] && diff -q <(tail -n +3 "$d/out1.txt") "$D/expected.txt" > /dev/null; then ok=$((ok+1)); else bad="$bad $(basename $d)"; fi
done
echo "configs=$total ok=$ok"
[ -n "$bad" ] && echo "BAD:$bad" | head -c 3000
echo
