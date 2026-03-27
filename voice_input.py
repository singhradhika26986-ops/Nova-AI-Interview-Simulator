def listen_from_browser():
    try:
        from streamlit_webrtc import AudioProcessorBase, webrtc_streamer
        import speech_recognition as sr
    except Exception:
        return "", "Voice input is unavailable because optional audio packages are not installed."

    class AudioProcessor(AudioProcessorBase):
        def __init__(self):
            self.recognizer = sr.Recognizer()
            self.text = "Listening..."

        def recv(self, frame):
            return frame

    ctx = webrtc_streamer(key="speech", audio_processor_factory=AudioProcessor)
    if ctx and ctx.audio_processor:
        return ctx.audio_processor.text, "Voice input session started."
    return "", "Voice input session is not active."
