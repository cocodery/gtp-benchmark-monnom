#!/bin/bash
# usage: tools/bench.sh <benchdir> [parallel=12] [timeout=600]
# 1. removes old configurations, 2. generates all configurations with
#    `nombench --byfile` (no runs), 3. runs every configuration once with
#    tools/runconfigs.sh (same command line as `nombench -r 1`, but in parallel and with
#    a timeout), 4. writes configmappings.csv.
D=$(realpath "$1"); P=$(basename "$D"/*.mnp .mnp); J=${2:-12}; TO=${3:-600}
T=$(dirname "$(realpath "$0")")
rm -rf "$D"/.BM_*
cd /data/workspace/monnom && . ./setpath.sh > /dev/null 2>&1
echo "== generating $P"
nombench --path "$D" --project "$P" --byfile 2>&1 | grep -v 'DONE!$' | grep -v '^   at ' | tail -20
echo "== generated $(ls -d "$D"/.BM_* | wc -l) configurations"
"$T/runconfigs.sh" "$D" "$P" "$J" "$TO"
"$T/mapping.sh" "$D" > /dev/null
