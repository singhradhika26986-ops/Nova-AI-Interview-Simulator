import json
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
from face_detection import detect_face
from qa_dataset import get_total_practice_question_count
from question_generator import build_interview_set, get_daily_practice_set, get_practice_questions, get_topics
from report_export import generate_report_pdf, generate_report_text


MAX_QUESTIONS = 5
ANSWER_TIME_LIMIT = 20
TOTAL_PRACTICE_QUESTIONS = get_total_practice_question_count()
SESSION_FILE = Path(__file__).with_name("remembered_session.json")

st.set_page_config(page_title="AI Interview Simulator", page_icon="AI", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(14, 116, 144, 0.12), transparent 26%),
            radial-gradient(circle at top right, rgba(15, 118, 110, 0.10), transparent 22%),
            linear-gradient(135deg, #f8fafc 0%, #e5edf5 44%, #f2fbf7 100%);
    }
    .card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(15, 23, 42, 0.05);
        border-radius: 26px;
        padding: 28px;
        box-shadow: 0 24px 68px rgba(15, 23, 42, 0.07);
        margin-bottom: 22px;
        backdrop-filter: blur(10px);
    }
    .mini-card {
        background: #ffffff;
        border-left: 6px solid #0f766e;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
    }
    .hero-title {
        font-size: 3.7rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #0f172a;
        margin: 0 0 10px 0;
    }
    .hero-subtitle {
        font-size: 1.08rem;
        color: #475569;
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
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.1), rgba(14, 116, 144, 0.11));
        color: #0f172a;
        padding: 9px 14px;
        border-radius: 999px;
        font-size: 0.92rem;
        font-weight: 600;
        border: 1px solid rgba(15, 23, 42, 0.06);
    }
    .section-title {
        font-size: 1.18rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        letter-spacing: -0.02em;
    }
    .nova-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(14, 116, 144, 0.12));
        border: 1px solid rgba(15, 23, 42, 0.06);
        color: #0f172a;
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
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.95));
        border: 1px solid rgba(15, 23, 42, 0.06);
        border-radius: 18px;
        padding: 16px;
    }
    .status-label {
        color: #64748b;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .status-value {
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 700;
    }
    .question-shell {
        padding: 22px;
        border-radius: 20px;
        background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.9));
        border: 1px solid rgba(15, 23, 42, 0.06);
        margin-bottom: 16px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
    }
    .question-text {
        color: #0f172a;
        font-size: 1.38rem;
        font-weight: 700;
        line-height: 1.55;
    }
    .note-box {
        padding: 14px 16px;
        border-radius: 16px;
        background: rgba(14, 116, 144, 0.08);
        border: 1px solid rgba(14, 116, 144, 0.12);
        color: #0f172a;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    div[data-testid="stButton"] > button {
        border-radius: 14px;
        border: none;
        min-height: 48px;
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #0f766e, #0f766e 35%, #0ea5a4 100%);
        color: white;
    }
    div[data-testid="stDownloadButton"] > button {
        border-radius: 14px;
        min-height: 46px;
        font-weight: 700;
    }
    div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
        border-radius: 14px;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stCaption {
        color: #94a3b8 !important;
    }
    .final-shell {
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.10), rgba(14, 116, 144, 0.08));
        border: 1px solid rgba(15, 23, 42, 0.06);
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
        background: linear-gradient(180deg, rgba(15, 118, 110, 0.10), rgba(14, 116, 144, 0.08));
        border: 1px solid rgba(15, 23, 42, 0.06);
        border-radius: 24px;
        padding: 24px;
        min-height: 100%;
    }
    .auth-title {
        color: #0f172a;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0 0 10px 0;
    }
    .auth-copy {
        color: #475569;
        font-size: 1rem;
        line-height: 1.75;
        margin: 0 0 18px 0;
    }
    .auth-list {
        margin: 0;
        padding-left: 18px;
        color: #0f172a;
        line-height: 1.9;
        font-weight: 600;
    }
    </style>
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
        "camera_enabled": False,
        "face_verified": None,
        "started": False,
        "topic": "Python",
        "question_index": 0,
        "interview_plan": [],
        "results": [],
        "spoken_prompts": set(),
        "last_audio_text": "",
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
        f"Hello {candidate_name}. I am Nova, your AI recruiter for today. "
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
                background: rgba(15, 118, 110, 0.08); border: 1px solid rgba(15, 118, 110, 0.12);
                color: #0f172a; font-weight: 700;">
        Answer Timer: <span id="nova-timer">{remaining_seconds}</span> seconds left
    </div>
    <script>
    const deadline = {int(deadline * 1000)};
    const timerElement = window.parent.document.getElementById("nova-timer");
    if (timerElement) {{
      const tick = () => {{
        const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
        timerElement.textContent = remaining;
      }};
      tick();
      setInterval(tick, 1000);
    }}
    </script>
    """
    st.markdown(timer_html, unsafe_allow_html=True)


def finalize_current_answer(current_user, current_round, answer, time_expired):
    current_index = st.session_state.question_index
    evaluation = evaluate_answer(
        answer=answer,
        question=current_round["question"],
        expected_answer=current_round["answer"],
        topic=st.session_state.topic,
        keywords=current_round.get("keywords", []),
    )

    if time_expired:
        evaluation["summary"] = (
            "The answer window expired after 20 seconds. The system evaluated the available response."
        )

    if evaluation["overall_score"] < 6 and not st.session_state.clarification_requested:
        st.session_state.pending_evaluation = evaluation
        st.session_state.clarification_requested = True
        st.session_state.question_started_at = time.time()
        st.session_state.live_feedback = (
            "I would like a clearer explanation. Please answer once more with a short definition, one relevant example, and a well-structured response."
        )
        safe_audio(st.session_state.live_feedback, prompt_key=f"clarify_intro_{current_index}")
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
    st.session_state.live_feedback = (
        "Thank you for your response. "
        + (
            "Your explanation was clear and well-structured. No major changes are needed."
            if evaluation["overall_score"] >= 7
            else "You should explain the concept more clearly, with a little more depth and structure."
        )
    )
    safe_audio(st.session_state.live_feedback, prompt_key=f"feedback_{current_index}")

    if current_index + 1 < len(st.session_state.interview_plan):
        st.session_state.question_index += 1
        st.session_state.question_started_at = time.time()
        st.session_state.conversation_stage = "question"
        safe_audio(
            "Your answer has been reviewed. We will now move to the next question.",
            prompt_key=f"next_{current_index}",
        )
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


def safe_audio(text, prompt_key=None):
    if not st.session_state.voice_enabled:
        return
    if prompt_key and prompt_key in st.session_state.spoken_prompts:
        return

    try:
        escaped_text = (
            text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", " ")
        )
        components.html(
            f"""
            <script>
            (() => {{
                const text = '{escaped_text}';
                const key = '{prompt_key or "default"}';
                window.__novaSpokenKeys = window.__novaSpokenKeys || {{}};
                if (window.__novaSpokenKeys[key]) return;
                const speakNow = () => {{
                    try {{
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.rate = 1.15;
                        utterance.pitch = 1.0;
                        utterance.volume = 1.0;
                        const voices = window.speechSynthesis.getVoices();
                        const preferredVoice = voices.find(v =>
                            /en-in|en-us|english/i.test(v.lang + ' ' + v.name)
                        );
                        if (preferredVoice) utterance.voice = preferredVoice;
                        window.speechSynthesis.speak(utterance);
                        window.__novaSpokenKeys[key] = true;
                    }} catch (e) {{}}
                }};
                speakNow();
                if (window.speechSynthesis.onvoiceschanged !== undefined) {{
                    window.speechSynthesis.onvoiceschanged = speakNow;
                }}
            }})();
            </script>
            """,
            height=0,
        )
        st.session_state.last_audio_text = text
        if prompt_key:
            st.session_state.spoken_prompts.add(prompt_key)
    except Exception:
        st.warning("Voice narration is unavailable right now. The app will continue without audio.")
        st.session_state.voice_enabled = False


def show_camera_tools():
    st.markdown("<div class='section-title'>Camera Readiness</div>", unsafe_allow_html=True)
    st.caption("Allow browser camera permission and capture one frame for face verification.")
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
                <div class="nova-badge">Nova Secure Access</div>
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
                "<div class='note-box'>Nova is guiding the session. Speak clearly after the microphone prompt appears.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.started and st.session_state.interview_plan:
            if st.session_state.conversation_stage == "intro":
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown("<div class='nova-badge'>Nova AI Recruiter</div>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Interview Introduction</div>", unsafe_allow_html=True)
                intro_text = st.session_state.live_feedback or build_intro_script(current_user["full_name"], topic)
                st.info(intro_text)
                safe_audio(intro_text, prompt_key="intro")
                st.caption("Nova is introducing the interview. The first question will start automatically.")
                st.markdown("</div>", unsafe_allow_html=True)
                time.sleep(6)
                st.session_state.conversation_stage = "question"
                st.session_state.question_started_at = time.time()
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
            if st.session_state.question_started_at is None:
                st.session_state.question_started_at = time.time()
            deadline = st.session_state.question_started_at + ANSWER_TIME_LIMIT

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='nova-badge'>Nova AI Recruiter</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-title'>Question {current_index + 1} of {len(st.session_state.interview_plan)}</div>",
                unsafe_allow_html=True,
            )
            if st.session_state.live_feedback:
                st.info(st.session_state.live_feedback)
            st.markdown("<div class='question-shell'>", unsafe_allow_html=True)
            st.markdown(f"<div class='question-text'>{prompt_text}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.caption(
                f"Difficulty: {current_round.get('difficulty', 'Not specified')} | Time limit: {ANSWER_TIME_LIMIT} seconds"
            )
            render_countdown(deadline)
            safe_audio(
                prompt_text,
                prompt_key=f"{'clarify' if is_clarification else 'question'}_{current_index}",
            )

            audio_answer = st.audio_input(
                "Speak your answer",
                key=f"audio_answer_{current_index}_{'clarify' if is_clarification else 'main'}",
            )
            transcript, transcript_error = transcribe_audio(audio_answer)
            if audio_answer is not None and not transcript and not transcript_error:
                st.info("Audio received. Nova is processing your answer.")
            if transcript_error:
                st.warning(transcript_error)
            if transcript:
                st.success("Voice answer captured successfully.")
                st.write(f"Transcript: {transcript}")
            else:
                st.caption(
                    "Click the microphone, record your answer, and stop recording. Nova will review it automatically after transcription."
                )

            answer = transcript.strip()
            time_expired = time.time() > deadline
            answer_key = f"{current_index}|{'clarify' if is_clarification else 'main'}|{answer}"

            if answer and answer_key != st.session_state.last_processed_answer_key:
                st.session_state.last_processed_answer_key = answer_key
                finalize_current_answer(current_user, current_round, answer, time_expired)

            if time_expired and not answer:
                st.warning("Time is up. Please record a short answer clearly into the microphone.")
                if st.button("Submit Timed-Out Response", use_container_width=True):
                    st.session_state.last_processed_answer_key = (
                        f"{current_index}|{'clarify' if is_clarification else 'main'}|timeout"
                    )
                    finalize_current_answer(current_user, current_round, "", True)

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
                st.caption("Nova has completed the interview assessment and prepared your final result summary.")
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
        show_camera_tools()
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
        <div class="nova-badge">Nova AI Recruiter Suite</div>
        <h1 class="hero-title">AI Interview Simulator</h1>
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
