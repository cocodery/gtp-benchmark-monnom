# morsecode

Morse-code translation and Levenshtein distance between all pairs of 799 frequent English words
(GTP `morsecode`, John Clements / Neil Van Dyke).

## Module mapping

| Racket                     | MonNom                   | Contents |
|----------------------------|--------------------------|----------|
| (Racket builtins and types)| `types.mn`               | `IText` (strings), `IVec` (vectors), `ICharTable` (`(HashTable Char String)`), `ICharPred`, `IGetScratch`, lists |
| (Racket builtins)          | `lib.mn`                 | `Text`, `Vec`, `CharTable`, cons lists, static `Builtins` (`make-vector`, `string->list`, `list->vector`, `string-append`, `char-downcase`) |
| `levenshtein.rkt`          | `levenshtein.mn`         | `CharEqPred` (`eq?`/`eqv?`/`equal?` on chars), `MakeVectorScratch`; static `Levenshtein` |
| `morse-code-strings.rkt`   | `morse-code-strings.mn`  | static `MorseStrings` |
| `morse-code-table.rkt`     | `morse-code-table.mn`    | static `MorseTable` |
| `main.rkt`                 | `main.mn`                | static `Main` |
| `base/frequency-small.rktd`| `words.mn`               | library file (not devolved): the words |

## Deviations

- Strings are `IText` objects (character codes); characters are `Int` codes.
- `morse-code-table.rkt` builds `char-table` by parsing a wikipedia excerpt with regular
  expressions when the module is instantiated (not timed); here the parsed table (dumped from
  Racket) is built directly. The table is created by `main` and passed to `string->morse`.
- The hash table with character keys is a 256-slot table indexed by the character code.
- The union-dispatching `levenshtein` (`LType`) is not ported (no type tests in MonNom; unused).
- Vectors are wrapped in `Vec` so that no `ArrayList` crosses a module boundary.
- `main` adds up the distances and the morse lengths so that there is a result to print.
- Input size is the original (all pairs of the 799 words of `frequency-small.rktd`).

## Expected output

`799 7069184 17413406`: number of words, sum of both Levenshtein distances over all pairs, sum of
the morse-code lengths, from the Typed Racket version (scratch copy of `main.rkt` with the sums).

## Results

- Fully typed: about 5 s (Typed Racket: 1.3 s).
- `nombench --byfile`: 216 configurations. All 96 configurations without structural files print
  the expected output; all 120 configurations with a structural file fail at run time
  (72 aborts on a `std::exception` while compiling, 43 segmentation faults, 5 `ERROR!`).
- Status: PARTIAL.
