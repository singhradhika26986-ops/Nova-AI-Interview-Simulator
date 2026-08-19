import asyncio
import tempfile


def _speak_edge_tts(text, voice="en-IN-PrabhatNeural", rate="+15%"):
    import edge_tts

    async def _generate():
        communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
        file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        await communicate.save(file.name)
        return file.name

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_generate())
        finally:
            loop.close()
    except RuntimeError:
        return asyncio.run(_generate())


def _speak_gtts(text, lang="en"):
    from gtts import gTTS

    tts = gTTS(text=text, lang=lang, slow=False)
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(file.name)
    return file.name


def speak(text, lang="en"):
    """Generate speech audio for the given text and return the mp3 file path.

    Uses a natural-sounding male voice (Microsoft Edge neural voice) by
    default. Falls back to Google TTS only if the primary engine is
    unreachable, so narration keeps working even if one service is down.
    """
    if not text.strip():
        raise ValueError("Text for speech cannot be empty.")

    try:
        return _speak_edge_tts(text)
    except Exception:
        return _speak_gtts(text, lang=lang)
