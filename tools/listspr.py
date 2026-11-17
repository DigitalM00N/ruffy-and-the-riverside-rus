import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy, re
sys.stdout.reconfigure(encoding="utf-8")
for fn in sys.argv[1:]:
    env = UnityPy.load(DATA + "/" + fn)
    f = list(env.files.values())[0]
    for o in f.objects.values():
        if o.type.name in ("Sprite", "Texture2D"):
            n = o.peek_name() if hasattr(o, "peek_name") else o.read().m_Name
            print(fn, o.type.name, o.path_id, n)
