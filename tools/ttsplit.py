import glob, os, numpy as np
from PIL import Image
from scipy import ndimage as nd
os.makedirs("img/tt_icons", exist_ok=True)
sheet = []
import sys
TH = float(sys.argv[1]) if len(sys.argv) > 1 else 31
for p in sorted(glob.glob("img/en/tt-*-english-*.png")):
    name = os.path.basename(p)[:-4]
    a = np.array(Image.open(p).convert("RGBA")).astype(int)
    r,g,b,al = a[...,0],a[...,1],a[...,2],a[...,3]
    solid = al > 20
    fillc = (al>200) & (((r>235)&(g>235)&(b>235)) | ((r>235)&(g>180)&(g<235)&(b>60)&(b<150)))
    core = nd.binary_erosion(fillc, iterations=9)
    lab, n = nd.label(core)
    sizes = nd.sum(core, lab, range(1, n+1))
    from scipy.spatial import ConvexHull
    from PIL import ImageDraw
    hull = Image.new("L", (a.shape[1], a.shape[0]), 0); hd = ImageDraw.Draw(hull)
    for i, s_ in enumerate(sizes):
        if s_ < (300 if 'ps5-english-spinattack' in name else 1500): continue
        ys, xs = np.where(lab == i + 1)
        pts = np.c_[xs, ys]
        try: h = ConvexHull(pts); poly = [tuple(map(int, pts[v])) for v in h.vertices]
        except Exception: continue
        hd.polygon(poly, fill=255)
    hullm = np.array(hull) > 0
    dist = nd.distance_transform_edt(~hullm)
    icon = (dist <= TH) & solid
    if "multiswap" in name:  # ряд иконок с плюсом сохраняем целиком
        rows = np.where(icon.any(1))[0]
        if len(rows): icon[:rows.max()+1] |= solid[:rows.max()+1]
    np.save(f"img/tt_icons/{name}.npy", icon)
    out = np.array(Image.open(p).convert("RGBA")); out[~icon] = (0,0,0,0)
    bg = Image.new("RGBA", (1024,512), (200,200,200,255)); bg.alpha_composite(Image.fromarray(out))
    sheet.append(bg.convert("RGB").resize((512,256)))
S = Image.new("RGB", (512*4, 256*7))
for i, im in enumerate(sheet): S.paste(im, ((i//7)*512, (i%7)*256))
S.save("img/annot/tt_icons.jpg", quality=75)
