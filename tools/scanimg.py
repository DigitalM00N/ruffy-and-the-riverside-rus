import sys, os, struct, glob; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
want = {1071: 'TranslatableImage', 749: 'TranslatableChild', 2469: 'TranslatedText', 2571:'TranslatedTextPro', 1178:'Translatable'}
files = sorted(glob.glob(DATA + "/level*")) + sorted(glob.glob(DATA + "/sharedassets*.assets")) + [DATA + "/resources.assets"]
files = [f for f in files if not f.endswith(".resS") and not f.endswith(".resource")]
out = open("translatables.tsv", "w", encoding="utf-8")
from collections import Counter
tot = Counter()
for fp in files:
    try: env = UnityPy.load(fp)
    except Exception as e: print("fail", fp, e); continue
    f = list(env.files.values())[0]
    ggm = [i+1 for i, e in enumerate(f.externals) if e.path.endswith("globalgamemanagers.assets")]
    if not ggm: continue
    c = Counter()
    for o in f.objects.values():
        if o.type.name != "MonoBehaviour": continue
        r = o.reader; r.Position = o.byte_start
        raw = r.read_bytes(min(o.byte_size, 32))
        fid, pid = struct.unpack_from("<iq", raw, 16)
        if fid in ggm and pid in want:
            c[want[pid]] += 1
            out.write(f"{os.path.basename(fp)}\t{o.path_id}\t{want[pid]}\n")
    if c: print(os.path.basename(fp), dict(c)); tot.update(c)
print(tot)
