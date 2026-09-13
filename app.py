import streamlit as st
import os
import json

from database import (
    create_tables,
    save_quiz,
    save_flashcards,
    save_quiz_result,
    save_flashcard_activity,
    get_subjects,
    get_study_history,
    get_overall_progress,
    get_subject_progress,
    get_total_flashcards,
)

from modules.pdf_quiz.pdf_extractor import extract_text_from_pdf
from modules.pdf_quiz.quiz_generator import generate_quiz
from modules.flashcards.flashcard_generator import generate_flashcards
from modules.document_processing.txt_extractor import extract_text_from_txt
from modules.document_processing.docx_extractor import extract_text_from_docx

try:
    from modules.educational_content.youtube_api import search_educational_videos
    YOUTUBE_AVAILABLE = True
except Exception:
    YOUTUBE_AVAILABLE = False


# ============================================================
# INITIALIZE
# ============================================================

create_tables()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="Lumyn-AI",
    page_icon="🧠",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "quiz": None,
    "flashcards": None,
    "submitted": False,
    "score": 0,
    "quiz_subject": "General",
    "quiz_type": "MCQ",
    "quiz_difficulty": "Medium",
    "flashcard_subject": "General",
    "document_name": None,
    "extracted_text": "",
    "youtube_results": [],
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


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
# MEMBER 1 - YOUTUBE EDUCATIONAL CONTENT
# ============================================================

st.header("📺 Educational Content")

st.write(
    "Search YouTube for educational videos related to "
    "the topic you are studying."
)

if not YOUTUBE_AVAILABLE:

    st.warning(
        "YouTube educational content module is not available. "
        "Check that "
        "modules/educational_content/youtube_api.py exists."
    )

else:

    youtube_topic = st.text_input(
        "🔎 Search educational videos",
        placeholder=(
            "Example: Python programming, "
            "Machine Learning, Flutter"
        ),
        key="youtube_topic",
    )

    youtube_count = st.slider(
        "Number of videos",
        min_value=1,
        max_value=10,
        value=6,
        key="youtube_count",
    )

    if st.button(
        "🔍 Search Educational Videos",
        use_container_width=True,
    ):

        if not youtube_topic.strip():

            st.warning(
                "Please enter a topic first."
            )

        else:

            try:

                with st.spinner(
                    "Searching YouTube educational videos..."
                ):

                    results = search_educational_videos(
                        youtube_topic.strip(),
                        youtube_count,
                    )

                st.session_state.youtube_results = results

                if results:

                    st.success(
                        f"Found {len(results)} educational "
                        f"video(s) for "
                        f"'{youtube_topic.strip()}'."
                    )

                else:

                    st.info(
                        "No educational videos were found "
                        "for this topic."
                    )

            except Exception as error:

                st.error(
                    f"❌ YouTube search failed:\n\n{error}"
                )

    # --------------------------------------------------------
    # DISPLAY YOUTUBE RESULTS
    # --------------------------------------------------------

    if st.session_state.youtube_results:

        st.subheader(
            "🎓 Recommended Educational Videos"
        )

        for video in st.session_state.youtube_results:

            with st.container(border=True):

                col1, col2 = st.columns([1, 2])

                # ------------------------------------------------
                # THUMBNAIL
                # ------------------------------------------------

                with col1:

                    if video.get("thumbnail_url"):

                        st.image(
                            video["thumbnail_url"],
                            use_container_width=True,
                        )

                # ------------------------------------------------
                # VIDEO DETAILS
                # ------------------------------------------------

                with col2:

                    st.markdown(
                        f"### {video.get('title', 'Untitled')}"
                    )

                    st.write(
                        f"**Channel:** "
                        f"{video.get('channel_title', 'Unknown')}"
                    )

                    description = video.get(
                        "description",
                        "",
                    )

                    if description:

                        st.write(
                            description[:400]
                        )

                    video_url = video.get(
                        "url",
                        "",
                    )

                    if video_url:

                        st.markdown(
                            f"[▶ Watch on YouTube]"
                            f"({video_url})"
                        )


st.divider()


# ============================================================
# GET SUBJECTS FROM DATABASE
# ============================================================

try:

    subjects = get_subjects()

except Exception:

    subjects = ["General"]


if not subjects:

    subjects = ["General"]


if "General" not in subjects:

    subjects.insert(0, "General")


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

st.header("📤 Upload Your Study Material")

uploaded_file = st.file_uploader(
    "Upload your document",
    type=[
        "pdf",
        "txt",
        "docx",
    ],
    help="Supported formats: PDF, TXT and DOCX",
)


