# gregor

Unit tests of the gregor date/time library (GTP `gregor`): clock, ISO-8601 printing, and
differences between all pairs of 38 dates, with time zones from `base/tzinfo`.

## Module mapping

| Racket | MonNom | Contents |
|--------|--------|----------|
| `core-adapter.rkt`, `gregor-adapter.rkt`, `tzinfo-adapter.rkt`, `base/types.rkt` | `types.mn` | `IYMD`, `IHMSN`, `IDate`, `ITime`, `IDateTime`, `IMoment`, `ITz`, `ITzOffset`, `ITzResult` (tzoffset/tzgap/tzoverlap), resolvers, `IClock`, `IParams`, plus `IText`, `IRat`, `IBig` |
| (builtins) + `base/tzinfo` | `lib.mn` | `Text`/`Txt` (strings, `~r`), `RatS`/`Q` (exact rationals), `BigS` (bignum result), `TzS`, `Params` (parameters), the tzinfo port (`TzOffsetS`, `TzGapS`, `TzOverlapS`, `Interval`, `Zone`, `ZoneinfoSource`, `Tzinfo`), benchmark harness (`ConstClock`, `Results`) |
| `core-structs.rkt`, `gregor-structs.rkt`, `hmsn.rkt`, `ymd.rkt` | `core.mn` | struct classes, static `Hmsn`, `Ymd` |
| `date.rkt`, `time.rkt`, `datetime.rkt` | `datetime.mn` | static `GDate`, `GTime`, `GDateTime` |
| `moment-base.rkt`, `moment.rkt`, `offset-resolvers.rkt`, `clock.rkt` | `moment.mn` | resolver closures, static `MomentBase`, `Resolvers`, `GMoment`, `Clock` |
| `difference.rkt`, `main.rkt` | `main.mn` | static `Difference`, `Main` |
| zoneinfo files | `tzdata.mn` | library file: intervals/offsets of America/New_York, America/Chicago, Etc/UTC |

13 typed modules are merged into 6 files to keep 486 configurations.

## Deviations

- Exact rationals (`Exact-Rational`) are mixed numbers whole + num/den with exact 128-bit
  intermediate products (`Q.MulDivMod`); `datetime-nanoseconds-between` produces bignums
  (year 9999 vs year 1), represented as days * NS/DAY + ns (`IBig`) and only used modulo P.
- Strings are `IText`; `~r` is reimplemented for the cases used (padding, `#:precision 9` of
  s + n/10^9).
- Parameters (`current-clock`, `current-timezone`, `current-tzinfo-source`) are fields of an
  `IParams` object; `parameterize` saves and restores them. Keyword/optional arguments are
  explicit. `current-timezone`'s initial value `(system-tzid)` is replaced by "Etc/UTC" (never
  used); `current-posix-seconds` (wall clock) errors if called (never called).
- tzinfo: the zone files are parsed by Racket offline and embedded (`tzdata.mn`); zones are built
  from that data on first use and memoized, as the original memoizes parsed files. UTC search
  compares `(floor t)` with integer bounds, which is equivalent for exact t.
- Exceptions (`raise-invalid-offset`, errors) stop the program (`ERROR`); never triggered.
- `main` checks the tests as the original and additionally accumulates checksums of the
  results (test count, ISO strings, `datetime<=?`, months/days/nanoseconds between,
  `moment=?`).
- Input: `(main 10 #t)` -> 200 iterations (typed Racket 2.7 s; MonNom 10 iterations: 0.12 s).

## Expected output

`2200 316800 117280650 148200 252412626 51609795 171235581 7600`, from the Typed Racket
version (scratch copy of `main.rkt` with the same checksums, 200 iterations).

## Results

- Fully typed: 2.4 s.
- `nombench --byfile`: 486 configurations. All 96 nominal configurations agree; 216 of 486
  agree in total. Every configuration with a structural `core.mn` or `lib.mn` fails (189
  segmentation faults, 81 runtime errors).
- Status: PARTIAL.
