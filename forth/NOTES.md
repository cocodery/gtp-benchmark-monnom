# forth

A Forth interpreter (GTP `forth`, Ben Greenman): commands are objects of class `command%`
with an `exec` closure, the environment is a list of commands, the stack a list of integers.

The project is called `GtpForth`, not `Forth`: with the project name `Forth` the runtime loads
project interfaces from the wrong library (the loader keeps a pointer to a temporary
`std::string` as a key of its library map, `Loader::GetLibrary` in
`sourcecode/Runtime/Parse/Loader.cpp`, so lookups that hash to the same bucket as `stdlib`
return the wrong library). `GtpForth` happens not to collide.

## Module mapping

| Racket                      | MonNom       | Contents |
|-----------------------------|--------------|----------|
| `base/command-types.rkt`    | `types.mn`   | interfaces `IText`, `ISymbol`, `ISymTable`, `IVal` (`Val`), `IValList`, `IStack` (`Stack`/`State`), `IPop`, `IBinop`, `IExec`, `IExecArgs`, `ICommand` (`Command%`), `IEnv`, `IResult`, `IEvalResult` |
| (Racket builtins)           | `lib.mn`     | `Txt` (string helpers), `Text`, `Symbol`, `SymTable` (symbol interning), `SymVal`/`IntVal` (reader values), cons lists `ValNil/ValCons`, `IntNil/IntCons`, `CmdNil/CmdCons`, multiple-value results `Pop`, `EvalResult`, results `ResExit/ResFalse/ResPair`, `ExecArgs` |
| `stack.rkt`                 | `stack.mn`   | static `Stack` |
| `command.rkt`               | `command.mn` | `Command`, `BinopCommand`, binop lambdas `PlusOp/MinusOp/TimesOp`, exec lambdas `BinopExec`, `ExitExec`, `HelpExec`, `DropExec`, `DupExec`, `OverExec`, `SwapExec`, `PushExec`, `ShowExec`; static `Commands` (`CMD*`, `exit?`, `help?`, `show?`, `find-command`, `show-help`) |
| `eval.rkt`                  | `eval.mn`    | exec lambdas `DefnExec`, `DefinedExec`; static `Eval` (`forth-eval*`, `forth-eval`, `forth-tokenize`, `de-nest`) |
| `main.rkt`                  | `main.mn`    | static `Main` |
| `base/history-100.txt`      | `history.mn` | library file (not devolved): the input lines as character codes |

## Deviations

- Strings: MonNom strings are opaque (no indexing, and `++` is not implemented by the runtime),
  so Racket strings are `IText` objects (character codes). Descriptions and messages are stored
  as packed character codes and printed character by character.
- Symbols: `read` interns symbols; here `SymTable` interns `IText`s (hash buckets) and `eq?` on
  symbols is reference equality. The symbol table is created in `main` and passed to
  `forth-eval*` (no global state in MonNom).
- `forth-tokenize` uses a small reader instead of Racket's `read`: whitespace-separated tokens,
  `[+-]?digit+` is an integer, everything else a lower-cased symbol (the input has no
  parentheses, so `de-nest` is the identity).
- `exec` takes `(E S v)` in Racket; instance methods and lambdas with more than two arguments
  crash the runtime (`EnsurePackedUnpacked` exception in `NomClass::GetDynamicDispatcherLookup`),
  so the three arguments are passed in one `IExecArgs` object (one per `forth-eval` call).
- Typed Racket's `Any` for the token list is `IValList` (it is always a list of reader values).
  `(eof-object? v)` / `(symbol? v)` tests on that list are always false and are omitted.
- `binop-command%` inherits from `command%` in Racket; here it is a separate class with the same
  fields plus `binop` (no inheritance in MonNom). `object-name` of the binop is passed explicitly.
- `CMD*` and `defn-command` are module-level constants in Racket; here they are rebuilt by every
  `forth-eval*` call (their symbols are interned once in the shared table).
- `#:random` style optional arguments do not occur; `(values ...)` results are objects.
- `LOOPS` is 2000 instead of 10: with 10 loops the program runs for 7 ms (Racket) / 7 ms
  (MonNom). Each loop is independent, so the printed result does not change.

## Expected output

Length of the final environment, depth of the final stack and the stack itself after the last
loop (`33`, `46`, `(5651387616 ...)`). The Typed Racket version does not type-check with the
installed Racket 8.17 (`eval.rkt:41`: occurrence typing of the `for/fold` accumulator `e`), so
the expected output comes from the untyped version (scratch copy of `main.rkt` with the
results printed); untyped and typed versions compute the same thing.

## Results

- Fully typed: about 1.2 s (Racket untyped with `LOOPS` = 2000: 0.8 s).
- `nombench --byfile`: 324 configurations. All 96 configurations without structural files
  (records/lambdas) print the expected output; 48 of the 228 configurations with a structural
  file do. The other 180 fail at run time:
  segmentation faults (72), `UNIMPLEMENTED!` (27, the runtime's multi-cast-list case for
  structural values), `Given value is not invokable!` (24),
  `Tried to load invokable value from field, but value has no lambda` (23),
  `No such method!` (18), `Cast failed!` (11), `std::exception` (4),
  `Called invalid IMT method!` (1). Every configuration in which `command.mn` or `lib.mn` is
  structural fails.
  Example: `.BM_SLCCSDCCLLCCCLLIIIIIICCCIIIIIIIICLLLCLCCCLCLCCCCLCCC` (only `command.mn`
  structural) runs the first `forth-eval*` call correctly and fails with `Cast failed!` in the
  second one, when the `exec` lambda of a re-created command record is cast to `IExec`.
- Status: PARTIAL (the port itself works; the failures are runtime errors on structural values).

## Open issues

- The `.mn` files printed by `nombench` into `.BM_*` print `continue` as `break 0;` and `break`
  as `break 0;` (`ContinueStmt.PrettyPrint`), so they cannot be recompiled as-is; `nombench`
  compiles its in-memory AST, so the generated `.mnil` files are correct.
