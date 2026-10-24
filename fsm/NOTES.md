# fsm

Evolutionary game theory: a population of finite-state automata plays repeated prisoner's
dilemma rounds, the fittest reproduce (GTP `fsm`, Matthias Felleisen / Linh Chi Nguyen).

The project is called `GtpFsm`: the project name `Fsm` triggers the runtime's library-loader bug
described in `../forth/NOTES.md`.

## Module mapping

| Racket                        | MonNom          | Contents |
|-------------------------------|-----------------|----------|
| `both/automata-adapted.rkt`   | `types.mn`      | interfaces `ITransition`, `ITransitions` (`Transition*`), `IAutomaton`, `IAutomatonPair` (values of `match-pair`), `IAutomatonVec` (`Automaton*`), `IPopulation`, `IIntList`, `IFloatList`, `IPoint`, `IPointList`, `IRng` |
| (Racket builtins)             | `lib.mn`        | `Rng` (exact port of Racket CS's `random`), cons lists `IntNil/IntCons`, `FloatNil/FloatCons`, `PointNil/PointCons` |
| `automata.rkt`                | `automata.mn`   | classes `Automaton`, `Transition`, `Transitions`, `AutomatonPair`, `PayoffPair`; static `Automata` |
| `population.rkt`              | `population.mn` | classes `AutomatonVec`, `Population`; static `Populations` |
| `utilities.rkt`               | `utilities.mn`  | static `Utilities` |
| `main.rkt`                    | `main.mn`       | class `Point` (the `(list n d)` of `simulation->lines`); static `Main` |

## Deviations

- `random`: `Rng` reproduces Racket CS's generator bit for bit (`(random-seed 7480)`,
  `(random n)` and `(random)`). Racket uses the global generator; here one `Rng` object is
  created in `main` and passed to `make-random-automaton`, `build-random-population`,
  `death-birth`, `choose-randomly`, `shuffle-vector` and `evolve` (extra parameter).
- `Payoff` (`Nonnegative-Real`) values are always exact integers in this program, so they are
  `Int`; `relative-average` divides the integer sum by `w * length` in floating point, which is
  the correctly rounded value of the exact quotient, as `exact->inexact` of the rational.
- Vectors are wrapped in project classes (`Transition`, `Transitions`, `AutomatonVec`) instead of
  passing `ArrayList`s across modules: an `ArrayList` created in untyped code is an
  `ArrayList<dyn>` and fails the cast when it reaches typed code that expects `ArrayList<Int>`.
- `PAYOFF-TABLE` is a module-level constant in Racket; here `match-pair` builds the 2x2 table once
  per call and the inner loop indexes it (MonNom has no usable static fields).
  The classic automata (`defects`, ...) build their transition tables per call for the same
  reason (they are unused by `main`, as in the original).
- `#:random q` is passed as `hasQ`/`q`; keyword arguments of `transitions` are positional.
- `choose-randomly`'s non-tail `let loop` is the recursive `FindIndex`; `for/list` loops build
  the lists in the same order.
- Input scaling: `(evolve (build-random-population 300) 500 100 20)` runs for 0.25 s in Typed
  Racket and 0.15 s in MonNom, so the number of cycles is 4000 instead of 500 (Racket typed with
  4000 cycles: 2.0 s). The expected output was recomputed with 4000 cycles.

## Expected output

Number of averages, their sum, the first and the last average (6 decimals):
`4000 11960.710667 1.892667 3.000000`, from the Typed Racket version (scratch copy of
`main.rkt` with 4000 cycles that prints these values with `real->decimal-string`).

## Results

- Fully typed: about 1.4 s.
- `nombench --byfile`: 486 configurations. All 96 configurations without structural files
  print the expected output; 120 of the 390 configurations with records/lambdas do. The other
  270 fail at run time: segmentation faults (183), `Tried to load invokable value from field,
  but value has no lambda` (57), `No such method!` (18), `std::exception` (9),
  `Cast failed!` (3). Every configuration in which `automata.mn` or `population.mn` is
  structural fails (for example `.BM_CCCSCCIIIIICCIIIIIICCCCCSDCCCC`, where only
  `population.mn` is structural, segfaults in JIT-compiled code; with a different random
  sequence the same configuration stops with `UNIMPLEMENTED!`, the multi-cast-list case for
  structural values). Renaming the fields so that no field and method share a name
  does not change these results.
- Status: PARTIAL.
