# suffixtree

Longest common substring of every pair of lines of `base/prufock.txt` (156 lines, 24336 pairs),
computed with Ukkonen's suffix-tree construction (GTP `suffixtree`, Danny Yoo's
`suffixtree` library).

## Module mapping

| Racket                      | MonNom        | Contents |
|-----------------------------|---------------|----------|
| `typed-data.rkt` + builtins | `types.mn`    | `IText` (strings), `IVec`, `IGensym`, `ILabel`, `INode`, `ITree`, the result interfaces of multiple-value functions (`INodeIndex`, `INodePair`, `IJump`, `IExtension`, `IMismatchAt`, `IMismatchIn`), the continuation interfaces of `node-follow/k` (`IMatchedAtNodeK`, `IMatchedInEdgeK`, `IMismatchedAtNodeK`, `IMismatchedInEdgeK`), `IFirstShot`, lists, `INodeMarks` (`make-hasheq`) |
| (Racket builtins)           | `lib.mn`      | `Text`, `Vec`, `Gensym`, `NodeMarks`, cons lists, static `Builtins` |
| `data.rkt` + `label.rkt` + `structs.rkt` | `data.mn` | `Label`, `Node`, `NoNode` (`#f` node), `SuffixTree`, static `Data`, static `Labels`; `NodePair`, `MismatchAt`, `MismatchIn`, static `Structs` (`node-follow/k`, `node-find-child`, ...) |
| `ukkonen.rkt`               | `ukkonen.mn`  | `NodeIndex`, `Jump`, `Extension`, `FirstShotLink`, `FirstShotNoop`, the four continuation classes, static `Ukkonen` |
| `lcs.rkt` + `main.rkt`      | `main.mn`     | `LcsState`, static `Lcs`, `Main` |
| `base/prufock.txt`          | `prufock.mn`  | library file (not devolved): the lines as packed code points (`tools/textlines.py`, wide mode) |

`label.rkt` was merged into `data.mn`, `structs.rkt` into `data.mn` and `lcs.rkt` into `main.mn`:
with 6 files `--byfile` produced 729 configurations; with 5 it produces 243.

## Deviations

- Strings are `IText` objects (character codes); label elements `(U Char Symbol)` are `Int`s:
  characters are code points (>= 0), the sentinel symbols made by `gensym` are negative numbers.
  `gensym`'s global counter is a `Gensym` object created by `main` and passed down.
- `(U #f Node)` is an `INode` whose `IsFalse()` is true (`NoNode`); no nulls or type tests.
- Multiple return values (`values`) become small result objects.
- `node-follow/k` takes four continuations; closures with more than two parameters crash the
  MonNom runtime, so the last two continuations receive argument bundles.
- `(make-hasheq)` from nodes to booleans (in `lcs.rkt`) is a table indexed by a per-node id
  assigned lazily from the `Gensym` counter (MonNom has no `eq-hash-code`).
- `structs.rkt`'s `tree-contains?` and other functions not used by the benchmark are not ported.
- `main` adds up the number of pairs, the lengths and the character codes of all the longest
  common substrings so that there is a result to print (inside the timed loop, as in the
  scratch Racket copy that produced the expected output).
- Input size is the original.

## Expected output

`24336 108592 9936787` (pairs, total length of the common substrings, sum of their character
codes), from the Typed Racket version (scratch copy of `main.rkt` that adds the three sums).
Typed Racket takes about 30 s.

## Results

- Fully typed: 1.8 s.
- `nombench --byfile`: 243 configurations. All 48 configurations without structural files print
  the expected output; of the 195 with a structural file, 96 agree and 99 fail at run time (65
  segmentation faults, 27 aborts on a `std::exception`, 7 `ERROR!` cast failures). Every
  configuration with a structural `lib.mn` fails.
- Status: PARTIAL.

Reproduce a failure:

```bash
cd /data/workspace/monnom && . ./setpath.sh && cd gtp-benchmarks-monnom/suffixtree/.BM_DCCCCSIIIIIIIIIIIIIIIIIIIICCSSCCCCCCCCCCCSCSSCCCCSCS && nom -p $PWD -o3 Suffixtree
```
