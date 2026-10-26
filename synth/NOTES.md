# synth

Music synthesis with lazy arrays (GTP `synth`, Vincent St-Amour; a copy of parts of
`math/array`): a melody sequenced with a sawtooth wave, mixed with a drum loop, converted to
16-bit samples.

## Module mapping

| Racket | MonNom | Contents |
|--------|--------|----------|
| `both/typed-data.rkt` + builtins | `types.mn` | `IIdx` (Indexes), `IFloatVec`, `IBoolBox`, `IProcBox`, `IProcVec`, `IIndexProc`, `IThunk`, `ISetProc`, `IIndexesThunk`, `IArray`, `IFloatFn`, `IFloat2Fn`, `IWave`, `IWeightedSignal`, `INote`, `IIdxCell`, `IDrumSamples`, `IRng`, lists |
| (Racket builtins) | `lib.mn` | vectors, boxes, thread cell, `WeightedSignal` (`list`), `Builtins` (rounding, `exact-floor`), `Rng` (Racket's PRNG), lists |
| `data.rkt`, `array-struct.rkt`, `array-utils.rkt` | `array.mn` | `ArrayS`, `MutableArray`, the array closures, static `ArrayStruct`, `ArrayUtils` |
| `array-broadcast.rkt`, `array-transform.rkt` | `array-ops.mn` | `StretchProc`, `AppendProc`, static `ArrayBroadcast`, `ArrayTransform` |
| `synth.rkt`, `mixer.rkt`, `sequencer.rkt`, `drum.rkt` | `synth.mn` | sawtooth, map, mix, note, drum closures; static `Synth`, `Mixer`, `Sequencer`, `Drum` |
| `main.rkt` | `main.mn` | static `Main` |

Ten modules are merged into six files (486 configurations).

## Deviations

- The parameters `array-strictness` (set to `#f` by synth.rkt before any array is built, never
  changed) and `array-broadcasting` (`#t`, or `'permissive` inside `mix`) are a constant and an
  explicit argument. `Settable-Array`/`Mutable-Array` are a class implementing `IArray`.
- `random` is an exact port of Racket CS's generator; the Racket reference was seeded with
  `(random-seed 4242)` in `drum.rkt` (the original is unseeded, so its output is
  nondeterministic), and MonNom seeds the same way. `bass-drum`/`snare` are built in `Main`
  before the timed region (module instantiation); the snare draws random numbers lazily during
  the run, as in Racket.
- `(expt (expt 2 1/12) k)` is `(2.0 ** (1.0 / 12.0)) ** (k + 0.0)` (Float `**`, i.e. C `pow`)
  and `(expt 2 bits-per-sample)` is `2 ** bits`; `exact-floor`/`round` of flonums are computed
  by binary search (no Float->Int conversion).
- Closure fields are copied to a local before being called (benchmark-generator limitation).
- `main` prints the length, sum and a rolling hash of the emitted samples.
- Input: LOOPS 6 -> 18 (MonNom LOOPS 6: 0.6 s).

## Expected output

`4010688 39395542133 36560312`, from the Typed Racket version (scratch copy with the seed, the
checksums and LOOPS 18; 21 s).

## Results

- Fully typed: 1.7 s.
- `nombench --byfile`: 486 configurations. All 96 nominal configurations agree; 144 of 486 agree
  in total. Every configuration with a structural `lib.mn`, `array.mn` or `synth.mn` fails
  (289 segmentation faults, 53 runtime errors).
- Status: PARTIAL.
