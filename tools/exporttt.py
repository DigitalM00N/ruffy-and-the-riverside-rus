import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
sys.stdout.reconfigure(encoding="utf-8")
files = sorted({l.split("\t")[0] for l in open("data/alltex.tsv", encoding="utf-8") if "\ttt-" in l})
for fn in files:
    env = UnityPy.load(DATA + "/" + fn)
    for o in list(env.files.values())[0].objects.values():
        if o.type.name != "Texture2D": continue
        t = o.read()
        if not t.m_Name.startswith("tt-"): continue
        dst = "img/en" if "-english-" in t.m_Name else "img/other"
        t.image.save(f"{dst}/{t.m_Name}.png")
        if "-english-" in t.m_Name: print(fn, t.m_Name, t.m_Width, t.m_Height, t.m_TextureFormat)
