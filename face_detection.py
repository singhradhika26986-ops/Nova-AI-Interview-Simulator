import numpy as np

try:
    import cv2
except Exception:
    cv2 = None


def detect_face(image_bytes=None):
    if cv2 is None:
        return False

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    if image_bytes:
        np_buffer = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
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
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    return len(faces) > 0
