# Generate monomorphic persistent 16-way tries keyed by an Int (stand-ins for Racket's
# immutable eq?-hash tables). Generic versions do not work: `new ArrayList<ITrie<E>>()` inside a
# generic class crashes the runtime (NomClassType::GenerateRTInstantiation).
# usage: trie_gen.py interfaces|classes Name:EntryType ...
# (needs list types <EntryType>List with classes <EntryType minus the I>Cons, see lists_gen.py;
#  Collect does not take an ArrayList: project types inside type arguments of instance-method
#  signatures are not devolved by the benchmark generator)
import sys

def iface(n, e):
    return ('# persistent 16-way trie of %s, keyed by an Int\ninterface I%sTrie\n{\n'
            '\tfun Get(Int id, %s dflt) : %s;\n\tfun Put(Int id, %s e) : I%sTrie;\n'
            '\tfun Collect(%sList acc) : %sList;\n}\n\n' % (e, n, e, e, e, n, e, e))

def classes(n, e):
    I = 'I%sTrie' % n
    return '''# an empty subtrie at the level that consumes the base-16 digit `div` of the id
class %(n)sTrieEmpty implements %(I)s
{
	private readonly Int div;
	public constructor(Int d)
	{
		div = d;
	}
	public fun Get(Int id, %(e)s dflt) : %(e)s
	{
		return dflt;
	}
	public fun Put(Int id, %(e)s e) : %(I)s
	{
		return new %(n)sTrieLeaf(id, e, div);
	}
	public fun Collect(%(e)sList acc) : %(e)sList
	{
		return acc;
	}
}

# a subtrie with a single entry (split into a node when a second id arrives)
class %(n)sTrieLeaf implements %(I)s
{
	private readonly Int key;
	private readonly %(e)s entry;
	private readonly Int div;
	public constructor(Int k, %(e)s e, Int d)
	{
		key = k;
		entry = e;
		div = d;
	}
	public fun Get(Int id, %(e)s dflt) : %(e)s
	{
		if (id == key)
		{
			return entry;
		}
		return dflt;
	}
	public fun Put(Int id, %(e)s e) : %(I)s
	{
		if (id == key)
		{
			return Tries.New%(n)sLeaf(id, e, div);
		}
		%(I)s empty = Tries.New%(n)sEmpty(div * 16);
		ArrayList<%(I)s> kids = new ArrayList<%(I)s>();
		Int i = 0;
		while (i < 16)
		{
			kids.Add(empty);
			i = i + 1;
		}
		%(I)s node = Tries.New%(n)sNode(kids, div);
		return node.Put(key, entry).Put(id, e);
	}
	public fun Collect(%(e)sList acc) : %(e)sList
	{
		return Tries.Cons%(n)s(entry, acc);
	}
}

class %(n)sTrieNode implements %(I)s
{
	private readonly ArrayList<%(I)s> kids;
	private readonly Int div;
	public constructor(ArrayList<%(I)s> k, Int d)
	{
		kids = k;
		div = d;
	}
	public fun Get(Int id, %(e)s dflt) : %(e)s
	{
		return kids.Get((id / div) %% 16).Get(id, dflt);
	}
	public fun Put(Int id, %(e)s e) : %(I)s
	{
		Int slot = (id / div) %% 16;
		ArrayList<%(I)s> copy = new ArrayList<%(I)s>();
		Int i = 0;
		while (i < 16)
		{
			copy.Add(kids.Get(i));
			i = i + 1;
		}
		copy.Set(slot, kids.Get(slot).Put(id, e));
		return Tries.New%(n)sNode(copy, div);
	}
	public fun Collect(%(e)sList acc) : %(e)sList
	{
		foreach (%(I)s k in kids)
		{
			acc = k.Collect(acc);
		}
		return acc;
	}
}

''' % {'n': n, 'e': e, 'I': I}

def factories(specs):
    o = ['# factories: a class that the benchmark generator turns into a record must not instantiate\n'
         '# itself in its own methods (the generator recurses forever)\nclass Tries\n{\n']
    for n, e in specs:
        I = 'I%sTrie' % n
        o.append('\tpublic static fun New%sEmpty(Int div) : %s\n\t{\n\t\treturn new %sTrieEmpty(div);\n\t}\n' % (n, I, n))
        o.append('\tpublic static fun New%sLeaf(Int id, %s e, Int div) : %s\n\t{\n\t\treturn new %sTrieLeaf(id, e, div);\n\t}\n' % (n, e, I, n))
        o.append('\tpublic static fun Cons%s(%s e, %sList l) : %sList\n\t{\n\t\treturn new %sCons(e, l);\n\t}\n' % (n, e, e, e, e[1:]))
        o.append('\tpublic static fun New%sNode(ArrayList<%s> kids, Int div) : %s\n\t{\n\t\treturn new %sTrieNode(kids, div);\n\t}\n' % (n, I, I, n))
    o.append('}\n\n')
    return ''.join(o)

mode = sys.argv[1]
specs = [tuple(s.split(':')) for s in sys.argv[2:]]
if mode == 'interfaces':
    sys.stdout.write(''.join(iface(n, e) for n, e in specs))
else:
    sys.stdout.write(''.join(classes(n, e) for n, e in specs) + factories(specs))
