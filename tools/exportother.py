import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy, re
pre = ("PC_", "Xbox_", "PS5_", "Switch_", "questheader_", "settings_", "camera_", "volume_")
for fn in ("sharedassets1.assets", "sharedassets2.assets"):
    env = UnityPy.load(DATA + "/" + fn)
    for o in list(env.files.values())[0].objects.values():
        if o.type.name != "Texture2D": continue
        t = o.read()
        if t.m_Name.startswith(pre) and "english" not in t.m_Name:
            t.image.save(f"img/other/{t.m_Name}.png")
