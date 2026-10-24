# quadU

The Quad typesetting system (GTP `quadU`, Matthew Butterick; formerly `quadBG`): typesets a sample document (line
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
| text measurements | `measdata.mn` | library file: the 295 text extents measured by racket/draw in the quadU run |

14 modules are merged into six files, as for quadT.

## How quadU differs from quadT, and how the port was derived

The port was made from the quadT port; every change is marked `quadU:` in the sources. The
quadU originals use coarser types (`Quad = (List* Symbol QuadAttrs (Listof Any))`, attributes
as alists of `Any`) and differ in behaviour, which the port reproduces:

- `merge-attrs` conses every attribute (its `duplicate?` test compares a key with whole
  attributes and is never true), so it returns the reversed concatenation of its arguments and
  attribute lists keep duplicates; `flatten-attrs` keeps all the other attributes in order;
- `quad-attr-ref` returns the first matching attribute whose value is not `#f`;
- `word-string` requires a string first item; `quad-height` defaults non-flonums to 0.0;
  `last-line?` tests `integer?` instead of asserting indexes; font sizes must be flonums;
- `block->lines` always uses `wrap-best` (`wrap-first` and `wrap-adaptive` are commented out);
- the sample document gives its attributes as alists (same attributes as quadT).

The result differs from quadT (273 drawn texts instead of 272).

## Deviations

- Quads are s-expressions in Racket. Here a quad is an `IQuad` (name, attributes, items), an
  attribute value an `IVal` with a kind for each case of `QuadAttrValue`, symbols interned Ints;
  `equal?` is structural. The deep predicates of quad-types.rkt check the name (and, for group
  quads, that the items are quads).
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
  region (one run: 0.1 s). Each run gives the same result (the Racket reference prints the
  result of the last of 20 runs).

## Expected output

`273 317263971` (drawn texts, checksum), from the Typed Racket version (scratch copy whose
`render-word` computes the same checksum; 20 runs, 74 s).

## Results

- Fully typed: 1.9 s (20 runs).
- `nombench --byfile`: 324 configurations. All 96 nominal configurations print the expected
  output; none of the 228 configurations with a structural file does (179 segmentation faults,
  48 `Given value is not invokable!`, 1 abort).
- Status: PARTIAL.

Reproduce a failure:

```bash
cd /data/workspace/monnom && . ./setpath.sh && cd gtp-benchmarks-monnom/quadU/.BM_.BM_CCCCCCSCSCCCCCCCIIIIIIIIIIIIIIIICCCCCIIIIIIIIIIIICCCIIIICCCCCSLDSSCCSSLCSCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCD && nom -p $PWD -o3 QuadU
```

