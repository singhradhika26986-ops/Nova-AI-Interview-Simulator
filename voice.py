import tempfile


def speak(text, lang="en"):
    if not text.strip():
        raise ValueError("Text for speech cannot be empty.")

    from gtts import gTTS

    tts = gTTS(text=text, lang=lang, slow=False)
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(file.name)
    return file.name
