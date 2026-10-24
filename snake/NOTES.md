# snake

Functional Snake game; folds over a recorded sequence of game events (GTP `snake`, David Van Horn).

## Module mapping

| Racket                     | MonNom            | Contents |
|----------------------------|-------------------|----------|
| `both/data-adaptor.rkt`    | `types.mn`        | interfaces `IPosn`, `IPosnList` (`(Listof Posn)` / `(NEListof Posn)`), `ISnake`, `IWorld`, `IRng` (pseudo-random generator) |
| `data.rkt` + `const.rkt`   | `data.mn`         | classes `Posn`, `PosnEmpty`, `PosnCons`, `Snake`, `World`; static `Data` (`posn=?`), static `Const` (`BOARD-WIDTH`, ..., `WORLD`) |
| `collide.rkt`              | `collide.mn`      | static `Collide` |
| `motion-help.rkt` + `cut-tail.rkt` | `motion-help.mn` | static `CutTail`, static `MotionHelp` |
| `motion.rkt`               | `motion.mn`       | class `Rng` (Racket's generator `r`), static `Motion` (`reset!`, `world->world`, ...) |
| `handlers.rkt`             | `handlers.mn`     | static `Handlers` |
| `main.rkt`                 | `main.mn`         | static `Main` (`replay`, `main`) |
| `base/snake-hist.rktd`     | `snake-hist.mn`   | library file (not devolved): the event history |

`const.rkt` is merged into `data.mn` and `cut-tail.rkt` into `motion-help.mn` to keep the
configuration count below 500 (each file with classes has 3 class variants and each file with
interfaces 3 interface variants under `--byfile`; without the merges there would be 1728
configurations).

## Deviations

- `Dir` (`(U "up" "down" "left" "right")`) is an `Int` (0 up, 1 down, 2 left, 3 right) and key
  strings are their character codes (`"w"` = 119, ...): MonNom strings cannot be compared by value.
- `posn` coordinates are `Real` in Racket but only ever hold integers; they are `Int` here.
- Racket's `random` is reproduced exactly: class `Rng` re-implements the Racket CS generator
  (MRG32k3a from Chez Scheme's `c/random.c`, including `random-seed`) with 64-bit integer
  arithmetic, and was checked against Racket output for several seeds and ranges.
- `reset!` reseeds a module-level generator in Racket. MonNom has no usable static fields, so
  `Motion.Reset()` returns a freshly seeded generator, and `replay` passes it to `world->world`
  (extra parameter on `world->world` and `snake-eat`).
- The history (`(Listof Any)` of s-expressions, read from the file) is an `ArrayList<Int>` of
  event codes, built by the library class `SnakeHist` before the timer starts; `match` becomes
  `Main.Step`.
- `replay` returns the final world (Racket returns `(void)`), so that `main` can print it.
- `or` / `and` are written as early returns (MonNom's `&&`/`||` do not short-circuit).
- Input size is the original (52457 events, `LOOPS` = 200).

## Expected output

Direction, number of segments, sum of `100*x+y` over the segments, food x, food y of the final
world after the last replay: `up 3 41565 26 7`. Computed with the Typed Racket version
(scratch copy of `main.rkt` changed to return and print the final world).

## Results

- Fully typed: about 0.75 s (Racket typed: 3.1 s).
- `nombench --byfile`: 432 configurations, all print the expected output
  (timed region 0.9-1.7 s under parallel load).
