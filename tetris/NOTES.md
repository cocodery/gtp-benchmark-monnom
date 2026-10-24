# tetris

Functional Tetris; replays a recorded sequence of game events (GTP `tetris`, David Van Horn).

## Module mapping

| Racket                      | MonNom           | Contents |
|-----------------------------|------------------|----------|
| `both/base-types.rkt`       | `types.mn`       | `IPosn`, `IBlock`, `IBlockList` (`BSet`), `ITetra`, `ITetraList`, `IWorld`, `IRng` |
| (Racket builtins)           | `lib.mn`         | `Rng` (exact port of Racket CS's `random`), cons lists `BlockNil/BlockCons`, `TetraNil/TetraCons`, static `Lists` (`length`, `list-ref`) |
| `data.rkt` + `consts.rkt`   | `data.mn`        | classes `Posn`, `Block`, `Tetra`, `World`; static `Data` (`posn=?`), static `Consts` |
| `bset.rkt` + `block.rkt`    | `bset.mn`        | static `BlockOps` (block.rkt), static `BSet` |
| `tetras.rkt` + `aux.rkt`    | `tetras.mn`      | static `Tetras`, static `Aux` (`list-pick-random`, `neg-1`, `tetras`) |
| `world.rkt` + `elim.rkt`    | `world.mn`       | static `Elim`, static `WorldOps` |
| `main.rkt`                  | `main.mn`        | static `Main` |
| `base/tetris-hist.rktd`     | `tetris-hist.mn` | library file (not devolved): the event history |

Four pairs of modules are merged to keep the number of configurations at 432 (with nine
separate modules plus the helper file it would be 6912).

## Deviations

- `Real` is `Float` (block coordinates are integers and tetra centers multiples of 1/2 in
  Racket, so floating point is exact here). `Color` (a symbol, never compared) is a `String`.
- Key strings are codes (2 "left", 3 "right", 4 "down", 5 "up", 6 "a", 7 "s"); the history is
  an `ArrayList<Int>` of event codes built by the library class `TetrisHist`.
- `random`: `Rng` reproduces Racket's generator exactly. `r` and `tetras` are module-level values
  of `aux.rkt`; here they are made once by `main` and passed to `world0`, `next-world`,
  `touchdown` and `list-pick-random` (extra parameters). As in Racket, the generator is not
  reseeded between replays.
- `ormap` / `andmap` / `filter` / `map` / `foldr` with lambdas are recursive functions or loops
  over the list, in the same order (`blocks-union` folds from the right as `foldr` does).
- `or` / `and` are early returns (MonNom's `&&` / `||` do not short-circuit).
- `(= x y)` on Reals goes through small `NumEq` helpers in the same file: comparing a `Float`
  directly with the result of an untyped interface method makes the runtime emit invalid LLVM
  code (`Instruction does not dominate all uses`, `Could not verify static method!`), which
  broke 192 configurations before the change. Comparisons between `Float` and `Int` need an
  explicit conversion (`+ 0.0`), as MonNom only mixes the two in arithmetic.
- Input scaling: `LOOPS` is 6 instead of 2 (2 loops: 0.43 s in MonNom, 3.4 s in Typed Racket).
  The generator state carries over between loops, so the expected output was recomputed with 6
  loops in Typed Racket (18.5 s).

## Expected output

Number of placed blocks, `sum(100x+y)` over them, center x and y of the current tetra,
`sum(100x+y)` over its blocks, and `game-over?` of the final world:
`94 40856.000000 4.000000 -1.000000 1594.000000 #t`, from the Typed Racket version (scratch
copy of `main.rkt` with `LOOPS` 6 that returns and prints the final world).

## Results

- Fully typed: about 1.25 s.
- `nombench --byfile`: 432 configurations, all print the expected output
  (timed region 1.6-7.3 s under parallel load).
- Status: DONE.
