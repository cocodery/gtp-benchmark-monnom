# GTP benchmark run of 2026-10-30, base mode

**All 7938 configurations of all 21 benchmarks print the expected result. No GTP bug was found in this run.**

At the 2026-10-27 run (`bugs/1027`), 4287 of 7938 passed. Every failure recorded there is gone.

## Setup

| | |
|---|---|
| Runtime | `nom-snapshot/nom-64543734-dirty-20261030`, sha1 `abd9caa0…`, Debug build |
| Source | commit `64543734` plus uncommitted changes, saved in `worktree-on-64543734.diff` |
| Mode | `nom -p <dir> -o3 <P>`, no `--trans`/`--sync` |
| Configurations | all deleted and regenerated with `nombench --byfile` in the benchmark folders |
| Run | 16 in parallel, 300 s timeout, one run per configuration |
| Duration | 21:29 to 23:59 |

The command was:

```bash
NOM=$PWD/nom-snapshot/nom-64543734-dirty-20261030 J=16 TO=300 \
  gtp-benchmark-monnom/tools/runall.sh gtp-benchmark-monnom/bugs/1030/results-64543734-dirty
```

`nom-snapshot/` is not tracked by git, so the binary exists only on this machine.

## Results

Times are seconds from each configuration's own timing line. They were measured under parallel load on a Debug build, so they show the spread between configurations but are not measurements for comparison. The "@1027" column is the pass count at `500c674c`.

| Benchmark | Configs | Pass | Pass @1027 | Min | Median | Max |
|---|---:|---:|---:|---:|---:|---:|
| acquire | 486 | 486 | 216 | 4.41 | 5.71 | 7.08 |
| dungeon | 486 | 486 | 157 | 1.03 | 1.54 | 1.95 |
| forth | 324 | 324 | 144 | 1.54 | 2.36 | 3.96 |
| fsm | 486 | 486 | 216 | 1.62 | 2.12 | 3.04 |
| fsmoo | 486 | 486 | 244 | 1.38 | 2.02 | 2.82 |
| gregor | 486 | 486 | 216 | 2.82 | 7.00 | 8.94 |
| jpeg | 486 | 486 | 138 | 1.16 | 1.76 | 2.44 |
| kcfa | 486 | 486 | 324 | 3.41 | 5.29 | 7.41 |
| lnm | 324 | 324 | 144 | 1.67 | 2.17 | 2.76 |
| mbta | 324 | 324 | 110 | 1.82 | 2.52 | 3.16 |
| morsecode | 216 | 216 | 144 | 7.04 | 9.14 | 11.02 |
| quadT | 324 | 324 | 96 | 2.81 | 4.22 | 6.12 |
| quadU | 324 | 324 | 96 | 2.20 | 3.16 | 4.80 |
| sieve | 27 | 27 | 27 | 3.64 | 4.68 | 6.64 |
| snake | 432 | 432 | 432 | 0.98 | 1.25 | 2.22 |
| suffixtree | 243 | 243 | 162 | 2.44 | 3.40 | 4.57 |
| synth | 486 | 486 | 216 | 2.16 | 3.91 | 6.33 |
| take5 | 486 | 486 | 323 | 1.27 | 1.74 | 2.43 |
| tetris | 432 | 432 | 432 | 1.78 | 3.19 | 7.65 |
| zombie | 162 | 162 | 162 | 1.57 | 2.01 | 2.41 |
| zordoz | 432 | 432 | 288 | 2.37 | 3.84 | 4.81 |
| **total** | **7938** | **7938** | **4287** | | | |

The result was checked beyond the pass count: every configuration exited with status 0, wrote nothing to stderr, and has an output file. Every `.gen.txt` shows two `DONE!` lines per configuration, so generation was complete.

`results-64543734-dirty/` holds `summary.txt`, the per-benchmark `.bad.txt` files (all empty) and the generator logs. No `.nogc.txt` files exist, because nothing failed and so nothing was rerun with the GC off.

## 1027 bug tests

`bugs/1027/run_test.sh` on the same snapshot: **12 of 12 tests pass.**

## Other findings

- **Not a GTP bug: the `bugs` functional test does not compile.** `experiments/monnom/function/bugs/BugTests.mn:921` calls `Main.Test_OverloadArgCount()`, added in `64543734`, but no such test is defined. It stops `run-function.sh bugs` and the no-argument `run_test.sh`. The other 29 tests all pass when run one at a time, and also in one process on a scratch copy without that line.
- **Generation is slow for quadT.** `nombench --byfile` took 28 minutes for its 324 configurations, and generation is serial.
- **`--trans` is not clean.** This run covers base mode only. See `bugs/1031`.