# ============================================================
# PROCESS UPLOADED DOCUMENT
# ============================================================

if uploaded_file is not None:

    st.success(
        f"✅ Uploaded: {uploaded_file.name}"
    )

    file_name = uploaded_file.name.lower()

    # --------------------------------------------------------
    # DETECT FILE TYPE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # TEMPORARY FILE
    # --------------------------------------------------------

    file_extension = os.path.splitext(
        uploaded_file.name
    )[1].lower()

    temp_file_path = os.path.join(
        BASE_DIR,
        f"uploaded_temp{file_extension}",
    )

    try:

        with open(
            temp_file_path,
            "wb",
        ) as file:

            file.write(
                uploaded_file.getbuffer()
            )

        extracted_text = ""

        # ----------------------------------------------------
        # EXTRACT TEXT
        # ----------------------------------------------------

        with st.spinner(
            f"📖 Extracting text from {file_type}..."
        ):

            if file_type == "PDF":

                extracted_text = extract_text_from_pdf(
                    temp_file_path
                )

            elif file_type == "TXT":

                extracted_text = extract_text_from_txt(
                    temp_file_path
                )

            elif file_type == "DOCX":

                extracted_text = extract_text_from_docx(
                    temp_file_path
                )

            else:

                raise ValueError(
                    "Unsupported document format."
                )

        # ----------------------------------------------------
        # CHECK TEXT
        # ----------------------------------------------------

        if (
            not extracted_text
            or not extracted_text.strip()
        ):

            raise ValueError(
                "No readable text was found in "
                "the document."
            )

        st.session_state.extracted_text = (
            extracted_text
        )

        st.session_state.document_name = (
            uploaded_file.name
        )

        st.success(
            f"✅ {file_type} text extracted successfully!"
        )

        # ----------------------------------------------------
        # VIEW TEXT
        # ----------------------------------------------------

        with st.expander(
            "📄 View Extracted Text"
        ):

            st.text_area(
                "Extracted Text",
                extracted_text,
                height=300,
                key="extracted_text_view",
            )

    except Exception as error:

        st.session_state.extracted_text = ""

        st.error(
            f"❌ {file_type} extraction failed:\n\n"
            f"{error}"
        )


# ============================================================
# GET EXTRACTED TEXT
# ============================================================

extracted_text = st.session_state.extracted_text


# ============================================================
# GENERATORS
# ============================================================

