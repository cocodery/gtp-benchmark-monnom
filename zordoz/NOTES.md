# zordoz

Search the parsed bytecode (`.zo`) of `typed-zo-find_rkt.zo` for all `branch` structs (GTP
`zordoz`, Ben Greenman's zo explorer: `init` runs the shell's `find` command).

## Module mapping

| Racket | MonNom | Contents |
|--------|--------|----------|
| `base/typed-zo-structs.rkt` (+ builtins) | `types.mn` | `IZo`, `IDatum` (any Racket value), `ISpec`, `ISpecField`, `ISpecThunk`, `ITransResult`, `IResult`, `IInitArgs`, `IText`, lists |
| `base/compiler-zo-structs.rkt`, `base/compiler-zo-parse.rkt`, builtins | `lib.mn` | `ZoS` (the zo structs), `DatumS`/`LeafS`, `Datums`, `Zo` (predicates), `Kinds` (the 58 struct kinds, generated), `Specs`, `UnforcedThunk`, `Trans`, `ZoParse` (decoder of the embedded graph), lists |
| `zo-string.rkt` | `zo-string.mn` | static `ZoString` (`zo->spec`, generated from the Racket source) |
| `zo-transition.rkt` | `zo-transition.mn` | static `ZoTransition` (generated from a transcribed table) |
| `zo-find.rkt` | `zo-find.mn` | `ResultS`, `TitleAndChildren`, static `ZoFind` |
| `zo-shell.rkt` | `zo-shell.mn` | static `ZoShell` (`init`, `find-all`, `zo-read`) |
| `main.rkt` | `main.mn` | static `Main` |
| `base/typed-zo-find_rkt.zo` | `zodata.mn` | library file: the parsed zo graph (7998 structs), serialized |

`tools/zordoz_gen.py` generates `zodata.mn`, the kind table, `zo-string.mn` and the body of
`zo-transition.mn` from the Racket sources and from a dump of the graph made with
`base/compiler-zo-parse.rkt`.

## Deviations

- The binary `.zo` file is not parsed: Racket parses it with the benchmark's own
  `compiler-zo-parse.rkt` and the resulting graph (all zo structs reachable through fields,
  pairs and vectors, with sharing and the 565 cycles preserved) is embedded. Values that are not
  zo structs, pairs, vectors or booleans (symbols, numbers, hashes, ...) are opaque leaves; the
  traversal never looks into them.
- MonNom has no struct subtyping or type tests: the 58 prefab zo structs are one node class with
  a kind id; `form?`, `expr?`, `binding?` etc. are predicates on the kind (generated from the
  struct hierarchy). Struct identity (`eq?`, `memq`) is the node id.
- Specs keep the field names; their thunks (which format the field values) are never forced by
  the benchmark and stop the program if forced (`zo->string` and the rest of the shell, its
  commands and printing, are not ported).
- `init`/`find-all` return the search results instead of discarding them; `main` prints the
  number of results and the sum of their path lengths after the timed region.
- Input size: the original (one search over `typed-zo-find_rkt.zo`).

## Expected output

`391 6278` (results, total path length), from the Typed Racket version (scratch copy whose
`find-all` prints these values; 0.6 s).

## Results

- Fully typed: 2.1 s.
- `nombench --byfile`: 432 configurations. All 192 nominal configurations agree; 288 of 432
  agree in total. Every configuration with a structural `lib.mn` fails (143 segmentation
  faults, 1 runtime error).
- Status: PARTIAL.
