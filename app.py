import json
import threading
import time
from pathlib import Path

import streamlit as st
import speech_recognition as sr
import streamlit.components.v1 as components

from answer_evaluator import evaluate_answer
from auth import (
    authenticate_session_token,
    authenticate_user,
    create_persistent_session,
    ensure_admin_user,
    logout_session_token,
    register_user,
)
from dashboard import show_dashboard
from database import (
    get_admin_summary,
    get_practice_progress,
    init_db,
    list_recent_interviews,
    list_user_interviews,
    save_interview,
    upsert_practice_progress,
)
from face_detection import analyze_frame, detect_face
from qa_dataset import get_total_practice_question_count
from question_generator import build_interview_set, get_daily_practice_set, get_practice_questions, get_topics
from report_export import generate_report_pdf, generate_report_text
from voice import speak

try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
    import av
    WEBRTC_AVAILABLE = True
except Exception:
    WEBRTC_AVAILABLE = False


MAX_QUESTIONS = 5


if WEBRTC_AVAILABLE:

    class ProctorVideoProcessor(VideoProcessorBase):
        """Continuously analyzes the candidate's webcam feed in the background
        (a few frames per second) and raises a flag when it looks like the
        candidate has turned away, left the frame, or the background has
        changed. The main app polls this flag every few seconds and has
        Smith speak a warning when it trips.
        """

        def __init__(self):
            self.lock = threading.Lock()
            self.away_streak = 0
            self.alert_flag = None
            self.baseline_hist = None
            self.last_check_ts = 0.0

        def recv(self, frame):
            img = frame.to_ndarray(format="bgr24")
            now = time.time()
            if now - self.last_check_ts > 0.6:
                self.last_check_ts = now
                try:
                    result = analyze_frame(img, self.baseline_hist)
                    with self.lock:
                        if self.baseline_hist is None:
                            self.baseline_hist = result["histogram"]
                        if not result["face_detected"]:
                            self.away_streak += 1
                            if self.away_streak >= 4 and self.alert_flag is None:
                                self.alert_flag = "no_face"
                                self.away_streak = 0
                        elif result["looking_away"]:
                            self.away_streak += 1
                            if self.away_streak >= 4 and self.alert_flag is None:
                                self.alert_flag = "looking_away"
                                self.away_streak = 0
                        elif result["background_changed"]:
                            if self.alert_flag is None:
                                self.alert_flag = "background_changed"
                            self.away_streak = 0
                        else:
                            self.away_streak = 0
                except Exception:
                    pass
            return frame

        def pop_alert(self):
            with self.lock:
                alert = self.alert_flag
                self.alert_flag = None
            return alert


    PROCTOR_MESSAGES = {
        "no_face": "Please sit properly in front of the camera. Do not move away.",
        "looking_away": "Please look at the screen. Do not try to cheat from any external source.",
        "background_changed": "Your background has changed. Do not try to cheat from any external source.",
    }


def render_proctor_stream():
    if not WEBRTC_AVAILABLE:
        st.caption("Live camera monitoring needs the streamlit-webrtc package.")
        return None
    ctx = webrtc_streamer(
        key="smith-proctor-stream",
        video_processor_factory=ProctorVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    )
    return ctx


def poll_proctor_alerts(ctx):
    if ctx is None or not ctx.state.playing or ctx.video_processor is None:
        return
    alert = ctx.video_processor.pop_alert()
    if alert:
        message = PROCTOR_MESSAGES.get(alert, "Please stay visible and still in front of the camera.")
        st.warning(f"⚠️ {message}")
        safe_audio(message, prompt_key=f"proctor_{alert}_{int(time.time())}")


def render_proctor_heartbeat(interval_seconds=4):
    components.html(
        f"""
        <script>
        setInterval(() => {{
            try {{
                const buttons = window.parent.document.querySelectorAll('button');
                for (const btn of buttons) {{
                    if (btn.innerText.includes("__proctor_heartbeat__")) {{
                        btn.click();
                        break;
                    }}
                }}
            }} catch (e) {{}}
        }}, {int(interval_seconds * 1000)});
        </script>
        """,
        height=0,
    )
    st.markdown('<div class="hb-marker"></div>', unsafe_allow_html=True)
    return st.button("__proctor_heartbeat__", key=f"proctor_heartbeat_{int(time.time() // interval_seconds)}")
ANSWER_TIME_LIMIT = 30
TOTAL_PRACTICE_QUESTIONS = get_total_practice_question_count()
SESSION_FILE = Path(__file__).with_name("remembered_session.json")

LOGO_PATH = Path(__file__).with_name("neuralix_logo.png")

