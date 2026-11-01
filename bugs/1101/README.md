# IMT transition comparison after the fixes, 2026-11-01

The same 415 variations as `../1031/imt`, timed in base, `--trans` and `--trans --sync`. `tables/<test>.md` has one row per variation, best first, and `SUMMARY.md` has the per-test figures.

**Result: suffixtree no longer loses time. It went from 13.7% slower than base to 4.0% faster. fsm, quadT, fsmoo and morsecode all improved too. synth lost its 15.8% gain, because that gain was parallel GC and not the IMT.**

| Test | Timed | Base (1031) | Trans (1031) | Base | Trans | Trans-sync | Trans vs base (1031) | Trans vs base | Trans ≥5% slower (1031) | Trans ≥5% slower |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| suffixtree | 64 | 1.964 s | 2.234 s | 1.601 s | 1.537 s | 1.546 s | -13.7% | **4.0%** | 54 | 1 |
| morsecode | 34 | 4.109 s | 4.227 s | 3.242 s | 3.100 s | 3.103 s | -2.9% | **4.4%** | 15 | 0 |
| fsmoo | 98 | 1.072 s | 1.031 s | 0.997 s | 0.916 s | 0.921 s | 3.9% | **8.1%** | 14 | 4 |
| fsm | 75 | 1.189 s | 1.069 s | 1.124 s | 0.994 s | 0.997 s | 10.2% | **11.5%** | 0 | 0 |
| quadT | 50 | 2.722 s | 2.558 s | 2.133 s | 2.000 s | 2.107 s | 6.0% | 6.2% | 1 | 4 |
| synth | 94 | 2.470 s | 2.079 s | 2.458 s | 2.421 s | 2.440 s | 15.8% | **1.5%** | 2 | 2 |

Times are the mean of the variations' medians. Positive percentages are faster than base.

## Setup

| | |
|---|---|
| Source | commit `47f9db09` plus the uncommitted changes below |
| Runtime | Release build (`-O3`) with clang-12 |
| Variations | the `.BM_*` folders used for `../1031/imt`; the compiler did not change |
| Runs | 3 passes, 9 runs per variation; 3735 runs, all exited 0 and matched `expected.txt` |
| Load | 4 jobs at a time, each pinned to two P-cores |

`python3 run_imt.py <outdir> 3 <nom>` reruns the timing, and `scripts/python/make_tables.py <outdir>` rebuilds the tables.

## Why suffixtree was slow

On the worst variation (`DDCCCSIIIIIIIIIIIIIIIIIIIICSSSDCCCCCSCCSSSCSSSSDSSCS`), a profile of the main thread during the timed window accounted for all of the 0.6 s lost:

| Cost | Base samples | Trans samples |
|---|---:|---:|
| Bridge (`CPP_NOM_GetIMTTransition` and its lookups) | 0 | 873 |
| Kernel | 1 | 214 |
| libc, mostly mutex lock and unlock | 6 | 132 |

There were two causes:

1. **Every new record paid for its transitions again.** It started on the root entries and took one bridge call per slot. suffixtree allocates 20M records.
2. **`--trans` ran a different GC.** Starting the worker called `GC_allow_register_threads`, which starts Boehm's marker threads and turns on allocator locking. Base had 1 thread and `--trans` had 17. `--sync` did this too, because the bridge created the worker even when it was not used.

## What changed

| Change | Files | Effect |
|---|---|---|
| New records start on the record's newest descriptor | `NomRecord.h`, `RecordHeader.cpp`, `NomVMIMTInterface.cpp`, header signatures | Bridge samples on the worst variation fell from 873 to 6 |
| The worker no longer uses the GC or the shared LLVM context; the main thread builds the IR | `NomIMTAsyncCompiler.cpp` | `--trans` uses the same serial GC as base, with 2 threads |
| Initial GC heap raised from 1 MB to 64 MB | `gcinclude_config.h` | Applies to every mode; see below |

Worst suffixtree variation, before the heap change:

| | Base | Old trans | New trans |
|---|---:|---:|---:|
| Pinned | 1.93 s | 2.54 s | 1.89 s |
| Unpinned | 1.93 s | 3.66 s | 1.90 s |

The unpinned row matters: `../1031/imt` was pinned, which hid most of this cost.

## Correction to the 1031 results

**The 1031 gains were partly parallel GC, not the IMT.** On one synth variation, old `--trans` took 2.33 s. With `GC_MARKERS=1` it took 2.90 s, the same as base, and IMT entries got almost no samples. So the 15.8% for synth was mostly marker threads running only in `--trans`. The figures here compare the two modes on the same GC, so they measure the IMT alone.

## Other ways to run faster

GC was about 40% of the timed window on the suffixtree variation, in both modes.

**Initial heap size, applied.** Median of 3, best and worst variation of each test, base and trans, against the 1 MB default:

| Initial heap | Geomean time | Worst case | RSS |
|---|---:|---:|---:|
| 16 MB | -9.2% | +2.5% | +7% |
| 32 MB | -12.5% | +2.3% | +15% |
| **64 MB** | **-14.9%** | **+2.4%** | **+29%** |
| 128 MB | -17.3% | +1.9% | +60% |

morsecode and suffixtree gain about 20% and quadT up to 42%. synth does not change. 64 MB was chosen because 128 MB adds 2 points for twice the extra memory. Set `GC_INITIAL_HEAP_SIZE` in the environment to try another size.

**Parallel marking, not applied.** With `GC_MARKERS=8` it is 4-5% faster by geomean, up to 18% on synth, but up to 6% slower on morsecode and suffixtree. It is left off so that base and `--trans` run the same GC. This was measured with a scratch switch and is not in the repository.

**Double cast, not fixed. This is the next thing to try.** With `--trans`, a reference result is cast at the call site even when `NomInterfaceCallTag` already cast it. On `fsmoo/.BM_DSSDDIIIIDDIIIIIIDSSDDCCDSSC` that is 299M casts against 231M. Fixing it means changing what `8214e890` set up to stop a crash, so it needs its own change and tests.

## Still open

- **4 fsmoo variations are about 21% slower.** They are the `DSS..IIII..IIIIIIDS..` rows at the bottom of `tables/fsmoo.md`. They do 30% more casts, as above. They also run 18 collections against 12 and spend twice as long in GC, although allocation counts are identical. Why is not known. They stay slower at heaps from 16 MB to 256 MB.
- **Variations with no slow calls are still up to 5-8% slower.** For example, the two fully typed suffixtree rows are 5% slower with 0.0M slow calls per second. They get nothing from the IMT, and pay for `--trans` anyway. Likely causes are plain vtable and IMT reads, and the call-site cast; neither was tested.
- **quadT sync is well behind async**, at 1.2% against 6.2%, because compiling on the main thread falls inside the timed window.

## Testing

- `run-function.sh --compare`: 9 of 9 pass, with identical output in all three modes.
- `imttransition` now reports `Installed: 1`, `Transitions: 0`, because later records start with the entry. `Runtime/IMT/CLAUDE.md` is updated.
- Building with GCC fails the `bugs` test on `Test_UnaryMinus` with an IR verification error. Unmodified `47f9db09` fails the same way, so this is not from these changes. The repo's `build/` was configured for GCC and has been reconfigured for clang-12, as `.claude/CLAUDE.md` says.
- Only the 415 selected variations were run. The other 1826 of these tests, and the other 15 tests, were not rerun.
