# IMT and GC changes, 2026-11-02

The same 415 selected variations as `../1101`, timed in base, `--trans` and `--trans --sync`. `tables/<test>.md` has one row per variation, best first. `SUMMARY.md` has the per-test figures.

**Result: synth, fsm and fsmoo run 12-17% faster than in `1101` in `--trans`, and the four fsmoo variations that were 21% slower than base are now 3-6% slower. synth's gain is in absolute time: it is still only 0.7% faster than base, because the speedup is in the GC that both modes share. morsecode and suffixtree are about 3% slower than in `1101`. quadT's lead over base shrank from 6.2% to 3.6%.**

| Test | Base, 1101 → 1102 | Trans, 1101 → 1102 | Trans change | Trans-sync | Trans vs base, 1101 → 1102 |
|---|---:|---:|---:|---:|---:|
| synth | 2.458 → 2.071 s | 2.421 → 2.058 s | 15.0% faster | 2.077 s | 1.5% → 0.7% |
| fsm | 1.124 → 0.951 s | 0.994 → 0.826 s | 16.9% faster | 0.832 s | 11.5% → 13.1% |
| fsmoo | 0.997 → 0.898 s | 0.916 → 0.805 s | 12.2% faster | 0.811 s | 8.1% → 10.4% |
| quadT | 2.133 → 1.939 s | 2.000 → 1.870 s | 6.5% faster | 1.993 s | 6.2% → 3.6% |
| morsecode | 3.242 → 3.294 s | 3.100 → 3.185 s | 2.7% slower | 3.183 s | 4.4% → 3.3% |
| suffixtree | 1.601 → 1.626 s | 1.537 → 1.586 s | 3.2% slower | 1.595 s | 4.0% → 2.5% |

Times are the mean of the variations' medians. Positive "trans vs base" is faster.

| Test | Variations ≥5% slower than base, 1101 → 1102 | ≥5% faster, 1101 → 1102 | Worst | Best |
|---|---:|---:|---:|---:|
| synth | 2 → 0 | 1 → 3 | -3.5% | 7.7% |
| fsm | 0 → 0 | 54 → 54 | -4.4% | 24.2% |
| fsmoo | 4 → 1 | 47 → 54 | -5.9% | 24.3% |
| quadT | 4 → 6 | 28 → 18 | -10.0% | 11.2% |
| morsecode | 0 → 0 | 16 → 9 | -1.2% | 10.2% |
| suffixtree | 1 → 0 | 18 → 13 | -3.7% | 12.7% |

## Setup

| | |
|---|---|
| Source | commit `c149e52f` plus the uncommitted changes below |
| Runtime | clang-12 build, run from a frozen copy of the binary |
| Runs | 3 passes, 9 runs per variation, median per mode; 3735 runs, all exited 0 and matched `expected.txt` |
| Load | 4 jobs at a time, each pinned to two P-cores; mode order rotates per pass |

`python3 run_imt.py <outdir> 3 <nom>` reruns the timing from `rates.csv`. `scripts/python/make_tables.py <outdir>` rebuilds the tables.

Being pinned to two cores limits the markers. Four variations timed unpinned, 3 runs each, agreed with the pinned results and showed no hidden slowdown:

| Variation (top of each test) | Old base | Old trans | New base | New trans |
|---|---:|---:|---:|---:|
| synth | 1.982 s | 1.909 s | 1.814 s | 1.702 s |
| suffixtree | 1.555 s | 1.352 s | 1.565 s | 1.385 s |
| morsecode | 3.104 s | 2.802 s | 3.128 s | 2.815 s |
| fsmoo | 0.911 s | 0.720 s | 0.805 s | 0.602 s |

## Why four fsmoo variations were 21% slower

It was not the IMT. A conservative stack scan was keeping dead lists alive.

`Main.Evolve` is not tail-recursive, so all 4000 frames stay on the stack. `pp = p.Payoffs()` is dead after `RelativeAverage`, but its pointer can stay in a callee-saved register. The recursive call's prologue then saves that register into the new frame, where Boehm treats it as a live pointer.

