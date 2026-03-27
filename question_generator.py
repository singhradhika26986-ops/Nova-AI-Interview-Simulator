import random
from datetime import date

from qa_dataset import practice_data, qa_data


def get_topics():
    return list(qa_data.keys())


def get_questions(topic):
    return qa_data.get(topic, [])


def build_interview_set(topic, total_questions=5):
    question_bank = get_questions(topic)
    if not question_bank:
        return []

    sample_size = min(total_questions, len(question_bank))
    return random.sample(question_bank, sample_size)


def generate_question(topic, asked_questions=None):
    asked_questions = set(asked_questions or [])
    available_questions = [
        item["question"] for item in get_questions(topic) if item["question"] not in asked_questions
    ]
    if not available_questions:
        return None
    return random.choice(available_questions)


def get_expected_answer(topic, question):
    for item in get_questions(topic):
        if item["question"] == question:
            return item.get("answer", "")
    return ""


def get_practice_questions(topic):
    return practice_data.get(topic, [])


def get_daily_practice_set(topic, limit=5):
    questions = get_practice_questions(topic)
    if not questions:
        return []
    seed_value = f"{topic}-{date.today().isoformat()}"
    rng = random.Random(seed_value)
    sample_size = min(limit, len(questions))
    return rng.sample(questions, sample_size)
