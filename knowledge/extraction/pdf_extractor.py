import fitz  # pymupdf
import pytesseract
from PIL import Image
import io
from transformers import BlipProcessor, BlipForConditionalGeneration

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")

model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)


def extract_pdf(file_path: str) -> list[dict]:
    """
    Opens a PDF and extracts text page by page.
    Returns a list of dicts: [{page: 1, text: "...", needs_ocr: bool}, ...]

    If a page has no embedded text (a scanned image), OCR and BLIP
    captioning run instead. needs_ocr is only True while a page is
    UNRESOLVED — once OCR successfully produces text, it flips back
    to False, because downstream code (chunking, the upload endpoint)
    uses this flag to decide what actually has usable text.
    """
    doc = fitz.open(file_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()

        if text:
            pages.append({"page": page_num + 1, "text": text, "needs_ocr": False})
            continue

        # No embedded text — this page is a scanned image. Run OCR + captioning.
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("jpeg")
        image = Image.open(io.BytesIO(img_bytes))

        ocr_image_text = pytesseract.image_to_string(image).strip()

        inputs = processor(images=image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(out[0], skip_special_tokens=True)

        combined_text = f"ocr text:{ocr_image_text}\ncaption text:{caption}"

        # OCR succeeded (even if the text is short) — this page now has
        # usable text, so needs_ocr flips to False.
        pages.append({"page": page_num + 1, "text": combined_text, "needs_ocr": False})

    doc.close()
    return pages
