# Rename private fields of every class in a .mn file to <name>Fld, inside that class body only.
# usage: renamefields.py file.mn...
import re, sys
for path in sys.argv[1:]:
    src = open(path).read()
    out = []
    pos = 0
    for m in re.finditer(r'^class \w+[^\n]*\n\{', src, re.M):
        start = m.start()
        # find matching closing brace of the class
        depth = 0
        i = m.end() - 1
        while True:
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = src[start:i + 1]
        fields = re.findall(r'^\s*private (?:readonly )?[\w<>, !?]+ (\w+);', body, re.M)
        for f in fields:
            body = re.sub(r'(?<![\w.])' + f + r'\b(?!\s*\()', f + 'Fld', body)
        out.append(src[pos:start])
        out.append(body)
        pos = i + 1
    out.append(src[pos:])
    open(path, 'w').write(''.join(out))
