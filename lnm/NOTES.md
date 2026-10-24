# lnm

L-N/M analysis of a GTP dataset (here: snake's): count the configurations that are within N
times the untyped running time when L type conversion steps are allowed (GTP `lnm`, Ben
Greenman). The project is called `GtpLnm` (the name `Lnm` triggers the runtime's
library-loader bug, see `../forth/NOTES.md`).

## Module mapping

| Racket                                            | MonNom          | Contents |
|---------------------------------------------------|-----------------|----------|
| `both/summary-adapted.rkt`, `both/modulegraph-adapted.rkt`, `both/pict-adapted.rkt` | `types.mn` | `IText`, `IRatio`, `IModuleGraph`, `IDataset`, `ISummary`, `IStringPred`, `ICountFn`, `ICache`, lists |
| (Racket builtins)                                 | `lib.mn`        | `Text`, `Txt`, `Ratio`/`Rat` (exact rationals), `Dataset`, `Cache`, lists |
| `bitstring.rkt`                                   | `bitstring.mn`  | static `Bitstring` |
| `summary.rkt` + `modulegraph.rkt`                 | `summary.mn`    | `ModuleGraph`, `Summary`; static `ModuleGraphs`, `Summaries` |
| `lnm-plot.rkt`                                    | `lnm-plot.mn`   | `CountFn` (closure of `count-variations`), `GoodPred` (closure of `make-variation->good?`); static `LnmPlot` |
| `main.rkt` + `spreadsheet.rkt`                    | `main.mn`       | static `Spreadsheet`, `Main` |
| `base/data/snake.rktd`                            | `snake-data.mn` | library file (not devolved): the dataset |

## Deviations

- **The plot library is not ported.** `lnm-plot` builds plots with `plot/typed/pict` (lines,
  ticks, `function`, `plot-pict`), a large untyped library that renders pictures. The port
  computes everything the typed code computes and, instead of rendering, applies the function
  it gives to plot's `function` renderer at the points where the renderer samples it: 100
  points `20 * i / 99` (exact rationals), for each of the four L values. These sample points
  were measured by instrumenting the Racket program (400 calls). Tick and line construction
  (`compute-xticks`, `compute-yticks`, `horizontal-line`, `vertical-line`) are not ported.
- `math/statistics`' `mean` is exact: the means and thresholds are exact rationals (`Ratio`),
  compared exactly as in Racket.
- Streams (`stream-map`, `stream-filter`, `stream-partition`) are computed eagerly as lists; the
  results are the same, the number of predicate calls may differ from the lazy version.
- The module graph is parsed from `base/module-graphs/snake.tex` before the timed region in
  Racket; here its adjacency list is embedded (computed with the same regular expressions).
- `log2` uses a loop instead of `(/ (log n) (log 2))` (no `log` in MonNom; the same value for
  the power-of-two dataset sizes).
- `rktd->spreadsheet` only evaluates the cells in the original (its output was replaced by
  `void`); the port does the same work (the bit strings of every row).
- Keyword arguments are positional. Input scaling: the timed block takes 0.44 s in MonNom
  (0.18 s in Typed Racket), so it is run 3 times.

## Expected output

Number of sampled values, their sum and the sum for each L value:
`400 50319 2885 9443 16752 21239`, from the Typed Racket version (scratch copy of
`lnm-plot.rkt` that records the calls plot makes to the sampled function).

## Results

- Fully typed: about 1.35 s.
- `nombench --byfile`: 324 configurations. All 96 configurations without structural files print
  the expected output; 48 of the 228 with records/lambdas do. The other 180 fail: 142
  segmentation faults and 38 `No such method!`.
- Status: PARTIAL (plot rendering not ported; structural configurations fail).