if extracted_text:

    st.divider()

    # ========================================================
    # STUDY ORGANIZATION
    # ========================================================

    st.header("📚 Study Organization")

    subject_option = st.selectbox(
        "📖 Select Subject",
        subjects,
        key="subject_select",
    )

    custom_subject = st.text_input(
        "Or enter a new subject",
        placeholder=(
            "Example: Python, Java, DBMS, "
            "Machine Learning"
        ),
    )

    if custom_subject.strip():

        selected_subject = (
            custom_subject.strip()
        )

    else:

        selected_subject = subject_option

    st.info(
        f"Current study subject: "
        f"**{selected_subject}**"
    )

    st.divider()


    # ========================================================
    # QUIZ GENERATOR
    # ========================================================

    st.header("📝 Quiz Generator")

    col1, col2, col3 = st.columns(3)

    # --------------------------------------------------------
    # NUMBER OF QUESTIONS
    # --------------------------------------------------------

    with col1:

        num_questions = st.slider(
            "📝 Number of questions",
            min_value=1,
            max_value=10,
            value=3,
        )

    # --------------------------------------------------------
    # DIFFICULTY
    # --------------------------------------------------------

    with col2:

        difficulty = st.selectbox(
            "🎯 Select Difficulty",
            [
                "Easy",
                "Medium",
                "Hard",
            ],
            index=1,
        )

    # --------------------------------------------------------
    # QUIZ TYPE
    # --------------------------------------------------------

    with col3:

        quiz_type = st.selectbox(
            "📝 Select Quiz Type",
            [
                "MCQ",
                "True-False",
                "Fill-in-the-Blanks",
            ],
        )

    st.info(
        f"Selected: **{difficulty}** difficulty | "
        f"**{quiz_type}** format | "
        f"**{num_questions}** questions | "
        f"**{selected_subject}** subject"
    )


    # ========================================================
    # GENERATE QUIZ BUTTON
    # ========================================================

    if st.button(
        "🚀 Generate Quiz",
        use_container_width=True,
        key="generate_quiz_button",
    ):

        try:

            with st.spinner(
                f"🤖 Generating "
                f"{difficulty} {quiz_type} quiz..."
            ):

                quiz = generate_quiz(
                    extracted_text,
                    num_questions,
                    difficulty,
                    quiz_type,
                )

            # ------------------------------------------------
            # CONVERT JSON STRING
            # ------------------------------------------------

            if isinstance(
                quiz,
                str,
            ):

                quiz = quiz.strip()

                quiz = quiz.replace(
                    "```json",
                    "",
                )

                quiz = quiz.replace(
                    "```",
                    "",
                )

                quiz = json.loads(
                    quiz.strip()
                )

            # ------------------------------------------------
            # VALIDATE
            # ------------------------------------------------

            if (
                not isinstance(
                    quiz,
                    list,
                )
                or len(quiz) == 0
            ):

                raise ValueError(
                    "AI returned an invalid "
                    "or empty quiz."
                )

            # ------------------------------------------------
            # SAVE QUIZ
            # ------------------------------------------------

            save_quiz(
                quiz,
                subject=selected_subject,
                quiz_type=quiz_type,
                difficulty=difficulty,
            )

            # ------------------------------------------------
            # SESSION
            # ------------------------------------------------

            st.session_state.quiz = quiz

            st.session_state.submitted = False

            st.session_state.score = 0

            st.session_state.quiz_subject = (
                selected_subject
            )

            st.session_state.quiz_type = (
                quiz_type
            )

            st.session_state.quiz_difficulty = (
                difficulty
            )

            st.success(
                f"🎉 {difficulty} {quiz_type} "
                f"quiz generated successfully!"
            )

        except Exception as error:

            st.error(
                f"❌ Quiz generation failed:\n\n"
                f"{error}"
            )


    # ========================================================
    # FLASHCARD GENERATOR
    # ========================================================

    st.divider()

    st.header("🧠 Flashcard Generator")

    flashcard_subject = st.text_input(
        "📚 Flashcard Subject",
        value=selected_subject,
        key="flashcard_subject_input",
    )

    if flashcard_subject.strip():

        flashcard_subject = (
            flashcard_subject.strip()
        )

    else:

        flashcard_subject = "General"


    num_flashcards = st.slider(
        "🧠 Number of flashcards",
        min_value=1,
        max_value=20,
        value=5,
    )


    # ========================================================
    # GENERATE FLASHCARDS
    # ========================================================

    if st.button(
        "🧠 Generate Flashcards",
        use_container_width=True,
        key="generate_flashcards_button",
    ):

        try:

            with st.spinner(
                "🤖 AI is generating "
                "your flashcards..."
            ):

                flashcards = generate_flashcards(
                    extracted_text,
                    num_flashcards,
                )

            # ------------------------------------------------
            # CONVERT JSON STRING
            # ------------------------------------------------

            if isinstance(
                flashcards,
                str,
            ):

                flashcards = flashcards.strip()

                flashcards = flashcards.replace(
                    "```json",
                    "",
                )

                flashcards = flashcards.replace(
                    "```",
                    "",
                )

                flashcards = json.loads(
                    flashcards.strip()
                )

            # ------------------------------------------------
            # VALIDATE
            # ------------------------------------------------

            if (
                not isinstance(
                    flashcards,
                    list,
                )
                or len(flashcards) == 0
            ):

                raise ValueError(
                    "AI returned invalid "
                    "or empty flashcards."
                )

            # ------------------------------------------------
            # SAVE FLASHCARDS
            # ------------------------------------------------

            save_flashcards(
                flashcards,
                subject=flashcard_subject,
            )

            # ------------------------------------------------
            # SAVE ACTIVITY
            # ------------------------------------------------

            try:

                save_flashcard_activity(
                    flashcard_subject,
                    len(flashcards),
                )

            except Exception:

                pass

            # ------------------------------------------------
            # SESSION
            # ------------------------------------------------

            st.session_state.flashcards = (
                flashcards
            )

            st.session_state.flashcard_subject = (
                flashcard_subject
            )

            st.success(
                f"🎉 {len(flashcards)} flashcards "
                f"generated successfully!"
            )

        except Exception as error:

            st.error(
                f"❌ Flashcard generation failed:\n\n"
                f"{error}"
            )


# ============================================================
# DISPLAY QUIZ
# ============================================================

