# Runtime bugs found by the GTP benchmark run of 2026-10-27

All configurations of all 20 benchmarks were run once in base mode (`nom -o3`, no `--trans`/`--sync`) with the runtime snapshot `nom-snapshot/nom-500c674c-20261027` (built from monnom commit `500c674c`, sha1 `5f1efe59…`). **4287 of 7938 configurations print the expected result.** The per-benchmark counts are in the README; the raw lists are in `results-500c674c/`.

Each bug below has a test function in `GtpBugs.mn`. Each test runs in its own process:

```bash
gtp-benchmark-monnom/bugs/1027/run_test.sh                        # all tests, nom from setpath.sh
NOM=$PWD/nom-snapshot/nom-500c674c-20261027 gtp-benchmark-monnom/bugs/1027/run_test.sh
gtp-benchmark-monnom/bugs/1027/run_test.sh Test_InvokeRecord -- -o3 --trans
```

On the snapshot, all 8 tests fail. A fixed runtime or compiler makes the corresponding test print `PASS`.

## How the failures were attributed

1. Every failing configuration was rerun with `GC_DONT_GC=1`. 2629 of the 3651 failures then pass. For the four benchmarks checked (acquire, dungeon, forth, fsmoo), an `LD_PRELOAD` shim that pads every `GC_malloc` by 64 bytes, with the GC still on, fixes exactly the same configurations. So these are all bug B1.
2. For the remaining 1022 failures, the failing JIT function was found by running the configuration under gdb (break on `NOM_RT_Fail`, or the SIGSEGV). An `INTEL_JIT_PROFILER64` agent library logged the address and name of every JIT-compiled function. Then the construct was rebuilt in a small program.

| Benchmark | Failing | Pass with GC off (B1) | Remaining failures |
|---|---|---|---|
| acquire | 270 | 108 | 162: 36 `Cast failed!` (G1), 126 segfaults (U2) |
| dungeon | 329 | 59 | 270: 132 B2, 48 B4, 90 `Cast failed!` (U1) |
| forth | 180 | 176 | 4: B5 |
| fsm | 270 | 270 | — |
| fsmoo | 242 | 80 | 162: 126 B2, 36 B3 |
| gregor | 270 | 222 | 48: 30 B5, 18 B3 |
| jpeg | 348 | 348 | — |
| kcfa | 162 | 162 | — |
| lnm | 180 | 180 | — |
| mbta | 214 | 198 | 16: B5 |
| morsecode | 72 | 72 | — |
| quadT | 228 | 48 | 180: 72 B4, 108 segfaults in an interface call-tag (B5 shape) |
| quadU | 228 | 48 | 180: 72 B4, 108 segfaults (same as quadT) |
| suffixtree | 81 | 81 | — |
| synth | 270 | 270 | — |
| take5 | 163 | 163 | — |
| zordoz | 144 | 144 | — |
| sieve, snake, tetris, zombie | 0 | | |

A configuration that fails because of B1 could hide a second bug only if that bug also disappeared with GC off. The "pass with GC off" column therefore counts configurations whose only bug is B1.

## Runtime bugs (B)

### B1: record allocations are too small (`Test_RecordFieldsGC`)
- **Symptom:** segfaults, `Dictionary entry not found`, `Invalid binary operation on non-primitive operand!`, `Cast failed!` and wrong results, all depending on when the GC runs. This is behind 2629 of the 3651 failures and appears in 17 benchmarks.
- **Cause:** the record layout is `StructuralValueHeader | dictionary pointer | char WrittenTags[n] | Fields[n]` (`RecordHeader::GetLLVMType(fieldCount)`). `CPP_NOM_RECORDALLOC` (`Runtime/NomVMInterface.cpp`) allocates only `RecordHeader::SizeOf() + 8 * (n + typeargs)`, and `SizeOf()` uses the layout with zero tag bytes. The last `ceil(n / 8)` words of every record lie past the end of the GC block. Boehm does not trace them, and the next allocation can overlap them. Also, `RecordHeader::GenerateReadField(builder, obj, Value *index)` uses `GetLLVMType()` (zero tags), so a dynamic field access uses a different offset from `GenerateReadField`/`GenerateWriteField` with a field count.
- **Repro:** keep one record that holds a list, allocate 200 000 more, read the first one. It works with `GC_DONT_GC=1` or with padded `GC_malloc`.

### B2: `this` in a nested record's field initializer is the new record (`Test_ThisInRecordInitializer`)
- **Symptom:** in a record method, `new(dyn fst = this, …) { … }` stores the *new* record in `fst`. Later calls on `fst` fail with `Dictionary entry not found` and `Tried to load invokable value from field, but value has no lambda method!`. This breaks dungeon (`cell.mn`) and fsmoo (`automata.mn`, `MatchPair`).
- **Cause:** `RecordHeader::GenerateConstructorCode` sets `(*env)[0] = newmem` (register 0 is `this`) before it compiles the field-initializer instructions, so they read the new record instead of the enclosing `this`.
- **Workaround in source:** `dyn me = this; return new(dyn fst = me, …)`.

