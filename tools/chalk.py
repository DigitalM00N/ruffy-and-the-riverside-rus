import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
def chalk_text(text, font_path, w, h, angle=0, seed=3, color=(246, 240, 232), bold=0, warp=25):
    """Меловая надпись, вписанная в w×h (до поворота)."""
    rng = np.random.default_rng(seed)
    S = 3  # суперсэмплинг
    size = h * S
    while True:
        f = ImageFont.truetype(font_path, size)
        b = f.getbbox(text, stroke_width=bold * S)
        if (b[2] - b[0]) <= w * S and (b[3] - b[1]) <= h * S or size < 10: break
        size -= 2
    W, H = b[2] - b[0] + 40 * S, b[3] - b[1] + 40 * S
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((20 * S - b[0], 20 * S - b[1]), text, font=f, fill=255, stroke_width=bold * S, stroke_fill=255)
    m = np.array(m).astype(np.float32) / 255
    # неровный край: смещение по шуму
    dx = nd.gaussian_filter(rng.standard_normal(m.shape), 6) * warp
    dy = nd.gaussian_filter(rng.standard_normal(m.shape), 6) * warp
    Y, X = np.mgrid[:H, :W].astype(np.float32)
    m = cv2.remap(m, X + dx.astype(np.float32), Y + dy.astype(np.float32), cv2.INTER_LINEAR)
    # меловая фактура: штрихи + зерно
    streak = nd.gaussian_filter(rng.standard_normal(m.shape), (1.2 * S, 5 * S))
    streak = (streak - streak.mean()) / (streak.std() + 1e-6)
    grain = rng.random(m.shape)
    tex = np.clip(0.78 + 0.22 * streak, 0, 1) * np.where(grain < 0.10, 0.45, 1.0)
    alpha = np.clip(m, 0, 1) * tex
    rgba = np.zeros((H, W, 4), np.uint8); rgba[..., :3] = color; rgba[..., 3] = (alpha * 255).astype(np.uint8)
    im = Image.fromarray(rgba).resize((W // S, H // S), Image.LANCZOS)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im.crop(im.getbbox())
