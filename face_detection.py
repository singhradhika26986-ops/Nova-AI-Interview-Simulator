import numpy as np

try:
    import cv2
except Exception:
    cv2 = None

_face_cascade = None
_eye_cascade = None


def _load_cascades():
    global _face_cascade, _eye_cascade
    if cv2 is None:
        return False
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    if _eye_cascade is None:
        _eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
    return True


def _decode_frame(image_bytes):
    if cv2 is None or not image_bytes:
        return None
    np_buffer = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    return frame


def detect_face(image_bytes=None):
    if not _load_cascades():
        return False

    if image_bytes:
        frame = _decode_frame(image_bytes)
        if frame is None:
            return False
    else:
        cap = cv2.VideoCapture(0)
        try:
            ret, frame = cap.read()
            if not ret:
                return False
        finally:
            cap.release()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, 1.3, 5)
    return len(faces) > 0


def analyze_proctoring(image_bytes, baseline_hist=None):
    """Run a lightweight proctoring check on a single camera frame.

    Returns a dict with:
      face_detected      - a face was found in the frame
      eyes_detected      - at least one eye was found inside the face region
      looking_away       - face present but eyes not found (likely turned
                            away or looking down/sideways)
      background_changed - the scene behind the candidate shifted a lot
                            compared to the baseline frame captured at the
                            start of the interview (possible camera move,
                            person swap, or new person entering frame)
      histogram           - the current frame's color histogram, to be
                            stored and passed back in as the next
                            baseline_hist
      message             - a short human-readable status
    """
    if not _load_cascades():
        return {
            "face_detected": None,
            "eyes_detected": None,
            "looking_away": False,
            "background_changed": False,
            "histogram": baseline_hist,
            "message": "Camera analysis is unavailable on this device.",
        }

    frame = _decode_frame(image_bytes)
    if frame is None:
        return {
            "face_detected": False,
            "eyes_detected": False,
            "looking_away": False,
            "background_changed": False,
            "histogram": baseline_hist,
            "message": "Could not read the camera frame.",
        }

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, 1.3, 5)
    face_detected = len(faces) > 0

    eyes_detected = False
    if face_detected:
        x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
        face_roi = gray[y:y + h, x:x + w]
        eyes = _eye_cascade.detectMultiScale(face_roi, 1.1, 8)
        eyes_detected = len(eyes) > 0

    looking_away = face_detected and not eyes_detected

    hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()

    background_changed = False
    if baseline_hist is not None:
        similarity = cv2.compareHist(
            np.array(baseline_hist, dtype=np.float32), hist, cv2.HISTCMP_CORREL
        )
        background_changed = similarity < 0.5

    if not face_detected:
        message = "No face detected. Please stay in front of the camera."
    elif looking_away:
        message = "Please look at the screen. Eyes were not detected."
    elif background_changed:
        message = "Background changed significantly since the interview started."
    else:
        message = "Camera check normal."

    return {
        "face_detected": face_detected,
        "eyes_detected": eyes_detected,
        "looking_away": looking_away,
        "background_changed": background_changed,
        "histogram": hist.tolist(),
        "message": message,
    }
