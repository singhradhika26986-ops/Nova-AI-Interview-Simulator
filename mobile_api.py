from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from answer_evaluator import evaluate_answer
from auth import (
    authenticate_session_token,
    authenticate_user,
    create_persistent_session,
    register_user,
)
from database import get_user_by_id, init_db, list_user_interviews
from question_generator import build_interview_set, get_practice_questions, get_topics


app = FastAPI(title="Smith AI Interview Mobile API", version="1.0.0")
init_db()


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class StartInterviewRequest(BaseModel):
    topic: str
    total_questions: int = 5


class EvaluateRequest(BaseModel):
    answer: str
    question: str
    expected_answer: str = ""
    topic: str
    session_token: Optional[str] = None
    keywords: list[str] = []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register")
def register(payload: RegisterRequest):
    success, message = register_user(payload.full_name, payload.email, payload.password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_token = create_persistent_session(user["id"])
    return {
        "session_token": session_token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


@app.get("/auth/me")
def me(session_token: str):
    user = authenticate_session_token(session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
    }


@app.get("/topics")
def topics():
    return {"topics": get_topics()}


@app.get("/practice/{topic}")
def practice(topic: str):
    return {"topic": topic, "questions": get_practice_questions(topic)}


@app.post("/interview/start")
def start_interview(payload: StartInterviewRequest):
    questions = build_interview_set(payload.topic, payload.total_questions)
    return {"topic": payload.topic, "questions": questions}


@app.post("/interview/evaluate")
def evaluate(payload: EvaluateRequest):
    result = evaluate_answer(
        answer=payload.answer,
        question=payload.question,
        expected_answer=payload.expected_answer,
        topic=payload.topic,
        keywords=payload.keywords,
    )
    return result


@app.get("/history/{user_id}")
def history(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"history": list_user_interviews(user_id)}
