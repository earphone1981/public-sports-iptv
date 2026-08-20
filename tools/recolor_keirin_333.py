from pathlib import Path
from PIL import Image

ROOT = Path('public_sports_logos_github_43/keirin_logos_github_ready')
TARGETS = ['matsudo.png','odawara.png','ito.png','toyama.png','nara.png','hofu.png']
TINT = (224, 160, 32)  # warm gold, subtle 333m marker
MIX = 0.14

for name in TARGETS:
    path = ROOT / name
    img = Image.open(path).convert('RGBA')
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            nr = round(r * (1 - MIX) + TINT[0] * MIX)
            ng = round(g * (1 - MIX) + TINT[1] * MIX)
            nb = round(b * (1 - MIX) + TINT[2] * MIX)
            px[x, y] = (nr, ng, nb, a)
    img.save(path, optimize=True)
    print('updated', path)
