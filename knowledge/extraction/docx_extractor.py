from docx import Document


def extract_docx(file_path: str) -> list[dict]:
    doc = Document(file_path)

    text_parts = []

    for para in doc.paragraphs:
        text = para.text.strip()

        if text:
            text_parts.append(text)

    full_text = "\n".join(text_parts)

    return [{"page": 1, "text": full_text, "needs_ocr": False}]


# print(
#     extract_docx(file_path="/home/vasanth/Desktop/AI_Engineer_8Week_Sprint_Plan.docx")
# )
