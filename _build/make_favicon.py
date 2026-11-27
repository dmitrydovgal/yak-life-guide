import sys
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]
BLUE = (26, 115, 232, 255); WHITE = (255, 255, 255, 255)
FONT = r'C:\Windows\Fonts\segoeuib.ttf'


def tile(size, text='Як?', radius=0.22, pad=0.0):
    """Синя плитка з білим «Як?» (як логотип сайту). Малюємо в 8x і зменшуємо."""
    S = size * 8
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    p = int(S * pad)
    d.rounded_rectangle([p, p, S - 1 - p, S - 1 - p], radius=int(S * radius), fill=BLUE)
    box = S - 2 * p
    fs = int(box * 0.62)
    while True:
        f = ImageFont.truetype(FONT, fs)
        l, t, r, b = d.textbbox((0, 0), text, font=f)
        if r - l <= box * 0.80: break
        fs -= 4
    x = (S - (r - l)) / 2 - l; y = (S - (b - t)) / 2 - t
    d.text((x, y), text, font=f, fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


if __name__ == '__main__':
    import os
    os.makedirs(OUT, exist_ok=True)
    ico = [tile(16, 'Як', radius=.18), tile(32), tile(48)]  # на 16px «?» зливається
    ico[2].save(os.path.join(OUT, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico[:2])
    tile(32).save(os.path.join(OUT, 'favicon-32.png'))
    tile(180, radius=0).save(os.path.join(OUT, 'apple-touch-icon.png'))  # iOS сам скруглює кути
    tile(192).save(os.path.join(OUT, 'icon-192.png'))
    tile(512).save(os.path.join(OUT, 'icon-512.png'))
    # Прев'ю для перевірки: як виглядає в реальних розмірах
    pv = Image.new('RGBA', (360, 80), (255, 255, 255, 255))
    x = 10
    for s in (16, 32, 48):
        pv.paste(tile(s), (x, 10), tile(s)); x += s + 20
    pv.paste(tile(48).resize((64, 64), Image.NEAREST), (x, 10)); x += 84
    big = tile(16).resize((64, 64), Image.NEAREST); pv.paste(big, (x, 10))
    pv.save(os.path.join(OUT, '_preview.png'))
