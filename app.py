import streamlit as st
from database import create_tables, save_quiz, save_flashcards

import os
import sys
import json


# ============================================================
# PATH SETUP
# ============================================================

create_tables()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_QUIZ_DIR = os.path.join(
    BASE_DIR,
    "modules",
    "pdf_quiz"
)

FLASHCARD_DIR = os.path.join(
    BASE_DIR,
    "modules",
    "flashcards"
)

sys.path.insert(0, PDF_QUIZ_DIR)
sys.path.insert(0, FLASHCARD_DIR)


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from pdf_extractor import extract_text_from_pdf
from quiz_generator import generate_quiz
from flashcard_generator import generate_flashcards


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Lumyn-AI",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "quiz" not in st.session_state:
    st.session_state.quiz = None

if "flashcards" not in st.session_state:
    st.session_state.flashcards = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "score" not in st.session_state:
    st.session_state.score = 0


# ============================================================
# HEADER
# ============================================================

st.title("🧠 Lumyn-AI")

st.subheader(
    "📄 AI-Powered PDF Quiz & Flashcard Generator"
)

st.write(
    "Upload a PDF and automatically generate "
    "interactive quizzes and flashcards using AI."
)

st.divider()


# ============================================================
# PDF UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📤 Upload your PDF",
    type=["pdf"]
)


# ============================================================
# WHEN PDF IS UPLOADED
# ============================================================

