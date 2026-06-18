# ASN Label Generator — Topstick 8790

Generates printable PDF sheets of QR-code labels for [Paperless-ngx](https://docs.paperless-ngx.com/) archive serial numbers (ASN).  
Designed for **Topstick 8790** label sheets (17.8 × 10 mm, 270 labels per A4 page).

Each label contains:
- A **QR code** that Paperless-ngx scans automatically to assign the ASN
- The **series prefix** and **number** in human-readable text

---

## Label series

| Code | Description |
|------|-------------|
| `CNTR` | Contracten |
| `REK`  | Rekeningen |
| `DIV`  | Diverse |
| `GAR`  | Garanties & Handleidingen |

Labels are formatted as `CNTR00001`, `REK00042`, etc. (5-digit zero-padded numbers).

---

## Requirements

Python 3.9+ and the following packages:

```bash
pip install reportlab qrcode pillow
```

---

## Usage

### Interactive menu (recommended)

Run without arguments to get the menu:

```
python generate_asn_labels.py
```

```
================================================
  ASN Sticker Generator  -  Topstick 8790
================================================

Kies een reeks:
  1. CNTR   Contracten
  2. REK    Rekeningen
  3. DIV    Diverse
  4. GAR    Garanties & Handleidingen
  5. Kalibratie raster (leeg raster voor uitlijning)

Keuze (1-5): 1
Reeks: CNTR - Contracten
Eerste nummer: 1
Aantal labels [270]:
Rand om elke sticker tekenen? (j/n) [n]: n

Klaar: 270 stickers (1 vel)  CNTR00001 t/m CNTR00270
Bestand: CNTR_00001.pdf
```

- Press **Enter** at "Aantal labels" to accept the default (270 = 1 full sheet).
- The output PDF is named automatically: `{SERIES}_{FIRST NUMBER}.pdf`

### Command line

```bash
# One sheet of CNTR labels starting at 1
python generate_asn_labels.py 1 --prefix CNTR

# Two sheets of REK labels starting at 271
python generate_asn_labels.py 271 --prefix REK --count 540

# Custom output filename
python generate_asn_labels.py 1 --prefix GAR --output garanties.pdf

# Print border around each label (useful for alignment checks)
python generate_asn_labels.py 1 --prefix DIV --border

# Print a calibration grid (empty boxes, no QR codes)
python generate_asn_labels.py --calibrate
```

---

## Printing tips

1. **Calibrate first** — run with `--calibrate` to generate an empty grid.  
   Print it on plain paper, hold it against a Topstick 8790 sheet in front of a light, and verify the boxes align with the physical labels.  
   If they are off, adjust `LEFT` and `TOP` at the top of the script.

2. **Print at 100%** — make sure your PDF viewer does not scale the page (disable "fit to page").

3. **Run with `--border`** on the first real sheet to double-check alignment before printing a full batch.

---

## Paperless-ngx integration

For automatic ASN detection, make sure your Paperless-ngx configuration matches the prefix you use:

```env
PAPERLESS_CONSUMER_ENABLE_ASN_BARCODE=true
PAPERLESS_CONSUMER_ASN_BARCODE_PREFIX=CNTR   # change per series
```

When a scanned document contains one of these QR-code labels, Paperless-ngx automatically assigns the corresponding ASN.

---

## Sheet layout — Topstick 8790

| Parameter | Value |
|-----------|-------|
| Label size | 17.8 × 10 mm |
| Layout | 10 columns × 27 rows |
| Labels per sheet | 270 |
| Left / right margin | 5 mm |
| Top / bottom margin | ≈ 12 / 15 mm |
| Column gap | 2.44 mm |
| Row gap | 0 mm (flush) |
