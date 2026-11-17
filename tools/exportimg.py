import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
T = {"sharedassets1.assets": [116, 268, 321, 349], "sharedassets2.assets": [175, 219, 349, 374, 405, 427]}
for fn, ids in T.items():
    env = UnityPy.load(DATA + "/" + fn)
    f = list(env.files.values())[0]
    for pid in ids:
        t = f.objects[pid].read()
        img = t.image
        img.save(f"img/en/{t.m_Name}.png")
        print(fn, pid, t.m_Name, t.m_Width, t.m_Height, t.m_TextureFormat, "mips", t.m_MipCount)