### B3: a record cast to two interfaces aborts with `UNIMPLEMENTED!` (`Test_RecordTwoInterfaces`)
- **Symptom:** after a record has been cast to `IA` and then to `IB`, the next interface call aborts with `UNIMPLEMENTED!`. This affects fsmoo (where the pair record from B2 is cast to both `IAutomatonPair` and `IAutomaton`) and gregor.
- **Cause:** the second cast turns the record's cast data into a cast list (tag bit 1). `NomInterfaceCallTag` jumps to an `UNIMPLEMENTED!` block for that case (`IR/CallTags/NomInterfaceCallTag.cpp`, `multiCastListBlock`).

### B4: a record with a `this` method cannot be invoked (`Test_InvokeRecord`)
- **Symptom:** `d(3, 4)` on `new { public fun this(dyn p, dyn n) : dyn { … } … }` aborts with `Given value is not invokable!`. The benchmark generator emits such records for classes that have a `this` method and other methods (dungeon's directions, quadT/quadU `Ocm`).
- **Cause:** `EnsureDynamicMethodInstruction::GenerateGetBestInvokeDispatcherDyn` accepts only values whose vtable has a raw-invoke entry (lambdas). Records with a `this` method don't get one.

### B5: a typed record field initialized from a `dyn` value is not cast (`Test_TypedRecordField`)
- **Symptom:** `new(ISym sub = v) { … sub.Chars() … }` with a `dyn` record `v` segfaults on the first interface call through `sub`. This appears in forth, gregor and mbta (where the record `new(IMBTA mbtaSubways = …, ITextList disabled = …)` in `main.mn` crashes in `MONNOM_RT_ICT_IMBTA…Station`). quadT/quadU crash in the same way in `MONNOM_RT_ICT_IVal…Kind`, which is likely the same bug (not reduced separately).
- **Cause:** the value is stored in the typed field without a cast, so the record never gets cast data. The interface call-tag reads that cast data (`StructuralValueHeader::GenerateReadCastData`), finds null, and dereferences it (`RTClassType::GenerateReadClassDescriptorLink`) without checking it.

## Benchmark-generator bug (G)

### G1: record fields get the type of their initializer, not of the class field
- **Symptom:** acquire's 36 `Cast failed!` configurations (all with a structural `admin.mn`). The record that replaces the `Inspector` class is compiled with fields of type `DecisionNil` and `PlayerNil` (visible in its JIT name `STRUCT_666$$…$CDecisionNil_0$$$$.$CPlayerNil_0…`), where the class declares `IDecisionList decisions` and `IPlayerList eliminated`. Writing `decisions = new DecisionCons(…)` in `Place` then fails the field cast.
- The `.mn` files that nombench writes into `.BM_*` show these fields as `dyn`, so they don't match the `.mnil` that is run. Recompiling a configuration's `.mn` files with `nomc` gives a different program. The bug can't be written as a source test, because the type checker rejects such code.

## Unresolved (U)

- **U1 (dungeon, 90 configurations, `Cast failed!`):** `Utils.Random(IRandomBox r, Int n)` calls `r.Next()` on the typed class `RandomBox`. The class's IMT stub `MONNOM_RT_IMT_RandomBox_0_9` calls `MONNOM_RT_ICT_IRandomBox_0$$$Next$$0$$/0/CInt_0$$$`, the record-style interface call-tag, which then fails its cast check on a class object. Repro: `.BM_CCCCCCCSCCSSSCCCCCCDIIIIIIIIIICCIIIIIIIIIIIICCCCCCCCCCCCCCCCCCCCCCC`. Not reproduced in a small program (one class plus one record implementing the same interface works).
- **U2 (acquire, 126 configurations, segfault):** all have a structural `admin.mn`. The one inspected crashes in `State.StateEliminate` reading `s.Board()` on the inspector record's `currentState` field. They are probably related to G1 (same record) but not confirmed. Repro: `.BM_DSLCCCCCCCCCCCLCCCCCCKKKKKLKKKKKKKKKKCCCCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKCCCSSCCCCCCCSDCCCLLCCSCCCCCCCCCCCDLCCCCCCCCCCCCSSSC`.

## Side findings (S), found while writing the repros

These don't affect the benchmarks (the ports avoid these constructs), but they have tests too:

- **S1 `Test_ErrorMessage`:** `ERROR("msg")` prints `ERROR!` instead of `msg`.
- **S2 `Test_VoidReturn` [compile]:** `return;` in a `Void` method crashes `nomc` with a `NullReferenceException`.
- **S3 `Test_InvokeRecordField` [compile]:** invoking a record field inside a record method (`fn(x)`) crashes `nomc` with a `NotImplementedException`. Copying it to a local first (`dyn g = fn; g(x)`) works.
- Not testable as a function: if the **last statement of the entry method `Main.Main`** is `ERROR(...)`, the JIT aborts with LLVM's `Cannot get value when an error exists!` assertion. The same `ERROR` at the end of any other `Void` method is fine.
