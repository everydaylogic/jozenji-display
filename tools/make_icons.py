#!/usr/bin/env python3
"""表示用ページのアイコン（カレンダーの絵）を作る。使い方: make_icons.py <出力フォルダ>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

out = Path(sys.argv[1])
colors = ["#b197fc", "#4dabf7", "#f06595", "#f2b705", "#51cf66"]
for size in (192, 512):
    s = size / 512
    im = Image.new("RGB", (size, size), "#0f1115")
    d = ImageDraw.Draw(im)
    # 安全域（maskable）に収まるよう中央寄せ
    d.rounded_rectangle([116 * s, 132 * s, 396 * s, 392 * s], radius=28 * s, outline="#f3f4f6", width=max(2, int(18 * s)))
    d.line([116 * s, 196 * s, 396 * s, 196 * s], fill="#f3f4f6", width=max(2, int(18 * s)))
    for x in (186, 326):
        d.line([x * s, 104 * s, x * s, 160 * s], fill="#f3f4f6", width=max(2, int(18 * s)))
    for i, c in enumerate(colors):
        y = 230 + i * 30
        d.rounded_rectangle([156 * s, y * s, 176 * s, (y + 18) * s], radius=4 * s, fill=c)
        d.rounded_rectangle([190 * s, (y + 5) * s, (300 + (i % 2) * 50) * s, (y + 13) * s], radius=4 * s, fill="#9aa0a8")
    im.save(out / f"icon-{size}.png", optimize=True)
print("ok")
