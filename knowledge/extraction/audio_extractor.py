# whisper = ACR(Automatic Speech Recognition)
import whisper

model = whisper.load_model("base", device="cpu")


def extract_audio(file_path):
    result = model.transcribe(file_path)

    return [{"page": 1, "text": result["text"], "needs_ocr": False}]


#
