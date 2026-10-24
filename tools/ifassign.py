# Finds `if`/`else` blocks that assign a local variable (lowercase name) without ending in
# return/continue/break: the MonNom compiler loses such assignments after the if (see README).
# usage: ifassign.py file.mn ...
import re, sys
for f in sys.argv[1:]:
    lines = open(f).read().split('\n')
    i = 0
    while i < len(lines):
        if re.match(r'\s*(if|else|elseif)\b', lines[i]) and i + 1 < len(lines) and lines[i + 1].strip() == '{':
            depth = 0; j = i + 1; body = []
            while j < len(lines):
                depth += lines[j].count('{') - lines[j].count('}')
                body.append(lines[j])
                if depth == 0: break
                j += 1
            inner = [l.strip() for l in body[1:-1]]
            last = [l for l in inner if l and not l.startswith('#')]
            ends = last and re.match(r'(return|continue|break|ERROR)\b', last[-1])
            for l in inner:
                m = re.match(r'([a-z][A-Za-z0-9]*)\s*=[^=]', l)
                if m and not ends:
                    print('%s:%d: %s' % (f, i + 1, l))
        i += 1
