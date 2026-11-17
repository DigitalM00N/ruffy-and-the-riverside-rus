import UnityPy, sys, collections
D = sys.argv[1]
env = UnityPy.load(D + "/globalgamemanagers", D + "/resources.assets")
gg = [f for n,f in env.files.items() if n.endswith("globalgamemanagers")][0]
for obj in gg.objects.values():
    if obj.type.name == "ResourceManager":
        t = obj.read_typetree()
        out = open("data/container.tsv","w",encoding="utf-8")
        for path, ptr in t["m_Container"]:
            out.write(f"{path}\t{ptr['m_FileID']}\t{ptr['m_PathID']}\n")
        print(len(t["m_Container"]))
