import streamlit as st
import random
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.data_loader import load_historical_stats, load_teams
from utils.banner import render_tournament_banner
from utils.footer import render_footer

render_tournament_banner()
st.markdown('<h2 style="text-align:center; margin:0.3rem 0;">🧠 World Cup Quiz</h2>', unsafe_allow_html=True)


stats = load_historical_stats()
teams = load_teams()


# --- "Did You Know?" rotating fact ---
st.markdown("---")
fact = stats.sample(1).iloc[0]
st.markdown(
    f'<div style="background:#0E1117; border-radius:12px; padding:1.2rem 1.5rem; margin:0.5rem 0;">'
    f'<p style="font-size:1.1rem; color:#ffffff; margin:0; text-align:center;">'
    f'💡 <b>{fact["CATEGORY"]}</b><br>{fact["STAT_VALUE"]}</p></div>',
    unsafe_allow_html=True,
)
st.markdown("---")


# --- Quiz question generator ---
def generate_questions(teams_df, stats_df, n=5):
    """Generate n multiple-choice questions from the data."""
    questions = []
    team_list = teams_df["TEAM_NAME"].tolist()

    generators = [
        _q_captain,
        _q_group,
        _q_confederation,
        _q_top_scorer,
        _q_ranking_range,
    ]

    random.shuffle(generators)
    for gen in generators[:n]:
        q = gen(teams_df, team_list)
        if q:
            questions.append(q)

    # Fill remaining with historical stat questions if needed
    while len(questions) < n and not stats_df.empty:
        q = _q_historical(stats_df)
        if q and q not in questions:
            questions.append(q)

    return questions[:n]


def _q_captain(teams_df, team_list):
    row = teams_df.sample(1).iloc[0]
    correct = row["CAPTAIN"]
    # Get other captains as distractors
    others = teams_df[teams_df["CAPTAIN"] != correct]["CAPTAIN"].drop_duplicates().tolist()
    if len(others) < 3:
        return None
    distractors = random.sample(others, 3)
    options = distractors + [correct]
    random.shuffle(options)
    return {
        "question": f"Who is the captain of {row['TEAM_NAME']}?",
        "options": options,
        "answer": correct,
    }


def _q_group(teams_df, team_list):
    row = teams_df.sample(1).iloc[0]
    correct = f"Group {row['GROUP_LETTER']}"
    all_groups = [f"Group {g}" for g in sorted(teams_df["GROUP_LETTER"].unique())]
    distractors = [g for g in all_groups if g != correct]
    if len(distractors) < 3:
        return None
    distractors = random.sample(distractors, 3)
    options = distractors + [correct]
    random.shuffle(options)
    return {
        "question": f"Which group is {row['TEAM_NAME']} in?",
        "options": options,
        "answer": correct,
    }


def _q_confederation(teams_df, team_list):
    row = teams_df.sample(1).iloc[0]
    correct = row["CONFEDERATION"]
    all_conf = teams_df["CONFEDERATION"].unique().tolist()
    distractors = [c for c in all_conf if c != correct]
    if len(distractors) < 3:
        distractors = distractors + ["OFC"]
    distractors = random.sample(distractors, min(3, len(distractors)))
    while len(distractors) < 3:
        distractors.append("OFC")
    options = distractors[:3] + [correct]
    random.shuffle(options)
    return {
        "question": f"Which confederation does {row['TEAM_NAME']} belong to?",
        "options": options,
        "answer": correct,
    }


def _q_top_scorer(teams_df, team_list):
    row = teams_df.sample(1).iloc[0]
    correct = row["TOP_SCORER"]
    others = teams_df[teams_df["TOP_SCORER"] != correct]["TOP_SCORER"].drop_duplicates().tolist()
    if len(others) < 3:
        return None
    distractors = random.sample(others, 3)
    options = distractors + [correct]
    random.shuffle(options)
    return {
        "question": f"Who is {row['TEAM_NAME']}'s top scorer heading into the 2026 World Cup?",
        "options": options,
        "answer": correct,
    }


