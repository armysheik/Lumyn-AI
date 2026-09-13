import sqlite3
from datetime import datetime


DATABASE_NAME = "study_materials.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


# ============================================================
# HELPER - CHECK COLUMN
# ============================================================

def column_exists(table_name, column_name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    connection.close()

    for column in columns:

        if column[1] == column_name:
            return True

    return False


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # SUBJECTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # QUIZZES
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            answer TEXT,
            subject TEXT DEFAULT 'General',
            quiz_type TEXT DEFAULT 'MCQ',
            difficulty TEXT DEFAULT 'Medium',
            created_at TEXT
        )
        """
    )

    # --------------------------------------------------------
    # FLASHCARDS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            subject TEXT DEFAULT 'General',
            created_at TEXT
        )
        """
    )

    # --------------------------------------------------------
    # STUDY HISTORY
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS study_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            quiz_type TEXT,
            difficulty TEXT,
            score INTEGER,
            total_questions INTEGER,
            flashcards_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    # ========================================================
    # MIGRATION FOR OLD DATABASE
    # ========================================================

    # --------------------------------------------------------
    # QUIZZES COLUMNS
    # --------------------------------------------------------

    quiz_columns = [
        ("subject", "TEXT DEFAULT 'General'"),
        ("quiz_type", "TEXT DEFAULT 'MCQ'"),
        ("difficulty", "TEXT DEFAULT 'Medium'"),
        ("created_at", "TEXT"),
    ]

    for column_name, column_type in quiz_columns:

        if not column_exists(
            "quizzes",
            column_name,
        ):

            cursor.execute(
                f"""
                ALTER TABLE quizzes
                ADD COLUMN {column_name}
                {column_type}
                """
            )

    # --------------------------------------------------------
    # FLASHCARD COLUMNS
    # --------------------------------------------------------

    flashcard_columns = [
        ("subject", "TEXT DEFAULT 'General'"),
        ("created_at", "TEXT"),
    ]

    for column_name, column_type in flashcard_columns:

        if not column_exists(
            "flashcards",
            column_name,
        ):

            cursor.execute(
                f"""
                ALTER TABLE flashcards
                ADD COLUMN {column_name}
                {column_type}
                """
            )

    connection.commit()
    connection.close()


# ============================================================
# SUBJECT FUNCTIONS
# ============================================================

def get_or_create_subject(subject):

    if not subject:
        subject = "General"

    subject = subject.strip()

    if not subject:
        subject = "General"

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM subjects
        WHERE name = ?
        """,
        (subject,),
    )

    result = cursor.fetchone()

    if result:

        subject_id = result[0]

    else:

        cursor.execute(
            """
            INSERT INTO subjects
            (name, created_at)
            VALUES (?, ?)
            """,
            (
                subject,
                datetime.now().isoformat(),
            ),
        )

        subject_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return subject_id


# ============================================================
# GET SUBJECTS
# ============================================================

def get_subjects():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM subjects
        ORDER BY name
        """
    )

    rows = cursor.fetchall()

    connection.close()

    subjects = []

    for row in rows:

        subjects.append(row[0])

    if "General" not in subjects:

        subjects.insert(0, "General")

    return subjects


# ============================================================
# SAVE QUIZ
# ============================================================

def save_quiz(
    quiz,
    subject="General",
    quiz_type="MCQ",
    difficulty="Medium",
):

    if not quiz:
        return

    get_or_create_subject(subject)

    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now().isoformat()

    for question in quiz:

        question_text = question.get(
            "question",
            "",
        )

        answer = question.get(
            "answer",
            "",
        )

        options = question.get(
            "options",
            {},
        )

        option_a = options.get(
            "A",
            "",
        )

        option_b = options.get(
            "B",
            "",
        )

        option_c = options.get(
            "C",
            "",
        )

        option_d = options.get(
            "D",
            "",
        )

        cursor.execute(
            """
            INSERT INTO quizzes
            (
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                answer,
                subject,
                quiz_type,
                difficulty,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                question_text,
                option_a,
                option_b,
                option_c,
                option_d,
                answer,
                subject,
                quiz_type,
                difficulty,
                created_at,
            ),
        )

    connection.commit()
    connection.close()


# ============================================================
# SAVE FLASHCARDS
# ============================================================

def save_flashcards(
    flashcards,
    subject="General",
):

    if not flashcards:
        return

    get_or_create_subject(subject)

    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now().isoformat()

    for card in flashcards:

        question = card.get(
            "question",
            "",
        )

        answer = card.get(
            "answer",
            "",
        )

        cursor.execute(
            """
            INSERT INTO flashcards
            (
                question,
                answer,
                subject,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                question,
                answer,
                subject,
                created_at,
            ),
        )

    connection.commit()
    connection.close()


