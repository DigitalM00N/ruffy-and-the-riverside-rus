import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
want = set(l.rstrip("\n") for l in open("signlist.txt", encoding="utf-8"))
rows = [l.rstrip("\n").split("\t") for l in open("data/alltex.tsv", encoding="utf-8")]
files = sorted({r[0] for r in rows if r[1] == "Texture2D" and r[3] in want})
done = set()
for fn in files:
    env = UnityPy.load(DATA + "/" + fn)
    for o in list(env.files.values())[0].objects.values():
        if o.type.name != "Texture2D": continue
        t = o.read()
        if t.m_Name in want and t.m_Name not in done:
            try:
                t.image.save(f"img/signs/{t.m_Name.strip()}.png"); done.add(t.m_Name)
            except Exception as e: print("fail", t.m_Name, e)
print(len(done))
