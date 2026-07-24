import pytesseract
from PIL import Image

_processor = None
_model = None


def _get_blip():
    global _processor, _model
    if _model is None:
        from transformers import BlipProcessor, BlipForConditionalGeneration

        _processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        _model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
    return _processor, _model


def extract_image(file_path):
    img = Image.open(file_path).convert("RGB")

    ocr_text = pytesseract.image_to_string(img).strip()

    processor, model = _get_blip()
    inputs = processor(images=img, return_tensors="pt")
    out = model.generate(**inputs, max_new_tokens=50)
    caption = processor.decode(out[0], skip_special_tokens=True)

    combined_text = f"ocr text:{ocr_text}\ncaption text:{caption}"
    return [{"page": 1, "text": combined_text, "needs_ocr": False}]