def _q_ranking_range(teams_df, team_list):
    row = teams_df.sample(1).iloc[0]
    ranking = int(row["FIFA_RANKING"])
    correct = f"#{ranking}"
    # Generate plausible distractors
    offsets = [-15, -8, +7, +12]
    random.shuffle(offsets)
    distractors = []
    for off in offsets:
        val = ranking + off
        if val < 1:
            val = ranking + abs(off)
        d = f"#{val}"
        if d != correct and d not in distractors:
            distractors.append(d)
        if len(distractors) == 3:
            break
    if len(distractors) < 3:
        return None
    options = distractors + [correct]
    random.shuffle(options)
    return {
        "question": f"What is {row['TEAM_NAME']}'s FIFA ranking?",
        "options": options,
        "answer": correct,
    }


def _q_historical(stats_df):
    row = stats_df.sample(1).iloc[0]
    if not row["TEAM_NAME"]:
        return None
    correct = row["TEAM_NAME"]
    others = stats_df[stats_df["TEAM_NAME"] != correct]["TEAM_NAME"].dropna().unique().tolist()
    others = [t for t in others if t]
    if len(others) < 3:
        return None
    distractors = random.sample(others, 3)
    options = distractors + [correct]
    random.shuffle(options)
    return {
        "question": f"Which country holds the record for: {row['CATEGORY']}?",
        "options": options,
        "answer": correct,
    }


# --- Quiz UI ---
# Initialize session state
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = generate_questions(teams, stats, n=3)
    st.session_state.quiz_submitted = False
    st.session_state.quiz_score = 0

questions = st.session_state.quiz_questions

if not questions:
    st.warning("Could not generate quiz questions. Please try again.")
else:

    # Display questions horizontally
    answers = {}
    cols = st.columns(len(questions))
    for i, q in enumerate(questions):
        with cols[i]:
            st.markdown(
                f'<div style="height:100px; background:#115675; border-radius:8px; padding:0.8rem; margin-bottom:0.5rem;">'
                f'<span style="font-size:1.15rem; font-weight:700; color:#ffffff;">Q{i+1}.</span>&nbsp;'
                f'<span style="font-size:1.05rem; color:#ffffff;">{q["question"]}</span></div>',
                unsafe_allow_html=True,
            )
            answers[i] = st.radio(
                f"Select answer for Q{i+1}",
                q["options"],
                index=None,
                key=f"quiz_q_{i}",
                label_visibility="collapsed",
            )

    # Buttons side by side
    st.markdown("")
    st.markdown("")
    st.markdown("")
    btn_col1, btn_col2, _ = st.columns([1.5, 1.2, 5.3])
    with btn_col1:
        submitted = st.button(
            "✅ Submit Answers",
            disabled=st.session_state.quiz_submitted,
        )
        if submitted and not st.session_state.quiz_submitted:
            score = 0
            for i, q in enumerate(questions):
                if answers[i] == q["answer"]:
                    score += 1
            st.session_state.quiz_score = score
            st.session_state.quiz_submitted = True
            st.rerun()
    with btn_col2:
        if st.button("🔄 New Quiz"):
            st.session_state.quiz_questions = generate_questions(teams, stats, n=3)
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score = 0
            st.rerun()

    # Show results
    if st.session_state.quiz_submitted:
        score = st.session_state.quiz_score
        total = len(questions)

        if score == total:
            st.balloons()
            msg = "Perfect score! You're a true World Cup expert! 🏆"
        elif score >= total * 0.6:
            msg = "Great job! You know your football! ⚽"
        else:
            msg = "Nice try! Come back and test yourself again! 💪"

        st.markdown(
            f'<div style="background:#115675; border-radius:12px; padding:1.5rem; margin:1rem 0; text-align:center;">'
            f'<p style="font-size:2rem; font-weight:800; color:#ffffff; margin:0;">{score} / {total}</p>'
            f'<p style="font-size:1.1rem; color:#ffffff; margin:0.5rem 0 0 0;">{msg}</p></div>',
            unsafe_allow_html=True,
        )

        # Show correct answers in the same horizontal layout
        st.markdown("")
        result_cols = st.columns(len(questions))
        for i, q in enumerate(questions):
            with result_cols[i]:
                user_answer = answers.get(i, "")
                correct_answer = q["answer"]
                is_correct = user_answer == correct_answer
                icon = "✅" if is_correct else "❌"
                if is_correct:
                    st.success(f"{icon} {correct_answer}")
                else:
                    st.error(f"{icon} ~~{user_answer}~~")
                    st.markdown(f"**Answer:** {correct_answer}")

render_footer()
