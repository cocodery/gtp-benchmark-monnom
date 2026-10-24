#!/bin/bash
# usage: tools/mapping.sh <benchdir> -- writes configmappings.csv with identity rows
D=$(realpath "$1")
{ echo "Config,Mapping"; for d in "$D"/.BM_*; do c=$(basename "$d"); c=${c#.BM_}; echo "$c,$c"; done; } > "$D/configmappings.csv"
wc -l < "$D/configmappings.csv"
