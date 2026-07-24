_model = None


def _get_whisper_model():
    global _model
    if _model is None:
        import whisper

        _model = whisper.load_model("base", device="cpu")
    return _model


def extract_audio(file_path):
    model = _get_whisper_model()
    result = model.transcribe(file_path)
    return [{"page": 1, "text": result["text"], "needs_ocr": False}]
