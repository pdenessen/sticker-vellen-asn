#!/usr/bin/env python3
"""
ASN sticker generator voor Paperless-ngx — Topstick 8790 (17.8 x 10 mm, 270/A4).

Gebruik:
    python generate_asn_labels.py              # interactief keuzemenu
    python generate_asn_labels.py 1 --prefix CNTR   # direct, 1 vel CNTR
    python generate_asn_labels.py --calibrate       # kalibratie raster
"""

import argparse
import io
from typing import Optional

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ── Topstick 8790 sheet geometry ─────────────────────────────────────────────
# Measured from physical sheet:
#   left/right margin 5 mm  → LEFT = RIGHT = 5 mm
#   top/bottom margin ~14 mm → symmetric: (297 - 27×10) / 2 = 13.5 mm
#   ~3 mm gap between columns (user-measured); row gap = 0 (labels are flush vertically)
#   GAP_X = (210 - 2×5 - 10×17.8) / 9 = 2.44 mm
LABEL_W   = 17.8 * mm
LABEL_H   = 10.0 * mm   # full physical label height; no vertical gap between rows
COLS      = 10
ROWS      = 27
LEFT      =  5.0 * mm
TOP       = 12.0 * mm   # 13.5 - 1.5 mm (3 mm excess split over top + bottom)
GAP_X     =  2.44 * mm
GAP_Y     =  0.0 * mm
# ─────────────────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
STEP_X = LABEL_W + GAP_X
STEP_Y = LABEL_H + GAP_Y

# ── Label series ─────────────────────────────────────────────────────────────
# QR codes always encode "ASN" + a globally unique 5-digit number.
# Each series gets a fixed base so all series share one Paperless-ngx prefix
# (PAPERLESS_CONSUMER_ASN_BARCODE_PREFIX=ASN).
#
#   code    description                 base   global range
#   CNTR    Contracten                     0   ASN00001 - ASN09999
#   REK     Rekeningen                10000   ASN10001 - ASN19999
#   DIV     Diverse                   20000   ASN20001 - ASN29999
#   GAR     Garanties & Handleidingen 30000   ASN30001 - ASN39999
#
# The label text shows the series code + the same global number,
# so the number visible on the sticker matches the ASN in Paperless.
SERIES = [
    ("CNTR", "Contracten",                          0),
    ("REK",  "Rekeningen",                     10_000),
    ("DIV",  "Diverse",                        20_000),
    ("GAR",  "Garanties & Handleidingen",      30_000),
]
QR_PREFIX = "ASN"
DIGITS    = 5
MAX_LOCAL = 9_999    # labels per series
# ─────────────────────────────────────────────────────────────────────────────


def _series_by_code(code: str) -> Optional[tuple]:
    for entry in SERIES:
        if entry[0] == code.upper():
            return entry
    return None


def _qr_image(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _draw_one_label(c: canvas.Canvas, x: float, y: float,
                    global_asn: int, series_name: str, border: bool) -> None:
    """Draw a single label with its bottom-left corner at (x, y) in points."""
    if border:
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.2)
        c.rect(x, y, LABEL_W, LABEL_H)

    PAD = 1.0 * mm

    # QR code encodes "ASN" + globally unique number (scanned by Paperless-ngx)
    qr_size = LABEL_H - 2 * PAD          # 8 mm
    qr_data = f"{QR_PREFIX}{global_asn:0{DIGITS}d}"
    c.drawImage(ImageReader(_qr_image(qr_data)),
                x + PAD, y + PAD, width=qr_size, height=qr_size, mask="auto")

    # Text: series code (top) + global ASN number (bottom) — matches Paperless ASN
    text_x = x + PAD + qr_size + PAD
    mid_y  = y + LABEL_H / 2

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 4.0)
    c.drawString(text_x, mid_y + 1.5, series_name)

    c.setFont("Helvetica", 5.0)
    c.drawString(text_x, mid_y - 5.5, f"{global_asn:0{DIGITS}d}")


def _draw_calibration(c: canvas.Canvas) -> None:
    """Draw an empty grid so you can check alignment without wasting ink."""
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.3)
    for row in range(ROWS):
        for col in range(COLS):
            x = LEFT + col * STEP_X
            y = PAGE_H - TOP - row * STEP_Y - LABEL_H
            c.rect(x, y, LABEL_W, LABEL_H)
            c.setFont("Helvetica", 2.8)
            c.drawString(x + 1, y + 1, f"{row*COLS+col+1}")
    c.showPage()


