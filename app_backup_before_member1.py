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

# ------------------------------------------------------------
# STUDY PROGRESS
# ------------------------------------------------------------

if "quizzes_taken" not in st.session_state:
    st.session_state.quizzes_taken = 0

if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0

if "correct_answers" not in st.session_state:
    st.session_state.correct_answers = 0

if "flashcards_generated" not in st.session_state:
    st.session_state.flashcards_generated = 0


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


        # ----------------------------------------------------
        # NUMBER OF QUESTIONS
        # ----------------------------------------------------

        num_questions = st.slider(
            "📝 Number of questions",
            min_value=1,
            max_value=10,
            value=3
        )


        # ----------------------------------------------------
        # DIFFICULTY LEVEL
        # ----------------------------------------------------

        difficulty = st.selectbox(
            "🎯 Select Difficulty",
            [
                "Easy",
                "Medium",
                "Hard"
            ]
        )


        # ----------------------------------------------------
        # QUIZ TYPE
        # ----------------------------------------------------

        quiz_type = st.selectbox(
            "📝 Select Quiz Type",
            [
                "MCQ"
            ]
        )


        # ----------------------------------------------------
        # SHOW CURRENT SELECTION
        # ----------------------------------------------------

        st.info(
            f"Selected: **{difficulty}** difficulty | "
            f"**{quiz_type}** format | "
            f"**{num_questions}** questions"
        )


        # ----------------------------------------------------
        # GENERATE QUIZ BUTTON
        # ----------------------------------------------------

        generate_button = st.button(
            "🚀 Generate Quiz",
            use_container_width=True
        )


        # ====================================================
        # GENERATE QUIZ
        # ====================================================

        if generate_button:

            st.info(
                f"🤖 AI is generating a "
                f"{difficulty} {quiz_type} quiz..."
            )

            try:

                # ------------------------------------------------
                # Generate quiz
                # ------------------------------------------------

                quiz = generate_quiz(
                    extracted_text,
                    num_questions,
                    difficulty
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


                if len(quiz) == 0:

                    raise ValueError(
                        "AI returned an empty quiz."
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
                    f"🎉 {difficulty} quiz generated successfully!"
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


        # ----------------------------------------------------
        # NUMBER OF FLASHCARDS
        # ----------------------------------------------------

        num_flashcards = st.slider(
            "🧠 Number of flashcards",
            min_value=1,
            max_value=10,
            value=5
        )


        # ----------------------------------------------------
        # FLASHCARD BUTTON
        # ----------------------------------------------------

        flashcard_button = st.button(
            "🧠 Generate Flashcards",
            use_container_width=True
        )


        # ====================================================
        # GENERATE FLASHCARDS
        # ====================================================

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


                if len(flashcards) == 0:

                    raise ValueError(
                        "AI returned empty flashcards."
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


                # ------------------------------------------------
                # Update flashcard statistics
                # ------------------------------------------------

                st.session_state.flashcards_generated += len(
                    flashcards
                )


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


        # ----------------------------------------------------
        # Display question
        # ----------------------------------------------------

        st.write(
            question_data["question"]
        )


        # ----------------------------------------------------
        # Display difficulty
        # ----------------------------------------------------

        if "difficulty" in question_data:

            st.caption(
                f"🎯 Difficulty: "
                f"{question_data['difficulty']}"
            )


        # ----------------------------------------------------
        # Display options
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # Save current result
        # ----------------------------------------------------

        st.session_state.score = score

        st.session_state.submitted = True


        # ----------------------------------------------------
        # Update study statistics
        # ----------------------------------------------------

        st.session_state.quizzes_taken += 1

        st.session_state.total_questions += len(quiz)

        st.session_state.correct_answers += score


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


    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🏆 Score",
            f"{score} / {total}"
        )


    with col2:

        st.metric(
            "📊 Accuracy",
            f"{percentage:.1f}%"
        )


    with col3:

        st.metric(
            "🎯 Difficulty",
            quiz[0].get("difficulty", "Medium")
        )


    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    st.progress(
        percentage / 100
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
            f"**Question:** "
            f"{card['question']}"
        )


        with st.expander(
            "👀 Show Answer"
        ):

            st.write(
                card["answer"]
            )


        st.divider()


# ============================================================
# ADVANCED STUDY PROGRESS DASHBOARD
# ============================================================

st.divider()

st.header("📊 Your Learning Dashboard")

st.write(
    "Track your learning performance and get personalized "
    "insights based on your quiz and flashcard activity."
)


# ============================================================
# GET PROGRESS DATA
# ============================================================

quizzes_taken = st.session_state.quizzes_taken

total_questions = st.session_state.total_questions

correct_answers = st.session_state.correct_answers

flashcards_generated = st.session_state.flashcards_generated


# ============================================================
# CALCULATE ACCURACY
# ============================================================

if total_questions > 0:

    accuracy = (
        correct_answers / total_questions
    ) * 100

else:

    accuracy = 0


# ============================================================
# LEARNING LEVEL
# ============================================================

if accuracy >= 90:

    learning_level = "🏆 Master Learner"

elif accuracy >= 80:

    learning_level = "🌟 Advanced Learner"

elif accuracy >= 60:

    learning_level = "📚 Active Learner"

elif accuracy > 0:

    learning_level = "🌱 Beginner Learner"

else:

    learning_level = "🚀 Start Learning"


# ============================================================
# LEARNING OVERVIEW
# ============================================================

st.subheader("🎯 Learning Overview")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "🏆 Learning Level",
        learning_level
    )


with col2:

    st.metric(
        "📈 Accuracy",
        f"{accuracy:.1f}%"
    )


with col3:

    st.metric(
        "🎯 Questions Mastered",
        f"{correct_answers}/{total_questions}"
    )


# ============================================================
# KNOWLEDGE MASTERY
# ============================================================

st.subheader("🧠 Overall Knowledge Mastery")


st.progress(
    min(accuracy / 100, 1.0)
)


if accuracy >= 80:

    st.success(
        f"🌟 Excellent! You have mastered "
        f"{accuracy:.1f}% of the questions you've attempted."
    )

elif accuracy >= 60:

    st.info(
        f"📚 Good progress! Your current mastery "
        f"is {accuracy:.1f}%. Keep practicing to reach 80%+."
    )

elif accuracy > 0:

    st.warning(
        f"🌱 You are building your knowledge. "
        f"Your current mastery is {accuracy:.1f}%."
    )

else:

    st.info(
        "🚀 Generate your first quiz to begin "
        "tracking your learning journey."
    )


# ============================================================
# LEARNING ACTIVITY
# ============================================================

st.subheader("📚 Learning Activity")


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "📝 Quizzes Taken",
        quizzes_taken
    )


