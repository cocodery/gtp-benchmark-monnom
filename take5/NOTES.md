# take5

The card game "6 nimmt!" with 10 players, played 1000 times (GTP `take5`, Matthias Felleisen),
written with `racket/class` (mixins, inner classes, `inherit-field`).

## Module mapping

| Racket                                    | MonNom      | Contents |
|-------------------------------------------|-------------|----------|
| `both/*-types.rkt`, `both/card-adapted.rkt` | `types.mn` | `ICard`, `ICardsFn`, `IBullsFn`, `ICardPool`, `ICardOrStack`, `IDeck`, `IPlayer`, `IInternal`, `IScore`, `IResult`, `IPlayed`, `IDealer`, lists |
| (Racket builtins)                         | `lib.mn`    | cons lists, stable merge sorts (Racket's `sort` is stable) |
| `card.rkt` + `basics.rkt` + `stack.rkt`   | `card.mn`   | `Card`; static `Cards`, `Basics`, `Stack` |
| `deck.rkt` + `card-pool.rkt`              | `deck.mn`   | `CardPool`, `Deck`, `CardArg`/`ListArg`; static `Decks` |
| `dealer.rkt` + `player.rkt`               | `dealer.mn` | `Dealer`, `Internal`, `Player`, `Score`, `Result`, `Played`, lambdas `DefaultOrder`, `ValuesShuffle`, `DefaultFaces`; static `Dealers` |
| `main.rkt`                                | `main.mn`   | static `Main` |

Pairs of modules are merged to keep the configuration count at 486.

## Deviations

- No class inheritance: the mixin chain `(for-player (for-dealer base-deck%))` is one class
  `Deck`; `internal%` (a class stored in a field of `dealer%`) is the class `Internal`, which
  wraps a player. `Internal%` implements `Player%`; `IInternal` repeats `IPlayer`'s methods
  instead of `extends IPlayer`, because casts to interfaces with inherited methods are not
  implemented by the runtime (`NomInterface::GetCheckReturnTypeFunction` throws).
- `(U Card (Listof Card))` (the argument of `replace-stack`) is `ICardOrStack`.
- Optional / keyword arguments are explicit; `play-game` is called with its defaults
  (`values`, `default-faces`). The unreachable defaults of `create-card-pool` (Racket's `shuffle`
  and `random-bulls` with its generator) are not ported: every call passes both arguments.
- `order` is a closure field of `player%`; it is copied to a local before the call, because the
  generator's type checker does not implement calling a record field (`GetLocalCallable`).
- The result is printed in Racket's notation.
- Input scaling: `LOOPS` is 6000 instead of 1000 (1000 games take 0.2 s in MonNom; Typed Racket
  needs 35 s for 1000). Every game is identical, so the result does not change.

## Expected output

`((after-round 2) ((1 0) (2 0) (3 0) (6 0) (7 0) (8 0) (0 56) (4 80) (9 80) (5 120)))`, the
result of the last game, from the Typed Racket version (it is also the expected value of the
benchmark's own test submodule).

## Results

- Fully typed: about 0.95 s.
- `nombench --byfile`: 486 configurations. All 96 configurations without structural files print
  the expected output; 230 of the 390 with records/lambdas do. The other 160 fail at run time:
  segmentation faults (95), `ERROR!` without message (32), `UNIMPLEMENTED!` (12),
  `No such method!` (9), `Tried to load invokable value from field` (8), `Cast failed!` (4).
- Status: PARTIAL.