st.set_page_config(
    page_title="Smith",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "AI",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 32%),
            radial-gradient(circle at top right, rgba(147, 51, 234, 0.20), transparent 30%),
            linear-gradient(160deg, #0B0B2A 0%, #170B3B 42%, #0A1A3D 100%);
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stMarkdown {
        color: #E5E9FF;
    }
    div[data-testid="stButton"] > button[kind="primary"],
    .stButton > button:first-child {
        background: linear-gradient(135deg, #7C3AED, #2563EB 55%, #0EA5E9 100%) !important;
        color: white !important;
        border: none !important;
    }
    .card {
        background: rgba(23, 17, 60, 0.65);
        border: 1px solid rgba(147, 197, 253, 0.16);
        border-radius: 26px;
        padding: 28px;
        box-shadow: 0 24px 68px rgba(2, 6, 23, 0.55), 0 0 0 1px rgba(124, 58, 237, 0.08);
        margin-bottom: 22px;
        backdrop-filter: blur(14px);
    }
    .mini-card {
        background: rgba(15, 23, 55, 0.85);
        border-left: 6px solid #38BDF8;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 12px 24px rgba(2, 6, 23, 0.4);
        color: #E5E9FF;
    }
    .hero-title {
        font-size: 3.7rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #C4B5FD, #93C5FD 60%, #67E8F9 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        margin: 0 0 10px 0;
    }
    .hero-subtitle {
        font-size: 1.08rem;
        color: #B9C2E8;
        line-height: 1.75;
        max-width: 920px;
        margin: 0;
    }
    .hero-pill-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 18px;
    }
    .hero-pill {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.28), rgba(14, 165, 233, 0.24));
        color: #EDE9FE;
        padding: 9px 14px;
        border-radius: 999px;
        font-size: 0.92rem;
        font-weight: 600;
        border: 1px solid rgba(147, 197, 253, 0.22);
    }
    .section-title {
        font-size: 1.18rem;
        font-weight: 700;
        color: #EDE9FE;
        margin-bottom: 12px;
        letter-spacing: -0.02em;
    }
    .smith-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.35), rgba(14, 165, 233, 0.30));
        border: 1px solid rgba(147, 197, 253, 0.24);
        color: #F3F0FF;
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .status-shell {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-top: 8px;
    }
    .status-card {
        background: linear-gradient(180deg, rgba(30, 27, 75, 0.85), rgba(15, 23, 55, 0.85));
        border: 1px solid rgba(147, 197, 253, 0.16);
        border-radius: 18px;
        padding: 16px;
    }
    .status-label {
        color: #93A3D6;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .status-value {
        color: #F3F0FF;
        font-size: 1.05rem;
        font-weight: 700;
    }
    .question-shell {
        padding: 22px;
        border-radius: 20px;
        background: linear-gradient(180deg, rgba(30, 27, 75, 0.75), rgba(11, 26, 61, 0.75));
        border: 1px solid rgba(56, 189, 248, 0.22);
        margin-bottom: 16px;
        box-shadow: inset 0 1px 0 rgba(147, 197, 253, 0.08);
    }
    .question-text {
        color: #F3F0FF;
        font-size: 1.38rem;
        font-weight: 700;
        line-height: 1.55;
    }
    .note-box {
        padding: 14px 16px;
        border-radius: 16px;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.22);
        color: #E5E9FF;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    div[data-testid="stButton"] > button {
        border-radius: 14px;
        border: none;
        min-height: 48px;
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(2, 6, 23, 0.4);
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #7C3AED, #4F46E5 45%, #0EA5E9 100%);
        color: white;
    }
    div[data-testid="stDownloadButton"] > button {
        border-radius: 14px;
        min-height: 46px;
        font-weight: 700;
        background: rgba(56, 189, 248, 0.16);
        color: #E5E9FF;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        border-radius: 14px;
        background: rgba(11, 15, 46, 0.6);
        color: #F3F0FF;
        border: 1px solid rgba(147, 197, 253, 0.2);
    }
    div[data-testid="stSelectbox"] div, div[data-baseweb="select"] {
        background: rgba(11, 15, 46, 0.6);
        color: #F3F0FF;
        border-radius: 14px;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A0A22 0%, #170B3B 55%, #0A1A3D 100%);
        border-right: 1px solid rgba(124, 58, 237, 0.25);
    }
    section[data-testid="stSidebar"] * {
        color: #E5E9FF !important;
    }
    section[data-testid="stSidebar"] .stCaption {
        color: #93A3D6 !important;
    }
    .final-shell {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.22), rgba(14, 165, 233, 0.16));
        border: 1px solid rgba(147, 197, 253, 0.2);
        border-radius: 22px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .auth-grid {
        display: grid;
        grid-template-columns: 1.05fr 1fr;
        gap: 18px;
        align-items: stretch;
    }
    .auth-hero {
        background: linear-gradient(180deg, rgba(124, 58, 237, 0.28), rgba(14, 165, 233, 0.18));
        border: 1px solid rgba(147, 197, 253, 0.2);
        border-radius: 24px;
        padding: 24px;
        min-height: 100%;
    }
    .auth-title {
        color: #F3F0FF;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0 0 10px 0;
    }
    .auth-copy {
        color: #C7CFF5;
        font-size: 1rem;
        line-height: 1.75;
        margin: 0 0 18px 0;
    }
    .auth-list {
        margin: 0;
        padding-left: 18px;
        color: #F3F0FF;
        line-height: 1.9;
        font-weight: 600;
    }
    @media (max-width: 900px) {
        .card {
            padding: 20px;
            border-radius: 22px;
        }
        .hero-title {
            font-size: 2.5rem;
            line-height: 1.12;
        }
        .hero-subtitle {
            font-size: 1rem;
            line-height: 1.65;
        }
        .auth-grid,
        .status-shell {
            grid-template-columns: 1fr;
        }
        .auth-title {
            font-size: 1.85rem;
        }
        .question-text {
            font-size: 1.16rem;
            line-height: 1.5;
        }
    }
    @media (max-width: 640px) {
        .card,
        .auth-hero,
        .question-shell,
        .final-shell {
            padding: 16px;
            border-radius: 18px;
        }
        .smith-badge,
        .hero-pill {
            font-size: 0.82rem;
            padding: 8px 12px;
        }
        .hero-title {
            font-size: 2rem;
            line-height: 1.08;
            letter-spacing: -0.03em;
            text-shadow: none;
        }
        .hero-subtitle,
        .auth-copy {
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .section-title {
            font-size: 1.02rem;
        }
        .question-text {
            font-size: 1.02rem;
        }
        .auth-title {
            font-size: 1.55rem;
            line-height: 1.2;
        }
        .auth-list {
            padding-left: 16px;
            line-height: 1.75;
        }
        div[data-testid="stButton"] > button {
            min-height: 44px;
        }
    }
    .bot-avatar-row {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
    }
    .bot-avatar {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        background: linear-gradient(135deg, #7C3AED, #2563EB 55%, #0EA5E9 100%);
        box-shadow: 0 0 0 6px rgba(124, 58, 237, 0.18);
        flex-shrink: 0;
    }
    .bot-avatar.speaking {
        animation: bot-pulse 1.1s ease-in-out infinite;
    }
    @keyframes bot-pulse {
        0% { box-shadow: 0 0 0 6px rgba(124, 58, 237, 0.28), 0 0 0 0 rgba(56, 189, 248, 0.5); }
        70% { box-shadow: 0 0 0 6px rgba(124, 58, 237, 0.28), 0 0 0 18px rgba(56, 189, 248, 0); }
        100% { box-shadow: 0 0 0 6px rgba(124, 58, 237, 0.28), 0 0 0 0 rgba(56, 189, 248, 0); }
    }
    .bot-status-text {
        font-weight: 700;
        color: #F3F0FF;
    }
    .bot-status-sub {
        font-size: 0.85rem;
        color: #93A3D6;
    }
    .sound-bars {
        display: inline-flex;
        align-items: flex-end;
        gap: 3px;
        height: 18px;
        margin-left: 10px;
    }
    .sound-bars span {
        width: 4px;
        background: #38BDF8;
        border-radius: 2px;
        animation: sound-bounce 0.9s ease-in-out infinite;
    }
    .sound-bars span:nth-child(1) { animation-delay: 0s; height: 6px; }
    .sound-bars span:nth-child(2) { animation-delay: 0.15s; height: 14px; }
    .sound-bars span:nth-child(3) { animation-delay: 0.3s; height: 9px; }
    .sound-bars span:nth-child(4) { animation-delay: 0.45s; height: 16px; }
    @keyframes sound-bounce {
        0%, 100% { transform: scaleY(0.4); }
        50% { transform: scaleY(1); }
    }
    .hb-marker + div[data-testid="stButton"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_bot_avatar(speaking: bool, label: str = None):
    bars = '<span class="sound-bars"><span></span><span></span><span></span><span></span></span>' if speaking else ""
    status = label or ("Smith is speaking..." if speaking else "Smith is listening")
    sub = "Please wait while the question is read out." if speaking else "Go ahead and answer when you're ready."
    st.markdown(
        f"""
        <div class="bot-avatar-row">
            <div class="bot-avatar {'speaking' if speaking else ''}">🤖</div>
            <div>
                <div class="bot-status-text">{status}{bars}</div>
                <div class="bot-status-sub">{sub}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_session_state():
    defaults = {
        "current_user": None,
        "session_token": "",
        "admin_mode": False,
        "voice_enabled": False,
        "voice_input_enabled": False,
        "camera_enabled": True,
        "face_verified": None,
        "started": False,
        "topic": "Python",
        "question_index": 0,
        "interview_plan": [],
        "results": [],
        "spoken_prompts": set(),
        "last_audio_text": "",
        "last_audio_seconds": 0,
        "proctor_baseline": None,
        "proctor_alerts": [],
        "completion_payload": None,
        "question_started_at": None,
        "intro_started_at": None,
        "clarification_requested": False,
        "pending_evaluation": None,
        "live_feedback": None,
        "last_processed_answer_key": "",
        "conversation_stage": "idle",
        "auth_checked": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_interview_state():
    st.session_state.started = False
    st.session_state.question_index = 0
    st.session_state.interview_plan = []
    st.session_state.results = []
    st.session_state.spoken_prompts = set()
    st.session_state.last_audio_text = ""
    st.session_state.completion_payload = None
    st.session_state.question_started_at = None
    st.session_state.intro_started_at = None
    st.session_state.clarification_requested = False
    st.session_state.pending_evaluation = None
    st.session_state.live_feedback = None
    st.session_state.last_processed_answer_key = ""
    st.session_state.conversation_stage = "idle"


def read_saved_session_token():
    if not SESSION_FILE.exists():
        return ""
    try:
        payload = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        return payload.get("session_token", "")
    except Exception:
        return ""


def write_saved_session_token(session_token):
    SESSION_FILE.write_text(
        json.dumps({"session_token": session_token}),
        encoding="utf-8",
    )


def clear_saved_session_token():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def build_intro_script(candidate_name, topic):
    return (
        f"Hello {candidate_name}. I am Smith, your AI recruiter for today. "
        f"I will guide you through a short and focused interview on {topic}. "
        "For a fair assessment, please avoid using Google, ChatGPT, or any other external source. "
        "Please answer naturally, confidently, and professionally, just as you would in a real interview."
    )


def build_clarification_prompt(topic):
    return (
        f"I would like a little more clarity in your {topic} answer. "
        "Please explain it once again with a crisp definition, one relevant example, and a more structured explanation."
    )


def transcribe_audio(audio_file):
    if audio_file is None:
        return "", ""

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        transcript = recognizer.recognize_google(audio_data)
        return transcript, ""
    except sr.UnknownValueError:
        return "", "I could not clearly understand the audio. Please speak again more clearly."
    except Exception:
        return "", "Voice transcription is unavailable right now. You can still answer using text."


def render_countdown(deadline):
    remaining_seconds = max(0, int(deadline - time.time()))
    timer_html = f"""
    <div style="margin: 10px 0 18px 0; padding: 12px 16px; border-radius: 14px;
                background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.25);
                color: #E0F2FE; font-weight: 700; font-family: sans-serif;">
        ⏱ Answer Timer: <span id="smith-timer">{remaining_seconds}</span> seconds left
    </div>
    <script>
    (() => {{
        const deadline = {int(deadline * 1000)};
        const timerElement = document.getElementById("smith-timer");
        const tick = () => {{
            const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
            if (timerElement) timerElement.textContent = remaining;
            if (remaining <= 0) {{
                clearInterval(intervalId);
                try {{
                    const buttons = window.parent.document.querySelectorAll('button');
                    for (const btn of buttons) {{
                        if (btn.innerText.includes("Submit Timed-Out Response")) {{
                            btn.click();
                            break;
                        }}
                    }}
                }} catch (e) {{}}
            }}
        }};
        tick();
        const intervalId = setInterval(tick, 1000);
    }})();
    </script>
    """
    components.html(timer_html, height=54)


def finalize_current_answer(current_user, current_round, answer, time_expired):
    current_index = st.session_state.question_index
    evaluation = evaluate_answer(
        answer=answer,
        question=current_round["question"],
        expected_answer=current_round["answer"],
        topic=st.session_state.topic,
        keywords=current_round.get("keywords", []),
    )

    if time_expired and not answer.strip():
        skip_message = "It's okay if you don't know the answer, let's move to the next question."
        evaluation["summary"] = skip_message
        st.session_state.results.append(
            {
                "question": current_round["question"],
                **evaluation,
            }
        )
        st.session_state.live_feedback = skip_message
        safe_audio(skip_message, prompt_key=f"skip_{current_index}")
        time.sleep(max(2, min(st.session_state.last_audio_seconds + 1, 10)))

        if current_index + 1 < len(st.session_state.interview_plan):
            st.session_state.question_index += 1
            st.session_state.question_started_at = None
            st.session_state.conversation_stage = "question"
        else:
            st.session_state.started = False
            st.session_state.conversation_stage = "completed"
            report_text, average_score, recommendation = save_completed_interview()
            st.session_state.completion_payload = {
                "report_text": report_text,
                "average_score": average_score,
                "recommendation": recommendation,
            }
        st.rerun()
        return

    if time_expired:
        evaluation["summary"] = (
            f"The answer window expired after {ANSWER_TIME_LIMIT} seconds. The system evaluated the available response."
        )

    if evaluation["overall_score"] < 6 and not st.session_state.clarification_requested:
        st.session_state.pending_evaluation = evaluation
        st.session_state.clarification_requested = True
        st.session_state.question_started_at = None
        st.session_state.live_feedback = (
            "I would like a clearer explanation. Please answer once more with a short definition, one relevant example, and a well-structured response."
        )
        safe_audio(st.session_state.live_feedback, prompt_key=f"clarify_intro_{current_index}")
        time.sleep(max(2, min(st.session_state.last_audio_seconds + 1, 10)))
        st.rerun()

    if st.session_state.clarification_requested:
        evaluation["summary"] = evaluation["summary"] + " Clarification round completed."
        st.session_state.clarification_requested = False
        st.session_state.pending_evaluation = None

    st.session_state.results.append(
        {
            "question": current_round["question"],
            **evaluation,
        }
    )
    matched_keywords = evaluation.get("strengths", [])
    keyword_line = ""
    for strength_line in matched_keywords:
        if "key technical points" in strength_line:
            keyword_line = strength_line.replace("You covered", "You mentioned").rstrip(".")
            break

    if evaluation["overall_score"] >= 7:
        spoken_feedback = (
            (keyword_line + ". " if keyword_line else "")
            + "That was a clear and well-structured answer."
        )
    else:
        spoken_feedback = (
            (keyword_line + ". " if keyword_line else "")
            + "Try to add a bit more depth and structure next time."
        )

    is_last_question = current_index + 1 >= len(st.session_state.interview_plan)
    spoken_feedback += (
        " That was the last question, let's wrap up." if is_last_question else " Let's move to the next question."
    )

    st.session_state.live_feedback = spoken_feedback
    safe_audio(spoken_feedback, prompt_key=f"feedback_{current_index}")
    time.sleep(max(2, min(st.session_state.last_audio_seconds + 1, 10)))

    if current_index + 1 < len(st.session_state.interview_plan):
        st.session_state.question_index += 1
        st.session_state.question_started_at = None
        st.session_state.conversation_stage = "question"
    else:
        st.session_state.started = False
        st.session_state.conversation_stage = "completed"
        report_text, average_score, recommendation = save_completed_interview()
        st.session_state.completion_payload = {
            "report_text": report_text,
            "average_score": average_score,
            "recommendation": recommendation,
            "pdf_bytes": generate_report_pdf(
                current_user["full_name"],
                st.session_state.topic,
                st.session_state.results,
            ),
        }
        st.session_state.live_feedback = (
            "We have reached the end of the interview. Thank you for your time and participation."
        )

    st.rerun()


def _estimate_speech_seconds(text):
    words = max(1, len(text.split()))
    return round(words / 2.5, 1)


def safe_audio(text, prompt_key=None):
    if not st.session_state.voice_enabled:
        return
    if prompt_key and prompt_key in st.session_state.spoken_prompts:
        return
    if not text or not text.strip():
        return

    try:
        audio_path = speak(text)
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        try:
            Path(audio_path).unlink(missing_ok=True)
        except Exception:
            pass
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        st.session_state.last_audio_text = text
        st.session_state.last_audio_seconds = _estimate_speech_seconds(text)
        if prompt_key:
            st.session_state.spoken_prompts.add(prompt_key)
    except Exception:
        st.warning(
            "Voice narration could not play right now (check your internet connection). "
            "The app will continue without audio for this line."
        )


def show_camera_tools():
    st.markdown("<div class='section-title'>Camera Readiness</div>", unsafe_allow_html=True)
    st.caption("Allow browser camera permission so Smith can verify you're ready before starting.")
    camera_shot = st.camera_input("Camera Check", key="browser_camera_input")
    if camera_shot is not None:
        st.session_state.face_verified = detect_face(camera_shot.getvalue())

    if st.session_state.face_verified is True:
        st.success("Face detected successfully. Camera is working.")
    elif st.session_state.face_verified is False and camera_shot is not None:
        st.warning("Camera opened, but face was not detected clearly. Please face the camera directly.")


def handle_start_interview(topic):
    reset_interview_state()
    st.session_state.started = True
    st.session_state.topic = topic
    st.session_state.interview_plan = build_interview_set(topic, MAX_QUESTIONS)
    st.session_state.intro_started_at = time.time()
    st.session_state.question_started_at = None
    st.session_state.conversation_stage = "intro"


def save_completed_interview():
    current_user = st.session_state.current_user
    report_text, average_score, recommendation = generate_report_text(
        current_user["full_name"],
        st.session_state.topic,
        st.session_state.results,
    )
    save_interview(
        current_user["id"],
        st.session_state.topic,
        average_score,
        recommendation,
        report_text,
        st.session_state.results,
    )
    return report_text, average_score, recommendation


def render_auth_screen():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    left_col, right_col = st.columns([1.05, 1])

    with left_col:
        st.markdown(
            """
            <div class="auth-hero">
                <div class="smith-badge">Smith Secure Access</div>
                <h2 class="auth-title">Welcome to Your Interview Workspace</h2>
                <p class="auth-copy">
                    Sign in once and continue your interview journey securely on this device.
                    Your interview history, analytics, and final reports will stay linked to your account.
                </p>
                <ul class="auth-list">
                    <li>Persistent login on the same device</li>
                    <li>Saved interview history and reports</li>
                    <li>Secure password protection</li>
                    <li>Admin analytics for project demonstration</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        login_tab, register_tab = st.tabs(["Login", "Register"])

        with login_tab:
            st.markdown("<div class='section-title'>Secure Login</div>", unsafe_allow_html=True)
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            st.caption("Login once and the app will remember you on this device.")
            if st.button("Login", type="primary", use_container_width=True):
                user = authenticate_user(email, password)
                if user:
                    session_token = create_persistent_session(user["id"])
                    write_saved_session_token(session_token)
                    st.session_state.current_user = user
                    st.session_state.session_token = session_token
                    st.session_state.admin_mode = user["role"] == "admin"
                    st.session_state.auth_checked = True
                    reset_interview_state()
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

        with register_tab:
            st.markdown("<div class='section-title'>Create Account</div>", unsafe_allow_html=True)
            full_name = st.text_input("Full Name", key="register_name")
            email = st.text_input("Email Address", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            if st.button("Create Account", use_container_width=True):
                success, message = register_user(full_name, email, password)
                if success:
                    st.success("Account created successfully. Please login once to continue.")
                else:
                    st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)


def render_student_interview_tab():
    current_user = st.session_state.current_user
    setup_col, utility_col = st.columns([1.55, 1])

    with setup_col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Interview Workspace</div>", unsafe_allow_html=True)
        if not st.session_state.started and st.session_state.conversation_stage != "completed":
            candidate_name = st.text_input(
                "Candidate Name",
                value=current_user["full_name"] if current_user else "Demo Candidate",
            )
            if candidate_name.strip() and candidate_name.strip() != current_user["full_name"]:
                st.session_state.current_user["full_name"] = candidate_name.strip()
            topic = st.selectbox(
                "Choose interview topic",
                get_topics(),
                index=get_topics().index(st.session_state.topic),
            )
            st.session_state.voice_enabled = st.toggle(
                "Enable voice narration",
                value=True if not st.session_state.started else st.session_state.voice_enabled,
                key="voice_toggle",
            )
            st.caption(
                "This interview is voice-first. Please allow microphone permission when your browser asks. "
                "For security reasons, browsers do not allow microphone recording to start fully automatically."
            )

            action_col1, action_col2 = st.columns(2)
            if action_col1.button("Start Interview", type="primary", use_container_width=True):
                handle_start_interview(topic)
                st.session_state.live_feedback = build_intro_script(current_user["full_name"], topic)
                safe_audio(st.session_state.live_feedback, prompt_key="intro")
                st.rerun()
            if action_col2.button("Reset Current Interview", use_container_width=True):
                reset_interview_state()
                st.rerun()
        else:
            st.success("Interview in progress")
            st.markdown(
                f"""
                <div class="status-shell">
                    <div class="status-card">
                        <div class="status-label">Candidate</div>
                        <div class="status-value">{current_user['full_name']}</div>
                    </div>
                    <div class="status-card">
                        <div class="status-label">Interview Topic</div>
                        <div class="status-value">{st.session_state.topic}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='note-box'>Smith is guiding the session. Speak clearly after the microphone prompt appears.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.started and st.session_state.interview_plan:
            if st.session_state.conversation_stage == "intro":
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<div class='smith-badge'>Smith AI Recruiter</div>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Interview Introduction</div>", unsafe_allow_html=True)
                intro_text = st.session_state.live_feedback or build_intro_script(current_user["full_name"], topic)
                render_bot_avatar(speaking=True, label="Smith is introducing the interview...")
                st.info(intro_text)
                safe_audio(intro_text, prompt_key="intro")
                st.caption("Smith is introducing the interview. The first question will start automatically.")
                st.markdown("</div>", unsafe_allow_html=True)
                time.sleep(max(4, min(st.session_state.last_audio_seconds + 1, 20)))
                st.session_state.conversation_stage = "question"
                st.session_state.question_started_at = None
                st.rerun()
                return

            current_index = st.session_state.question_index
            current_round = st.session_state.interview_plan[current_index]
            is_clarification = st.session_state.clarification_requested
            prompt_text = (
                build_clarification_prompt(st.session_state.topic)
                if is_clarification
                else current_round["question"]
            )
            question_prompt_key = f"{'clarify' if is_clarification else 'question'}_{current_index}"

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='smith-badge'>Smith AI Recruiter</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-title'>Question {current_index + 1} of {len(st.session_state.interview_plan)}</div>",
                unsafe_allow_html=True,
            )
            if st.session_state.live_feedback:
                st.info(st.session_state.live_feedback)
            st.markdown("<div class='question-shell'>", unsafe_allow_html=True)
            st.markdown(f"<div class='question-text'>{prompt_text}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.question_started_at is None:
                # Speaking phase: bot narrates the question, timer has not started yet.
                render_bot_avatar(speaking=True)
                safe_audio(prompt_text, prompt_key=question_prompt_key)
                st.caption("🔊 If the audio did not start by itself, tap the play button above once — the timer will start right after Smith finishes speaking.")
                begin_clicked = st.button("I'm ready, start the timer", key=f"begin_{current_index}_{question_prompt_key}", use_container_width=True)
                wait_seconds = max(2, min(int(st.session_state.last_audio_seconds) + 1, 15))
                auto_advance_html = f"""
                <script>
                setTimeout(() => {{
                    try {{
                        const buttons = window.parent.document.querySelectorAll('button');
                        for (const btn of buttons) {{
                            if (btn.innerText.includes("I'm ready, start the timer")) {{
                                btn.click();
                                break;
                            }}
                        }}
                    }} catch (e) {{}}
                }}, {wait_seconds * 1000});
                </script>
                """
                components.html(auto_advance_html, height=0)
                st.markdown("</div>", unsafe_allow_html=True)
                if begin_clicked:
                    st.session_state.question_started_at = time.time()
                    st.rerun()
                return

            deadline = st.session_state.question_started_at + ANSWER_TIME_LIMIT
            render_bot_avatar(speaking=False)
            st.caption(
                f"Difficulty: {current_round.get('difficulty', 'Not specified')} | Time limit: {ANSWER_TIME_LIMIT} seconds"
            )
            render_countdown(deadline)

            audio_answer = st.audio_input(
                "Speak your answer (tap the mic to record, tap again to stop)",
                key=f"audio_answer_{current_index}_{'clarify' if is_clarification else 'main'}",
            )
            transcript, transcript_error = transcribe_audio(audio_answer)
            if audio_answer is not None and not transcript and not transcript_error:
                st.info("Audio received. Smith is processing your answer.")
            if transcript_error:
                st.warning(transcript_error)
            if transcript:
                st.success("Voice answer captured successfully.")
                st.write(f"Transcript: {transcript}")
            else:
                st.caption(
                    "Click the microphone, record your answer, and stop recording. Smith will review it automatically after transcription."
                )

            answer = transcript.strip()
            time_expired = time.time() > deadline
            answer_key = f"{current_index}|{'clarify' if is_clarification else 'main'}|{answer}"

            if answer and answer_key != st.session_state.last_processed_answer_key:
                st.session_state.last_processed_answer_key = answer_key
                finalize_current_answer(current_user, current_round, answer, time_expired)

            if not answer:
                if time_expired:
                    st.warning("Time is up. Submitting automatically...")
                st.caption("The answer auto-submits when the timer ends. You can also submit early:")
                if st.button("Submit Timed-Out Response", use_container_width=True, key=f"timeout_btn_{current_index}_{'clarify' if is_clarification else 'main'}"):
                    st.session_state.last_processed_answer_key = (
                        f"{current_index}|{'clarify' if is_clarification else 'main'}|timeout"
                    )
                    finalize_current_answer(current_user, current_round, "", True)

            if st.session_state.camera_enabled and WEBRTC_AVAILABLE:
                st.markdown("<div class='section-title'>Live Proctoring</div>", unsafe_allow_html=True)
                st.caption("Camera stays on during the interview. Smith will speak up if you look away, leave the frame, or the background changes.")
                ctx = render_proctor_stream()
                poll_proctor_alerts(ctx)
                render_proctor_heartbeat()

            st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.results:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            show_dashboard(st.session_state.results)
            st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.conversation_stage == "completed" and st.session_state.completion_payload:
                payload = st.session_state.completion_payload
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Final Interview Outcome</div>", unsafe_allow_html=True)
                st.markdown("<div class='final-shell'>", unsafe_allow_html=True)
                safe_audio(st.session_state.live_feedback, prompt_key="completed")
                st.success(f"Average Score: {payload['average_score']}/10")
                st.info(f"Recommendation: {payload['recommendation']}")
                st.write(
                    "Final feedback: "
                    + (
                        "Your interview performance was strong and well-structured."
                        if payload["average_score"] >= 7
                        else "Your interview performance showed potential, but it needs clearer explanation and more confident delivery."
                    )
                )
                st.write("We have reached the end of the interview.")
                st.caption("Smith has completed the interview assessment and prepared your final result summary.")
                st.markdown("</div>", unsafe_allow_html=True)
                st.download_button(
                    label="Download Text Report",
                    data=payload["report_text"],
                    file_name="interview_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
                if payload["pdf_bytes"]:
                    st.download_button(
                        label="Download PDF Report",
                        data=payload["pdf_bytes"],
                        file_name="interview_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.caption("PDF export needs `reportlab` installed.")
                st.caption("This interview session will close automatically.")
                time.sleep(5)
                reset_interview_state()
                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    with utility_col:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Candidate Snapshot</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="status-shell">
                <div class="status-card">
                    <div class="status-label">Candidate</div>
                    <div class="status-value">{current_user['full_name']}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Role</div>
                    <div class="status-value">{current_user['role'].title()}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Topic</div>
                    <div class="status-value">{st.session_state.topic}</div>
                </div>
                <div class="status-card">
                    <div class="status-label">Completed Rounds</div>
                    <div class="status-value">{len(st.session_state.results)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Email: {current_user['email']}")
        if st.session_state.last_audio_text:
            st.caption(f"Last voice prompt: {st.session_state.last_audio_text}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if not st.session_state.started:
            show_camera_tools()
        else:
            st.caption("Camera is live in the main interview panel while the interview is running.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_practice_tab():
    current_user = st.session_state.current_user
    progress_rows = get_practice_progress(current_user["id"])
    progress_map = {row["question_id"]: row for row in progress_rows}

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Interview Practice Library</div>", unsafe_allow_html=True)
    st.caption(
        f"This library contains {TOTAL_PRACTICE_QUESTIONS} professional practice questions with model answers."
    )

    filter_col1, filter_col2 = st.columns([1.2, 1])
    with filter_col1:
        practice_topic = st.selectbox("Practice Topic", get_topics(), key="practice_topic")
    with filter_col2:
        difficulty_filter = st.selectbox(
            "Difficulty",
            ["All", "Easy", "Medium", "Hard"],
            key="practice_difficulty",
        )

    search_term = st.text_input(
        "Search Question",
        key="practice_search",
        placeholder="Search by concept or keyword...",
    ).strip().lower()

    daily_set = get_daily_practice_set(practice_topic, limit=5)
    bookmarked_count = sum(1 for row in progress_rows if row["is_bookmarked"])
    completed_count = sum(1 for row in progress_rows if row["is_completed"])
    topic_questions = get_practice_questions(practice_topic)
    topic_completed = sum(
        1 for item in topic_questions if progress_map.get(item["question"], {}).get("is_completed")
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Bookmarked", bookmarked_count)
    metric_col2.metric("Completed", completed_count)
    metric_col3.metric("Topic Progress", f"{topic_completed}/{len(topic_questions)}")

    with st.expander("Daily Random Practice Set"):
        for item in daily_set:
            st.write(f"- {item['question']}")

    questions = get_practice_questions(practice_topic)
    filtered_questions = []
    for item in questions:
        if difficulty_filter != "All" and item["difficulty"] != difficulty_filter:
            continue
        if search_term and search_term not in item["question"].lower() and search_term not in item["answer"].lower():
            continue
        filtered_questions.append(item)

    st.write(f"Showing {len(filtered_questions)} questions")

    for index, item in enumerate(filtered_questions, start=1):
        question_id = item["question"]
        row = progress_map.get(question_id, {})
        bookmarked = bool(row.get("is_bookmarked"))
        completed = bool(row.get("is_completed"))
        with st.expander(f"{index}. {item['question']}"):
            st.caption(f"Difficulty: {item['difficulty']}")
            st.markdown("**Model Answer**")
            st.write(item["answer"])
            st.markdown("**Keywords To Mention**")
            st.write(", ".join(item["keywords"]))
            action_col1, action_col2 = st.columns(2)
            bookmark_label = "Remove Bookmark" if bookmarked else "Bookmark"
            complete_label = "Mark Incomplete" if completed else "Mark Completed"
            if action_col1.button(bookmark_label, key=f"bookmark_{practice_topic}_{index}", use_container_width=True):
                upsert_practice_progress(
                    current_user["id"],
                    practice_topic,
                    question_id,
                    is_bookmarked=0 if bookmarked else 1,
                )
                st.rerun()
            if action_col2.button(complete_label, key=f"complete_{practice_topic}_{index}", use_container_width=True):
                upsert_practice_progress(
                    current_user["id"],
                    practice_topic,
                    question_id,
                    is_completed=0 if completed else 1,
                )
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_history_tab():
    current_user = st.session_state.current_user
    history = list_user_interviews(current_user["id"])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Interview History</div>", unsafe_allow_html=True)
    if not history:
        st.info("No saved interviews yet. Complete an interview to build your portfolio history.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    total_attempts = len(history)
    average_score = round(sum(item["average_score"] for item in history) / total_attempts, 1)
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Total Attempts", total_attempts)
    metric_col2.metric("Average Score", f"{average_score}/10")
    metric_col3.metric("Latest Recommendation", history[0]["recommendation"])

    for item in history:
        created_at = item["created_at"]
        with st.expander(f"{created_at} | {item['topic']} | {item['average_score']}/10"):
            st.write(f"Recommendation: {item['recommendation']}")
            st.download_button(
                label=f"Download Report #{item['id']}",
                data=item["report_text"],
                file_name=f"interview_report_{item['id']}.txt",
                mime="text/plain",
                key=f"download_history_{item['id']}",
            )

            rounds = json.loads(item["rounds_json"])
            for index, round_item in enumerate(rounds, start=1):
                st.markdown("<div class='mini-card'>", unsafe_allow_html=True)
                st.write(f"Question {index}: {round_item['question']}")
                st.write(f"Score: {round_item['overall_score']}/10")
                st.write(f"Verdict: {round_item['verdict']}")
                st.write(f"Summary: {round_item['summary']}")
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_profile_tab():
    current_user = st.session_state.current_user
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Profile</div>", unsafe_allow_html=True)
    st.write(f"Full Name: {current_user['full_name']}")
    st.write(f"Email: {current_user['email']}")
    st.write(f"Role: {current_user['role'].title()}")
    st.caption("Your interview history and downloadable reports are stored locally in SQLite.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_admin_tab():
    summary = get_admin_summary()
    recent_interviews = list_recent_interviews(limit=12)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Admin Analytics</div>", unsafe_allow_html=True)
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    stat_col1.metric("Users", summary["total_users"])
    stat_col2.metric("Students", summary["total_students"])
    stat_col3.metric("Interviews", summary["total_interviews"])
    stat_col4.metric("Average Score", f"{summary['average_score']}/10")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Topic Breakdown</div>", unsafe_allow_html=True)
    if summary["topic_breakdown"]:
        for item in summary["topic_breakdown"]:
            st.write(
                f"{item['topic']}: {item['interview_count']} interviews | Avg Score {item['avg_score']}/10"
            )
    else:
        st.info("No interviews recorded yet.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Weakest Topics</div>", unsafe_allow_html=True)
    if summary["weak_topics"]:
        for item in summary["weak_topics"]:
            st.write(f"{item['topic']}: average score {item['avg_score']}/10")
    else:
        st.info("Weak topic analytics will appear after interview data is available.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recent Interviews</div>", unsafe_allow_html=True)
    if recent_interviews:
        for interview in recent_interviews:
            st.markdown("<div class='mini-card'>", unsafe_allow_html=True)
            st.write(f"Candidate: {interview['full_name']} ({interview['email']})")
            st.write(f"Topic: {interview['topic']}")
            st.write(f"Score: {interview['average_score']}/10")
            st.write(f"Recommendation: {interview['recommendation']}")
            st.write(f"Created At: {interview['created_at']}")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No interview records yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_app():
    user = st.session_state.current_user
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), use_container_width=True)
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Current Mode: {'Admin' if st.session_state.admin_mode else 'Student'}")
    st.sidebar.write(f"Signed in as: {user['full_name']}")
    st.sidebar.write(f"Role: {user['role'].title()}")
    st.sidebar.caption("Your login is remembered on this device, so you do not need to sign in repeatedly.")
    if st.sidebar.button("Logout", use_container_width=True):
        logout_session_token(st.session_state.session_token)
        clear_saved_session_token()
        st.session_state.current_user = None
        st.session_state.session_token = ""
        st.session_state.admin_mode = False
        reset_interview_state()
        st.rerun()

    if user["role"] == "admin":
        tab_practice, tab_interview, tab_history, tab_profile, tab_admin = st.tabs(
            ["Practice", "Interview", "History", "Profile", "Admin Dashboard"]
        )
    else:
        tab_practice, tab_interview, tab_history, tab_profile = st.tabs(
            ["Practice", "Interview", "History", "Profile"]
        )
        tab_admin = None

    with tab_practice:
        render_practice_tab()
    with tab_interview:
        render_student_interview_tab()
    with tab_history:
        render_history_tab()
    with tab_profile:
        render_profile_tab()
    if tab_admin is not None:
        with tab_admin:
            render_admin_tab()


init_db()
ensure_admin_user()
init_session_state()

if not st.session_state.auth_checked:
    remembered_token = read_saved_session_token()
    remembered_user = authenticate_session_token(remembered_token)
    if remembered_user:
        st.session_state.current_user = remembered_user
        st.session_state.session_token = remembered_token
        st.session_state.admin_mode = remembered_user["role"] == "admin"
    st.session_state.auth_checked = True

st.markdown(
    """
    <div class="card">
        <div class="smith-badge">Smith Interview Suite</div>
        <h1 class="hero-title">Smith</h1>
        <p class="hero-subtitle">
            Recruiter-style mock interviews with smart feedback, analytics, and report export.
        </p>
        <div class="hero-pill-row">
            <span class="hero-pill">Technical Interview Practice</span>
            <span class="hero-pill">Instant AI Feedback</span>
            <span class="hero-pill">Performance Analytics</span>
            <span class="hero-pill">Exportable Reports</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.current_user is None:
    render_auth_screen()
else:
    render_app()
