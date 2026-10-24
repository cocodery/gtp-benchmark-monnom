# Generate monomorphic cons-list interfaces / classes (stand-ins for Racket's (Listof T)).
# Generic lists cannot be used across modules: the benchmark generator does not devolve project
# types nested in type arguments of instance-method signatures, and instances created in untyped
# code (C<dyn>) fail casts to C<T> in typed code.
# usage: lists_gen.py interfaces|classes Iface:Elem:Prefix ...
#   e.g. lists_gen.py classes ISymList:ISymbol:Sym  -> classes SymNil, SymCons implementing ISymList
import sys

def iface(i, t):
    return ('# (Listof %s)\ninterface %s\n{\n\tfun IsEmpty() : Bool;\n\tfun First() : %s;\n'
            '\tfun Rest() : %s;\n}\n\n' % (t, i, t, i))

def classes(i, t, c):
    return ('class %sNil implements %s\n{\n\tpublic constructor()\n\t{\n\t}\n'
            '\tpublic fun IsEmpty() : Bool\n\t{\n\t\treturn true;\n\t}\n'
            '\tpublic fun First() : %s\n\t{\n\t\tERROR("car: empty list");\n\t}\n'
            '\tpublic fun Rest() : %s\n\t{\n\t\tERROR("cdr: empty list");\n\t}\n}\n\n'
            'class %sCons implements %s\n{\n\tprivate readonly %s first;\n\tprivate readonly %s rest;\n'
            '\tpublic constructor(%s f, %s r)\n\t{\n\t\tfirst = f;\n\t\trest = r;\n\t}\n'
            '\tpublic fun IsEmpty() : Bool\n\t{\n\t\treturn false;\n\t}\n'
            '\tpublic fun First() : %s\n\t{\n\t\treturn first;\n\t}\n'
            '\tpublic fun Rest() : %s\n\t{\n\t\treturn rest;\n\t}\n}\n\n'
            % (c, i, t, i, c, i, t, i, t, i, t, i))

mode = sys.argv[1]
for spec in sys.argv[2:]:
    i, t, c = spec.split(':')
    sys.stdout.write(iface(i, t) if mode == 'interfaces' else classes(i, t, c))
