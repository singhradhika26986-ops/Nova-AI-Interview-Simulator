import streamlit as st


def _get_average(scores):
    return round(sum(scores) / len(scores), 1) if scores else 0.0


def _get_hiring_signal(avg_score):
    if avg_score >= 8:
        return "High potential"
    if avg_score >= 6:
        return "Promising with practice"
    return "Needs more interview preparation"


def show_dashboard(results):
    if not results:
        st.info("Complete at least one round to view performance analytics.")
        return

    try:
        import matplotlib.pyplot as plt
    except Exception:
        st.warning("Matplotlib is not installed, so charts are unavailable.")
        return

    scores = [result["overall_score"] for result in results]
    avg_score = _get_average(scores)
    best_score = max(scores)
    weakest_score = min(scores)

    st.markdown(
        "<div style='font-size:1.15rem;font-weight:700;color:#0f172a;margin-bottom:12px;'>Performance Dashboard</div>",
        unsafe_allow_html=True,
    )
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Average Score", f"{avg_score}/10")
    metric_col2.metric("Best Round", f"{best_score}/10")
    metric_col3.metric("Weakest Round", f"{weakest_score}/10")
    metric_col4.metric("Recruiter Signal", _get_hiring_signal(avg_score))

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(range(1, len(scores) + 1), scores, marker="o", linewidth=2, color="#0f766e")
    ax.set_title("Interview Progress")
    ax.set_xlabel("Question Number")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 10)
    ax.grid(alpha=0.3)
    st.pyplot(fig, clear_figure=True)

    latest = results[-1]
    rubric = latest["rubric"]

    rubric_fig, rubric_ax = plt.subplots(figsize=(7, 3.5))
    rubric_ax.bar(
        ["Technical", "Communication", "Completeness"],
        [
            rubric["technical_accuracy"],
            rubric["communication"],
            rubric["completeness"],
        ],
        color=["#1d4ed8", "#9333ea", "#f59e0b"],
    )
    rubric_ax.set_ylim(0, 10)
    rubric_ax.set_title("Latest Answer Rubric")
    st.pyplot(rubric_fig, clear_figure=True)
