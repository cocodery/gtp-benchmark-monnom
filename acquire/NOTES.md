# acquire

Simulation of the board game Acquire with an administrator and two kinds of automated players
(GTP `acquire`, Matthias Felleisen): 12 players (6 "ordered", 6 "random"), 100 turns per game.

## Module mapping

| Racket | MonNom | Contents |
|--------|--------|----------|
| `base/types.rkt`, `board-adapted.rkt`, `state-adapted.rkt`, `tree-adapted.rkt` | `types.mn` | `ITile`, `IBoard`, `IShares`, `IPlayer`, `IState`, `IDecision`, `IScoreEntry`, `ITurnResult`, `IRunResult`, `IStrategy`, `ITurn` (Turn%), `IPlayerExt` (Player%), `IAdministrator` (Administrator%), `ITree` (ATree%), `IPlaced` (Placed%), `IHandOut`, closures, lists |
| (Racket builtins) | `lib.mn` | `Text`/`Txt`, `BoardMap` and `SharesMap` (immutable hash tables), `Rng` (Racket's `random`), benchmark checksums (`Totals`), lists |
| `auxiliaries.rkt`, `basics.rkt`, `board.rkt` | `board.mn` | static `Aux`, `Basics`, `Board`; `TileS`, `MergingWhichS`, `RandomTile` (randomly-pick as a value) |
| `state.rkt`, `tree.rkt` | `state.mn` | `PlayerS`, `StateS`, `ScoreEntryS`, `NoExternal`, static `State`; `StateTree` (state%), `LPlacedTree` (lplaced%), `PlacedS` (placed%), `HandOutS`, static `ATree`, `Tree` |
| `strategy.rkt`, `player.rkt`, `admin.rkt` | `admin.mn` | strategy closures (`StrategyD`, pickers), `PlayerExtS` (player%), `TurnS` (turn%), `Administrator` (administrator%), static `Strategy`, `PlayerFactory`, `Admin` |
| `main.rkt` | `main.mn` | static `Main` |

Nine modules are merged into four files (486 configurations).

## Deviations

- Classes: `racket/class` classes become MonNom classes; inheritance (`state%`, `lplaced%` from
  `atree%`) becomes classes implementing `ITree` with the inherited methods in a static class.
  `is-a? tree lplaced%` is `IsLPlaced()`. `in-sandbox` never fails in the benchmark (errors are
  not caught by `let/ec` either), so the failure continuations are never taken.
- Hotels (strings) are Ints in alphabetical order, rows (symbols) Ints, `Content` and spot kinds
  Ints; `(Option X)` is -1 or a flag. `Board` and `Shares` (immutable hash tables) are copied
  arrays; the board's iteration order is by position (only order-independent uses: sizes,
  relabeling). `equal?` on players compares all fields (the external player% by identity).
- `random` is an exact port of Racket CS's generator, seeded with 5 as `main.rkt` does.
- Keyword/optional arguments are explicit; multiple values are result objects; instance methods
  have at most two parameters (bundles such as `INextArgs`, `ITraversalArgs`).
- `*create-board-with-hotels`, `distinct-and-properly-formed`, `*create-state`, `*cs0` and the
  display functions are not used by the benchmark and are not ported.
- `main` returns nothing in the original; here the statuses, the number of states and a hash of
  the final scores of all games are accumulated and printed after the timed region.
- Input: `(main 100)` -> 10 games (MonNom: 30 s for 100 games; 1 game and 10 games checked
  against Racket).

## Expected output

`0 10 0 0 450 864012975` (games ending done / exhausted / score / IMPOSSIBLE, total states,
hash of the scores), from the Typed Racket version (scratch copy of `main.rkt` with the
checksums and `(main 10)`; 2.2 s).

## Results

- Fully typed: 3.0 s (10 games).
- `nombench --byfile`: 486 configurations. All 96 nominal configurations print the expected
  output; 216 of 486 agree in total. Every configuration with a structural `lib.mn` or
  `admin.mn` fails (254 segmentation faults, 16 runtime errors).
- Status: PARTIAL.

Reproduce a failure:

```bash
cd /data/workspace/monnom && . ./setpath.sh && cd gtp-benchmarks-monnom/acquire/.BM_.BM_CCCCCCCSSSDSSCCSSCSSCIIIIICIIIIIIIIIISSSSIIIIIIIIIIIIIIIIIIIIIIIIIIIIICCCCCCSSCSSSCCSCCCCCSCSCSSSSCSSCCCCSSSCSSCSCCSSCCCD && nom -p $PWD -o3 GtpAcquire
```

