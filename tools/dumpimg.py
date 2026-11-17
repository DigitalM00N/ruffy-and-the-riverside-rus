import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
rows = [l.split("\t") for l in open("translatables.tsv", encoding="utf-8").read().splitlines() if "TranslatableImage" in l]
byfile = {}
for f, pid, _ in rows: byfile.setdefault(f, []).append(int(pid))
out = open("images.txt", "w", encoding="utf-8")
for fn, pids in byfile.items():
    env = load("globalgamemanagers.assets", fn)
    f = [x for n, x in env.files.items() if n.endswith(fn)][0]
    for pid in pids:
        t = f.objects[pid].read_typetree()
        go = f.objects[t["m_GameObject"]["m_PathID"]].read()
        out.write(f"{fn} {pid} GO={go.m_Name} {({k:v for k,v in t.items() if k not in ('m_GameObject','m_Script','m_Enabled')})}\n")
        out.write("   externals: " + str([(i+1, e.path) for i, e in enumerate(f.externals)][:8]) + "\n")
