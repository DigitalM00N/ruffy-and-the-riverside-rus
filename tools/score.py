import numpy as np, cv2
from PIL import Image, ImageFilter
from scipy import ndimage as nd
G = {
"О": [".####.","##..##","##..##","##..##","##..##","##..##",".####."],
"Ч": ["##..##","##..##","##..##",".#####","....##","....##","....##"],
"К": ["##..##","##.##.","####..","###...","####..","##.##.","##..##"],
"И": ["##..##","##..##","##.###","######","###.##","##..##","##..##"],
"Й": [".####.","##..##","##.###","######","###.##","##..##","##..##"],
"Е": ["######","##....","##....","#####.","##....","##....","######"],
"-": ["......","......","......",".####.","......","......","......"],
"М": ["##..##","######","######","##..##","##..##","##..##","##..##"],
"Т": ["######","..##..","..##..","..##..","..##..","..##..","..##.."],
"Р": ["#####.","##..##","##..##","#####.","##....","##....","##...."],
}
def text_mask(txt):
    cols = []; HH = max(len(G[c]) for c in txt)
    for i, ch in enumerate(txt):
        rows = ["." * len(G[ch][0])] * (HH - len(G[ch])) + G[ch]
        g = np.array([[c == "#" for c in row] for row in rows])
        cols.append(g)
        if i < len(txt) - 1: cols.append(np.zeros((HH, 1), bool))
    return np.concatenate(cols, 1)
def render(txt, unit, colors, glow=True):
    m = text_mask(txt); pad = 2
    m = np.pad(m, pad)
    H, W = m.shape
    fill = np.zeros((H, W, 4), np.uint8)
    x = pad
    for i, ch in enumerate(txt):
        w = len(G[ch][0]); fill[:, x:x + w][m[:, x:x + w]] = colors[i]; x += w + 1
    outline = nd.binary_dilation(m, structure=np.ones((3, 3)))
    big = lambda arr: np.kron(arr, np.ones((unit, unit), arr.dtype)) if arr.ndim == 2 else np.kron(arr, np.ones((unit, unit, 1), arr.dtype))
    fill_b = big(fill); out_b = big(outline.astype(np.uint8)) > 0
    img = np.zeros_like(fill_b)
    img[out_b] = (21, 0, 0, 255)
    img[fill_b[..., 3] > 0] = fill_b[fill_b[..., 3] > 0]
    # жёлтое свечение
    glow = Image.fromarray((out_b * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(unit * 0.9))
    g = np.zeros_like(img); g[..., 0] = 255; g[..., 1] = 245; g[..., 2] = 0; g[..., 3] = (np.array(glow) * 0.75).astype(np.uint8)
    if not glow: g[..., 3] = 0
    base = Image.fromarray(g); base.alpha_composite(Image.fromarray(img)); return base

src = Image.open("img/signs/ScoreUIRework3.png").convert("RGBA"); a = np.array(src)
mask = np.zeros(a.shape[:2], np.uint8)
mask[98:174, 64:352] = 255; mask[224:262, 128:376] = 255
rgb = cv2.inpaint(a[..., :3][:, :, ::-1].copy(), mask, 9, cv2.INPAINT_TELEA)[:, :, ::-1]
al = cv2.inpaint(a[..., 3].copy(), mask, 9, cv2.INPAINT_TELEA)
b = a.copy(); b[..., :3] = rgb; b[..., 3] = al
im = Image.fromarray(b)
sc = render("ОЧКИ", 8, [(255, 253, 0, 255)] * 4)
im.alpha_composite(sc, (207 - sc.width // 2, 137 - sc.height // 2))
stops = [(222, 90, 222), (190, 110, 235), (150, 140, 240), (95, 185, 235), (125, 210, 175), (170, 210, 120), (205, 200, 80), (235, 190, 40), (252, 182, 0)]
ym = render("ЙЕ-О-МЕТР", 3, [c + (255,) for c in stops])
im.alpha_composite(ym, (252 - ym.width // 2, 243 - ym.height // 2))
im.save("img/ru/ScoreUIRework3.png")
bg = Image.new("RGBA", im.size, (90, 90, 90, 255)); bg.alpha_composite(im)
o = Image.new("RGBA", src.size, (90, 90, 90, 255)); o.alpha_composite(src)
c = Image.new("RGB", (600, 600)); c.paste(o.convert("RGB"), (0, 0)); c.paste(bg.convert("RGB"), (0, 300))
c.resize((1200, 1200), Image.NEAREST).save("img/preview/score_cmp.png"); print("ok")