if uploaded_file is not None:

    st.success(
        f"✅ Uploaded: {uploaded_file.name}"
    )

    # --------------------------------------------------------
    # Save uploaded PDF
    # --------------------------------------------------------

    temp_pdf_path = os.path.join(
        BASE_DIR,
        "uploaded_temp.pdf"
    )

    with open(temp_pdf_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    # --------------------------------------------------------
    # Extract PDF text
    # --------------------------------------------------------

    st.info(
        "📖 Extracting text from PDF..."
    )

    try:

        extracted_text = extract_text_from_pdf(
            temp_pdf_path
        )

        st.success(
            "✅ PDF text extracted successfully!"
        )

    except Exception as error:

        st.error(
            f"❌ PDF extraction failed: {error}"
        )

        extracted_text = ""


    # ========================================================
    # SHOW EXTRACTED TEXT
    # ========================================================

    if extracted_text:

        with st.expander(
            "📄 View Extracted PDF Text"
        ):

            st.text_area(
                "Extracted Text",
                extracted_text,
                height=300
            )

        st.divider()


        # ====================================================
        # QUIZ SECTION
        # ====================================================

        st.header("📝 Quiz Generator")

        num_questions = st.slider(
            "📝 Number of questions",
            min_value=1,
            max_value=10,
            value=3
        )

        generate_button = st.button(
            "🚀 Generate Quiz",
            use_container_width=True
        )


        if generate_button:

            st.info(
                "🤖 AI is generating your quiz..."
            )

            try:

                quiz = generate_quiz(
                    extracted_text,
                    num_questions
                )

                # ------------------------------------------------
                # Convert JSON string if necessary
                # ------------------------------------------------

                if isinstance(quiz, str):

                    quiz = quiz.strip()

                    quiz = quiz.replace(
                        "```json",
                        ""
                    )

                    quiz = quiz.replace(
                        "```",
                        ""
                    )

                    quiz = quiz.strip()

                    quiz = json.loads(quiz)


                # ------------------------------------------------
                # Validate quiz
                # ------------------------------------------------

                if not isinstance(quiz, list):

                    raise ValueError(
                        "Quiz format is invalid. "
                        "Expected a list of questions."
                    )


                # ------------------------------------------------
                # Save quiz to database
                # ------------------------------------------------

                save_quiz(quiz)


                # ------------------------------------------------
                # Store quiz in session
                # ------------------------------------------------

                st.session_state.quiz = quiz

                st.session_state.submitted = False

                st.session_state.score = 0

                st.success(
                    "🎉 Quiz generated successfully!"
                )


            except Exception as error:

                st.error(
                    f"❌ Quiz generation failed:\n\n{error}"
                )


        # ====================================================
        # FLASHCARD SECTION
        # ====================================================

        st.divider()

        st.header("🧠 Flashcard Generator")

        num_flashcards = st.slider(
            "🧠 Number of flashcards",
            min_value=1,
            max_value=10,
            value=5
        )

        flashcard_button = st.button(
            "🧠 Generate Flashcards",
            use_container_width=True
        )


        if flashcard_button:

            st.info(
                "🤖 AI is generating your flashcards..."
            )

            try:

                flashcards = generate_flashcards(
                    extracted_text,
                    num_flashcards
                )


                # ------------------------------------------------
                # Convert JSON string if necessary
                # ------------------------------------------------

                if isinstance(flashcards, str):

                    flashcards = flashcards.strip()

                    flashcards = flashcards.replace(
                        "```json",
                        ""
                    )

                    flashcards = flashcards.replace(
                        "```",
                        ""
                    )

                    flashcards = flashcards.strip()

                    flashcards = json.loads(
                        flashcards
                    )


                # ------------------------------------------------
                # Validate flashcards
                # ------------------------------------------------

                if not isinstance(
                    flashcards,
                    list
                ):

                    raise ValueError(
                        "Flashcard format is invalid. "
                        "Expected a list of flashcards."
                    )


                # ------------------------------------------------
                # Save flashcards to SQLite
                # ------------------------------------------------

                save_flashcards(
                    flashcards
                )


                # ------------------------------------------------
                # Store flashcards in session
                # ------------------------------------------------

                st.session_state.flashcards = flashcards

                st.success(
                    "🎉 Flashcards generated successfully!"
                )


            except Exception as error:

                st.error(
                    f"❌ Flashcard generation failed:\n\n{error}"
                )


# ============================================================
# DISPLAY QUIZ
# ============================================================

if st.session_state.quiz is not None:

    st.divider()

    st.header("📝 Your Quiz")

    quiz = st.session_state.quiz

    answers = {}


    # ========================================================
    # QUESTIONS
    # ========================================================

    for i, question_data in enumerate(quiz):

        st.markdown(
            f"### Question {i + 1}"
        )

        st.write(
            question_data["question"]
        )

        options = question_data["options"]

        option_keys = list(
            options.keys()
        )


        selected = st.radio(
            "Select your answer:",
            option_keys,
            format_func=lambda key:
                f"{key}. {options[key]}",
            key=f"answer_{i}"
        )

        answers[i] = selected

        st.divider()


    # ========================================================
    # SUBMIT BUTTON
    # ========================================================

    if st.button(
        "✅ Submit Quiz",
        use_container_width=True
    ):

        score = 0

        for i, question_data in enumerate(quiz):

            correct_answer = question_data["answer"]

            if answers[i] == correct_answer:

                score += 1


        st.session_state.score = score

        st.session_state.submitted = True


# ============================================================
# QUIZ RESULT
# ============================================================

if (
    st.session_state.quiz is not None
    and st.session_state.submitted
):

    quiz = st.session_state.quiz

    score = st.session_state.score

    total = len(quiz)

    percentage = (
        score / total
    ) * 100


    st.divider()

    st.header("🎯 Quiz Result")


    st.metric(
        "Score",
        f"{score} / {total}"
    )


    st.progress(
        percentage / 100
    )


    st.write(
        f"### 📊 Percentage: {percentage:.1f}%"
    )


    # ========================================================
    # PERFORMANCE
    # ========================================================

    if percentage >= 80:

        st.success(
            "🏆 Excellent! Great job!"
        )

    elif percentage >= 50:

        st.warning(
            "👍 Good attempt! Keep practicing."
        )

    else:

        st.error(
            "📚 Keep learning and try again."
        )


    # ========================================================
    # ANSWER REVIEW
    # ========================================================

    st.subheader(
        "📖 Answer Review"
    )


    for i, question_data in enumerate(quiz):

        correct = question_data["answer"]

        st.write(
            f"**Question {i + 1}:** "
            f"Correct Answer → **{correct}**"
        )


# ============================================================
# DISPLAY FLASHCARDS
# ============================================================

if st.session_state.flashcards is not None:

    st.divider()

    st.header("🧠 Your Flashcards")

    flashcards = st.session_state.flashcards


    for i, card in enumerate(
        flashcards,
        start=1
    ):

        st.markdown(
            f"### 🗂️ Flashcard {i}"
        )

        st.write(
            f"**Question:** {card['question']}"
        )

        with st.expander(
            "👀 Show Answer"
        ):

            st.write(
                card["answer"]
            )

        st.divider()