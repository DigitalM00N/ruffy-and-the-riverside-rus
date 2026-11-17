"""Собирает resources.assets с русским текстом в слоте en/ и патчем шрифтов."""
import sys, os, shutil
sys.path.insert(0, os.path.dirname(__file__))
from common import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RU = os.path.join(ROOT, "ru")
BACKUP_DIR = os.environ.get("RUFFY_BACKUP", os.path.join(ROOT, "backup"))
BACKUP = os.path.join(BACKUP_DIR, "resources.assets")
OUT = os.environ.get("RUFFY_OUT", os.path.join(ROOT, "build"))
DATA_FILES = os.path.join(ROOT, "data")
SLOT = "en"

if not os.path.exists(BACKUP):
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    shutil.copy2(DATA + "/resources.assets", BACKUP)

import UnityPy
env = UnityPy.load(DATA + "/globalgamemanagers.assets", BACKUP)
env.typetree_generator = gen()
f = [x for n, x in env.files.items() if n.endswith("resources.assets")][0]

rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(DATA_FILES, "container.tsv"), encoding="utf-8")]
n = 0
for path, fid, pid in rows:
    if not path.startswith(SLOT + "/"): continue
    src = os.path.join(RU, path[len(SLOT) + 1:] + ".txt")
    if not os.path.exists(src): continue
    obj = f.objects[int(pid)]
    if obj.type.name != "TextAsset": continue
    d = obj.read()
    old = d.m_Script
    if isinstance(old, bytes): old = old.decode("utf-8", "replace")
    text = open(src, encoding="utf-8").read().replace("\r\n", "\n")
    if "\r\n" in old: text = text.replace("\n", "\r\n")
    d.m_Script = text
    d.save()
    n += 1
print("replaced text assets:", n)

# Динамический fallback-шрифт (LiberationSans SDF - Fallback): включаем multi-atlas,
# чтобы кириллица не упиралась в один атлас 512x512.
obj = f.objects.get(10117)
t = obj.read_typetree() if obj else {}
if t.get("m_Name") != "LiberationSans SDF - Fallback":
    raise SystemExit("Неподдерживаемая версия игры (ожидается v1.2.0): структура ресурсов отличается.")
t["m_IsMultiAtlasTexturesEnabled"] = 1
obj.save_typetree(t)

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "resources.assets"), "wb").write(f.save())
print("written", os.path.getsize(os.path.join(OUT, "resources.assets")))

# Название языка в меню настроек: English -> Русский (сцены level1, level2)
for lv in ("level1", "level2"):
    bk = os.path.join(BACKUP_DIR, lv)
    if not os.path.exists(bk): shutil.copy2(DATA + "/" + lv, bk)
    env2 = UnityPy.load(DATA + "/globalgamemanagers.assets", bk)
    env2.typetree_generator = gen()
    lf = [x for n, x in env2.files.items() if n.endswith(lv)][0]
    for obj in lf.objects.values():
        if obj.type.name != "MonoBehaviour": continue
        r = obj.reader; r.Position = obj.byte_start
        if b"Deutsch" not in r.read_bytes(obj.byte_size): continue
        t = obj.read_typetree()
        for l in t.get("languages", []):
            if l["code"] == 0: l["name"] = "Русский"
        obj.save_typetree(t)
    open(os.path.join(OUT, lv), "wb").write(lf.save())
    print("patched", lv)

# Картинки с текстом (sharedassets1/2): Texture2D с именем *_english заменяются на img/ru/<имя>.png
from PIL import Image
IMG = os.environ.get("RUFFY_IMG", os.path.join(ROOT, "img", "ru"))
_ru = {os.path.splitext(f)[0] for f in os.listdir(IMG)}
_rows = [l.rstrip(chr(10)).split(chr(9)) for l in open(os.path.join(DATA_FILES, "alltex.tsv"), encoding="utf-8")]
_files = sorted({r[0] for r in _rows if r[1] == "Texture2D" and r[3] in _ru})
for sa in _files:
    bk = os.path.join(BACKUP_DIR, sa)
    if not os.path.exists(bk): shutil.copy2(DATA + "/" + sa, bk)
    env3 = UnityPy.load(bk)
    sf = list(env3.files.values())[0]
    n = 0; names = set()
    for obj in sf.objects.values():
        if obj.type.name != "Texture2D": continue
        t = obj.read()
        png = os.path.join(IMG, t.m_Name + ".png")
        if not os.path.exists(png): continue
        im = Image.open(png).convert("RGBA")
        assert im.size == (t.m_Width, t.m_Height), (t.m_Name, im.size)
        t.set_image(im)
        t.save(); n += 1
        names.add(t.m_Name)
    # спрайты: «плотный» меш по контуру англ. текста -> полный прямоугольник
    import struct
    for obj in sf.objects.values():
        if obj.type.name != "Sprite": continue
        st = obj.read_typetree()
        if st["m_Name"] not in names: continue
        rd = st["m_RD"]; r = st["m_Rect"]; ppu = st["m_PixelsToUnits"]; pv = st["m_Pivot"]
        w, h = r["width"], r["height"]
        x0, x1 = -pv["x"] * w / ppu, (1 - pv["x"]) * w / ppu
        y0, y1 = -pv["y"] * h / ppu, (1 - pv["y"]) * h / ppu
        old = bytes(rd["m_IndexBuffer"]); od = bytes(rd["m_VertexData"]["m_DataSize"])
        i0, i1, i2 = struct.unpack_from("<3H", old, 0)
        P = [struct.unpack_from("<2f", od, i * 12) for i in (i0, i1, i2)]
        cross = (P[1][0]-P[0][0])*(P[2][1]-P[0][1]) - (P[1][1]-P[0][1])*(P[2][0]-P[0][0])
        pos = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
        uv = [(0, 0), (1, 0), (0, 1), (1, 1)]
        tris = [0, 2, 1, 1, 2, 3] if cross < 0 else [0, 1, 2, 2, 1, 3]
        vdata = b"".join(struct.pack("<3f", x, y, 0) for x, y in pos) + b"".join(struct.pack("<2f", *u) for u in uv)
        rd["m_VertexData"]["m_VertexCount"] = 4
        rd["m_VertexData"]["m_DataSize"] = vdata
        rd["m_IndexBuffer"] = struct.pack("<6H", *tris)
        sm = rd["m_SubMeshes"][0]; sm["indexCount"] = 6; sm["vertexCount"] = 4; sm["firstByte"] = 0; sm["firstVertex"] = 0
        rd["textureRect"] = {"x": r["x"], "y": r["y"], "width": w, "height": h}
        rd["textureRectOffset"] = {"x": 0.0, "y": 0.0}
        obj.save_typetree(st); print("sprite mesh -> quad", st["m_Name"])
    open(os.path.join(OUT, sa), "wb").write(sf.save())
    print("textures", sa, n)
