import os
import re


FILLER_WORDS = {"um", "uh", "like", "basically", "actually", "you know"}


def _tokenize(text):
    return re.findall(r"[a-zA-Z0-9+#.]+", text.lower())


def _extract_score(value):
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(value))
    if not match:
        return None
    return float(match.group(1))


def _grade_length(answer):
    word_count = len(_tokenize(answer))
    if word_count >= 70:
        return 10
    if word_count >= 45:
        return 8
    if word_count >= 25:
        return 6
    if word_count >= 10:
        return 4
    return 2


def _grade_keyword_coverage(answer, keywords):
    if not keywords:
        return 6, []

    answer_lower = answer.lower()
    matched = [keyword for keyword in keywords if keyword.lower() in answer_lower]
    coverage_ratio = len(matched) / len(keywords)

    if coverage_ratio >= 0.8:
        score = 10
    elif coverage_ratio >= 0.6:
        score = 8
    elif coverage_ratio >= 0.4:
        score = 6
    elif coverage_ratio > 0:
        score = 4
    else:
        score = 2

    return score, matched


def _grade_communication(answer):
    sentences = [sentence.strip() for sentence in re.split(r"[.!?]", answer) if sentence.strip()]
    filler_count = sum(1 for token in _tokenize(answer) if token in FILLER_WORDS)
    if len(sentences) >= 3 and filler_count <= 2:
        return 9
    if len(sentences) >= 2 and filler_count <= 4:
        return 7
    if len(sentences) >= 1:
        return 5
    return 2


def _build_local_feedback(answer, expected_answer, keywords):
    if not answer.strip():
        return {
            "overall_score": 0.0,
            "verdict": "Needs attention",
            "strengths": ["No answer was submitted."],
            "improvements": ["Write a complete answer before submitting."],
            "summary": "The answer was empty, so the interview round could not be evaluated.",
            "rubric": {
                "technical_accuracy": 0,
                "communication": 0,
                "completeness": 0,
            },
        }

    accuracy_score, matched_keywords = _grade_keyword_coverage(answer, keywords)
    communication_score = _grade_communication(answer)
    completeness_score = _grade_length(answer)
    overall_score = round((accuracy_score * 0.5) + (communication_score * 0.25) + (completeness_score * 0.25), 1)

    if overall_score >= 8:
        verdict = "Strong answer"
    elif overall_score >= 6:
        verdict = "Good foundation"
    elif overall_score >= 4:
        verdict = "Average answer"
    else:
        verdict = "Needs attention"

    strengths = []
    improvements = []

    if matched_keywords:
        strengths.append("You covered key technical points such as " + ", ".join(matched_keywords[:3]) + ".")
    else:
        improvements.append("Mention the main technical keywords related to the concept.")

    if len(_tokenize(answer)) >= 35:
        strengths.append("Your answer has reasonable depth and is not too short.")
    else:
        improvements.append("Increase the depth of your explanation with one example or use case.")

    if communication_score >= 7:
        strengths.append("Your explanation is fairly clear and easy to follow.")
    else:
        improvements.append("Structure the answer in two or three clean sentences for better clarity.")

    if expected_answer and expected_answer.lower() not in answer.lower():
        improvements.append("Try to align more closely with the expected definition or standard explanation.")

    if not strengths:
        strengths.append("You attempted the question and provided some relevant content.")

    if not improvements:
        improvements.append("Add one practical example to make the answer more interview ready.")

    return {
        "overall_score": overall_score,
        "verdict": verdict,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "summary": "This score is based on keyword coverage, communication clarity, and answer completeness.",
        "rubric": {
            "technical_accuracy": accuracy_score,
            "communication": communication_score,
            "completeness": completeness_score,
        },
    }


def _build_openai_feedback(answer, question, expected_answer, topic, keywords):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    prompt = f"""
You are a technical interviewer. Evaluate the candidate answer.

Topic: {topic}
Question: {question}
Expected answer: {expected_answer}
Important keywords: {", ".join(keywords)}
Candidate answer: {answer}

Respond in plain text with this format:
Overall Score: <number out of 10>
Verdict: <short verdict>
Strengths:
- ...
- ...
Improvements:
- ...
- ...
Summary: <1 short paragraph>
Technical Accuracy: <score out of 10>
Communication: <score out of 10>
Completeness: <score out of 10>
"""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt.strip()}],
        )
        text = response.choices[0].message.content or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        strengths = []
        improvements = []
        summary = "AI evaluation completed."
        verdict = "Reviewed"
        overall_score = 6.0
        technical_accuracy = 6.0
        communication = 6.0
        completeness = 6.0
        target = None

        for line in lines:
            lower = line.lower()
            if lower.startswith("overall score:"):
                extracted = _extract_score(line)
                if extracted is not None:
                    overall_score = extracted
            elif lower.startswith("verdict:"):
                verdict = line.split(":", 1)[1].strip()
            elif lower.startswith("strengths:"):
                target = "strengths"
            elif lower.startswith("improvements:"):
                target = "improvements"
            elif lower.startswith("summary:"):
                summary = line.split(":", 1)[1].strip()
                target = None
            elif lower.startswith("technical accuracy:"):
                extracted = _extract_score(line)
                if extracted is not None:
                    technical_accuracy = extracted
            elif lower.startswith("communication:"):
                extracted = _extract_score(line)
                if extracted is not None:
                    communication = extracted
            elif lower.startswith("completeness:"):
                extracted = _extract_score(line)
                if extracted is not None:
                    completeness = extracted
            elif line.startswith("-"):
                if target == "strengths":
                    strengths.append(line.lstrip("- ").strip())
                elif target == "improvements":
                    improvements.append(line.lstrip("- ").strip())

        if not strengths:
            strengths = ["The answer addressed at least part of the question."]
        if not improvements:
            improvements = ["Add more precise technical details and one practical example."]

        return {
            "overall_score": round(float(overall_score), 1),
            "verdict": verdict,
            "strengths": strengths[:3],
            "improvements": improvements[:3],
            "summary": summary,
            "rubric": {
                "technical_accuracy": round(float(technical_accuracy), 1),
                "communication": round(float(communication), 1),
                "completeness": round(float(completeness), 1),
            },
        }
    except Exception:
        return None


def evaluate_answer(answer, question="", expected_answer="", topic="", keywords=None):
    keywords = keywords or []
    ai_feedback = _build_openai_feedback(answer, question, expected_answer, topic, keywords)
    if ai_feedback:
        return ai_feedback
    return _build_local_feedback(answer, expected_answer, keywords)