A census of reachable objects at collection 17 found 3938 lists of exactly 300 nodes, 56.7 MB in all, with no heap object pointing at them.

Whether a variation retains depended on inlining and register allocation, not on the mode. Many variations retained in both modes. The four slow ones retained in `--trans` only, so they looked like an IMT loss.

| Variation `DSSCCIIIICCIIIIIIDSSCCCCCSSC` | Base, 1101 | Trans, 1101 | Base, 1102 | Trans, 1102 |
|---|---:|---:|---:|---:|
| Run time | 0.648 s | 0.784 s | 0.659 s | 0.690 s |
| Live heap, last collection | 0.4 MB | 55.9 MB | 0.09 MB | 0.09 MB |
| GC time | 11.5 ms | 110 ms | 8.0 ms | 8.8 ms |

After the change, the sampled fsmoo and fsm variations keep under 1 MB and spend 7-12 ms in GC, down from 55-75 MB and about 110 ms in those that retained.

## Changes

1. **Clear callee-saved registers before self-recursive calls** (`ClearRegistersBeforeRecursion`, `NomJIT.cpp`). Applies to all modes.
2. **Start the GC markers in every mode** (`GC_start_mark_threads`, `Runtime.cpp`). This gives the parallel marking without the allocator locking that `GC_allow_register_threads` turns on. synth ran 10.7% faster, against 10.8% with locking. morsecode ran 1-2% slower, against 6% with locking.
3. **Cast results in the IMT entry, not at the call site** (`NomIMTUtils.cpp`, `CallCheckedInstanceMethod.cpp`). Each record call now casts once, and class objects do not cast at all. This cuts the cost of `--trans` on fully typed synth from about 7% to about 3%.

Change 3 also fixes a soundness bug. Old entries did not check primitive results, so a `dyn` method returning a string through `fun Get() : Int` gave `656027616575320` under `--trans --sync` and kept running. It now fails with `Cast failed!`.

The cast went through three steps, because each earlier form cost too much:

| Form of the entry cast | quadT top variation, trans |
|---|---:|
| Call-site cast (old, unsound for primitives) | 1.73 s |
| Full call-tag cast in every entry | 2.86 s |
| Inline closed cast, skipped if the method declares a subtype | 1.93 s |
| One compiled cast per return type (kept) | 1.76 s |

Inlining added about 240 ms of IR building to the main thread. Inlining only in entries with few call-tags did not beat the kept form overall.

## Checks

- `run-function.sh --compare`: 9 of 9 passed.
- `imttransition` IMT counters are unchanged.
- Scratch programs with wrong-typed results (`Int`, closed interface, generic `T`) fail a cast in all modes through installed entries. Their correct versions print the right values. They are not in the repository.

## Still open

- **synth against base.** The IMT gives it 0.7%. The earlier 15.8% was a GC difference between the modes, and `1101` explains that. Fully typed variations are still about 3% slower. An invariant vtable load would remove part of that, but it drops the top variation's gain from 6% to 1%, so it can only be applied where the receiver cannot be a record. That was not tried.
- **quadT.** Base gained more than `--trans`, and 6 variations are ≥5% slower than base, up from 4. The worst is 10.0% slower. Those entries now pay casts that were skipped before, and also compile one cast function per return type. How much each contributes was not separated.
- **morsecode and suffixtree are about 3% slower than in `1101`.** Both have small live heaps, so parallel marking costs more than it saves. That accounts for about 1.6%, the slowdown in base. On suffixtree the rest is likely the new result casts: the kept form was 5-9% behind old `--trans` on two variations. This was not measured separately.
- **What the register clearing misses.** Mutual recursion, recursion through interface or dynamic calls, and dead values in stack spill slots. Its cost on a call-heavy recursive program was not measured alone.
- **synth's 107 MB live heap** appears in every sampled variation and both modes. It was not checked whether the program needs all of it.
- Only the 415 selected variations were rerun, on this build.
