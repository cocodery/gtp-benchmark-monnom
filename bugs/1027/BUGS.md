# Runtime bugs found by the GTP benchmark run of 2026-10-27

All configurations of all 20 benchmarks were run once in base mode (`nom -o3`, no `--trans`/`--sync`) with the runtime snapshot `nom-snapshot/nom-500c674c-20261027` (built from monnom commit `500c674c`, sha1 `5f1efe59…`). **4287 of 7938 configurations print the expected result.** The per-benchmark counts are in the README; the raw lists are in `results-500c674c/`.

Each bug below has a test function in `GtpBugs.mn`. Each test runs in its own process:

```bash
gtp-benchmark-monnom/bugs/1027/run_test.sh                        # all tests, nom from setpath.sh
NOM=$PWD/nom-snapshot/nom-500c674c-20261027 gtp-benchmark-monnom/bugs/1027/run_test.sh
gtp-benchmark-monnom/bugs/1027/run_test.sh Test_InvokeRecord -- -o3 --trans
```

On the snapshot, the first 8 tests fail. `Test_ManyRecordFields` (G1) and `Test_NoLambdaOpt` (S4) were added later. A fixed runtime or compiler makes the corresponding test print `PASS`. A test whose block line ends in `[flags: …]` gets those runtime flags as well (`Test_NoLambdaOpt` runs with `--nolambdaopt`). `run_test.sh` sources `setpath.sh` from the repository root itself. Until 2026-10-29 it looked in `gtp-benchmark-monnom/` instead, so it only worked when `PATH` was already set.

## How the failures were attributed

1. Every failing configuration was rerun with `GC_DONT_GC=1`. 2629 of the 3651 failures then pass. For the four benchmarks checked (acquire, dungeon, forth, fsmoo), an `LD_PRELOAD` shim that pads every `GC_malloc` by 64 bytes, with the GC still on, fixes exactly the same configurations. So these are all bug B1.
2. For the remaining 1022 failures, the failing JIT function was found by running the configuration under gdb (break on `NOM_RT_Fail`, or the SIGSEGV). An `INTEL_JIT_PROFILER64` agent library logged the address and name of every JIT-compiled function. Then the construct was rebuilt in a small program.

