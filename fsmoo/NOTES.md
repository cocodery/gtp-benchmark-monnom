# fsmoo

The object-oriented variant of `fsm`: automata and the population are `racket/class` objects
(GTP `fsmoo`). Neither class uses inheritance (both extend `object%`), so they map to MonNom
classes directly.

## Module mapping

| Racket                          | MonNom          | Contents |
|---------------------------------|-----------------|----------|
| `both/automata-adapted.rkt`, `both/population-adapted.rkt` | `types.mn` | `ITransition`, `ITransitions`, `IAutomaton` (the `Automaton` class type: init-fields as getters/setters, public methods), `IAutomatonPair`, `IPopulation`, `IIntList`, `IFloatList`, `IPoint`, `IPointList`, `IRng` |
| (Racket builtins)               | `lib.mn`        | `Rng` (exact port of Racket CS's `random`), cons lists (same file as in `fsm`) |
| `automata.rkt`                  | `automata.mn`   | `automaton%` = class `Automaton`; `Transition`, `Transitions`, `AutomatonPair`, `PayoffPair`; static `Automata` (`make-random-automaton`, `defects`, ..., `transitions`) |
| `population.rkt`                | `population.mn` | `population%` = class `Population`; static `Populations` (`build-random-population`) |
| `utilities.rkt`                 | `utilities.mn`  | static `Utilities` (same file as in `fsm`) |
| `main.rkt`                      | `main.mn`       | class `Point`; static `Main` |

## Deviations

- `random`: exact port of Racket's generator, seeded with 7480 as in `main.rkt`. The global
  generator is a field of the population object (given to `build-random-population`).
- `#:random q` of `death-birth` is a `Float` where a negative value stands for `#f` (Payoffs are
  non-negative). A comparison result cannot be passed as a `Bool` argument (the runtime throws in
  `GenerateFunctionCall`), so `Populations.ChooseRandomly` picks the call with `true`/`false`.
- `get-field` / `set-field!` on the other automaton are interface methods (`Current`,
  `SetCurrent`, ...); the boxes of `match-pair` are local variables. `match-pair` keeps the
  original's use of `this`'s table for both automata.
- `(new automaton% ...)` inside `reset` and `clone` goes through the static `Automata.New`: the
  benchmark generator recurses forever (stack overflow) when it turns a class that instantiates
  itself into a record.
- `PAYOFF-TABLE` (created once in the `let` around the class in Racket) is built once per
  `match-pair` call; the private `compute-payoffs` is a public method (private methods cannot be
  called with `this.` in MonNom).
- Vectors are `ArrayList`s that never leave their module (`Population`'s `a*`/`b*`) or are
  wrapped in classes (`Transition`, `Transitions`).
- Input scaling: 500 cycles take 0.13 s in MonNom (Typed Racket: 51 s, dominated by contracts
  on the class boundary). The MonNom version runs 4000 cycles; the expected output was
  recomputed with 4000 cycles in Typed Racket (6.3 minutes).

## Expected output

`4000 11578.255000 1.876333 2.900000` (number of averages, sum, first, last; 6 decimals), from
the Typed Racket version with 4000 cycles (scratch copy of `main.rkt` that prints these values).

## Results

- Fully typed: about 1.0 s.
- `nombench --byfile`: 486 configurations. All 96 configurations without structural files print
  the expected output; 148 of the 390 configurations with records/lambdas do. The other 242 fail
  at run time: `Tried to load invokable value from field, but value has no lambda` (126),
  segmentation faults (53), `UNIMPLEMENTED!` (46), `No such method!` (14), `Cast failed!` (3).
  Every configuration with a structural `automata.mn` fails.
- Status: PARTIAL.
