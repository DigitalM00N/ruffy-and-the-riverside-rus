import sys; sys.path.insert(0, sys.argv[1])
from common import *
for fn in sys.argv[2:]:
    env = load(fn)
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour": continue
        try:
            t = obj.read_typetree()
        except Exception as e:
            continue
        if "m_CharacterTable" not in t: continue
        cps = sorted(c["m_Unicode"] for c in t["m_CharacterTable"])
        print(fn, obj.path_id, t["m_Name"], "mode", t.get("m_AtlasPopulationMode"), "src", t.get("m_SourceFontFile"), "chars", len(cps), "cyr", sum(1 for c in cps if 0x400<=c<0x500),
              "fallbacks", [ (x["m_FileID"],x["m_PathID"]) for x in t.get("m_FallbackFontAssetTable",[])], "atlas", t.get("m_AtlasWidth"), t.get("m_AtlasHeight"), "pt", t["m_FaceInfo"]["m_PointSize"])