if st.session_state.quiz is not None:

    st.divider()

    st.header("📝 Your Quiz")

    quiz = st.session_state.quiz

    answers = {}

    # --------------------------------------------------------
    # QUESTIONS
    # --------------------------------------------------------

    for i, question_data in enumerate(
        quiz
    ):

        st.markdown(
            f"### Question {i + 1}"
        )

        st.write(
            question_data.get(
                "question",
                "",
            )
        )

        # ----------------------------------------------------
        # DIFFICULTY
        # ----------------------------------------------------

        if "difficulty" in question_data:

            st.caption(
                f"🎯 Difficulty: "
                f"{question_data['difficulty']}"
            )

        # ----------------------------------------------------
        # MCQ / TRUE-FALSE
        # ----------------------------------------------------

        if "options" in question_data:

            options = question_data[
                "options"
            ]

            if isinstance(
                options,
                dict,
            ):

                option_keys = list(
                    options.keys()
                )

                selected = st.radio(
                    "Select your answer:",
                    option_keys,
                    format_func=lambda key: (
                        f"{key}. "
                        f"{options[key]}"
                    ),
                    key=f"answer_{i}",
                )

                answers[i] = selected

        # ----------------------------------------------------
        # FILL IN THE BLANK
        # ----------------------------------------------------

        else:

            answers[i] = st.text_input(
                "✏️ Your answer:",
                key=f"answer_{i}",
            )

        st.divider()


    # ========================================================
    # SUBMIT QUIZ
    # ========================================================

    if st.button(
        "✅ Submit Quiz",
        use_container_width=True,
        key="submit_quiz_button",
    ):

        score = 0

        for i, question_data in enumerate(
            quiz
        ):

            correct_answer = str(
                question_data.get(
                    "answer",
                    "",
                )
            ).strip()

            user_answer = str(
                answers.get(
                    i,
                    "",
                )
            ).strip()

            # ------------------------------------------------
            # DIRECT ANSWER CHECK
            # ------------------------------------------------

            if (
                user_answer.lower()
                == correct_answer.lower()
            ):

                score += 1

            # ------------------------------------------------
            # ACCEPTED ANSWERS
            # ------------------------------------------------

            elif (
                "accepted_answers"
                in question_data
            ):

                accepted_answers = (
                    question_data.get(
                        "accepted_answers",
                        [],
                    )
                )

                accepted_answers = [
                    str(answer)
                    .strip()
                    .lower()
                    for answer
                    in accepted_answers
                ]

                if (
                    user_answer.lower()
                    in accepted_answers
                ):

                    score += 1

        # ----------------------------------------------------
        # SAVE SESSION RESULT
        # ----------------------------------------------------

        st.session_state.score = score

        st.session_state.submitted = True

        # ----------------------------------------------------
        # SAVE RESULT TO SQLITE
        # ----------------------------------------------------

        try:

            save_quiz_result(
                subject=(
                    st.session_state.quiz_subject
                ),
                quiz_type=(
                    st.session_state.quiz_type
                ),
                difficulty=(
                    st.session_state.quiz_difficulty
                ),
                score=score,
                total_questions=len(quiz),
            )

        except Exception as error:

            st.warning(
                "Quiz completed, but result "
                "could not be saved: "
                f"{error}"
            )

        st.rerun()


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

    if total > 0:

        percentage = (
            score / total
        ) * 100

    else:

        percentage = 0


    st.divider()

    st.header("🎯 Quiz Result")


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🏆 Score",
            f"{score} / {total}",
        )


    with col2:

        st.metric(
            "📊 Accuracy",
            f"{percentage:.1f}%",
        )


    with col3:

        st.metric(
            "📚 Subject",
            st.session_state.quiz_subject,
        )


    st.progress(
        min(
            percentage / 100,
            1.0,
        )
    )


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


    for i, question_data in enumerate(
        quiz
    ):

        correct = question_data.get(
            "answer",
            "",
        )

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

    flashcards = (
        st.session_state.flashcards
    )

    st.caption(
        f"Subject: "
        f"{st.session_state.flashcard_subject}"
    )


    for i, card in enumerate(
        flashcards,
        start=1,
    ):

        with st.container(
            border=True
        ):

            st.markdown(
                f"### 🗂️ Flashcard {i}"
            )

            st.write(
                f"**Question:** "
                f"{card.get('question', '')}"
            )

            with st.expander(
                "👀 Show Answer"
            ):

                st.write(
                    card.get(
                        "answer",
                        "",
                    )
                )


# ============================================================
# MEMBER 1 - PERSISTENT STUDY DASHBOARD
# ============================================================

st.divider()

st.header(
    "📊 Your Learning Dashboard"
)

st.write(
    "Your study activity is stored in SQLite "
    "so your quiz scores, subjects, and progress "
    "can be viewed again."
)


