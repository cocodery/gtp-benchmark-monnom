# quadT

The Quad typesetting system (GTP `quadT`, Matthew Butterick): typesets a sample document (line
breaking with the TeX-like OCM algorithm, hyphenation, columns via a constraint solver, pages)
and renders it with a PDF drawing context.

## Module mapping

| Racket | MonNom | Contents |
|--------|--------|----------|
| `base/core-types.rkt`, `base/quad-types.rkt`, `ocm-struct-adapted.rkt`, `penalty-struct-adapted.rkt` (+ builtins) | `types.mn` | `IQuad`, `IAttr`, `IItem`, `IVal` (QuadAttrValue), `IPenalty`, `IOcm`, `IMatrixProc`, `IEntryToValue`, vectors, `IPatterns`, `IMeasureTable`, `IEnv`, `IConstraintFn`, `IProblem`, `IDc`, `IRenderer`, lists |
| builtins, `base/csp`, racket/draw | `lib.mn` | `Text`/`Txt`, `Sym` (interned symbols), `ValS`/`QuadS`/`AttrS`/`ItemS` and `Vals` (s-expression values, `equal?`), vectors, `Fl` (flonum rounding), `TextMap`, `PatternTable`, `MeasureTableS`/`Measures`, `EnvS`, `RecordingDc`, `Problem` (csp), lists |
| `quads.rkt`, `world.rkt`, `sugar-list.rkt`, `utils.rkt` | `quads.mn` | static `World`, `Quads`, `SugarList`, `Utils` |
| `hyphenate.rkt`, `measure.rkt` | `hyphenate.mn` | static `Hyphenate`, `Measure` |
| `wrap.rkt`, `ocm.rkt`, `ocm-struct.rkt`, `penalty-struct.rkt` | `wrap.mn` | `PenaltyS`, `OcmS`, `Minima`, `PenaltyProc` and other closures, static `Ocm`, `Wrap` |
| `quad-main.rkt`, `quick-sample.rkt`, `render.rkt`, `main.rkt` | `main.mn` | constraint closures, static `QuadMain`, `QuickSample`, `AbstractRenderer`, `PdfRenderer`, `Main` |
| `hyphenate.rkt`'s pattern table | `hyphdata.mn` | library file: the 4938 hyphenation patterns |
| text measurements | `measdata.mn` | library file: the 301 text extents measured by racket/draw |

14 modules are merged into six files (324 configurations).

## Deviations

- Quads are s-expressions in Racket. Here a quad is an `IQuad` (name, attributes, items), an
  attribute value an `IVal` with a kind for each case of `QuadAttrValue`, symbols interned Ints;
  `equal?` is structural. The deep predicates of quad-types.rkt check the name (and, for group
  quads, that the items are quads).
- `merge-attrs` builds a mutable hash and returns `hash->list`: the order of Racket's hash table
  is replaced by the order of first occurrence (one entry per key, last value). Checked: the
  Racket benchmark with that order gives the same result.
- racket/draw: the text extents (`get-text-extent` with the system fonts) are those measured by
  the Racket run on the reference machine, embedded; `pdf-dc%` is replaced by a recording
  context that counts the drawn texts and keeps a checksum of their characters, positions and
  sizes (the PDF bytes are discarded by the original too). The font cache file is absent in the
  original (load/update do nothing).
- base/csp: only the subset used (one variable, unary function constraints, backtracking with
  forward checking); the solution generator (racket/generator) is replaced by returning the
  first solution, which is what `get-solution` takes.
- Regular expressions (`\w+`, `\p{Zs}`, `.`) are matched by hand; parameters are constants (the
  `parameterize` of `world:quality-default` in `main.rkt` has no effect: that parameter is never
  read); keyword/optional arguments are explicit; the module-level state of hyphenate.rkt and
  measure.rkt is an `IEnv`; instance methods have at most two parameters.
- `fu-formula` (needs `fllog`/`stddev`) is only used by `wrap-adaptive`, which is not called; it
  stops the program if called.
- Input: the original sample; the typesetting and rendering are repeated 20 times in the timed
  region (one run: 0.1 s). Each run gives the same result (checked in Racket).

## Expected output

`272 858009901` (drawn texts, checksum), from the Typed Racket version (scratch copy whose
`render-word` computes the same checksum; 20 runs, 9.8 s).

## Results

- Fully typed: 2.0 s (20 runs).
- `nombench --byfile`: 324 configurations. All 96 nominal configurations print the expected
  output; none of the 228 configurations with a structural file does (180 segmentation faults,
  48 `Given value is not invokable!`). Every configuration with a structural `lib.mn`,
  `wrap.mn` or `main.mn` fails.
- Status: PARTIAL.

Reproduce a failure:

```bash
cd /data/workspace/monnom && . ./setpath.sh && cd gtp-benchmarks-monnom/quadT/.BM_.BM_CCCCCCSCSCCCCCCCIIIIIIIIIIIIIIIICCCCCIIIIIIIIIIIICCCIIIICCCCCSLDSSCCSSLCSCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD && nom -p $PWD -o3 QuadT
```

