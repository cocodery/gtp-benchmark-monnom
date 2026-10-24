# Translate the `mid-test` and `standard-example` expressions of kcfa's main.rkt into MonNom
# builder code (one statement per node, so that no expression is deeply nested).
# Variables are interned by number (the generator numbers distinct symbol names); labels are
# gensyms created at construction time, in the same order as Racket's evaluation.
# usage: kcfa_gen.py <main.rkt>
import re, sys

src = open(sys.argv[1]).read()

def parse(s, i):
    while s[i].isspace():
        i += 1
    if s[i] == '(':
        i += 1
        out = []
        while True:
            while s[i].isspace():
                i += 1
            if s[i] == ')':
                return out, i + 1
            x, i = parse(s, i)
            out.append(x)
    if s[i] == "'":
        x, i = parse(s, i + 1)
        return ['quote', x], i
    m = re.match(r"[^\s()']+", s[i:])
    return m.group(0), i + m.end()

def defn(name):
    j = src.index('(define ' + name)
    form, _ = parse(src, j)
    return form[2]

names = {}
def var(n):
    if n not in names:
        names[n] = len(names)
    return names[n]

lines = []
cnt = [0]
def fresh():
    cnt[0] += 1
    return 'e%d' % cnt[0]

def gen(x):
    head = x[0]
    if head == 'make-ref':
        v = x[1][1]
        t = fresh()
        lines.append('\t\tIExp %s = Main.MakeRef(st, st.Var(%d));' % (t, var(v)))
        return t
    if head == 'make-lambda':
        formals = x[1][1]
        # Racket evaluates (new-label) before the body argument? No: (Lam (new-label) formals call)
        # is inside make-lambda, after its arguments (formals, call) were evaluated by the caller.
        body = gen(x[2])
        t = fresh()
        fl = 'new SymNil()'
        for f in reversed(formals):
            fl = 'new SymCons(st.Var(%d), %s)' % (var(f), fl)
        lines.append('\t\tIExp %s = Main.MakeLambda(st, %s, %s);' % (t, fl, body))
        return t
    if head == 'make-call':
        parts = [gen(a) for a in x[1:]]
        t = fresh()
        al = 'new ExpNil()'
        for a in reversed(parts[1:]):
            al = 'new ExpCons(%s, %s)' % (a, al)
        lines.append('\t\tIExp %s = Main.MakeCall(st, %s, %s);' % (t, parts[0], al))
        return t
    if head == 'make-let':
        v = x[1][1]
        e = gen(x[2])
        c = gen(x[3])
        t = fresh()
        lines.append('\t\tIExp %s = Main.MakeLet(st, st.Var(%d), %s, %s);' % (t, var(v), e, c))
        return t
    raise Exception(head)

out = []
for name, meth in [('mid-test', 'MidTest'), ('standard-example', 'StandardExample')]:
    lines = []
    r = gen(defn(name))
    out.append('\t# (define %s ...)\n\tpublic static fun %s(ISymTable st) : IExp\n\t{\n' % (name, meth))
    out.append('\n'.join(lines) + '\n\t\treturn %s;\n\t}\n' % r)
sys.stdout.write(''.join(out))
sys.stderr.write('%d variables, %d nodes\n' % (len(names), cnt[0]))
