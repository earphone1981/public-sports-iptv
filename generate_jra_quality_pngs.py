from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'public_sports_logos_github_43' / 'jra_quality'
OUT.mkdir(parents=True, exist_ok=True)
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_OBLIQUE = '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'


def font_for(text, max_w, max_h, path=FONT_BOLD):
    size = max(12, int(max_h))
    while size > 10:
        f = ImageFont.truetype(path, size)
        box = f.getbbox(text)
        if box[2] - box[0] <= max_w and box[3] - box[1] <= max_h:
            return f
        size -= 1
    return ImageFont.truetype(path, 10)


def main_ch(src):
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    d = ImageDraw.Draw(im)
    y0 = int(h * 0.68)
    # Clean only the old right-side text area; keep the original GCH/jockey mark.
    d.rounded_rectangle((int(w * .62), y0 + int(h*.035), int(w*.965), int(h*.93)), radius=int(h*.035), fill=(7, 105, 58, 255))
    x1, y1, x2, y2 = int(w*.64), int(h*.725), int(w*.955), int(h*.91)
    d.rounded_rectangle((x1, y1, x2, y2), radius=int(h*.025), fill=(247, 204, 54, 255), outline=(222, 172, 22, 255), width=max(2, w//280))
    text = 'MAIN Ch'
    f = font_for(text, (x2-x1)*.88, (y2-y1)*.63, FONT_OBLIQUE)
    b = d.textbbox((0,0), text, font=f)
    tx = x1 + (x2-x1-(b[2]-b[0]))/2
    ty = y1 + (y2-y1-(b[3]-b[1]))/2 - b[1]
    d.text((tx,ty), text, font=f, fill=(17,17,17,255))
    return im


def local_web5(src):
    im = Image.open(src).convert('RGBA')
    w, h = im.size
    d = ImageDraw.Draw(im)
    y0 = int(h * .67)
    # Replace the old HOKKAIDO/LOCAL lower panel completely.
    d.rounded_rectangle((int(w*.012), y0, int(w*.988), int(h*.965)), radius=int(h*.035), fill=(1, 104, 58, 255), outline=(29, 187, 87, 255), width=max(2,w//260))
    sep_x = int(w*.685)
    d.line((sep_x, int(h*.725), sep_x, int(h*.91)), fill='white', width=max(2,w//300))
    f1 = font_for('LOCAL', w*.55, h*.18, FONT_OBLIQUE)
    f2 = font_for('WEB5', w*.25, h*.15, FONT_OBLIQUE)
    b1 = d.textbbox((0,0),'LOCAL',font=f1)
    b2 = d.textbbox((0,0),'WEB5',font=f2)
    d.text((int(w*.12), int(h*.79)-b1[1]), 'LOCAL', font=f1, fill='white')
    d.text((int(w*.73), int(h*.80)-b2[1]), 'WEB5', font=f2, fill='white')
    return im


def save_pair(im, stem):
    for q in ('hq','lq'):
        im.convert('RGB').save(OUT / f'{stem}_{q}.png', optimize=True)


def main():
    gch = main_ch(ROOT / 'gch.png')
    east = Image.open(ROOT / 'east_web3.png').convert('RGBA')
    west = Image.open(ROOT / 'west_web4.png').convert('RGBA')
    local_src = ROOT / 'local_web5.png'
    if not local_src.exists():
        local_src = ROOT / 'hokkaido_local.png'
    local = local_web5(local_src)

    save_pair(gch, 'gch')
    save_pair(east, 'east')
    save_pair(west, 'west')
    save_pair(local, 'local')

    gch.convert('RGB').save(ROOT / 'gch.png', optimize=True)
    east.convert('RGB').save(ROOT / 'east_web3.png', optimize=True)
    west.convert('RGB').save(ROOT / 'west_web4.png', optimize=True)
    local.convert('RGB').save(ROOT / 'local_web5.png', optimize=True)

    # Old SVG/Hokkaido variants are deliberately removed to avoid mixed logo sets.
    for p in OUT.glob('*.svg'):
        p.unlink()
    for name in ('hokkaido_hq.png', 'hokkaido_lq.png'):
        p = OUT / name
        if p.exists():
            p.unlink()
    old = ROOT / 'hokkaido_local.png'
    if old.exists():
        old.unlink()


if __name__ == '__main__':
    main()
