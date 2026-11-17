import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
for lv in ("level1", "level2"):
    env = load("globalgamemanagers.assets", lv)
    f = [x for n, x in env.files.items() if n.endswith(lv)][0]
    for obj in f.objects.values():
        if obj.type.name != "MonoBehaviour": continue
        r = obj.reader; r.Position = obj.byte_start
        if b"Deutsch" not in r.read_bytes(obj.byte_size): continue
        try: t = obj.read_typetree()
        except Exception as e: print(lv, obj.path_id, "ERR", e); continue
        def walk(x, p=""):
            if isinstance(x, dict):
                for k, v in x.items(): walk(v, p + "." + k)
            elif isinstance(x, list):
                for i, v in enumerate(x): walk(v, f"{p}[{i}]")
            elif isinstance(x, str) and x in ("English","Deutsch") or (isinstance(x,str) and "Espa" in x):
                print(lv, obj.path_id, p, repr(x))
        walk(t)
        print(lv, obj.path_id, list(t.keys()))
