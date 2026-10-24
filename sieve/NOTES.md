# sieve

Prime numbers via a stream library (GTP `sieve`, Ben Greenman).

## Module mapping

| Racket (typed/)  | MonNom        | Contents |
|------------------|---------------|----------|
| `streams.rkt`    | `streams.mn`  | interfaces `IStream` (struct `stream`), `IStreamThunk` (`(-> stream)`), `IUnfold` (the two values of `stream-unfold`), `INatList` (`(Listof Natural)`); classes `Stream`, `Unfold`, `NatNil`, `NatCons`; static class `Streams` (`make-stream`, `stream-unfold`, `stream-get`, `stream-take`) |
| `main.rkt`       | `main.mn`     | lambda classes `CountFromThunk`, `SiftThunk`, `SieveThunk` (the three `lambda`s), static class `Main` (`count-from`, `sift`, `sieve`, `main`) |

## Deviations

- `stream-unfold` returns two values in Racket; here it returns an `IUnfold` object.
- `stream-get` is tail-recursive in Racket; here it is a `while` loop (same number of unfolds: `i+1`).
- `stream-take` (unused by `main`, as in the original) returns a cons list `INatList`.
- The thunk type `(-> stream)` is the custom interface `IStreamThunk` and not the builtin
  `Fun<IStream>`: the benchmark generator does not devolve project types that appear as type
  arguments inside instance-method signatures (`fun Rest() : Fun<IStream>` stays `Fun<IStream>`
  when `IStream` is removed, and the configuration then fails to type-check and aborts `nombench`).
- `primes` is a module-level definition in Racket, so it is built before the timer starts; the
  timed region is `(stream-get primes 6666)`, as in `(time (main))`.
- Input size is the original (`N-1 = 6666`).

## Expected output

`66919` (the 6667th prime), from the Typed Racket version with `(void ...)` replaced by
`(displayln ...)` in a scratch copy of `main.rkt`.

## Results

- Fully typed: about 2.2 s (Racket typed: 2.2 s).
- `nombench --byfile`: 27 configurations (`streams.mn` 3 class variants x 3 interface
  variants, `main.mn` 3 variants), all print `66919`.

## Comparison with `experiments/monnom/sieve`

The older hand-written version computes `stream-get primes 9999` (prints `104729`) instead of
the GTP input 6666, accesses the `Stream` class fields directly (no `stream-unfold`, no
`stream-take`, no interface for the stream struct) and is generated without `--byfile`
(384 configurations).
