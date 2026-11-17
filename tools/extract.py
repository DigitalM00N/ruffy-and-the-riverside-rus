import UnityPy, sys, os
D, lang, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
env = UnityPy.load(D + "/resources.assets")
f = list(env.files.values())[0]
rows = [l.rstrip("\n").split("\t") for l in open("data/container.tsv", encoding="utf-8")]
for path, fid, pid in rows:
    if not path.startswith(lang + "/"): continue
    obj = f.objects.get(int(pid))
    if obj is None or obj.type.name != "TextAsset": 
        print("skip", path, obj and obj.type.name); continue
    d = obj.read()
    p = os.path.join(outdir, path + ".txt")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = d.m_Script
    if isinstance(data, str): data = data.encode("utf-8", "surrogateescape")
    open(p, "wb").write(data)
