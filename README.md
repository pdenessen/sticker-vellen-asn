# ASN Label Generator — Topstick 8790

Generates printable PDF sheets of QR-code labels for [Paperless-ngx](https://docs.paperless-ngx.com/) archive serial numbers (ASN).  
Designed for **Topstick 8790** label sheets (17.8 × 10 mm, 270 labels per A4 page).

Each label contains:
- A **QR code** that Paperless-ngx scans automatically to assign the ASN
- The **series prefix** and **number** in human-readable text

---

## Label series

| Code | Description | ASN range in Paperless |
|------|-------------|------------------------|
| `CNTR` | Contracten | ASN00001 – ASN09999 |
| `REK`  | Rekeningen | ASN10001 – ASN19999 |
| `DIV`  | Diverse | ASN20001 – ASN29999 |
| `GAR`  | Garanties & Handleidingen | ASN30001 – ASN39999 |

Each series uses a fixed block of globally unique ASN numbers. The QR code always encodes `ASN` + the 5-digit global number (e.g. `ASN10001`), which is what Paperless-ngx stores as the document's ASN. The label text shows the series code + the same number (e.g. `REK` / `10001`), so the number on the sticker always matches what you see in Paperless.

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
========================================================
  ASN Sticker Generator  -  Topstick 8790
========================================================

Kies een reeks:
  1. CNTR   Contracten                       (ASN 00001 - 09999)
  2. REK    Rekeningen                       (ASN 10001 - 19999)
  3. DIV    Diverse                          (ASN 20001 - 29999)
  4. GAR    Garanties & Handleidingen        (ASN 30001 - 39999)
  5. Kalibratie raster (leeg raster voor uitlijning)

Keuze (1-5): 2

Reeks  : REK - Rekeningen
Bereik : ASN10001 - ASN19999

Eerste nummer (1-9999) [1]:
Aantal labels [270]:
Rand om elke sticker tekenen? (j/n) [n]: n

Klaar  : 270 stickers (1 vel)
Labels : REK10001 t/m REK10270
QR data: ASN10001 t/m ASN10270
Bestand: REK_10001.pdf
```

- Press **Enter** at "Eerste nummer" and "Aantal labels" to accept defaults.
- The output PDF is named automatically: `{SERIES}_{GLOBAL ASN}.pdf`

### Command line

The `start` argument is the series-relative number (1–9999); the script adds the series offset automatically.

```bash
# One sheet of CNTR labels starting at series nr 1 (QR: ASN00001 - ASN00270)
python generate_asn_labels.py 1 --prefix CNTR

# Second sheet of REK labels starting at series nr 271 (QR: ASN10271 - ASN10540)
python generate_asn_labels.py 271 --prefix REK --count 270

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

All QR codes use the single prefix `ASN`, so only one setting is needed — no changes required when switching series:

```env
PAPERLESS_CONSUMER_ENABLE_ASN_BARCODE=true
PAPERLESS_CONSUMER_ASN_BARCODE_PREFIX=ASN
PAPERLESS_CONSUMER_BARCODE_UPSCALE=1.5
```

When a scanned document contains one of these QR-code labels, Paperless-ngx reads the barcode and assigns the matching ASN (the global number, e.g. `10001`). The series (CNTR / REK / DIV / GAR) is visible on the label text but is not part of the barcode.

To automatically route documents to the correct folder/tag by series, use **Workflows** in the Paperless UI:
- Trigger: *Barcode matches* `^ASN0[0-9]{4}$` → assign Document Type "Contracten"
- Trigger: *Barcode matches* `^ASN1[0-9]{4}$` → assign Document Type "Rekeningen"
- etc.

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
