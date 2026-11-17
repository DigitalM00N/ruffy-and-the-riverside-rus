import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
def textmask(a):
    r,g,b,al = a[...,0],a[...,1],a[...,2],a[...,3]
    navy = (al>150) & (b>r+40) & (b<150) & (r<70) & (g<100)
    filled = nd.binary_fill_holes(nd.binary_dilation(navy, iterations=2))
    return navy, filled
out = {}
for name in sys.argv[1:]:
    im = Image.open(f"img/en/{name}.png").convert("RGBA"); a = np.array(im).astype(int)
    navy, filled = textmask(a)
    lab, n = nd.label(nd.binary_dilation(filled, iterations=7))
    words = []
    for sl in nd.find_objects(lab):
        if filled[sl].sum() < 300: continue
        words.append([sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])
    words.sort(key=lambda b: (b[1]//30, b[0]))
    out[name] = words
    bg = Image.new("RGBA", im.size, (255,255,255,255)); bg.alpha_composite(im); d = ImageDraw.Draw(bg)
    f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
    for k,(x0,y0,x1,y1) in enumerate(words):
        d.rectangle([x0,y0,x1,y1], outline=(255,0,0), width=2); d.text((x0+2,y0+2), str(k), fill=(255,0,255), font=f)
    bg.convert("RGB").save(f"img/annot/{name}_w.jpg", quality=80)
json.dump(out, open("img/words.json","w"))
for k,v in out.items(): print(k, len(v))
