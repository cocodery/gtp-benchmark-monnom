# IMT transition comparison, 2026-11-01

**Superseded by `../../1101`.** The gains below include parallel GC that ran only in `--trans`, so they overstate the IMT, and synth in particular.

Six GTP tests chosen for heavy interface calls on records, timed in base, `--trans` and `--trans --sync`. `tables/<test>.md` has one row per variation, best first. `SUMMARY.md` has the per-test figures.

**Result: `--trans` is clearly faster on synth and fsm, about 10-14% at the median. fsmoo and quadT gain a little, morsecode does not change, and suffixtree gets 11% slower. No test needs lambda functions in IMT entries.**

| Test | Timed | Median base | Median trans | Median sync | Trans faster | Variations ≥5% faster | Variations ≥5% slower |
|---|---:|---:|---:|---:|---:|---:|---:|
| synth | 94 | 2.217 s | 1.915 s | 1.932 s | 13.9% | 92 | 2 |
| fsm | 75 | 1.203 s | 1.078 s | 1.082 s | 10.5% | 72 | 0 |
| quadT | 50 | 2.799 s | 2.726 s | 2.843 s | 3.3% | 16 | 1 |
| fsmoo | 98 | 1.094 s | 1.055 s | 1.056 s | 2.6% | 47 | 14 |
| morsecode | 34 | 4.174 s | 4.177 s | 4.162 s | -1.1% | 0 | 15 |
| suffixtree | 64 | 1.986 s | 2.237 s | 2.219 s | -11.4% | 0 | 54 |

"Trans faster" is the median of the per-variation percentages, so it can differ slightly from comparing the two median columns. Positive is faster.

Average runtime is the mean of the variations' medians, over the timed variations only. Each `tables/<test>.md` ends with the same figures in an average row.

| Test | Average base | Average trans | Average trans-sync | Trans vs base | Trans-sync vs base |
|---|---:|---:|---:|---:|---:|
| synth | 2.470 s | 2.079 s | 2.104 s | 15.8% faster | 14.8% faster |
| fsm | 1.189 s | 1.069 s | 1.075 s | 10.2% faster | 9.6% faster |
| quadT | 2.722 s | 2.558 s | 2.664 s | 6.0% faster | 2.1% faster |
| fsmoo | 1.072 s | 1.031 s | 1.035 s | 3.9% faster | 3.5% faster |
| morsecode | 4.109 s | 4.227 s | 4.237 s | 2.9% slower | 3.1% slower |
| suffixtree | 1.964 s | 2.234 s | 2.245 s | 13.7% slower | 14.3% slower |

## Setup

| | |
|---|---|
| Source | commit `47f9db09` |
| Runtime | Release build (`-O3`) of that commit; generated variations from `nomc` at `641c0a38`, whose compiler sources are unchanged in `47f9db09` |
| Runs | 3 passes, 9 runs per variation, median per mode; 3735 runs, all exited 0 and matched `expected.txt` |
| Load | 4 jobs at a time, each pinned to two P-cores; mode order rotates per pass |

`python3 run_imt.py <outdir> 3 <nom>` reruns the timing from `rates.csv`. `scripts/python/make_tables.py <outdir>` rebuilds the tables.

## How the tests were chosen

An instrumented scratch build counted calls into `CPP_NOM_GetIMTTransition`, by reason, with installing turned off. It is not in the repository.

1. 6 structural variations of each of the 21 tests were surveyed.
2. All 2241 variations of the six chosen tests were counted: `all-variations-slow-calls.csv`.
3. Timed: the 403 variations with at least 1M slow calls per second, plus the 2 lowest in each test as controls, 415 in total.

**The tables are not the whole of each test.** The other 1826 variations were not timed. Medians here describe variations that can benefit, not the test as a whole.

snake, lnm, kcfa, mbta and quadU were left out because rough timings showed `--trans` slower. Those timings came from the counting build, which inflates slow-path cost, so that evidence is weak.

## Do these tests need lambdas in IMT entries?

**No.** Across all 2241 variations and 33 billion slow-path calls, these counts were both zero:

| Case | Count | Meaning |
|---|---:|---|
| Lambda field | 0 | a record method held in a field, rejected by `CheckCallTagMethodExist` |
| Lambda object | 0 | receiver with no `NomRecord` |

Each of the 2241 was counted with `--trans --sync` and installing off. 675 of them have `L` variants. Those are `this`-only classes turned into lambdas, and they are called by raw invoke, which does not use IMT slots. The benchmark sources contain no lambdas, and the generator does not produce lambda-field records.

This holds with default flags. With `--nolambdaopt` lambdas do reach the record call-tag (see the comment in `CPP_NOM_GetIMTTransition`), but that was not measured. The survey of the other 15 tests also found zero, on samples only.

## What limits the gain

- **Entries work, but each new object still falls back.** On the top variation of each test, compiles were few (8 to 110) while 1-20% of slow calls remained, nearly all of them known transitions. That is the per-object cost described in `Runtime/IMT/CLAUDE.md`.

| Test | Top variation trans faster | Slow calls left |
|---|---:|---:|
| synth | 12.4% | 1.0% |
| morsecode | 3.2% | 4.6% |
| fsm | 12.8% | 7.2% |
| fsmoo | 11.8% | 7.2% |
| suffixtree | -24.9% | 11.6% |
| quadT | 5.5% | 19.5% |

- **`--trans` has a cost of its own.** Controls with almost no slow calls were slower in some tests: suffixtree -4.4% and -9.6%, synth -6.3% and -7.0%, quadT -1.9% and -5.6%. The likely cause, not tested, is that `--trans` turns the vtable and IMT reads into plain loads, so LLVM cannot hoist them out of loops. Reference results are also cast at the call site (`CallCheckedInstanceMethod.cpp`).
- **suffixtree is not explained.** Its loss is larger than its controls', and it leaves fewer slow calls than quadT, which gains. Its slowdown was not traced.

## Corrections to earlier reports

- The rough figures from this investigation, such as fsm 2.98 s to 1.48 s, came from the counting build and overstated the gain. Use the tables here.
- `Runtime/IMT/CLAUDE.md` still says `NomInterfaceCallTag` skips its cast for reference results. `8214e890` removed that skip, so with `--trans` a reference result that goes through the call-tag is now also cast at the call site.
