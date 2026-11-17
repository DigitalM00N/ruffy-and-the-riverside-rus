import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
env = UnityPy.load(DATA + "/globalgamemanagers.assets", sys.argv[1]); env.typetree_generator = gen()
f = [x for n, x in env.files.items() if n.endswith("resources.assets")][0]
rows = [l.rstrip("\n").split("\t") for l in open("data/container.tsv", encoding="utf-8")]
pid = [int(p) for a,b,p in rows if a == "en/ui/title"][0]
s=f.objects[pid].read().m_Script; print(type(s), repr(s.encode("utf-8","surrogateescape")[:60]) if isinstance(s,str) else s[:60])
print(f.objects[10117].read_typetree()["m_IsMultiAtlasTexturesEnabled"])
