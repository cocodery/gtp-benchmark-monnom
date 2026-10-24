# Print a MonNom expression building an IText for each string literal given on the command line
# (packed 9 characters per Int, see Txt.PushWord in the benchmark's lib.mn).
# usage: textlit.py 'string' ...
import sys

def pack(chunk):
    v = 0
    for i, ch in enumerate(chunk):
        assert 0 < ord(ch) < 128
        v |= ord(ch) << (7 * i)
    return v

for s in sys.argv[1:]:
    s = s.encode().decode('unicode_escape')
    e = 'Txt.Empty()'
    for i in range(0, len(s), 9):
        e = 'Txt.PushWord(%s, %d)' % (e, pack(s[i:i + 9]))
    print(e)
