# jpeg

JPEG decoding and re-encoding (GTP `jpeg`, Andy Wingo's guile-jpeg): reads `base/test.jpg`
(500x375, with EXIF data), parses the EXIF segment, and writes the image back as a baseline
JPEG with recomputed quantization and Huffman tables.

## Module mapping

| Racket | MonNom | Contents |
|--------|--------|----------|
| `base/typedefs.rkt`, jfif struct types, builtins | `types.mn` | `IBytes`, `IVec`, `IPort`, `IBitPort`, `IHuffman`, `IQTables`, `IHTables`, `IFreqs`, `IHuffmanTables`, `IBlockArray`, `IMcu`, `IMcuArray`, `ICodesMcu`, `ICodesArray`, `IComponent`, `IFrame`, `IMisc`, `IParams`, `IJfif`, `IJfifState`, `IInterp`, `IPT`, `IText`, `ITypeParser`, `IValueInterpreter`, `IExifState`, `ISymbols`, `IScanComponent(s)`, lists |
| builtins, `base/math/array`, `base/bytevectors-6-typed.rkt` | `lib.mn` | bytes, vectors, byte ports, the typedefs vectors (`BitPortV`, `HuffmanV`, `QTablesV`, ...), strict row-major arrays, strings, symbols, `Interps`, `Bits` (bitwise operations), `Bytevectors`, `Builtins`, lists |
| `bit-ports.rkt` + `huffman.rkt` | `huffman.mn` | static `BitPorts`, `Huffman` |
| `jfif.rkt` | `jfif.mn` | struct classes, `ScanComponentV`, closures of `allocate-dct-matrix`, static `Jfif` |
| `exif.rkt` | `exif.mn` | type parsers and value interpreters (closure classes), `ExifStateS`, static `Exif` |
| `main.rkt` | `main.mn` | `DimsAndExif`, static `Main` |
| `base/test.jpg` | `testjpg.mn` | library file: the 63832 bytes, packed 7 per Int |

`bit-ports.rkt` and `huffman.rkt` are merged (486 instead of 729 configurations).

## Deviations

- MonNom has no bitwise operators at run time: `arithmetic-shift`, `bitwise-and/ior`,
  `bitwise-bit-set?` are computed arithmetically on two's-complement values (`Bits`).
- Ports are byte ports over embedded data; strings, symbols (interned Ints) and the `Interp`
  union (`IInterp` with a kind) are lib stand-ins. `(U #f Natural)` vector elements are -1.
- math/array is replaced by strict arrays built in row-major order (build-array is strict by
  default in math/array, so each element is computed once, as here).
- Module-level constants of jfif.rkt (`normal-order`, `*initial-params*`, `FAKE-HUFF`) and the
  tables of exif.rkt are state objects made by `main` before the timed region and passed down.
- Multiple values are result objects or a one-element vector (max-size in huffman.rkt).
- `jpeg-dimensions` (unused) is not ported; `main` keeps the values `main.rkt` discards
  (dimensions, EXIF entries, output bytes) and prints a digest of them after the timed region.
- Input: `main` is run 15 times in the timed region (one run takes 0.08 s); every run is
  independent and gives the same result, so the expected output is that of one Racket run.

## Expected output

`500 375 24 5036 62856 800812380`: width, height, number of main EXIF entries, a digest of their
values, length and rolling hash of the written JPEG, from the Typed Racket version (scratch
copy of `main.rkt` printing these values; one run, 0.47 s).

## Results

- Fully typed: 1.1 s (15 runs).
- `nombench --byfile`: 486 configurations. All 96 nominal configurations agree; 140 of 486
  agree in total. Every configuration with a structural `lib.mn`, `jfif.mn` or `exif.mn`
  fails (263 segmentation faults, 54 aborts, 29 runtime errors).
- Status: PARTIAL.
