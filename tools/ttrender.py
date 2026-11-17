import glob, os, sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(__file__))
import render as R
R.STY["ty"] = ((255, 242, 70), (247, 75, 8)); R.STY["tb"] = ((165, 238, 255), (30, 140, 235))
DARK = (33, 4, 33, 255)
TXT = {
  "beejump": [("В воздухе", "tb"), ("Пчелиный прыжок", "ty")],
  "multiswap": [("МУЛЬТИОБМЕН", "ty")],
  "run": [("Бег", "ty")],
  "scan": [("Взять", "ty")],
  "spinattack": [("Держи", "tb"), ("Атака вихрем", "ty")],
  "stomp attack": [("В воздухе", "tb"), ("Удар сверху", "ty")],
  "throw": [("Бросок", "ty")],
}
os.makedirs("img/ru", exist_ok=True)
sheet = []
for p in sorted(glob.glob("img/en/tt-*-english-*.png")):
    name = os.path.basename(p)[:-4]; act = name.split("-english-")[1]
    src = Image.open(p).convert("RGBA"); a = np.array(src)
    icon = np.load(f"img/tt_icons/{name}.npy")
    solid = a[..., 3] > 40
    txt = solid & ~nd.binary_dilation(icon, iterations=4)
    txt = nd.binary_opening(txt, iterations=2)
    lab, n = nd.label(txt)
    comps = []
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = lab[sl] == i
        if m.sum() < 2500: continue
        comps.append((sl[0].start, sl[0].stop, sl[1].start, sl[1].stop))
    want = TXT[act]
    comps.sort(key=lambda c: (c[0] + c[1]) / 2)
    cy = [(c[0] + c[1]) / 2 for c in comps]
    k = len(want)
    gaps = sorted(range(1, len(cy)), key=lambda i: cy[i] - cy[i-1], reverse=True)[:k-1]
    cuts = sorted(gaps); groups = []; prev = 0
    for c in cuts + [len(comps)]: groups.append(comps[prev:c]); prev = c
    out = np.array(src); out[~icon] = (0, 0, 0, 0)
    im = Image.fromarray(out)
    iy = np.where(icon.any(1))[0]
    for (text, sty), g in zip(want, groups):
        y0 = min(c[0] for c in g); y1 = max(c[1] for c in g); x0 = min(c[2] for c in g); x1 = max(c[3] for c in g)
        band = icon[y0:y1].any(0); ix = np.where(band)[0]
        h = (y1 - y0) * 0.50
        cx = (x0 + x1) / 2
        if len(ix):
            icx = (ix.min() + ix.max()) / 2
            if icx > cx:   # иконка справа: текст прижат к ней справа
                anchor, x = "rc", ix.min() - 14; maxw = x - 4
            else:          # иконка слева
                anchor, x = "lc", ix.max() + 14; maxw = 1020 - x
        else:
            anchor, x, maxw = "cc", int(cx), 1012
        lab_img = R.label(text, h, sty, 0.075, False, stroke_col=DARK, outer=((255, 255, 255, 255), 0.075))
        if lab_img.width > maxw:
            lab_img = lab_img.resize((maxw, int(lab_img.height * maxw / lab_img.width)), Image.LANCZOS)
        if anchor == "cc":
            x = min(max(x, lab_img.width // 2 + 4), 1024 - lab_img.width // 2 - 4)
        R.place(im, lab_img, x, (y0 + y1) // 2, anchor, -3)
    im.save(f"img/ru/{name}.png")
    bg = Image.new("RGBA", im.size, (200, 200, 200, 255)); bg.alpha_composite(im)
    sheet.append(bg.convert("RGB").resize((512, 256)))
S = Image.new("RGB", (512 * 4, 256 * 7))
for i, s in enumerate(sheet): S.paste(s, ((i // 7) * 512, (i % 7) * 256))
S.save("img/preview/tt_ru.jpg", quality=80)
print("ok")
