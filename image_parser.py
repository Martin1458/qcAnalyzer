import json
import re
import difflib
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Proportional cell coordinates (fraction of image width/height).
# Derived from the Rocket League CHAT settings layout.
# Each row maps to the first d-pad press; each column to the second.
ROWS = [
    (0.330, 0.362),  # up
    (0.415, 0.447),  # left
    (0.500, 0.532),  # right
    (0.585, 0.617),  # down
]
COLS = [
    (0.253, 0.354),  # up
    (0.383, 0.483),  # left
    (0.509, 0.607),  # right
    (0.609, 0.760),  # down
]
DIRECTIONS = ["up", "left", "right", "down"]


def preprocess(crop):
    # Upscale, convert to grayscale, boost contrast for cleaner OCR
    crop = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
    crop = crop.convert("L")
    crop = ImageEnhance.Contrast(crop).enhance(2.0)
    return crop


def ocr_cell(crop):
    processed = preprocess(crop)
    text = pytesseract.image_to_string(
        processed, config="--psm 7 --oem 3"
    ).strip()
    return text


def normalize(text):
    # Strip the "[N] " prefix the game adds, lowercase, remove punctuation
    text = re.sub(r"^\[?\d+\]?\s*", "", text)
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def best_match(raw_text, options):
    # Strip the "[N] " prefix and surrounding noise, try both normalized and raw
    stripped = re.sub(r"^[^a-zA-Z$!]*\[?\d+\]?\s*", "", raw_text).strip()
    norm = re.sub(r"[^a-z0-9 ]", "", stripped.lower()).strip()
    best_id, best_score = None, 0.0
    for id_, phrase in options.items():
        # Normalized comparison (letters/digits only)
        norm_phrase = re.sub(r"[^a-z0-9 ]", "", phrase.lower()).strip()
        score_norm = difflib.SequenceMatcher(None, norm, norm_phrase).ratio() if norm else 0.0
        # Raw comparison (keeps special chars like $#@%!)
        score_raw = difflib.SequenceMatcher(None, stripped.lower(), phrase.lower()).ratio()
        score = max(score_norm, score_raw)
        if score > best_score:
            best_score = score
            best_id = id_
    return best_id, best_score


def parse(image_path, options_path, output_path):
    img = Image.open(image_path)
    w, h = img.size

    with open(options_path, encoding="utf-8") as f:
        options = json.load(f)

    result = {}
    for ri, (row_dir, (y1f, y2f)) in enumerate(zip(DIRECTIONS, ROWS)):
        result[row_dir] = {}
        for ci, (col_dir, (x1f, x2f)) in enumerate(zip(DIRECTIONS, COLS)):
            box = (int(x1f * w), int(y1f * h), int(x2f * w), int(y2f * h))
            crop = img.crop(box)
            raw = ocr_cell(crop)
            id_, score = best_match(raw, options)
            phrase = options.get(id_, "?")
            if score < 0.4:
                print(f"  WARNING low confidence r{ri+1}c{ci+1} ({row_dir}->{col_dir}): "
                      f"OCR={repr(raw)}  best={repr(phrase)} (score={score:.2f})")
            else:
                print(f"  r{ri+1}c{ci+1} ({row_dir}->{col_dir}): {repr(phrase)} (score={score:.2f})")
            result[row_dir][col_dir] = id_

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
    print(f"\nWrote {output_path}")
    return result


if __name__ == "__main__":
    parse("image.png", "qc_options.json", "image_filled.json")
