# mbta

Path finding in a model of Boston's subway: 9 checked requests plus a path query for every
pair of green-line and blue-line stations (GTP `mbta`, Matthias Felleisen).

## Module mapping

| Racket                                          | MonNom        | Contents |
|-------------------------------------------------|---------------|----------|
| `base/t-graph-types.rkt`, `base/t-view-types.rkt` | `types.mn`  | `IText`, `IOptText`, `IStationLine`, `IPathElem`, `IColorLines`, `IConnection`, `ILineConnections`, `IStationChoice`, `IGraph`, `IEdgeProperty`, `IMBTA`, `IManage`, `ITextSet`, lists |
| (Racket builtins) + `base/my-graph.rkt` / `base/graph` | `lib.mn` | `Text`, `NoText`/`SomeText`, static `Txt` (string-trim, string-split, string-join, format, regexp-quote matching, ...), `TextSet`, `Graph`, `EdgeProperty`, static `Builtins` (line sets), lists |
| `t-graph.rkt`                                   | `t-graph.mn`  | `StationLine`, `ColorLines`, `Connection`, `LineConnections`, `StationChoice`, `PartialLine`, `Hlc`, `LineFile`, `mbta%` = `Mbta`; static `TGraph` |
| `t-view.rkt`                                    | `t-view.mn`   | `CommentElem`, `StopElem`, `manage%` = `Manage`; static `TView` |
| `run-t.rkt`                                     | `run-t.mn`    | static `RunT` |
| `main.rkt`                                      | `main.mn`     | static `Main` |
| `base/*.dat`                                    | `dat.mn`      | library file (not devolved): the four line files |

## Deviations

- **Neighbor order.** Racket's graph library keeps the neighbors of a station in an immutable
  hash set and `find-path/aux` iterates it, so the order of the found paths, and therefore which
  of several equally good paths `pick-best-path` returns, depends on Racket's string hash
  codes. With the original order the totals are 792 / 14412 / 445184; with neighbors sorted by
  `string<?` they are 792 / 14411 / 445148, and with the reverse order 14295 lines. MonNom
  cannot reproduce Racket's hash order, so both sides use neighbors sorted by `string<?`: the
  port keeps them sorted, and the reference was computed with a scratch copy of
  `base/my-graph.rkt` whose `in-neighbors` sorts. The rest of the algorithm is unchanged.
- Strings are `IText` (character codes). The three regular expressions of `run-t.rkt`, the
  `#px"--* (.*)"` of `line-specification?` and the `regexp-quote` search of `station` are
  matched by hand with the same semantics (leftmost match, greedy groups).
- `Line` is an index 0..9 and `(Setof Line)` a bit set (`&`, `|` and `2 ** line`).
  `set-map` lists the lines in index order (only the content, not the length, of `render`'s
  result depends on that order).
- The graph library is ported only as far as it is used: `unweighted-graph/directed`,
  `in-neighbors` and an edge property with `#:init`.
- Hash tables and sets of strings are bucket tables (`TextSet`, `Graph`, `EdgeProperty`); the
  immutable hash `H-Line->Connection*` is a copied 10-slot table (`Hlc`).
- `manage` (module-level in `run-t.rkt`, built by reading the graph) is created by `main`
  before the timer and passed to `run-t`.
- The `loop` of `insert-switch` has three arguments; it is a static function because instance
  methods cannot take more than two arguments.
- `main` prints the number of queries, the total number of result lines and the total length
  of the results (all independent of hash orders). Input scaling: the original query set runs
  for 0.48 s, so the whole set (including the 9 checked requests, which restore the disabled
  list) is run 3 times.

## Expected output

`792 14411 445148` from the Typed Racket version with sorted neighbors (scratch copy of
`main.rkt` that adds up the line counts and lengths, and of `base/my-graph.rkt` with the
sorted `in-neighbors`).

## Results

- Fully typed: about 1.45 s (Typed Racket, original order: 0.69 s for one round of queries).
- `nombench --byfile`: 324 configurations. All 96 configurations without structural files print
  the expected output; 10 of the 228 with records/lambdas do. The other 218 fail: 166
  segmentation faults, `No such method!` (16), `ERROR!` (13), `Cast failed!` (13),
  `UNIMPLEMENTED!` (5), `Tried to load invokable value from field` (2), and 2 configurations
  with a structural `t-view.mn` finish normally but print a wrong line count (14412 instead of
  14411), e.g. `.BM_CCDCCSDCCCCCDJJJJJJJJJJJJJJJJJJJJJJDCCDDSDCDCCCCCCDCDDCCSCCCCCCDDC`.
- Status: PARTIAL.
