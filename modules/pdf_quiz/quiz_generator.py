import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from modules.pdf_quiz.pdf_extractor import extract_text_from_pdf


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# INITIALIZE GROQ LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ============================================================
# QUIZ GENERATION PROMPT
# ============================================================

prompt = ChatPromptTemplate.from_template("""
You are an expert educational quiz generator.

Create exactly {num_questions} questions from the
document text provided below.

Quiz type:
{quiz_type}

Difficulty:
{difficulty}

IMPORTANT RULES:

- Questions must be based ONLY on the document text.
- Follow the selected quiz type exactly.
- Follow the selected difficulty level.
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT include ```json or ```.

============================================================
MCQ FORMAT
============================================================

If quiz type is MCQ, use exactly:

[
    {{
        "question": "Question text",
        "options": {{
            "A": "Option A",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D"
        }},
        "answer": "A",
        "difficulty": "{difficulty}",
        "type": "MCQ"
    }}
]

Rules:
- Exactly 4 options.
- Exactly one correct answer.
- Answer must be A, B, C or D.

============================================================
TRUE/FALSE FORMAT
============================================================

If quiz type is True/False, use exactly:

[
    {{
        "question": "Statement",
        "options": {{
            "A": "True",
            "B": "False"
        }},
        "answer": "A",
        "difficulty": "{difficulty}",
        "type": "True/False"
    }}
]

Rules:
- Exactly two options.
- A must be True.
- B must be False.
- Exactly one correct answer.
- The statement must be objectively true or false.

============================================================
FILL-IN-THE-BLANK FORMAT
============================================================

If quiz type is Fill-in-the-Blanks, use exactly:

[
    {{
        "question": "The ______ is responsible for ...",
        "answer": "correct answer",
        "accepted_answers": [
            "correct answer"
        ],
        "difficulty": "{difficulty}",
        "type": "Fill-in-the-Blanks"
    }}
]

Rules:
- Use exactly one blank in each question.
- Do NOT use multiple blanks.
- The answer must be directly supported by the document.
- Include alternative accepted answers only when they have the same meaning.

============================================================
DOCUMENT TEXT
============================================================

{text}
""")


# ============================================================
# CREATE LANGCHAIN CHAIN
# ============================================================

chain = prompt | llm | StrOutputParser()


# ============================================================
# GENERATE QUIZ
# ============================================================

def generate_quiz(
    text,
    num_questions=5,
    difficulty="Medium",
    quiz_type="MCQ"
):
    """
    Generate MCQ, True/False or Fill-in-the-Blanks quiz.
    """

    response = chain.invoke({
        "text": text,
        "num_questions": num_questions,
        "difficulty": difficulty,
        "quiz_type": quiz_type
    })

    response = response.strip()

    # Remove Markdown code fences if AI adds them
    if response.startswith("```json"):
        response = response[7:]

    if response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    quiz = json.loads(response)

    # Basic validation
    if not isinstance(quiz, list):
        raise ValueError("AI returned invalid quiz format.")

    if len(quiz) == 0:
        raise ValueError("AI returned an empty quiz.")

    return quiz


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    sample_text = """
    Python is a high-level programming language.
    Artificial Intelligence is the simulation of human intelligence
    by machines.
    Machine Learning is a subset of Artificial Intelligence.
    """

    for quiz_type in [
        "MCQ",
        "True/False",
        "Fill-in-the-Blanks"
    ]:

        print("\n" + "=" * 60)
        print(f"TESTING: {quiz_type}")
        print("=" * 60)

        quiz = generate_quiz(
            sample_text,
            3,
            "Easy",
            quiz_type
        )

        print(json.dumps(quiz, indent=4))