| Benchmark | Failing | Pass with GC off (B1) | Pass with B1 + B4 fix | Remaining failures |
|---|---|---|---|---|
| acquire | 270 | 108 | **270** | — (the 36 `Cast failed!` were G1, the 126 segfaults U2; both are B1's `fieldCount` bug) |
| dungeon | 329 | 59 | 167 | 162, all with B2's message: the 132 B2, and 30 of the 90 U1, which now get past B4 and hit B2. The 48 B4 and the other 60 U1 pass |
| forth | 180 | 176 | 176 | 4: B5 |
| fsm | 270 | 270 | **270** | — |
| fsmoo | 242 | 80 | 80 | 162: 126 B2, 36 B3 |
| gregor | 270 | 222 | 222 | 48: 30 B5, 18 B3 |
| jpeg | 348 | 348 | **348** | — |
| kcfa | 162 | 162 | **162** | — |
| lnm | 180 | 180 | **180** | — |
| mbta | 214 | 198 | 198 | 16: B5 |
| morsecode | 72 | 72 | **72** | — |
| quadT | 228 | 48 | **228** | — (72 B4; of the 108 segfaults, 72 were B1's `fieldCount` bug and 36 then failed with B4) |
| quadU | 228 | 48 | **228** | — (same as quadT) |
| suffixtree | 81 | 81 | **81** | — |
| synth | 270 | 270 | **270** | — |
| take5 | 163 | 163 | **163** | — |
| zordoz | 144 | 144 | **144** | — |
| sieve, snake, tetris, zombie | 0 | | | |
| **total** | **3651** | **2629** | **3259** | **392** |

A configuration that fails because of B1 could hide a second bug only if that bug also disappeared with GC off. The "pass with GC off" column therefore counts configurations whose only bug is B1.

The "pass with B1 + B4 fix" column (2026-10-29) counts configurations that were rerun with the fixes, with the GC on, the same way `runconfigs.sh` runs them. These were run:
- with the B1 fix: every configuration in the "pass with GC off" column, and acquire's 162 remaining failures (G1, U2), which all pass;
- with the B1 and B4 fixes: all remaining failures of dungeon, quadT and quadU (630). Of these, 468 pass. The 162 dungeon configurations in the last column all fail with B2's message (`Tried to load invokable value from field, but value has no lambda method!`), including the 30 U1 configurations that used to fail with `Cast failed!`. The 276 that passed but were not attributed to B4 were run once more with the B1 fix alone, to split the two fixes (see B4).

So 3259 of the 3651 failures are fixed (bold: the whole benchmark now passes). The remaining failures of forth, fsmoo, gregor and mbta (B2, B3, B5) were not rerun. The runtime used was `500c674c` plus the fix. The exception is suffixtree, which was run with the current tree plus the fix, because its `.BM_*` folders were regenerated later and the `500c674c` runtime aborts while loading them.

## Runtime bugs (B)

### B1: record allocations are too small (`Test_RecordFieldsGC`)
- **Symptom:** segfaults, `Dictionary entry not found`, `Invalid binary operation on non-primitive operand!`, `Cast failed!` and wrong results, all depending on when the GC runs. This is behind 2629 of the 3651 failures and appears in 17 benchmarks.
- **Cause:** the record layout is `StructuralValueHeader | dictionary pointer | char WrittenTags[n] | Fields[n]` (`RecordHeader::GetLLVMType(fieldCount)`). `CPP_NOM_RECORDALLOC` (`Runtime/NomVMInterface.cpp`) allocates only `RecordHeader::SizeOf() + 8 * (n + typeargs)`, and `SizeOf()` uses the layout with zero tag bytes. The last `ceil(n / 8)` words of every record lie past the end of the GC block. Boehm does not trace them, and the next allocation can overlap them. Also, `RecordHeader::GenerateReadField(builder, obj, Value *index)` uses `GetLLVMType()` (zero tags), so a dynamic field access uses a different offset from `GenerateReadField`/`GenerateWriteField` with a field count.
- **Repro:** keep one record that holds a list, allocate 200 000 more, read the first one. It works with `GC_DONT_GC=1` or with padded `GC_malloc`.
- **How it is triggered:** `StructuralValueHeader` is 24 bytes, so the record header is 32 bytes (24 + 8 for the dictionary pointer). The tag bytes start at offset 32 and are padded to 8 bytes, so the fields start at `32 + alignTo(n, 8)`. A record with 1 field needs 48 bytes, but `CPP_NOM_RECORDALLOC` asked for `32 + 8 = 40`. The missing bytes are not always past the end of the block, because Boehm rounds the request up to 16 bytes (40 → 48). What breaks it is that Boehm, with interior pointers enabled (the default), adds one byte to every request and **never traces the last word of the block**. A small C test with `GC_MALLOC` shows this:

  | request | block | pointer stored at | after `GC_gcollect` |
  |---|---|---|---|
  | 40 | 48 | 40 (last word) | target collected |
  | 48 | 64 | 40 | kept |
  | 56 | 64 | 56 (last word) | target collected |
  | 56 | 64 | 48 | kept |

  So in `Test_RecordFieldsGC` the record's only field (`slots`, at offset 40 of a 48-byte block) is not traced. Once nothing else points to the `ArrayList`, the next collection frees it, and the memory is reused by the next `MkHolder` call. Which fields are lost depends on `n` and on Boehm's size classes (for example, with `n = 2` the request of 48 bytes gets a 64-byte block and the fields happen to be traced). Whether a program fails depends on when the GC runs, which explains why the symptoms vary so much.
- **Second problem, found while fixing:** `GenerateConstructorCode` and `NomRecordField::GenerateRead` passed `hasRawInvoke` (a `bool`) as the `fieldCount` argument of `GenerateWriteField`/`GenerateReadField`. With lambda optimization on, that is `GetLLVMType(1)`. This has the same field offset as `GetLLVMType(n)` only when `alignTo(n, 8) = 8`, so it only shows with more than 8 fields. With 10 fields, the constructor and field reads use offset 40, while `NomRecordField::GenerateWrite` (which passes `Fields.size()`) uses 48. The constructor's `memset` of the 10 tag bytes (offsets 32–41) then overwrites the low bytes of field 0. Also, a write in a record method is not seen by the next read: `f9 = 90; return f9;` returns the old value. This was checked with the allocator fix but not this one: printing `f0` crashed, and the write was lost. With `--nolambdaopt` it is `GetLLVMType(0)`: the constructor writes field 0 over the tag bytes, then the `memset` of the tags clears it. `--nolambdaopt` also aborted for an unrelated reason (S4); with S4 fixed, `Test_RecordFieldsGC` and `Test_ManyRecordFields` pass with `--nolambdaopt` too.
- **Not a bug:** `GenerateReadField(builder, obj, Value *index)` uses the zero-tag layout, but its only caller (the dynamic-dispatch field entry in `RTVTable.cpp`) passes an index that already includes `fieldsOffset = (offset of Fields in GetLLVMType(n) − offset in GetLLVMType()) / 8`, computed in `NomRecord.cpp`. So dynamic field access was already correct.
- **Fix:**
  - `CPP_NOM_RECORDALLOC` (`Runtime/NomVMInterface.cpp`) now allocates the size of `RecordHeader::GetLLVMType(numfields)` plus the type arguments: `tagsOffset + alignTo(numfields, 8) + 8 * (numfields + numtargs)`, where `tagsOffset` is taken once from the cached zero-field layout. It does not call `StructType::get` at allocation time, so JIT'd code never touches the `LLVMContext`.
  - `RecordHeader::GenerateConstructorCode` (`RuntimeData/Headers/RecordHeader.cpp`) and `NomRecordField::GenerateRead` (`IR/NomField.cpp`) now pass `Fields.size()` as the field count.
- **Verified:** `Test_RecordFieldsGC` passes with `-o3`, `-o0`, `-o3 --trans` and `-o3 --sync`, and still fails with only the allocator change reverted. A record with 10 fields (constructor writes, method reads and writes, dynamic reads, 200 000 more allocations with GC on) gives the right values in all modes.
- **Benchmarks:** all 2629 configurations that failed only because of B1, in 17 benchmarks, now print the expected result with the GC on (`nom -o3`, as `runconfigs.sh` runs them). So do acquire's 162 G1/U2 configurations, which were the `fieldCount` part. The `.mnil` files match different runtimes, so the runs used two builds. The suffixtree `.BM_*` folders were regenerated on 2026-10-28 at 09:31, and the `500c674c` runtime aborts while loading them (`terminate ... char const*`), with or without the fix, so suffixtree's 81 configurations were run with the current tree plus the fix. All other configurations were run with `500c674c` plus the fix. B1 is not involved in that abort. The table above has the per-benchmark counts.

### B2: `this` in a nested record's field initializer is the new record (`Test_ThisInRecordInitializer`)
- **Symptom:** in a record method, `new(dyn fst = this, …) { … }` stores the *new* record in `fst`. Later calls on `fst` fail with `Dictionary entry not found` and `Tried to load invokable value from field, but value has no lambda method!`. This breaks dungeon (`cell.mn`) and fsmoo (`automata.mn`, `MatchPair`).
- **Cause:** `RecordHeader::GenerateConstructorCode` sets `(*env)[0] = newmem` (register 0 is `this`) before it compiles the field-initializer instructions, so they read the new record instead of the enclosing `this`.
- **Workaround in source:** `dyn me = this; return new(dyn fst = me, …)`.

### B3: a record cast to two interfaces aborts with `UNIMPLEMENTED!` (`Test_RecordTwoInterfaces`)
- **Symptom:** after a record has been cast to `IA` and then to `IB`, the next interface call aborts with `UNIMPLEMENTED!`. This affects fsmoo (where the pair record from B2 is cast to both `IAutomatonPair` and `IAutomaton`) and gregor.
- **Cause:** the second cast turns the record's cast data into a cast list (tag bit 1). `NomInterfaceCallTag` jumps to an `UNIMPLEMENTED!` block for that case (`IR/CallTags/NomInterfaceCallTag.cpp`, `multiCastListBlock`).

### B4: a record with a `this` method cannot be invoked (`Test_InvokeRecord`)
- **Symptom:** `d(3, 4)` on `new { public fun this(dyn p, dyn n) : dyn { … } … }` aborts with `Given value is not invokable!`. The benchmark generator emits such records for classes that have a `this` method and other methods (dungeon's directions, quadT/quadU `Ocm`).
- **Cause:** `EnsureDynamicMethodInstruction::GenerateGetBestInvokeDispatcherDyn` accepts only values marked as having a raw invoke. It then calls the raw-invoke pointer stored in the object header, with the receiver and the lambda call-tag. With the default `RTConfig_UseLambdaOffset`, the mark is bit 3 of the vtable pointer: an invokable value's descriptor starts 8 bytes into its 256-aligned global. Lambdas get that 8-byte prefix and store their body as the raw invoke. `NomRecord::createLLVMElement` hard-coded `bool hasRawInvoke = false;`, so a record's descriptor never got the prefix, and `GenerateConstructorCode` was called without a raw-invoke pointer. Meanwhile `NomRecord::GetHasRawInvoke()` returned true for every record (`NomLambdaOptimizationLevel > 0`), which only feeds the vtable `Flags` used when the lambda offset is turned off. So `Flags` claimed that all records were invokable, and the pointer bit said none were.
- **Fix** (`IR/Data/NomRecord.cpp`, `.h`):
  - New `NomRecord::GetRawInvokeMethod()` returns the `this` method (the one with an empty name). `GetHasRawInvoke()` is now true only when the record has one (and lambda optimization is on), so `Flags` and the pointer bit agree.
  - `createLLVMElement` uses `GetHasRawInvoke()` for the descriptor prefix and passes the `this` method's dynamic dispatcher (`NOMMON_RT_DD_<method>`, already built by `GetDynamicDispatcherLookup`) to `GenerateConstructorCode` as the raw invoke. That dispatcher already has the IMT function type, checks the lambda call-tag for the arity, and calls the method with the record as receiver: the same contract as a lambda body.
  - A typed call through a functional interface (`interface IAdd { fun this(Int a, Int b) : Int; }`) passes the *interface* call-tag to the raw invoke instead. For the `this` dispatcher only, a call-tag mismatch now follows the lambda protocol (`NomLambdaBody`): if the tag is an interface call-tag (a function pointer), it is tail-called with the dispatcher as its first argument. The tag then converts the arguments and calls back with the lambda call-tag. A lambda call-tag of another arity (an odd constant) still gives "Called record method with invalid number of arguments!". A lambda would jump to that constant.
- **Verified:** `Test_InvokeRecord` passes with `-o3`, `-o0`, `-o3 --trans` and `-o3 --sync`. A wider test gives the right results in the same four modes:
  - a record with `this`, a field and another method: invoke, named call and field read;
  - the record held in another record's field, invoked after reading it back and directly through the field (`h.fn(2, 2)`);
  - a 10-field record whose `this` writes a field;
  - a cast to a functional interface `IAdd` and a typed call through it;
  - a wrong arity: still an error;
  - a record without `this`: still "Given value is not invokable!".

  `experiments/monnom/function/bugs` passes 29 of 29 tests under `-o3`, `-o0` and `-o3 --trans`.
- **Compiler check:** a record's `this` method (named `""` by the parser, `Parser/Decls/MethodDecl.cs`) is found by a linear scan (`NomRecord::GetRawInvokeMethod`), and the dynamic-dispatch lookup takes the first entry with a name. `nomc` used to accept two `this` methods in one record. The runtime then silently used the first one, and with different arities, a call matching the second one failed with "invalid number of arguments". `VisitStructExpr` (`TypeChecker/CodeTransformer.cs`) now rejects a second `this` method, next to the existing duplicate-field check: "A record can have only one this method; this record already has one (file:line:col)". `nomc` and nombench were rebuilt with the change, and both test suites give the same results as before in `-o3`, `-o3 --trans` and `-o3 --nolambdaopt`.
  - Named record methods with the same name are still accepted, because overloading by signature is meant to be allowed. The runtime does not support it yet. In a record with `Get(dyn x)` and `Get(dyn x, dyn y)`, a call matching the first one works, both dynamically and through an interface. A call matching the second one (`ITwo.Get(1, 2)` through an interface, and also `r.Get(1, 2)`) fails with "Called record method Get with invalid number of arguments!". The lookup matches by name, finds the first `Get`, and that method's dispatcher rejects the arity. Supporting it would need one dispatcher per name that branches on the call-tag's arity across the overloads. No benchmark has such a record.
- **Benchmarks** (`500c674c` plus the B1 and B4 fixes, all remaining failures of dungeon, quadT and quadU, 630 configurations):
  - All 192 B4 configurations pass (dungeon 48, quadT 72, quadU 72).
  - quadT and quadU's 108 segfaults each pass too. Rerun with the B1 fix alone, 72 of them pass, so they were B1's `fieldCount` bug. The other 36 then fail with `Given value is not invokable!`, so B4 was behind them.
  - dungeon's U1 was B4 as well; see U1. quadT and quadU now pass completely.

  The table above has the counts.

### B5: a typed record field initialized from a `dyn` value is not cast (`Test_TypedRecordField`)
- **Symptom:** `new(ISym sub = v) { … sub.Chars() … }` with a `dyn` record `v` segfaults on the first interface call through `sub`. This appears in forth, gregor and mbta (where the record `new(IMBTA mbtaSubways = …, ITextList disabled = …)` in `main.mn` crashes in `MONNOM_RT_ICT_IMBTA…Station`). quadT/quadU crash in the same way in `MONNOM_RT_ICT_IVal…Kind`, which is likely the same bug (not reduced separately).
- **Cause:** the value is stored in the typed field without a cast, so the record never gets cast data. The interface call-tag reads that cast data (`StructuralValueHeader::GenerateReadCastData`), finds null, and dereferences it (`RTClassType::GenerateReadClassDescriptorLink`) without checking it.

## G1: writes to a record with more than 8 fields go to the wrong slot (`Test_ManyRecordFields`)

G1 was first listed as a benchmark-generator bug. It is a runtime bug: the `fieldCount` problem described under B1, and it is fixed together with B1. It is not the same issue as G1 in `experiments/monnom/function/bugs/BUGS.md` (generic instance methods, already fixed).

- **Symptom:** acquire's 36 `Cast failed!` configurations, all with a structural `admin.mn`, fail the same way with or without the GC.
- **What was wrong in the first analysis:**
  - The JIT name `STRUCT_666$$…$CDecisionNil_0$$$$.$CPlayerNil_0…` encodes the record constructor's *initializer argument types* (`NomRecord`'s `initializerArgTypes`), not the field types. The generator binds `decisions__bm_fresh_22 = new DecisionNil()` in a `letvar` and passes it in, so that argument has static type `DecisionNil`.
  - The fields themselves are `dyn`, both in the generated `.mn` and in the tree nombench compiles: the `Struct` case of `FullDevolution.cs` runs every field through `FullDevolutionVisitorUntyped.VisitFieldDecl`. Plain `nomc` compiles the same `letvar … in new(dyn decisions = …)` pattern correctly.
- **Cause:** the record that replaces `TurnS` (`admin.mn`) has 14 fields. As described under B1, the constructor and `NomRecordField::GenerateRead` passed `hasRawInvoke` as `fieldCount`, so they used the field offset of a 1-field record (40). `NomRecordField::GenerateWrite` passed `Fields.size()`, which with 14 fields gives offset 48. So `decisions = new DecisionCons(…)` in a record method writes one slot too far, into the next field (`eliminated`). The next read of `decisions` still sees the old value, and the overwritten field later holds a value of the wrong type, hence `Cast failed!`. The offsets don't depend on the GC, which is why turning the GC off did not help.
- **Test:** `Test_ManyRecordFields` builds a 10-field record whose method does `decisions = Main.MkCons(decisions); return decisions.Len();` twice, then reads `cash` and `eliminated`.
  - Expected: `1 2 7 0`.
  - With the B1 allocator fix but the old `fieldCount` calls: `FAIL got 0 0 7 1`. The write is lost and lands in `eliminated`.
  - With the fix: `PASS` with `-o3`, `-o0` and `-o3 --trans`.
- **Fix:** the `fieldCount` part of the B1 fix (`RecordHeader::GenerateConstructorCode` and `NomRecordField::GenerateRead` now pass `Fields.size()`).
- **Benchmarks:** the G1 repro is `.BM_DSLCCCCCCCCCCCLCCCCCCIIIIILIIIIIIIIIICCCCIIIIIIIIIIIIIIIIIIIIIIIIIIIIICCCSSCCCCCCCSDCCCLLCCSCCCCCCCCCCCDLCCCCCCCCCCCCSSSC`.
  - With `500c674c` rebuilt unpatched, it fails with `Cast failed!` with the GC on and off.
  - With `500c674c` plus the fix, it prints the expected result with the GC on and off.
  - All 36 G1 configurations and all 126 U2 configurations pass with the fix.
  - `Test_ManyRecordFields` can't be run on `500c674c`: its runtime aborts while loading `.mnil` files from the current `nomc`.

## Unresolved (U)

- **U1 (dungeon, 90 configurations, `Cast failed!`), resolved: it was B4.** With the B4 fix, 60 of the 90 pass (including the repro below), and the other 30 now fail with B2's message instead. With the B1 fix alone, all 60 still fail with `Cast failed!`. The original analysis: `Utils.Random(IRandomBox r, Int n)` calls `r.Next()` on the typed class `RandomBox`. The class's IMT stub `MONNOM_RT_IMT_RandomBox_0_9` calls `MONNOM_RT_ICT_IRandomBox_0$$$Next$$0$$/0/CInt_0$$$`, the record-style interface call-tag, which then fails its cast check on a class object. Repro: `.BM_CCCCCCCSCCSSSCCCCCCDIIIIIIIIIICCIIIIIIIIIIIICCCCCCCCCCCCCCCCCCCCCCC`. Not reproduced in a small program (one class plus one record implementing the same interface works).
- **U2 (acquire, 126 configurations, segfault), resolved:** all have a structural `admin.mn`. The one inspected crashes in `State.StateEliminate` reading `s.Board()` on the `currentState` field of the `TurnS` record (14 fields). It was the same bug as G1: a field write in a record method went to the next slot, so a field later held a value of another type. All 126 configurations print the expected result with the B1/G1 fix. Repro: `.BM_DSLCCCCCCCCCCCLCCCCCCKKKKKLKKKKKKKKKKCCCCKKKKKKKKKKKKKKKKKKKKKKKKKKKKKCCCSSCCCCCCCSDCCCLLCCSCCCCCCCCCCCDLCCCCCCCCCCCCSSSC`.

## Side findings (S), found while writing the repros

These don't affect the benchmarks (the ports avoid these constructs), but they have tests too:

- **S1 `Test_ErrorMessage`:** `ERROR("msg")` prints `ERROR!` instead of `msg`.
- **S2 `Test_VoidReturn` [compile]:** `return;` in a `Void` method crashes `nomc` with a `NullReferenceException`.
- **S3 `Test_InvokeRecordField` [compile]:** invoking a record field inside a record method (`fn(x)`) crashes `nomc` with a `NotImplementedException`. Copying it to a local first (`dyn g = fn; g(x)`) works.
- **S4 `Test_NoLambdaOpt` [flags: `--nolambdaopt`], fixed:** with `--nolambdaopt`, every program aborted while the runtime loaded (`terminate called after throwing an instance of 'std::exception*'`). Details:
  - **Cause:** `RTVTable::GenerateFindDynamicDispatcherPair` (the path that loads an invokable value from a field) and `EnsureDynamicMethodInstruction::GenerateGetBestInvokeDispatcherDyn` (`v(…)` on a `dyn` value) always read the raw-invoke pointer. `RefValueHeader::GenerateReadRawInvoke` throws when lambda optimization is off, and the field path is compiled for the standard library's interfaces at startup. Beyond the crash, the mode was unfinished: without lambda optimization a lambda gets no raw-invoke pointer (`StructuralValueHeader` even drops the slot), its dynamic-dispatch list is empty and its IMT slots are error stubs, so nothing could invoke it. The intended design is visible in `NomClass.cpp` and `NomInterface.cpp`, which keep `this` methods in the method tables only without lambda optimization: `this` is dispatched as an ordinary method named `""`.
  - **Fix**, without lambda optimization only:
    - `RTVTable::GetFindInvokeDispatcherFunction` builds a per-module function `MONNOM_RT_FIND_INVOKE_DISPATCHER` that looks up the dynamic dispatcher of `""` in a value. Both invoke paths call it instead of reading the raw-invoke pointer. It is a function, not inline code, because the lookup contains the field path, which would otherwise generate itself recursively.
    - `NomLambda`: the dispatch list is `[{"", body}, end]`, with the `""` bucket starting at the body entry. The body already has the dispatcher signature and checks the lambda call-tag. The IMT slots forward to the interface call-tag (`MONNOM_RT_LAMBDA_IMT_FORWARD`, like a record's IMT entries), which then goes through the record call-tag and the `""` lookup.
    - `NomRecord`: records already have a `""` dispatcher for their `this` method. `GetHasRawInvoke()` (the vtable flag and pointer bit, meaning "invokable", as for lambdas) no longer depends on the level, and the raw-invoke pointer is stored only with lambda optimization.
    - `CPP_NOM_GetIMTTransition` returns early for a value without a `NomRecord` (a lambda reached through a functional interface with `--trans`). It has no IMT graph, and its descriptor is constant. This was a segfault in `NomIMTGraph::GetIMTGraph(nullptr)`.
  - **Test:** a dynamic invoke of a lambda, a lambda in a record field, a record with `this`, and typed calls through a functional interface on a record and on a lambda. With the old code it aborts (exit 134). With the fix it passes in every mode, with and without `--nolambdaopt`. `experiments/monnom/function/bugs` passes 29 of 29 under `-o3`, `-o0`, `-o3 --trans`, `-o3 --sync`, `-o3 --trans --sync` and each of these with `--nolambdaopt`. In the same 10 modes this file's tests give the same results: only B2, B5, S1 and S3 fail. `function/imtshare` prints `68010` with `--trans`, `--trans --sync` and both with `--nolambdaopt`.
- Not testable as a function: if the **last statement of the entry method `Main.Main`** is `ERROR(...)`, the JIT aborts with LLVM's `Cannot get value when an error exists!` assertion. The same `ERROR` at the end of any other `Void` method is fine.
