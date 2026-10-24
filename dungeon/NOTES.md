# dungeon

Random dungeon generation with a cell class hierarchy (GTP `dungeon`, Vincent St-Amour).

## Module mapping

| Racket                                   | MonNom     | Contents |
|------------------------------------------|------------|----------|
| `base/cell-types.rkt`, typed adapters    | `types.mn` | `ICell`, `ICellClass`, `ICellClasses`, `IPos`, `IGrid`, `IRoom`, `IDirection`, lists, caches |
| (Racket builtins)                        | `lib.mn`   | `Pos` (vector), `Grid`, `PosCache` (hash keyed by Pos), `RandomBox` (box), cons lists, `Builtins` |
| `cell.rkt` + `message-queue.rkt`         | `cell.mn`  | `CellClass`, `Cell`, `NoCell`, `CellClasses`, `MessageQueue`, static `Cells` |
| `grid.rkt`                               | `grid.mn`  | `DirLeft/Right/Up/Down` (left/right/up/down functions), static `GridOps` |
| `utils.rkt`                              | `utils.mn` | static `Utils` (the fixed list of "random" numbers and helpers) |
| `main.rkt`                               | `main.mn`  | `Room`, `NoRoom`, ..., static `Main` |

## Deviations

- No class inheritance and classes are not values in MonNom: every Racket class is a
  `CellClass` object (with its superclass, for `is-a?`), every instance a `Cell` that dispatches
  on the kind of the class that defines a method (`inherit`/`super` become delegation).
- Module state (caches, the cell classes, utils.rkt's box of numbers) is created in `Main` and
  passed explicitly. `(U #f Room)` is an `IRoom` whose `Exists()` is false.
- `utils.rkt`'s list `orig` is built by a loop from packed Ints: as one nested `new IntCons(...)`
  expression of 300 elements the benchmark generator never finished (it hung for 45 minutes on
  one configuration).
- `parse-grid` (never called) is not ported. `main` prints the last generated grid as a checksum.
- Input: LOOPS 100 -> 200 (typed Racket 100 loops: 25 s; MonNom 200 loops: 1.0 s).

## Expected output

`1098 49846 115253359 2` (length, sum of character codes, rolling hash of the shown grid, and a
count of non-void cells), from the Typed Racket version (scratch copy of `main.rkt` with the
same checksum and 200 loops).

## Results

- Fully typed: 1.0 s.
- `nombench --byfile`: 486 configurations. All 96 nominal configurations print the expected
  output; 156 of 486 agree in total. Every configuration with a structural `cell.mn` or
  `grid.mn` fails (201 segmentation faults, 129 `ERROR!`/runtime errors).
- Status: PARTIAL.