with col2:

    st.metric(
        "❓ Questions",
        total_questions
    )


with col3:

    st.metric(
        "✅ Correct",
        correct_answers
    )


with col4:

    st.metric(
        "🧠 Flashcards",
        flashcards_generated
    )


# ============================================================
# PERFORMANCE BREAKDOWN
# ============================================================

st.subheader("📊 Performance Breakdown")


if total_questions > 0:

    wrong_answers = (
        total_questions - correct_answers
    )

    col1, col2 = st.columns(2)


    with col1:

        st.write("### ✅ Correct Answers")

        st.progress(
            correct_answers / total_questions
        )

        st.write(
            f"{correct_answers} correct out of "
            f"{total_questions} questions"
        )


    with col2:

        st.write("### ❌ Questions to Review")

        st.progress(
            wrong_answers / total_questions
        )

        st.write(
            f"{wrong_answers} questions need more practice"
        )

else:

    st.info(
        "Complete a quiz to see your performance breakdown."
    )


# ============================================================
# SMART AI STUDY RECOMMENDATION
# ============================================================

st.subheader("💡 Smart Study Recommendation")


if quizzes_taken == 0:

    recommendation = (
        "🚀 Start your learning journey by uploading a "
        "document and generating your first quiz."
    )

elif accuracy >= 90:

    recommendation = (
        "🏆 Outstanding performance! Try Hard difficulty "
        "questions to challenge yourself further."
    )

elif accuracy >= 80:

    recommendation = (
        "🌟 Great work! You have a strong understanding. "
        "Try Hard difficulty and create flashcards for revision."
    )

elif accuracy >= 60:

    recommendation = (
        "📚 You're making good progress. Review your "
        "incorrect answers and practice with Medium difficulty."
    )

else:

    recommendation = (
        "🌱 Focus on understanding the basics first. "
        "Use Easy quizzes and review your flashcards regularly."
    )


st.info(recommendation)


# ============================================================
# ACHIEVEMENTS
# ============================================================

st.subheader("🏅 Achievements")


achievements = []


if quizzes_taken >= 1:

    achievements.append(
        "🎯 First Quiz Completed"
    )


if quizzes_taken >= 5:

    achievements.append(
        "🔥 Quiz Explorer"
    )


if quizzes_taken >= 10:

    achievements.append(
        "🏆 Quiz Master"
    )


if flashcards_generated >= 5:

    achievements.append(
        "🧠 Flashcard Starter"
    )


if flashcards_generated >= 20:

    achievements.append(
        "📚 Revision Champion"
    )


if accuracy >= 80:

    achievements.append(
        "🌟 80% Accuracy"
    )


if accuracy >= 90:

    achievements.append(
        "💎 90% Accuracy"
    )


if not achievements:

    st.write(
        "🔒 Complete quizzes and create flashcards "
        "to unlock achievements!"
    )

else:

    for achievement in achievements:

        st.success(
            achievement
        )


# ============================================================
# LEARNING JOURNEY
# ============================================================

st.subheader("🚀 Your Learning Journey")


journey_progress = min(
    quizzes_taken / 10,
    1.0
)


st.progress(
    journey_progress
)


if quizzes_taken < 10:

    remaining = 10 - quizzes_taken

    st.write(
        f"🔥 **{quizzes_taken}/10 quizzes completed** "
        f"— only **{remaining} more** to reach your next milestone!"
    )

else:

    st.success(
        "🏆 10 quizzes completed! "
        "You've reached the learning milestone."
    )


# ============================================================
# STUDY STATUS
# ============================================================

st.subheader("📖 Study Status")


if accuracy >= 80:

    st.success(
        "🟢 You are performing strongly. "
        "Keep challenging yourself."
    )

elif accuracy >= 60:

    st.warning(
        "🟡 You are progressing well. "
        "More revision can improve your score."
    )

elif accuracy > 0:

    st.error(
        "🔴 More practice is recommended. "
        "Review flashcards and retry quizzes."
    )

else:

    st.info(
        "⚪ No quiz activity yet."
    )


# ============================================================
# FINAL MOTIVATION
# ============================================================

if quizzes_taken > 0:

    st.divider()

    st.markdown(
        "## 🌟 Keep Going!"
    )

    st.write(
        "Every quiz you complete and every flashcard you "
        "review helps strengthen your learning."
    )

    st.progress(
        min(accuracy / 100, 1.0)
    )

    st.caption(
        "🧠 Learn • Practice • Review • Improve • Master"
    )