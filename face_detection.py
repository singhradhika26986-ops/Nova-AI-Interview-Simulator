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


def analyze_frame(frame, baseline_hist=None):
    """Run a lightweight proctoring check on a single raw BGR frame (numpy array).

    Returns a dict with:
      face_detected      - a face was found in the frame
      eyes_detected       - at least one eye was found inside the face region
      looking_away        - face present but eyes not found, OR the face is
                             shifted far from the frame center (head turned
                             left/right/up/down)
      background_changed  - the scene behind the candidate shifted a lot
                             compared to the baseline frame captured earlier
      histogram            - the current frame's color histogram, to be
                             stored and passed back in as the next
                             baseline_hist
      message              - a short human-readable status
    """
    empty_result = {
        "face_detected": False,
        "eyes_detected": False,
        "looking_away": False,
        "background_changed": False,
        "histogram": baseline_hist,
        "message": "Camera analysis is unavailable.",
    }

    if not _load_cascades() or frame is None:
        return empty_result

    frame_h, frame_w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, 1.3, 5)
    face_detected = len(faces) > 0

    eyes_detected = False
    off_center = False
    if face_detected:
        x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
        face_roi = gray[y:y + h, x:x + w]
        eyes = _eye_cascade.detectMultiScale(face_roi, 1.1, 8)
        eyes_detected = len(eyes) > 0

        face_center_x = x + w / 2
        face_center_y = y + h / 2
        horiz_offset = abs(face_center_x - frame_w / 2) / (frame_w / 2)
        vert_offset = abs(face_center_y - frame_h / 2) / (frame_h / 2)
        off_center = horiz_offset > 0.32 or vert_offset > 0.38

    looking_away = (face_detected and not eyes_detected) or off_center

    hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()

    background_changed = False
    if baseline_hist is not None:
        similarity = cv2.compareHist(
            np.array(baseline_hist, dtype=np.float32), hist, cv2.HISTCMP_CORREL
        )
        background_changed = similarity < 0.5

    if not face_detected:
        message = "No face detected. Please sit in front of the camera."
    elif looking_away:
        message = "Head or eye movement detected."
    elif background_changed:
        message = "Background changed significantly."
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


def analyze_proctoring(image_bytes, baseline_hist=None):
    """Same as analyze_frame but takes JPEG/PNG bytes (e.g. from st.camera_input)."""
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
    return analyze_frame(frame, baseline_hist)
