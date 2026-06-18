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
                    asn: int, prefix: str, digits: int, border: bool) -> None:
    """Draw a single label with its bottom-left corner at (x, y) in points."""
    if border:
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.2)
        c.rect(x, y, LABEL_W, LABEL_H)

    PAD = 1.0 * mm

    # QR code — square, centred vertically, flush left with padding
    qr_size = LABEL_H - 2 * PAD          # 8 mm
    asn_str = f"{prefix}{asn:0{digits}d}"
    c.drawImage(ImageReader(_qr_image(asn_str)),
                x + PAD, y + PAD, width=qr_size, height=qr_size, mask="auto")

    # Text to the right of the QR code
    text_x = x + PAD + qr_size + PAD
    mid_y  = y + LABEL_H / 2

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 4.0)
    c.drawString(text_x, mid_y + 1.5, prefix)

    c.setFont("Helvetica", 5.0)
    c.drawString(text_x, mid_y - 5.5, f"{asn:0{digits}d}")


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


def generate(start: int, count: int, prefix: str, digits: int,
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
                _draw_one_label(c, x, y, start + idx, prefix, digits, border)
                idx += 1
            if idx >= count:
                break
        if idx < count:
            c.showPage()
    c.save()


SERIES = [
    ("CNTR", "Contracten"),
    ("REK",  "Rekeningen"),
    ("DIV",  "Diverse"),
    ("GAR",  "Garanties & Handleidingen"),
]
DIGITS = 5   # zero-padding width: CNTR00001


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
    print("=" * 48)
    print("  ASN Sticker Generator  -  Topstick 8790")
    print("=" * 48)
    print()
    print("Kies een reeks:")
    for i, (code, desc) in enumerate(SERIES, 1):
        print(f"  {i}. {code:<5}  {desc}")
    print(f"  {len(SERIES)+1}. Kalibratie raster (leeg raster voor uitlijning)")
    print()

    keuze = _ask_int(f"Keuze (1-{len(SERIES)+1})")
    print()

    # Calibration grid
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

    prefix, desc = SERIES[keuze - 1]
    print(f"Reeks: {prefix} - {desc}")
    start = _ask_int("Eerste nummer")
    count = _ask_int("Aantal labels", default=COLS * ROWS)
    border = input("Rand om elke sticker tekenen? (j/n) [n]: ").strip().lower() == "j"
    print()

    sheets = -(-count // (COLS * ROWS))
    output = f"{prefix}_{start:0{DIGITS}d}.pdf"
    generate(start, count, prefix, DIGITS, output, border)

    first = f"{prefix}{start:0{DIGITS}d}"
    last  = f"{prefix}{start + count - 1:0{DIGITS}d}"
    print(f"Klaar: {count} stickers ({sheets} vel{'len' if sheets != 1 else ''})"
          f"  {first} t/m {last}")
    print(f"Bestand: {output}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ASN sticker generator — Topstick 8790 — Paperless-ngx",
        epilog="Zonder argumenten: interactief keuzemenu.",
    )
    ap.add_argument("start", type=int, nargs="?", help="Eerste ASN nummer")
    ap.add_argument("--prefix", default="ASN", help="Reeks prefix (bijv. CNTR)")
    ap.add_argument("--count", type=int, default=COLS * ROWS, help="Aantal stickers")
    ap.add_argument("--digits", type=int, default=DIGITS, help="Nul-opvulling breedte")
    ap.add_argument("--output", "-o", help="PDF bestandsnaam")
    ap.add_argument("--border", action="store_true", help="Rand om elke sticker")
    ap.add_argument("--calibrate", action="store_true", help="Kalibratie raster")
    args = ap.parse_args()

    # No arguments → interactive menu
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

    start  = args.start
    output = args.output or f"{args.prefix}_{start:0{args.digits}d}.pdf"
    sheets = -(-args.count // (COLS * ROWS))
    generate(start, args.count, args.prefix, args.digits, output, args.border)

    first = f"{args.prefix}{start:0{args.digits}d}"
    last  = f"{args.prefix}{start + args.count - 1:0{args.digits}d}"
    print(f"{args.count} stickers ({sheets} vel)  {first} t/m {last} -> {output}")


if __name__ == "__main__":
    main()