def generate(global_start: int, count: int, series_name: str,
             output: str, border: bool) -> None:
    c = canvas.Canvas(output, pagesize=A4)
    idx = 0
    while idx < count:
        for row in range(ROWS):
            for col in range(COLS):
                if idx >= count:
                    break
                x = LEFT + col * STEP_X
                y = PAGE_H - TOP - row * STEP_Y - LABEL_H
                _draw_one_label(c, x, y, global_start + idx, series_name, border)
                idx += 1
            if idx >= count:
                break
        if idx < count:
            c.showPage()
    c.save()


def _ask_int(prompt: str, default: Optional[int] = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  Voer een geldig getal in.")


def interactive() -> None:
    print()
    print("=" * 56)
    print("  ASN Sticker Generator  -  Topstick 8790")
    print("=" * 56)
    print()
    print("Kies een reeks:")
    for i, (code, desc, base) in enumerate(SERIES, 1):
        lo = base + 1
        hi = base + MAX_LOCAL
        print(f"  {i}. {code:<5}  {desc:<30}  (ASN {lo:05d} - {hi:05d})")
    print(f"  {len(SERIES)+1}. Kalibratie raster (leeg raster voor uitlijning)")
    print()

    keuze = _ask_int(f"Keuze (1-{len(SERIES)+1})")
    print()

    if keuze == len(SERIES) + 1:
        output = "kalibratie.pdf"
        c = canvas.Canvas(output, pagesize=A4)
        _draw_calibration(c)
        c.save()
        print(f"Kalibratie raster opgeslagen als: {output}")
        print("Print op gewoon papier en leg over een Topstick 8790 vel.")
        return

    if keuze < 1 or keuze > len(SERIES):
        print("Ongeldige keuze.")
        return

    code, desc, base = SERIES[keuze - 1]
    print(f"Reeks  : {code} - {desc}")
    print(f"Bereik : ASN{base+1:05d} - ASN{base+MAX_LOCAL:05d}")
    print()

    local_start  = _ask_int(f"Eerste nummer (1-{MAX_LOCAL})", default=1)
    global_start = base + local_start
    count        = _ask_int("Aantal labels", default=COLS * ROWS)
    border       = input("Rand om elke sticker tekenen? (j/n) [n]: ").strip().lower() == "j"
    print()

    sheets = -(-count // (COLS * ROWS))
    output = f"{code}_{global_start:0{DIGITS}d}.pdf"
    generate(global_start, count, code, output, border)

    first_g = global_start
    last_g  = global_start + count - 1
    print(f"Klaar  : {count} stickers ({sheets} vel{'len' if sheets != 1 else ''})")
    print(f"Labels : {code}{first_g:0{DIGITS}d} t/m {code}{last_g:0{DIGITS}d}")
    print(f"QR data: ASN{first_g:0{DIGITS}d} t/m ASN{last_g:0{DIGITS}d}")
    print(f"Bestand: {output}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ASN sticker generator - Topstick 8790 - Paperless-ngx",
        epilog="Zonder argumenten: interactief keuzemenu.",
    )
    ap.add_argument("start", type=int, nargs="?",
                    help="Eerste serienummer binnen de reeks (1-9999)")
    ap.add_argument("--prefix", default="CNTR",
                    help="Reeks: CNTR | REK | DIV | GAR")
    ap.add_argument("--count", type=int, default=COLS * ROWS,
                    help="Aantal stickers")
    ap.add_argument("--output", "-o", help="PDF bestandsnaam")
    ap.add_argument("--border", action="store_true",
                    help="Rand om elke sticker")
    ap.add_argument("--calibrate", action="store_true",
                    help="Kalibratie raster")
    args = ap.parse_args()

    if args.start is None and not args.calibrate:
        interactive()
        return

    if args.calibrate:
        output = args.output or "kalibratie.pdf"
        c = canvas.Canvas(output, pagesize=A4)
        _draw_calibration(c)
        c.save()
        print(f"Kalibratie raster -> {output}")
        return

    series = _series_by_code(args.prefix)
    if series is None:
        print(f"Onbekende reeks: {args.prefix}. Kies uit: CNTR, REK, DIV, GAR")
        return

    code, desc, base = series
    global_start = base + args.start
    output = args.output or f"{code}_{global_start:0{DIGITS}d}.pdf"
    sheets = -(-args.count // (COLS * ROWS))
    generate(global_start, args.count, code, output, args.border)

    first_g = global_start
    last_g  = global_start + args.count - 1
    print(f"{args.count} stickers ({sheets} vel)  "
          f"ASN{first_g:0{DIGITS}d} - ASN{last_g:0{DIGITS}d}  -> {output}")


if __name__ == "__main__":
    main()