# ============================================================
# OVERALL PROGRESS
# ============================================================

try:

    overall = get_overall_progress()

except Exception:

    overall = {
        "quizzes_taken": 0,
        "total_questions": 0,
        "correct_answers": 0,
        "accuracy": 0,
    }


# ============================================================
# TOTAL FLASHCARDS
# ============================================================

try:

    total_flashcards = (
        get_total_flashcards()
    )

except Exception:

    total_flashcards = 0


quizzes_taken = overall.get(
    "quizzes_taken",
    0,
)

total_questions = overall.get(
    "total_questions",
    0,
)

correct_answers = overall.get(
    "correct_answers",
    0,
)

accuracy = overall.get(
    "accuracy",
    0,
)


# ============================================================
# LEARNING METRICS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "📝 Quizzes Taken",
        quizzes_taken,
    )


with col2:

    st.metric(
        "❓ Questions",
        total_questions,
    )


with col3:

    st.metric(
        "✅ Correct",
        correct_answers,
    )


with col4:

    st.metric(
        "🧠 Flashcards",
        total_flashcards,
    )


# ============================================================
# OVERALL MASTERY
# ============================================================

st.subheader(
    "🧠 Overall Knowledge Mastery"
)

st.progress(
    min(
        float(accuracy) / 100,
        1.0,
    )
)

st.write(
    f"Current overall accuracy: "
    f"**{float(accuracy):.1f}%**"
)


# ============================================================
# SUBJECT-WISE PROGRESS
# ============================================================

st.subheader(
    "📚 Subject-wise Progress"
)


try:

    subject_progress = (
        get_subject_progress()
    )

except Exception:

    subject_progress = []


if subject_progress:

    for item in subject_progress:

        subject = item.get(
            "subject",
            "General",
        )

        subject_accuracy = float(
            item.get(
                "accuracy",
                0,
            )
        )

        st.write(
            f"**{subject}** — "
            f"{subject_accuracy:.1f}% accuracy"
        )

        st.progress(
            min(
                subject_accuracy / 100,
                1.0,
            )
        )

else:

    st.info(
        "Complete a quiz to see "
        "subject-wise progress."
    )


# ============================================================
# STUDY HISTORY
# ============================================================

st.subheader(
    "🕒 Study History"
)


try:

    history = get_study_history(
        limit=20
    )

except Exception:

    history = []


if history:

    for item in history:

        subject = item.get(
            "subject",
            "General",
        )

        activity_type = item.get(
            "activity_type",
            "Study",
        )

        score = item.get(
            "score",
            None,
        )

        total = item.get(
            "total_questions",
            None,
        )

        created_at = item.get(
            "created_at",
            "",
        )


        if (
            score is not None
            and total is not None
        ):

            st.write(
                f"📘 **{subject}** | "
                f"{activity_type} | "
                f"Score: {score}/{total} | "
                f"{created_at}"
            )

        else:

            st.write(
                f"📘 **{subject}** | "
                f"{activity_type} | "
                f"{created_at}"
            )

else:

    st.info(
        "No study history yet. "
        "Complete a quiz or generate flashcards."
    )


# ============================================================
# SMART RECOMMENDATION
# ============================================================

st.subheader(
    "💡 Smart Study Recommendation"
)


if quizzes_taken == 0:

    recommendation = (
        "🚀 Start by uploading a document and "
        "generating your first quiz."
    )

elif accuracy >= 90:

    recommendation = (
        "🏆 Excellent performance! Try Hard "
        "difficulty questions and use YouTube "
        "resources for advanced topics."
    )

elif accuracy >= 80:

    recommendation = (
        "🌟 Great work! Continue with Hard quizzes "
        "and revise using flashcards."
    )

elif accuracy >= 60:

    recommendation = (
        "📚 Good progress. Review incorrect answers "
        "and practice Medium difficulty questions."
    )

else:

    recommendation = (
        "🌱 Focus on the basics. Use Easy quizzes, "
        "flashcards, and educational videos for revision."
    )


st.info(
    recommendation
)


# ============================================================
# ACHIEVEMENTS
# ============================================================

st.subheader(
    "🏅 Achievements"
)

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


if total_flashcards >= 5:

    achievements.append(
        "🧠 Flashcard Starter"
    )


if total_flashcards >= 20:

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


if achievements:

    for achievement in achievements:

        st.success(
            achievement
        )

else:

    st.info(
        "🔒 Complete quizzes and create "
        "flashcards to unlock achievements!"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🧠 Lumyn-AI • Learn • Practice • Review • Improve • Master"
)