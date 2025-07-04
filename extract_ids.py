import re
import os
import pytesseract
import pandas as pd
import cv2

# ─── CONFIG ───────────────────────────────────────────────────────────────────

# Path to the folder with your ID images
IMAGE_FOLDER = 'id_images'

# Output spreadsheet
OUTPUT_XLSX = 'extracted_id_data.xlsx'

# Optional: if you ever add a custom tesseract path, uncomment & edit:
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

# ─── FUNCTIONS ────────────────────────────────────────────────────────────────

def preprocess_image(image_path):
    """Load image, convert to B&W, threshold and denoise for best OCR."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Otsu threshold
    _, thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Median blur
    return cv2.medianBlur(thr, 3)

def extract_text(img):
    """Run Tesseract OCR on preprocessed image."""
    return pytesseract.image_to_string(img, lang='ron+eng')  # Romanian + English

def parse_fields(text):
    """
    From the raw OCR text, extract:
      - CNP: 13 consecutive digits
      - Nume: text after 'Nume' or 'Name'
      - Domiciliu: text after 'Domiciliu'
    """
    data = {'CNP': '', 'Nume': '', 'Domiciliu': ''}

    # Find CNP (13 digits)
    m = re.search(r'\b(\d{13})\b', text)
    if m:
        data['CNP'] = m.group(1)

    # For each line, look for name and domicile
    for line in text.splitlines():
        line = line.strip()
        # Nume (Romanian) or Name
        if not data['Nume'] and re.search(r'\b(Nume|Name)\b *:?', line, re.IGNORECASE):
            parts = line.split(':', 1)
            data['Nume'] = parts[1].strip() if len(parts) > 1 else ''
        # Domiciliu
        elif not data['Domiciliu'] and 'Domiciliu' in line:
            parts = line.split(':', 1)
            data['Domiciliu'] = parts[1].strip() if len(parts) > 1 else ''

    return data

# ─── MAIN ────────────────────────────────────────────────────────────────────

def process_all_images(folder):
    rows = []
    for fn in os.listdir(folder):
        if not fn.lower().endswith(('.jpg','.jpeg','.png')):
            continue
        path = os.path.join(folder, fn)
        print(f"→ Processing {fn}")
        pre = preprocess_image(path)
        txt = extract_text(pre)
        fields = parse_fields(txt)
        fields['Image'] = fn
        rows.append(fields)

    if not rows:
        print("No images found in", folder)
        return

    df = pd.DataFrame(rows)
    # Save to Excel
    df.to_excel(OUTPUT_XLSX, index=False)
    print(f"\n✅ Done! Results written to {OUTPUT_XLSX}")

if __name__ == "__main__":
    process_all_images(IMAGE_FOLDER)
    # To install all required modules, run:
    # pip install opencv-python pytesseract pandas

    # You also need to have Tesseract-OCR installed on your system.
    # On Ubuntu: sudo apt-get install tesseract-ocr
    # On Windows: Download from https://github.com/tesseract-ocr/tesseract