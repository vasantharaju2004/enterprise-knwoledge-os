# preprocessing image
# pillow(PIL) is for resize, and reshape of the file
# python wrapper as ocr
# pip install tesseract-ocr
import pytesseract
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")

model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
)

# pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"


def extract_image(file_path):
    # ocr + captioning
    img = Image.open(file_path).convert("RGB")

    # ocr(tesseract) text extraction engine
    ocr_text = pytesseract.image_to_string(img)

    # captioning
    inputs = processor(images=img, return_tensors="pt")

    out = model.generate(**inputs, max_new_tokens=50)

    caption = processor.decode(out[0], skip_special_tokens=True)

    combined_text = f"ocr text:{ocr_text}\ncaption text:{caption}"

    return [{"page": 1, "text": combined_text, "needs_ocr": False}]


# print(extract_image("//home/vasanth/Desktop/K vasantha Raju/love types.png"))
