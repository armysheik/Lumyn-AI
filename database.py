import sqlite3

DATABASE_NAME = "study_materials.db"


# ============================================================
# Database Connection
# ============================================================

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


# ============================================================
# Create Tables
# ============================================================

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# Save Quiz
# ============================================================

def save_quiz(quiz):
    connection = get_connection()
    cursor = connection.cursor()

    for question in quiz:
        cursor.execute("""
            INSERT INTO quizzes
            (question, option_a, option_b, option_c, option_d, answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            question["question"],
            question["options"]["A"],
            question["options"]["B"],
            question["options"]["C"],
            question["options"]["D"],
            question["answer"]
        ))

    connection.commit()
    connection.close()


# ============================================================
# Save Flashcards
# ============================================================

def save_flashcards(flashcards):
    connection = get_connection()
    cursor = connection.cursor()

    for card in flashcards:
        cursor.execute("""
            INSERT INTO flashcards (question, answer)
            VALUES (?, ?)
        """, (
            card["question"],
            card["answer"]
        ))

    connection.commit()
    connection.close()


# ============================================================
# Test Database
# ============================================================

if __name__ == "__main__":

    create_tables()

    sample_flashcards = [
        {
            "question": "What is Python?",
            "answer": "Python is a high-level programming language."
        },
        {
            "question": "What is AI?",
            "answer": "AI is the simulation of human intelligence by machines."
        }
    ]

    save_flashcards(sample_flashcards)

    print("Flashcards saved successfully!")  