#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

A program that draws one invented passport spread for the Republic of
Kestrelia — a foggy North Atlantic archipelago of lighthouse-keepers —
as a single 1024x720 PNG: a data page (portrait, fields, machine-readable
strip) on the left, a visa page (arrival/departure stamps from three
neighbouring countries, one telling visa condition) on the right.

Every date agrees: issued 04 JAN 2029, expires 03 JAN 2039; all stamps
fall between those dates, in paired arrival/departure order. The MRZ
check digits are computed with the real ICAO 9303 algorithm, not typed.

No network, no external files beyond the bundled fonts. Pillow only.
Output: os.environ.get("MAKEFUN_OUTPUT_DIR", "/output") + "/entry.png"
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1024, 720
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

BASE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE, "fonts")
SYS_FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def load_font(name, size):
    for d in (FONT_DIR, SYS_FONT_DIR):
        p = os.path.join(d, name)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def sans(size, bold=False):
    return load_font("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def serif(size, bold=False):
    return load_font("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf", size)


def mono(size):
    return load_font("DejaVuSansMono.ttf", size)


# --- palette: one restrained document palette, used everywhere ---------
PAPER = (245, 240, 227)      # cream passport paper
PAPER_D = (238, 231, 214)    # slightly darker cream
NAVY = (31, 58, 95)          # document ink
NAVY_SOFT = (58, 84, 120)
GREY = (96, 100, 104)        # small-label grey
RULE = (120, 130, 145)       # hairline rules
GOLD = (176, 141, 60)        # coat-of-arms gold
INK_BLUE = (43, 76, 140)     # stamp blue
INK_RED = (140, 47, 47)      # stamp red
INK_GREEN = (47, 107, 79)    # stamp green
INK_PURPLE = (90, 61, 122)   # stamp purple


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(draw, box, top, bottom):
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0)
        draw.line([(x0, y), (x1, y)], fill=lerp(top, bottom, t))


def text_c(draw, cx, y, s, font, fill):
    w = draw.textlength(s, font=font)
    draw.text((cx - w / 2, y), s, font=font, fill=fill)


def text_r(draw, x, y, s, font, fill):
    w = draw.textlength(s, font=font)
    draw.text((x - w, y), s, font=font, fill=fill)


# --- ICAO 9303 MRZ check digits (weights 7,3,1) -----------------------
_MRZ_VAL = {c: i for i, c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}


def mrz_check(s):
    total = 0
    for i, ch in enumerate(s):
        v = _MRZ_VAL.get(ch, 0) if ch != "<" else 0
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    """TD3 two-line MRZ, 44 chars each, with real ICAO 9303 check digits."""
    line1 = "P<KSTVENNOR<<MARA"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "KST290104"  # 9-char document number; shown the same in the fields
    dob = "980617"
    exp = "390103"
    opt = "<" * 15  # positions 29-43; composite check digit at 44
    composite = doc + mrz_check(doc) + dob + mrz_check(dob) \
        + exp + mrz_check(exp) + opt
    line2 = doc + mrz_check(doc) + "KST" + dob + mrz_check(dob) + "F" \
        + exp + mrz_check(exp) + opt + mrz_check(composite)
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