# ============================================================
# SAVE QUIZ RESULT
# ============================================================

def save_quiz_result(
    subject,
    quiz_type,
    difficulty,
    score,
    total_questions,
):

    get_or_create_subject(subject)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO study_history
        (
            subject,
            activity_type,
            quiz_type,
            difficulty,
            score,
            total_questions,
            flashcards_count,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject,
            "Quiz",
            quiz_type,
            difficulty,
            score,
            total_questions,
            0,
            datetime.now().isoformat(),
        ),
    )

    connection.commit()
    connection.close()


# ============================================================
# SAVE FLASHCARD ACTIVITY
# ============================================================

def save_flashcard_activity(
    subject,
    total_cards,
):

    get_or_create_subject(subject)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO study_history
        (
            subject,
            activity_type,
            quiz_type,
            difficulty,
            score,
            total_questions,
            flashcards_count,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject,
            "Flashcards",
            None,
            None,
            None,
            None,
            total_cards,
            datetime.now().isoformat(),
        ),
    )

    connection.commit()
    connection.close()


# ============================================================
# GET STUDY HISTORY
# ============================================================

def get_study_history(
    subject=None,
    limit=20,
):

    connection = get_connection()
    cursor = connection.cursor()

    if subject:

        cursor.execute(
            """
            SELECT
                id,
                subject,
                activity_type,
                quiz_type,
                difficulty,
                score,
                total_questions,
                flashcards_count,
                created_at
            FROM study_history
            WHERE subject = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                subject,
                limit,
            ),
        )

    else:

        cursor.execute(
            """
            SELECT
                id,
                subject,
                activity_type,
                quiz_type,
                difficulty,
                score,
                total_questions,
                flashcards_count,
                created_at
            FROM study_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

    rows = cursor.fetchall()

    connection.close()

    history = []

    for row in rows:

        history.append(
            {
                "id": row[0],
                "subject": row[1],
                "activity_type": row[2],
                "quiz_type": row[3],
                "difficulty": row[4],
                "score": row[5],
                "total_questions": row[6],
                "flashcards_count": row[7],
                "created_at": row[8],
            }
        )

    return history


# ============================================================
# OVERALL PROGRESS
# ============================================================

def get_overall_progress():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            COALESCE(SUM(total_questions), 0),
            COALESCE(SUM(score), 0)
        FROM study_history
        WHERE activity_type = 'Quiz'
        """
    )

    row = cursor.fetchone()

    connection.close()

    quizzes_taken = row[0] or 0
    total_questions = row[1] or 0
    correct_answers = row[2] or 0

    if total_questions > 0:

        accuracy = (
            correct_answers
            / total_questions
        ) * 100

    else:

        accuracy = 0

    return {
        "quizzes_taken": quizzes_taken,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": accuracy,
    }


# ============================================================
# SUBJECT-WISE PROGRESS
# ============================================================

def get_subject_progress():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            subject,
            COUNT(*),
            COALESCE(SUM(total_questions), 0),
            COALESCE(SUM(score), 0)
        FROM study_history
        WHERE activity_type = 'Quiz'
        GROUP BY subject
        ORDER BY subject
        """
    )

    rows = cursor.fetchall()

    connection.close()

    progress = []

    for row in rows:

        subject = row[0]
        quizzes = row[1]
        total_questions = row[2]
        correct_answers = row[3]

        if total_questions > 0:

            accuracy = (
                correct_answers
                / total_questions
            ) * 100

        else:

            accuracy = 0

        progress.append(
            {
                "subject": subject,
                "quizzes": quizzes,
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy": accuracy,
            }
        )

    return progress


# ============================================================
# TOTAL FLASHCARDS
# ============================================================

def get_total_flashcards():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM flashcards
        """
    )

    result = cursor.fetchone()

    connection.close()

    return result[0] if result else 0


# ============================================================
# CREATE DATABASE WHEN FILE IS RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    create_tables()

    print(
        "✅ SQLite database and tables "
        "created successfully."
    )