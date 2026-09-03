import os
from PIL import Image, ImageDraw, ImageFont

def add_glow_text(draw, position, text, font, text_color, glow_color, glow_radius=4):
    x, y = position
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    draw.text((x, y), text, font=font, fill=text_color)

def process_avatar():
    img_path = "assets/line_avatar.jpg"
    out_path = "assets/line_avatar_text.jpg"
    if not os.path.exists(img_path):
        return

    base = Image.open(img_path).convert("RGBA")
    w, h = base.size

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 底部加上半透明漸層黑遮罩以襯托文字 (適度拉高以防被圓形裁切)
    banner_h = int(h * 0.28)
    gradient = Image.new("RGBA", (w, banner_h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for i in range(banner_h):
        alpha = int(230 * (i / banner_h))
        g_draw.line([(0, i), (w, i)], fill=(5, 10, 20, alpha))
    overlay.paste(gradient, (0, h - banner_h), gradient)

    # 加載字型
    font_main = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", int(h * 0.072))
    font_sub = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", int(h * 0.036))

    text_main = "戰鬥陀螺X"
    text_sub = "官方正版  ‧  補貨即時通知"

    # 主標題置中 (保持在圓形安全區域內)
    bbox_m = font_main.getbbox(text_main)
    w_m = bbox_m[2] - bbox_m[0]
    pos_m = ((w - w_m) // 2, h - banner_h + int(banner_h * 0.22))
    add_glow_text(draw, pos_m, text_main, font_main, text_color=(255, 255, 255), glow_color=(230, 0, 20), glow_radius=5)

    # 副標題置中
    bbox_s = font_sub.getbbox(text_sub)
    w_s = bbox_s[2] - bbox_s[0]
    pos_s = ((w - w_s) // 2, h - banner_h + int(banner_h * 0.60))
    add_glow_text(draw, pos_s, text_sub, font_sub, text_color=(0, 240, 255), glow_color=(0, 40, 80), glow_radius=3)

    final = Image.alpha_composite(base, overlay).convert("RGB")
    final.save(out_path, quality=95)
    print("頭像加工完成:", out_path)

def process_cover():
    img_path = "assets/line_cover.jpg"
    out_path = "assets/line_cover_text.jpg"
    if not os.path.exists(img_path):
        return

    base = Image.open(img_path).convert("RGBA")
    w, h = base.size

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 左上方精緻暗色漸層襯底
    top_h = int(h * 0.38)
    gradient = Image.new("RGBA", (w, top_h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for i in range(top_h):
        alpha = int(190 * (1 - (i / top_h)))
        g_draw.line([(0, i), (w, i)], fill=(5, 10, 20, alpha))
    overlay.paste(gradient, (0, 0), gradient)

    font_title = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", int(h * 0.125))
    font_cn = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", int(h * 0.062))
    font_sub = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", int(h * 0.038))

    text_title = "BEYBLADE X"
    text_cn = "官方正版有貨情報中心"
    text_sub = "7 大官方通路 24H 實時監控  ‧  拒絕黃牛 原價搶購"

    pad_x = int(w * 0.04)
    pad_y = int(h * 0.04)

    add_glow_text(draw, (pad_x, pad_y), text_title, font_title, text_color=(255, 255, 255), glow_color=(0, 220, 255), glow_radius=6)
    add_glow_text(draw, (pad_x, pad_y + int(h * 0.125)), text_cn, font_cn, text_color=(255, 220, 0), glow_color=(180, 50, 0), glow_radius=4)
    add_glow_text(draw, (pad_x, pad_y + int(h * 0.20)), text_sub, font_sub, text_color=(220, 240, 255), glow_color=(0, 20, 50), glow_radius=3)

    final = Image.alpha_composite(base, overlay).convert("RGB")
    final.save(out_path, quality=95)
    print("封面加工完成:", out_path)

if __name__ == "__main__":
    process_avatar()
    process_cover()
