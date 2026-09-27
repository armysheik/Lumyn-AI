import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# INITIALIZE GROQ LLM
# ============================================================

try:
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0
    )
except Exception as error:
    llm = None
    llm_initialization_error = error


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
- Do NOT include ```json or ```

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
        "question": "The _____ is responsible for ...",
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

    # --------------------------------------------------------
    # Validate input text
    # --------------------------------------------------------

    if text is None:
        raise ValueError(
            "No document text was provided for quiz generation."
        )

    if not isinstance(text, str):
        raise ValueError(
            "Invalid document content. Expected text input."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "The document does not contain any readable text."
        )

    # --------------------------------------------------------
    # Validate number of questions
    # --------------------------------------------------------

    if not isinstance(num_questions, int):
        raise ValueError(
            "Number of questions must be a whole number."
        )

    if num_questions <= 0:
        raise ValueError(
            "Number of questions must be greater than zero."
        )

    if num_questions > 50:
        raise ValueError(
            "Number of questions cannot exceed 50."
        )

    # --------------------------------------------------------
    # Validate difficulty
    # --------------------------------------------------------

    allowed_difficulties = {
        "Easy",
        "Medium",
        "Hard"
    }

    if difficulty not in allowed_difficulties:
        raise ValueError(
            "Invalid difficulty. Please select Easy, Medium, or Hard."
        )

    # --------------------------------------------------------
    # Validate quiz type
    # --------------------------------------------------------

    allowed_quiz_types = {
        "MCQ",
        "True/False",
        "Fill-in-the-Blanks"
    }

    if quiz_type not in allowed_quiz_types:
        raise ValueError(
            "Invalid quiz type. Please select MCQ, True/False, "
            "or Fill-in-the-Blanks."
        )

    # --------------------------------------------------------
    # Check LLM initialization
    # --------------------------------------------------------

    if llm is None:
        raise RuntimeError(
            "AI service could not be initialized. "
            "Please check your Groq API configuration."
        )

    # --------------------------------------------------------
    # Create chain
    # --------------------------------------------------------

    chain = prompt | llm | StrOutputParser()

    # --------------------------------------------------------
    # Call AI model
    # --------------------------------------------------------

    try:
        response = chain.invoke({
            "text": text,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "quiz_type": quiz_type
        })

    except Exception as error:
        error_message = str(error)

        if "api" in error_message.lower():
            raise RuntimeError(
                "AI API error while generating the quiz. "
                "Please check your Groq API key and connection."
            ) from error

        if "timeout" in error_message.lower():
            raise RuntimeError(
                "The AI service took too long to respond. "
                "Please try generating the quiz again."
            ) from error

        if "rate" in error_message.lower():
            raise RuntimeError(
                "The AI service rate limit was reached. "
                "Please wait and try again."
            ) from error

        raise RuntimeError(
            f"AI quiz generation failed: {error}"
        ) from error

    # --------------------------------------------------------
    # Validate AI response
    # --------------------------------------------------------

    if response is None:
        raise ValueError(
            "The AI returned no response while generating the quiz."
        )

    if not isinstance(response, str):
        response = str(response)

    response = response.strip()

    if not response:
        raise ValueError(
            "The AI returned an empty response. "
            "Please try generating the quiz again."
        )

    # --------------------------------------------------------
    # Remove Markdown code fences if AI adds them
    # --------------------------------------------------------

    if response.startswith("```json"):
        response = response[7:].strip()

    elif response.startswith("```"):
        response = response[3:].strip()

    if response.endswith("```"):
        response = response[:-3].strip()

    # --------------------------------------------------------
    # Convert AI response to JSON
    # --------------------------------------------------------

    try:
        quiz = json.loads(response)

    except json.JSONDecodeError as error:
        raise ValueError(
            "The AI returned an invalid quiz response. "
            "Please try generating the quiz again."
        ) from error

    # --------------------------------------------------------
    # Validate quiz structure
    # --------------------------------------------------------

    if not isinstance(quiz, list):
        raise ValueError(
            "AI returned an invalid quiz format. "
            "Expected a list of questions."
        )

    if len(quiz) == 0:
        raise ValueError(
            "AI returned an empty quiz. "
            "Please try generating the quiz again."
        )

    # --------------------------------------------------------
    # Validate each question
    # --------------------------------------------------------

    validated_quiz = []

    for index, question in enumerate(quiz, start=1):

        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index} has an invalid format."
            )

        if "question" not in question:
            raise ValueError(
                f"Question {index} is missing the question text."
            )

        if not isinstance(question["question"], str):
            raise ValueError(
                f"Question {index} contains invalid question text."
            )

        if not question["question"].strip():
            raise ValueError(
                f"Question {index} contains empty question text."
            )

        # Validate MCQ
        if quiz_type == "MCQ":

            options = question.get("options")

            if not isinstance(options, dict):
                raise ValueError(
                    f"Question {index} has invalid MCQ options."
                )

            required_options = {"A", "B", "C", "D"}

            if set(options.keys()) != required_options:
                raise ValueError(
                    f"Question {index} must contain exactly four options: "
                    "A, B, C and D."
                )

            answer = question.get("answer")

            if answer not in required_options:
                raise ValueError(
                    f"Question {index} has an invalid correct answer."
                )

        # Validate True/False
        elif quiz_type == "True/False":

            options = question.get("options")

            if not isinstance(options, dict):
                raise ValueError(
                    f"Question {index} has invalid True/False options."
                )

            if options != {
                "A": "True",
                "B": "False"
            }:
                raise ValueError(
                    f"Question {index} must contain True and False options."
                )

            answer = question.get("answer")

            if answer not in {"A", "B"}:
                raise ValueError(
                    f"Question {index} has an invalid True/False answer."
                )

        # Validate Fill-in-the-Blanks
        elif quiz_type == "Fill-in-the-Blanks":

            answer = question.get("answer")

            if not isinstance(answer, str) or not answer.strip():
                raise ValueError(
                    f"Question {index} has an invalid fill-in-the-blank answer."
                )

            question_text = question["question"]

            blank_count = question_text.count("_____")

            if blank_count != 1:
                raise ValueError(
                    f"Question {index} must contain exactly one blank."
                )

        validated_quiz.append(question)

    # --------------------------------------------------------
    # Return validated quiz
    # --------------------------------------------------------

    return validated_quiz


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

        try:
            quiz = generate_quiz(
                sample_text,
                3,
                "Easy",
                quiz_type
            )

            print(json.dumps(quiz, indent=4))

        except Exception as error:
            print(f"Quiz generation failed: {error}")