"""Рендер русских надписей поверх картинок. Спецификации в img/specs.py"""
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as nd
FONT = "C:/Windows/Fonts/comicz.ttf"
STY = {"y": ((248, 236, 130), (247, 172, 5)), "b": ((120, 200, 250), (40, 110, 210)),
       "w": ((255, 255, 255), (250, 250, 250)), "p": ((255, 247, 66), (255, 196, 0))}
NAVY = (5, 50, 82, 255)

def textmask(a):
    r,g,b,al = a[...,0],a[...,1],a[...,2],a[...,3]
    navy = (al>120) & (b>r+40) & (b<150) & (r<70) & (g<100)
    filled = nd.binary_fill_holes(nd.binary_dilation(navy, iterations=2))
    return filled

def erase(im, rects, extra=None, grow=4, shadow=16, restore=None):
    a = np.array(im).astype(int)
    filled = textmask(a) if extra is None else extra(a)
    region = np.zeros(filled.shape, bool)
    for x0,y0,x1,y1 in rects: region[y0:y1, x0:x1] = True
    m = nd.binary_dilation(filled & region, iterations=grow)
    # тень: тёмные полупрозрачные пиксели рядом с текстом
    near = nd.binary_dilation(filled & region, iterations=shadow)
    dark = (a[...,0]<70)&(a[...,1]<70)&(a[...,2]<90)&(a[...,3]<250)
    m |= near & dark & region
    out = np.array(im); out[m] = (255,255,255,0)
    # восстановление фона из версий картинки на других языках
    if restore:
        todo = m.copy()
        for vp in restore:
            v = Image.open(vp).convert("RGBA")
            if v.size != im.size: continue
            va = np.array(v).astype(int)
            vf = textmask(va)
            vdark = (va[...,0]<70)&(va[...,1]<70)&(va[...,2]<90)&(va[...,3]<250)
            bad = nd.binary_dilation(vf, iterations=grow+2) | (nd.binary_dilation(vf, iterations=shadow) & vdark)
            ok = todo & ~bad
            out[ok] = np.array(v)[ok]; todo &= ~ok
            if not todo.any(): break
    return Image.fromarray(out)

def label(text, h, style="y", outline=None, shadow=True, pad=None, stroke_col=NAVY, font=FONT, outer=None, hard_shadow=False):
    """Рисует надпись высотой примерно h px (кегль подбирается по высоте прописных)."""
    size = int(h * 1.05)
    f = ImageFont.truetype(font, size)
    bw = max(1, int(size * 0.035))
    sw = max(2, int(size * (outline if outline is not None else 0.10))) + bw
    ow = int(size * outer[1]) if outer else 0
    sw_all = sw + ow
    bb = f.getbbox(text, stroke_width=sw_all)
    W, H = bb[2]-bb[0] + sw_all*2 + int(size*0.3), bb[3]-bb[1] + sw_all*2 + int(size*0.3)
    ox, oy = -bb[0] + sw_all, -bb[1] + sw_all
    # маска заливки
    fill_m = Image.new("L", (W, H), 0); ImageDraw.Draw(fill_m).text((ox, oy), text, font=f, fill=255, stroke_width=bw, stroke_fill=255)
    stroke_m = Image.new("L", (W, H), 0); ImageDraw.Draw(stroke_m).text((ox, oy), text, font=f, fill=255, stroke_width=sw, stroke_fill=255)
    top, bot = STY[style]
    ys = np.linspace(0, 1, H)[:, None]
    fa = np.array(fill_m) > 0
    rows = np.where(fa.any(1))[0]; y0, y1 = (rows[0], rows[-1]) if len(rows) else (0, H)
    t = np.clip((np.arange(H) - y0) / max(1, y1 - y0), 0, 1)[:, None]
    grad = np.zeros((H, W, 4), np.uint8)
    for c in range(3): grad[..., c] = (top[c] + (bot[c]-top[c]) * t).astype(np.uint8)
    grad[..., 3] = 255
    gimg = Image.fromarray(grad)
    res = Image.new("RGBA", (W, H), (0,0,0,0))
    if outer:
        om = Image.new("L", (W, H), 0); ImageDraw.Draw(om).text((ox, oy), text, font=f, fill=255, stroke_width=sw_all, stroke_fill=255)
        stroke_m_sh = om
    else: stroke_m_sh = stroke_m
    if shadow:
        sh = Image.new("RGBA", (W, H), (0,0,0,0))
        sh.putalpha(stroke_m_sh.point(lambda v: int(v*0.55)))
        if not hard_shadow: sh = sh.filter(ImageFilter.GaussianBlur(max(1, size*0.04)))
        res.alpha_composite(sh, (int(size*0.06), int(size*0.08)))
    if outer:
        o_img = Image.new("RGBA", (W, H), outer[0]); o_img.putalpha(om); res.alpha_composite(o_img)
    st = Image.new("RGBA", (W, H), stroke_col); st.putalpha(stroke_m)
    res.alpha_composite(st)
    gimg.putalpha(fill_m); res.alpha_composite(gimg)
    return res.crop(res.getbbox())

def place(base, img, x, y, anchor="lt", angle=0, maxw=None):
    if maxw and img.width > maxw:
        img = img.resize((maxw, int(img.height * maxw / img.width)), Image.LANCZOS)
    if angle: img = img.rotate(angle, resample=Image.BICUBIC, expand=True)
    w, h = img.size
    if anchor[0] == "c": x -= w//2
    elif anchor[0] == "r": x -= w
    if anchor[1] == "c": y -= h//2
    elif anchor[1] == "b": y -= h
    base.alpha_composite(img, (int(x), int(y)))

if __name__ == "__main__":
    sys.path.insert(0, "img"); import specs
    os.makedirs("img/ru", exist_ok=True); os.makedirs("img/preview", exist_ok=True)
    only = sys.argv[1:]
    for name, sp in specs.SPECS.items():
        if only and name not in only: continue
        im = Image.open(f"img/en/{name}.png").convert("RGBA")
        if sp.get("blank"): im = Image.new("RGBA", im.size, (255,255,255,0))
        else:
            import glob
            base = name.split("_")[0] + "_"
            rest = sorted(glob.glob(f"img/other/{base}*.png"), key=lambda p: ("german" not in p, p))
            im = erase(im, sp["erase"], extra=sp.get("mask"), grow=sp.get("grow", 4), restore=rest)
        prev_r = 0
        for it in sp["items"]:
            text, x, y, h = it[:4]; o = it[4] if len(it) > 4 else {}
            lab = label(text, h, o.get("style", "y"), o.get("outline"), o.get("shadow", True), stroke_col=o.get("stroke", NAVY), font=o.get("font", FONT), outer=o.get("outer"), hard_shadow=o.get("hard", False))
            if x is None: x = prev_r + o.get("gap", int(h*0.35))
            place(im, lab, x, y, o.get("anchor", "lc"), o.get("angle", 0), o.get("maxw"))
            prev_r = x + lab.width
        im.save(f"img/ru/{name}.png")
        bg = Image.new("RGBA", im.size, (225,225,225,255)); bg.alpha_composite(im)
        bg.convert("RGB").save(f"img/preview/{name}.jpg", quality=85)
        print("ok", name)
