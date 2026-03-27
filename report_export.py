from io import BytesIO


def build_recommendation(average_score):
    if average_score >= 8:
        return "Strong candidate"
    if average_score >= 6.5:
        return "Promising with some improvement needed"
    if average_score >= 5:
        return "Needs more practice before interviews"
    return "Not interview ready yet"


def generate_report_text(user_name, topic, results):
    if not results:
        return "", 0.0, "No recommendation"

    average_score = round(sum(item["overall_score"] for item in results) / len(results), 1)
    recommendation = build_recommendation(average_score)

    lines = [
        "SARA Interview Assessment Report",
        "=" * 36,
        f"Candidate: {user_name}",
        f"Interview Domain: {topic}",
        f"Overall Score: {average_score}/10",
        f"Recruiter Recommendation: {recommendation}",
        "",
    ]

    for index, result in enumerate(results, start=1):
        lines.extend(
            [
                f"Round {index}: {result['question']}",
                f"Round Score: {result['overall_score']}/10",
                f"Verdict: {result['verdict']}",
                "Key Strengths:",
                *[f"- {item}" for item in result["strengths"]],
                "Areas For Improvement:",
                *[f"- {item}" for item in result["improvements"]],
                f"Recruiter Note: {result['summary']}",
                "",
            ]
        )

    return "\n".join(lines), average_score, recommendation


def generate_report_pdf(user_name, topic, results):
    if not results:
        return None

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    report_text, average_score, recommendation = generate_report_text(user_name, topic, results)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x_margin = 0.7 * inch
    y = height - 0.8 * inch

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(x_margin, y, "SARA Interview Report")
    y -= 0.35 * inch

    pdf.setFont("Helvetica", 11)
    header_lines = [
        f"Candidate: {user_name}",
        f"Topic: {topic}",
        f"Average Score: {average_score}/10",
        f"Recommendation: {recommendation}",
        "",
    ]
    for line in header_lines:
        pdf.drawString(x_margin, y, line)
        y -= 0.22 * inch

    for line in report_text.splitlines()[6:]:
        if y < 0.8 * inch:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = height - 0.8 * inch
        pdf.drawString(x_margin, y, line[:110])
        y -= 0.2 * inch

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
