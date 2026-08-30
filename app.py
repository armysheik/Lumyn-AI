import streamlit as st
import os
import json

from database import create_tables, save_quiz, save_flashcards

from modules.pdf_quiz.pdf_extractor import extract_text_from_pdf
from modules.pdf_quiz.quiz_generator import generate_quiz

from modules.flashcards.flashcard_generator import generate_flashcards

from modules.document_processing.txt_extractor import extract_text_from_txt
from modules.document_processing.docx_extractor import extract_text_from_docx


# ============================================================
# INITIALIZE DATABASE
# ============================================================

create_tables()


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# STREAMLIT PAGE CONFIGURATION
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
    "📚 AI-Powered Document Quiz & Flashcard Generator"
)

st.write(
    "Upload a PDF, TXT, or DOCX document and automatically "
    "generate interactive quizzes and flashcards using AI."
)

st.divider()


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📤 Upload your document",
    type=["pdf", "txt", "docx"]
)


# ============================================================
# WHEN DOCUMENT IS UPLOADED
# ============================================================

if uploaded_file is not None:

    st.success(
        f"✅ Uploaded: {uploaded_file.name}"
    )

    # --------------------------------------------------------
    # Detect file type
    # --------------------------------------------------------

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        file_type = "PDF"

    elif file_name.endswith(".txt"):
        file_type = "TXT"

    elif file_name.endswith(".docx"):
        file_type = "DOCX"

    else:
        file_type = "UNKNOWN"

    st.info(
        f"📄 File type detected: **{file_type}**"
    )


    # ========================================================
    # SAVE UPLOADED FILE TEMPORARILY
    # ========================================================

    file_extension = os.path.splitext(
        uploaded_file.name
    )[1].lower()

    temp_file_path = os.path.join(
        BASE_DIR,
        f"uploaded_temp{file_extension}"
    )

    with open(temp_file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())


    # ========================================================
    # EXTRACT TEXT
    # ========================================================

    st.info(
        f"📖 Extracting text from {file_type}..."
    )

    extracted_text = ""

    try:

        # ----------------------------------------------------
        # PDF
        # ----------------------------------------------------

        if file_type == "PDF":

            extracted_text = extract_text_from_pdf(
                temp_file_path
            )

            success_message = (
                "✅ PDF text extracted successfully!"
            )


        # ----------------------------------------------------
        # TXT
        # ----------------------------------------------------

        elif file_type == "TXT":

            extracted_text = extract_text_from_txt(
                temp_file_path
            )

            success_message = (
                "✅ TXT text extracted successfully!"
            )


        # ----------------------------------------------------
        # DOCX
        # ----------------------------------------------------

        elif file_type == "DOCX":

            extracted_text = extract_text_from_docx(
                temp_file_path
            )

            success_message = (
                "✅ DOCX text extracted successfully!"
            )


        else:

            raise ValueError(
                "Unsupported document format."
            )


        # ----------------------------------------------------
        # Check extracted text
        # ----------------------------------------------------

        if not extracted_text or not extracted_text.strip():

            raise ValueError(
                "No readable text was found in the document."
            )

        st.success(success_message)


    except Exception as error:

        st.error(
            f"❌ {file_type} extraction failed:\n\n{error}"
        )

        extracted_text = ""


    # ========================================================
    # SHOW EXTRACTED TEXT
    # ========================================================

    if extracted_text:

        with st.expander(
            f"📄 View Extracted {file_type} Text"
        ):

            st.text_area(
                "Extracted Text",
                extracted_text,
                height=300
            )

        st.success(
            "✅ Extracted text is ready to be passed to the AI."
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