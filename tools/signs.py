import os, sys, glob, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as nd
F = "C:/Windows/Fonts/"
rng = np.random.default_rng(1)

def inpaint(img, mask, r=7):
    rgb = np.array(img.convert("RGB"))[:, :, ::-1].copy()
    out = cv2.inpaint(rgb, (mask * 255).astype(np.uint8), r, cv2.INPAINT_TELEA)[:, :, ::-1]
    a = np.array(img); a[..., :3] = np.where(mask[..., None], out, a[..., :3]); return Image.fromarray(a)

def fit_font(path, text, maxw, maxh):
    s = maxh
    while s > 6:
        f = ImageFont.truetype(path, s); b = f.getbbox(text)
        if b[2] - b[0] <= maxw and b[3] - b[1] <= maxh: return f
        s -= 2
    return ImageFont.truetype(path, 6)

def draw_center(img, text, box, font_path, fill, stroke=0, stroke_fill=None, maxh=None, noise=0.0, angle=0):
    x0, y0, x1, y1 = box
    f = fit_font(font_path, text, x1 - x0, maxh or (y1 - y0))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    b = d.textbbox((0, 0), text, font=f, stroke_width=stroke)
    x = (x0 + x1) / 2 - (b[0] + b[2]) / 2; y = (y0 + y1) / 2 - (b[1] + b[3]) / 2
    d.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if noise:
        a = np.array(layer); n = rng.random(a.shape[:2]); a[..., 3] = (a[..., 3] * np.where(n < noise, 0.35, 1.0)).astype(np.uint8)
        layer = Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.6))
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC, center=((x0 + x1) / 2, (y0 + y1) / 2))
    img.alpha_composite(layer); return img

os.makedirs("img/ru", exist_ok=True)
S = "img/signs/"

# 1. LOST -> ПРОПАЛ
im = Image.open(S + "Ballen missing schild.png").convert("RGBA"); a = np.array(im).astype(int)
m = np.zeros(a.shape[:2], bool); reg = (slice(95, 445), slice(170, 880))
dark = (a[..., 0] < 170) & (a[..., 1] < 130) & (a[..., 2] < 100)
m[reg] = nd.binary_dilation(dark[reg], iterations=5)
im = inpaint(im, m, 9)
draw_center(im, "ПРОПАЛ", (150, 105, 875, 430), F + "georgiab.ttf", (70, 32, 12, 255))
im.save("img/ru/Ballen missing schild.png")

# 2. WANTED -> РОЗЫСК
im = Image.open(S + "Forest_Runnerr_WANTED_poster.png").convert("RGBA"); a = np.array(im).astype(int)
m = np.zeros(a.shape[:2], bool); reg = (slice(16, 104), slice(36, 222))
dark = (a[..., 0] < 170) & (a[..., 1] < 130) & (a[..., 2] < 100)
m[reg] = nd.binary_dilation(dark[reg], iterations=2)
im = inpaint(im, m, 4)
draw_center(im, "РОЗЫСК", (38, 22, 220, 98), F + "georgiab.ttf", (70, 32, 12, 255))
im.save("img/ru/Forest_Runnerr_WANTED_poster.png")

# 3. SHOP -> ЛАВКА (мел на красной доске; выбран вариант Inkfree b2 warp60)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chalk import chalk_text
im = Image.open(S + "Mole_shop_Icon.png").convert("RGBA"); a = np.array(im).astype(int)
red = (a[..., 0] > 110) & (a[..., 1] < 110) & (a[..., 2] < 90) & (a[..., 3] > 200)
red[:340] = False
board = nd.binary_fill_holes(nd.binary_closing(red, iterations=12))
board_in = nd.binary_erosion(board, iterations=9)
chalk = (a[..., 0] > 150) & (a[..., 1] > 100) & (a[..., 2] > 85)
m = np.zeros(a.shape[:2], bool); m[:, 145:422] = True
m &= nd.binary_erosion(board, iterations=4) & nd.binary_dilation(chalk, iterations=3)
# заливка: известные пиксели — только внутренность доски без мела, затем размытие внутри маски
rgb = np.array(im.convert("RGB")).astype(np.float32)
known = board_in & ~m
acc = np.zeros_like(rgb); w = np.zeros(m.shape, np.float32)
for sig in (4, 8, 16, 32, 64):
    k = nd.gaussian_filter(known.astype(np.float32), sig)
    v = np.stack([nd.gaussian_filter(rgb[..., c] * known, sig) for c in range(3)], -1)
    fillc = v / np.maximum(k, 1e-4)[..., None]
    sel = (w == 0) & (k > 0.02)
    acc[sel] = fillc[sel]; w[sel] = 1
acc[w == 0] = np.median(rgb[known], 0)
noise = np.random.default_rng(5).normal(0, 5, rgb.shape)
out = np.array(im); out[..., :3] = np.where(m[..., None], np.clip(acc + noise, 0, 255), rgb).astype(np.uint8)
im = Image.fromarray(out)
t = chalk_text("ЛАВКА", F + "Inkfree.ttf", 262, 72, angle=7, bold=2, warp=60)
im.alpha_composite(t, (289 - t.width // 2, 432 - t.height // 2))
im.save("img/ru/Mole_shop_Icon.png")

# 4. CAP LAB (мел, прозрачный фон)
p = glob.glob(S + "Gro*")[0]; im = Image.open(p).convert("RGBA"); a = np.array(im)
for x0, y0, x1, y1 in [(505, 60, 1640, 268), (20, 160, 405, 375), (1688, 335, 2005, 548), (1400, 665, 1985, 800), (192, 912, 366, 1014)]:
    a[y0:y1, x0:x1, 3] = 0
im = Image.fromarray(a)
W = (255, 255, 255, 235); SP = F + "segoeprb.ttf"
draw_center(im, "КЕПКИ", (540, 70, 1610, 255), SP, W, noise=0.12)
draw_center(im, "выпуски", (26, 170, 400, 280), SP, W, noise=0.12)
draw_center(im, "синий", (60, 290, 360, 370), SP, W, noise=0.12)
draw_center(im, "вышивка", (1693, 380, 2000, 500), SP, W, noise=0.12)
draw_center(im, "цвета ткани", (1406, 672, 1976, 794), SP, W, noise=0.12)
draw_center(im, "красный", (170, 915, 400, 1010), SP, W, noise=0.12)
im.save("img/ru/" + os.path.basename(p))

# 5. SCORE / YEAH-O-METER — отдельный скрипт с пиксельным шрифтом
import runpy; runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "score.py"))

# превью
names = ["Ballen missing schild", "Forest_Runnerr_WANTED_poster", "Mole_shop_Icon", os.path.basename(p)[:-4], "ScoreUIRework3"]
ims = []
for n in names:
    i = Image.open(f"img/ru/{n}.png").convert("RGBA"); i.thumbnail((600, 600)); bg = Image.new("RGBA", i.size, (110, 110, 110, 255)); bg.alpha_composite(i); ims.append(bg.convert("RGB"))
W_ = sum(i.width for i in ims); H_ = max(i.height for i in ims); P = Image.new("RGB", (W_, H_), (50, 50, 50)); x = 0
for i in ims: P.paste(i, (x, 0)); x += i.width
P.save("img/preview/signs_ru.jpg", quality=85); print("ok")
