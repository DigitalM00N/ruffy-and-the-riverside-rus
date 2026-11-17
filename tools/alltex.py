import sys, os, glob; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
sys.stdout.reconfigure(encoding="utf-8")
files = sorted(glob.glob(DATA + "/sharedassets*.assets")) + [DATA + "/resources.assets"] + sorted(glob.glob(DATA + "/level*"))
files = [f for f in files if not f.endswith((".resS", ".resource"))]
out = open("data/alltex.tsv", "w", encoding="utf-8")
for fp in files:
    env = UnityPy.load(fp)
    for o in list(env.files.values())[0].objects.values():
        if o.type.name in ("Texture2D", "Sprite"):
            try: n = o.peek_name()
            except Exception: n = o.read().m_Name
            out.write(f"{os.path.basename(fp)}\t{o.type.name}\t{o.path_id}\t{n}\n")