# --- coat of arms: a lighthouse in a shield, drawn once, used twice ---
def draw_arms(draw, cx, cy, s, ink=NAVY, gold=GOLD):
    """Small lighthouse emblem: shield outline, tower, beams, waves."""
    w = s
    h = int(s * 1.15)
    x0, y0 = cx - w // 2, cy - h // 2
    x1, y1 = cx + w // 2, cy + h // 2
    draw.rounded_rectangle([x0, y0, x1, y1], radius=s // 6,
                           outline=ink, width=max(2, s // 18))
    # tower: tapered, striped
    tw = s // 5
    tx0, tx1 = cx - tw // 2, cx + tw // 2
    ty0, ty1 = y0 + int(s * 0.28), y1 - int(s * 0.22)
    draw.polygon([(tx0, ty1), (tx0 + 2, ty0), (tx1 - 2, ty0), (tx1, ty1)],
                 fill=ink)
    draw.rectangle([tx0 + 1, ty0 + (ty1 - ty0) // 3, tx1 - 1,
                    ty0 + (ty1 - ty0) // 3 + 3], fill=PAPER)
    draw.rectangle([tx0 + 1, ty0 + 2 * (ty1 - ty0) // 3, tx1 - 1,
                    ty0 + 2 * (ty1 - ty0) // 3 + 3], fill=PAPER)
    # lamp room + light beams
    draw.rectangle([cx - tw // 2 - 2, ty0 - 7, cx + tw // 2 + 2, ty0],
                   fill=gold)
    draw.ellipse([cx - 3, ty0 - 13, cx + 3, ty0 - 7], fill=gold)
    draw.line([(cx - tw // 2 - 2, ty0 - 9), (x0 + 3, ty0 - 16)],
              fill=gold, width=2)
    draw.line([(cx + tw // 2 + 2, ty0 - 9), (x1 - 3, ty0 - 16)],
              fill=gold, width=2)
    # waves
    for k, yy in enumerate((y1 - 12, y1 - 7)):
        draw.arc([x0 + 4, yy - 4, x1 - 4, yy + 4], 200, 340,
                 fill=ink, width=2)
    return (x0, y0, x1, y1)


# --- the portrait: front-facing head-and-shoulders, flat, muted -------
def draw_portrait():
    pw, ph = 196, 246
    img = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # studio background: soft grey-blue vertical gradient
    vgrad(d, (0, 0, pw, ph), (143, 163, 181), (109, 130, 150))
    d.rectangle([0, 0, pw - 1, ph - 1], outline=(90, 105, 122), width=2)
    skin = (217, 169, 134)
    skin_d = (198, 148, 112)
    hair = (74, 52, 38)
    cap = (38, 62, 96)
    coat = (44, 58, 84)
    # shoulders / coat
    d.pieslice([8, 196, pw - 8, 300], 180, 360, fill=coat)
    d.polygon([(8, 246), (8, 226), (62, 196), (pw - 62, 196),
               (pw - 8, 226), (pw - 8, 246)], fill=coat)
    # shirt collar + tie-less V
    d.polygon([(82, 196), (98, 196), (98, 222), (82, 208)], fill=(232, 228, 218))
    d.polygon([(114, 196), (98, 196), (98, 222), (114, 208)], fill=(232, 228, 218))
    # brass lighthouse brooch on the left lapel
    d.ellipse([52, 214, 62, 224], fill=(176, 141, 60))
    d.polygon([(55, 224), (57, 214), (59, 214), (59, 224)], fill=(176, 141, 60))
    # neck
    d.rectangle([86, 168, 110, 200], fill=skin_d)
    d.rectangle([86, 168, 110, 176], fill=(190, 140, 104))
    # ears
    d.ellipse([52, 108, 66, 132], fill=skin)
    d.ellipse([130, 108, 144, 132], fill=skin)
    # head
    d.ellipse([58, 52, 138, 158], fill=skin)
    d.ellipse([58, 52, 138, 158], outline=(190, 140, 104), width=1)
    # soft cheek shading
    d.ellipse([62, 118, 92, 142], fill=(210, 152, 118))
    d.ellipse([104, 118, 134, 142], fill=(210, 152, 118))
    # hair: side locks framing the face, parted centre
    d.pieslice([56, 48, 140, 128], 180, 360, fill=hair)
    d.ellipse([56, 92, 74, 160], fill=hair)
    d.ellipse([122, 92, 140, 160], fill=hair)
    d.polygon([(58, 96), (72, 60), (86, 96), (78, 100)], fill=hair)
    d.polygon([(138, 96), (124, 60), (110, 96), (118, 100)], fill=hair)
    # knitted fisherman's cap: dome + ribbed band
    d.pieslice([54, 30, 142, 96], 180, 360, fill=cap)
    d.rectangle([54, 62, 142, 84], fill=cap)
    for x in range(58, 142, 8):
        d.line([(x, 64), (x, 82)], fill=(28, 48, 78), width=2)
    d.rectangle([54, 62, 142, 68], fill=(28, 48, 78))
    d.ellipse([92, 26, 104, 38], fill=(28, 48, 78))  # cap button
    # brows, eyes, nose, mouth: small, symmetric, neutral
    d.line([(70, 104), (86, 101)], fill=(58, 40, 28), width=3)
    d.line([(110, 101), (126, 104)], fill=(58, 40, 28), width=3)
    d.ellipse([70, 108, 86, 116], fill=(250, 246, 238))
    d.ellipse([110, 108, 126, 116], fill=(250, 246, 238))
    d.ellipse([75, 109, 81, 115], fill=(40, 30, 24))
    d.ellipse([115, 109, 121, 115], fill=(40, 30, 24))
    d.line([(97, 116), (95, 130), (98, 132)], fill=(190, 140, 104), width=2)
    d.line([(88, 142), (108, 142)], fill=(150, 96, 84), width=2)
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img


# --- stamps ------------------------------------------------------------
def rect_stamp(text_lines, color, size=(210, 92), angle=-6, font_size=12):
    """Rectangular ink stamp on its own layer, rotated, semi-transparent."""
    w, h = size
    layer = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = (w + 40) // 2, (h + 40) // 2
    d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
                        radius=6, outline=color + (200,), width=3)
    d.rounded_rectangle([cx - w // 2 + 5, cy - h // 2 + 5,
                         cx + w // 2 - 5, cy + h // 2 - 5],
                        radius=4, outline=color + (160,), width=1)
    f = sans(font_size, bold=True)
    f_small = sans(font_size - 2, bold=True)
    total = len(text_lines) * (font_size + 4)
    y = cy - total // 2
    for i, line in enumerate(text_lines):
        ff = f_small if len(line) > 22 else f
        text_c(d, cx, y, line, ff, color + (210,))
        y += font_size + 4
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    return layer


def circle_stamp(top_text, mid_text, bottom_text, color, r=52, angle=-8):
    """Circular entry stamp with text set on an arc, top and bottom."""
    size = r * 2 + 48
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx = cy = size // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r],
              outline=color + (200,), width=3)
    d.ellipse([cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6],
              outline=color + (150,), width=1)
    f = sans(11, bold=True)
    # arc text: one character at a time, rotated along the circle
    def arc(s, radius, start_deg, end_deg, flip=False):
        n = len(s)
        for i, ch in enumerate(s):
            ang = math.radians(start_deg + (end_deg - start_deg) * i / max(1, n - 1))
            x = cx + radius * math.sin(ang)
            y = cy - radius * math.cos(ang)
            glyph = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glyph)
            gd.text((8, 8), ch, font=f, fill=color + (210,), anchor="mm")
            rot = math.degrees(ang) if not flip else math.degrees(ang) + 180
            glyph = glyph.rotate(-rot, resample=Image.BICUBIC, expand=False)
            layer.alpha_composite(glyph, (int(x - 8), int(y - 8)))
    arc(top_text, r - 12, -52, 52)
    # bottom arc: tight 56-degree span so the year sits legibly at the
    # bottom of the circle instead of scattering to the sides
    arc(bottom_text, r - 14, 208, 152, flip=True)
    text_c(d, cx, cy - 16, mid_text, sans(13, bold=True), color + (210,))
    d.line([(cx - 26, cy + 2), (cx + 26, cy + 2)], fill=color + (180,), width=1)
    text_c(d, cx, cy + 8, "PORT VENNOR", sans(9, bold=True), color + (200,))
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    return layer


# --- the spread ---------------------------------------------------------
def build_spread():
    random.seed(20291121)
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    # paper tone: gentle vertical fall + faint fibre speckle
    vgrad(d, (0, 0, W, H), (246, 241, 229), (240, 233, 216))
    for _ in range(900):
        x = random.randrange(W)
        y = random.randrange(H)
        d.point((x, y), fill=(232, 224, 204))
    # outer border + centre gutter (the fold of the open spread)
    d.rectangle([10, 10, W - 11, H - 11], outline=NAVY, width=2)
    d.rectangle([14, 14, W - 15, H - 15], outline=RULE, width=1)
    d.line([(512, 16), (512, H - 16)], fill=(200, 190, 168), width=3)
    d.line([(510, 16), (510, H - 16)], fill=(214, 204, 182), width=1)
    d.line([(514, 16), (514, H - 16)], fill=(214, 204, 182), width=1)
    # faint guilloche arcs in the four outer corners
    for (cx, cy) in ((30, 30), (994, 30), (30, 690), (994, 690)):
        for r in range(18, 60, 7):
            d.arc([cx - r, cy - r, cx + r, cy + r], 0, 360,
                  fill=(176, 164, 138), width=1)

    # ================= LEFT PAGE: the data page ========================
    LX, RX = 24, 506
    # header: arms + country name, one type system throughout
    draw_arms(d, 72, 62, 46)
    text_c(d, 300, 40, "REPUBLIC OF KESTRELIA", serif(23, bold=True), NAVY)
    text_c(d, 300, 72, "PASSPORT  ·  VEGABRÉF", sans(11, bold=True), NAVY_SOFT)
    text_r(d, RX, 72, "Nº KST290104", sans(11, bold=True), NAVY)
    d.line([(LX, 100), (RX, 100)], fill=RULE, width=1)
    d.line([(LX, 103), (RX, 103)], fill=RULE, width=1)

    # portrait in its photo box, with a printed caption line
    photo = draw_portrait()
    img.paste(photo, (36, 124), photo)
    d.rectangle([36, 124, 231, 369], outline=NAVY, width=2)
    text_c(d, 134, 374, "PHOTOGRAPH  ·  MYND", sans(8), GREY)

    # data fields: two columns, label in 8 pt caps + Kestrel gloss,
    # value in 13 pt bold — the same sizes on every row, no exceptions
    fields_l = [
        ("SURNAME / ÆTT", "VENNOR"),
        ("GIVEN NAMES / FOR", "MARA"),
        ("NATIONALITY / ÞJÓÐ", "KESTRELIAN"),
        ("DATE OF BIRTH / FÆÐING", "17 JUN 1998"),
        ("PLACE OF BIRTH / FÆÐSTAÐ", "PORT VENNOR"),
    ]
    fields_r = [
        ("SEX / KYN", "F"),
        ("HEIGHT / HÆÐ", "172 CM"),
        ("EYES / AUGU", "GREY-GREEN"),
        ("DATE OF ISSUE / ÚTGÁFA", "04 JAN 2029"),
        ("DATE OF EXPIRY / GILDI", "03 JAN 2039"),
    ]
    for col_x, fields in ((248, fields_l), (378, fields_r)):
        y = 126
        for label, value in fields:
            d.text((col_x, y), label, font=sans(8), fill=GREY)
            d.text((col_x, y + 12), value, font=sans(13, bold=True), fill=NAVY)
            y += 47
    # authority + holder's signature, full width under the fields
    d.line([(LX, 402), (RX, 402)], fill=RULE, width=1)
    d.text((LX, 414), "ISSUING AUTHORITY / ÚTGÁFUSTOÐ", font=sans(8), fill=GREY)
    d.text((LX, 426), "PORT VENNOR · HARBOUR OFFICE 3", font=sans(13, bold=True), fill=NAVY)
    d.text((LX, 462), "HOLDER'S SIGNATURE / UNDIRSKRIFT", font=sans(8), fill=GREY)
    d.text((LX, 474), "Mara Vennor", font=serif(17), fill=NAVY)
    d.line([(LX, 500), (RX, 500)], fill=RULE, width=1)
    # machine-readable strip, on its own band, real ICAO check digits
    d.rectangle([LX, 516, RX, 640], fill=PAPER_D)
    d.line([(LX, 516), (RX, 516)], fill=NAVY, width=1)
    d.line([(LX, 640), (RX, 640)], fill=NAVY, width=1)
    l1, l2 = mrz_lines()
    f_mrz = mono(15)
    d.text((LX + 12, 534), l1, font=f_mrz, fill=NAVY)
    d.text((LX + 12, 566), l2, font=f_mrz, fill=NAVY)
    d.text((LX + 12, 606), "P<KST — MACHINE READABLE ZONE", font=sans(8), fill=GREY)
    text_c(d, 265, 668, "— 1 —", sans(10), GREY)

    # ================= RIGHT PAGE: visas and stamps ====================
    VX, WX = 528, 1000
    # faint lighthouse watermark behind the stamps
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    draw_arms(wd, 764, 380, 300, ink=(31, 58, 95), gold=(176, 141, 60))
    wm = wm.filter(ImageFilter.GaussianBlur(2))
    wm.putalpha(wm.split()[3].point(lambda a: a // 14))
    img.alpha_composite(wm)
    d = ImageDraw.Draw(img, "RGBA")
    text_c(d, 764, 40, "VISAS", serif(23, bold=True), NAVY)
    text_c(d, 764, 72, "VEGABRÉF  ·  INN- OG ÚTGANGA", sans(11, bold=True), NAVY_SOFT)
    d.line([(VX, 100), (WX, 100)], fill=RULE, width=1)
    d.line([(VX, 103), (WX, 103)], fill=RULE, width=1)

    # three neighbouring countries, arrival then departure, all after
    # the 04 JAN 2029 issue date, in chronological order down the page
    img.alpha_composite(circle_stamp("ALDERVAAL", "02 MAR", "2030",
                                     INK_BLUE, r=50, angle=-8), (548, 132))
    img.alpha_composite(rect_stamp(["ALDERVAAL", "DEPARTURE",
                                    "09 MAR 2030", "PORT OF ALDER"],
                                   INK_BLUE, size=(216, 88), angle=5),
                        (742, 150))
    img.alpha_composite(rect_stamp(["MERROW", "ARRIVAL",
                                    "14 SEP 2030", "FERRY TERMINAL"],
                                   INK_RED, size=(216, 88), angle=-5),
                        (548, 268))
    img.alpha_composite(circle_stamp("MERROW", "21 SEP", "2030",
                                     INK_RED, r=50, angle=7), (800, 268))
    img.alpha_composite(circle_stamp("NORDHAVN", "05 MAY", "2031",
                                     INK_PURPLE, r=50, angle=-6), (548, 404))
    img.alpha_composite(rect_stamp(["NORDHAVN", "DEPARTURE",
                                    "12 MAY 2031", "NORTH QUAY"],
                                   INK_PURPLE, size=(216, 88), angle=6),
                        (742, 408))
    # THE telling detail: the lantern condition, in red, across the page
    img.alpha_composite(rect_stamp(["CONDITION 7", "BEARER MUST CARRY",
                                    "A LANTERN AFTER DARK",
                                    "FOG ORDINANCE 12"],
                                   INK_RED, size=(330, 96), angle=-2),
                        (600, 540))
    # fee stamp: the small print that says what the country runs on
    img.alpha_composite(rect_stamp(["FERRY FEE PAID", "12 KESTRELS"],
                                   INK_GREEN, size=(170, 62), angle=8,
                                   font_size=11),
                        (792, 626))
    text_c(d, 764, 668, "— 2 —", sans(10), GREY)
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    img = build_spread()
    out = os.path.join(OUT_DIR, "entry.png")
    img.convert("RGB").save(out, format="PNG", optimize=True)
    print(f"wrote {out} {img.size[0]}x{img.size[1]} "
          f"{os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
