
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

Read the document text provided below.

Create exactly {num_questions} questions.

QUIZ TYPE: {quiz_type}

DIFFICULTY LEVEL: {difficulty}


DIFFICULTY RULES:

- Easy:
  Test basic facts, definitions, and direct information
  clearly stated in the document.

- Medium:
  Test understanding, relationships between concepts,
  and interpretation of information from the document.

- Hard:
  Test deeper understanding, comparison, reasoning,
  and application of concepts from the document.


QUIZ TYPE RULES:


1. MCQ

Create multiple-choice questions.

Each question must contain exactly 4 options.

Options must be labelled A, B, C and D.

There must be exactly one correct answer.

Use this JSON format:

[
    {{
        "question": "Question text",
        "options": {{
            "A": "Option A",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D"
        }},
        "answer": "B",
        "difficulty": "{difficulty}",
        "type": "MCQ"
    }}
]


2. TRUE_FALSE

Create True/False questions.

The options must contain exactly:

A = True
B = False

The answer must be either "A" or "B".

Use this JSON format:

[
    {{
        "question": "Question statement",
        "options": {{
            "A": "True",
            "B": "False"
        }},
        "answer": "A",
        "difficulty": "{difficulty}",
        "type": "True/False"
    }}
]


3. FILL_BLANK

Create fill-in-the-blank questions.

Replace an important word or phrase with a blank.

Use exactly one option containing the correct answer.

Use this JSON format:

[
    {{
        "question": "Python is a ______ programming language.",
        "options": {{
            "A": "high-level"
        }},
        "answer": "A",
        "difficulty": "{difficulty}",
        "type": "Fill in the Blank"
    }}
]


IMPORTANT:

- Questions must be based ONLY on the provided document text.
- Do not use outside knowledge.
- Create exactly {num_questions} questions.
- Follow the selected quiz type exactly.
- Follow the selected difficulty exactly.
- There must be exactly one correct answer.
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT include ```json or ```.


DOCUMENT TEXT:

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
    Generate structured quiz data.

    Supported difficulty:
        Easy
        Medium
        Hard

    Supported quiz types:
        MCQ
        True/False
        Fill in the Blank
    """

    # --------------------------------------------------------
    # Validate difficulty
    # --------------------------------------------------------

    allowed_difficulties = [
        "Easy",
        "Medium",
        "Hard"
    ]

    if difficulty not in allowed_difficulties:

        raise ValueError(
            "Difficulty must be Easy, Medium, or Hard."
        )


    # --------------------------------------------------------
    # Validate quiz type
    # --------------------------------------------------------

    allowed_quiz_types = [
        "MCQ",
        "True/False",
        "Fill in the Blank"
    ]

    if quiz_type not in allowed_quiz_types:

        raise ValueError(
            "Quiz type must be MCQ, True/False, "
            "or Fill in the Blank."
        )


    # --------------------------------------------------------
    # Generate response
    # --------------------------------------------------------

    response = chain.invoke({
        "text": text,
        "num_questions": num_questions,
        "difficulty": difficulty,
        "quiz_type": quiz_type
    })


    # --------------------------------------------------------
    # Remove Markdown code blocks
    # --------------------------------------------------------

    response = response.strip()

    if response.startswith("```json"):

        response = response[7:]


    if response.startswith("```"):

        response = response[3:]


    if response.endswith("```"):

        response = response[:-3]


    response = response.strip()


    # --------------------------------------------------------
    # Convert JSON text to Python object
    # --------------------------------------------------------

    quiz = json.loads(response)


    # --------------------------------------------------------
    # Validate quiz
    # --------------------------------------------------------

    if not isinstance(quiz, list):

        raise ValueError(
            "Quiz format is invalid. "
            "Expected a list of questions."
        )


    return quiz


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    # Path to sample PDF

    pdf_path = "data/sample_pdfs/sample.pdf"


    print("=" * 60)
    print("           LUMYN-AI QUIZ GENERATOR")
    print("=" * 60)


    # --------------------------------------------------------
    # Step 1: Read PDF
    # --------------------------------------------------------

    print("\nReading PDF...")
    print(f"PDF: {pdf_path}")


    text = extract_text_from_pdf(
        pdf_path
    )


    if not text.strip():

        print(
            "\nNo text could be extracted from the PDF."
        )

        exit()


    print(
        "PDF text extracted successfully."
    )


    # --------------------------------------------------------
    # Step 2: Select Difficulty
    # --------------------------------------------------------

    print("\nSelect Difficulty:")
    print("1. Easy")
    print("2. Medium")
    print("3. Hard")


    difficulty_choice = input(
        "Enter difficulty choice: "
    )


    difficulty_map = {

        "1": "Easy",

        "2": "Medium",

        "3": "Hard"

    }


    difficulty = difficulty_map.get(
        difficulty_choice,
        "Medium"
    )


    # --------------------------------------------------------
    # Step 3: Select Quiz Type
    # --------------------------------------------------------

    print("\nSelect Quiz Type:")
    print("1. MCQ")
    print("2. True/False")
    print("3. Fill in the Blank")


    quiz_choice = input(
        "Enter quiz type choice: "
    )


    quiz_type_map = {

        "1": "MCQ",

        "2": "True/False",

        "3": "Fill in the Blank"

    }


    quiz_type = quiz_type_map.get(
        quiz_choice,
        "MCQ"
    )


    print(
        f"\nSelected Difficulty: {difficulty}"
    )

    print(
        f"Selected Quiz Type: {quiz_type}"
    )


    # --------------------------------------------------------
    # Step 4: Generate Quiz
    # --------------------------------------------------------

    print(
        "\nGenerating quiz using AI..."
    )


    quiz = generate_quiz(
        text,
        num_questions=3,
        difficulty=difficulty,
        quiz_type=quiz_type
    )


    # --------------------------------------------------------
    # Step 5: Display Quiz
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("                 GENERATED QUIZ")
    print("=" * 60)


    for index, question in enumerate(
        quiz,
        start=1
    ):

        print(
            f"\nQuestion {index}:"
        )


        print(
            question["question"]
        )


        for key, value in question[
            "options"
        ].items():

            print(
                f"{key}. {value}"
            )


        print(
            f"Correct Answer: "
            f"{question['answer']}"
        )


        print(
            f"Difficulty: "
            f"{question['difficulty']}"
        )


        print(
            f"Type: "
            f"{question['type']}"
        )


    print("\n" + "=" * 60)
    print("QUIZ GENERATION COMPLETED")
    print("=" * 60)

