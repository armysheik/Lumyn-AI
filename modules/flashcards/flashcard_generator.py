import json
import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ============================================================
# GENERATE FLASHCARDS
# ============================================================

def generate_flashcards(text, num_flashcards=5):
    """
    Generate flashcards from the provided study material.

    Returns a list of dictionaries containing:
    - question
    - answer
    """

    # --------------------------------------------------------
    # Validate input text
    # --------------------------------------------------------

    if text is None:
        raise ValueError(
            "No text was provided for flashcard generation."
        )

    if not isinstance(text, str):
        raise ValueError(
            "Invalid study material. Expected text input."
        )

    text = text.strip()

    if not text:
        raise ValueError(
            "No text was provided for flashcard generation."
        )

    # --------------------------------------------------------
    # Validate number of flashcards
    # --------------------------------------------------------

    if not isinstance(num_flashcards, int):
        raise ValueError(
            "Number of flashcards must be a whole number."
        )

    if num_flashcards <= 0:
        raise ValueError(
            "Number of flashcards must be greater than zero."
        )

    if num_flashcards > 50:
        raise ValueError(
            "Number of flashcards cannot exceed 50."
        )

    # --------------------------------------------------------
    # Validate Groq API key
    # --------------------------------------------------------

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing from the .env file. "
            "Please configure the API key before generating flashcards."
        )

    # --------------------------------------------------------
    # Create prompt
    # --------------------------------------------------------

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an AI study assistant.

Create useful flashcards from the provided study material.

Return ONLY a valid JSON array.

Each flashcard must have exactly these two fields:

- question
- answer

Example format:

[
  {
    "question": "What is Python?",
    "answer": "Python is a high-level programming language."
  }
]

Rules:

- Do not add markdown.
- Do not add explanations outside the JSON.
- Do not add extra fields.
- Questions and answers must be based only on the provided study material.
"""
        ),
        (
            "human",
            """
Generate {num_flashcards} flashcards from the following study material:

{text}
"""
        )
    ])

    # --------------------------------------------------------
    # Initialize Groq model
    # --------------------------------------------------------

    try:
        model = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.3,
            api_key=GROQ_API_KEY
        )

    except Exception as error:
        raise RuntimeError(
            f"Unable to initialize the AI service: {error}"
        ) from error

    # --------------------------------------------------------
    # Create chain
    # --------------------------------------------------------

    chain = prompt | model

    # --------------------------------------------------------
    # Generate flashcards using AI
    # --------------------------------------------------------

    try:
        response = chain.invoke({
            "text": text,
            "num_flashcards": num_flashcards
        })

    except Exception as error:
        error_message = str(error)

        if "api" in error_message.lower():
            raise RuntimeError(
                "AI API error while generating flashcards. "
                "Please check your Groq API key and connection."
            ) from error

        if "timeout" in error_message.lower():
            raise RuntimeError(
                "The AI service took too long to respond. "
                "Please try generating the flashcards again."
            ) from error

        if "rate" in error_message.lower():
            raise RuntimeError(
                "The AI service rate limit was reached. "
                "Please wait and try again."
            ) from error

        raise RuntimeError(
            f"Flashcard generation failed: {error}"
        ) from error

    # --------------------------------------------------------
    # Validate AI response
    # --------------------------------------------------------

    if response is None:
        raise ValueError(
            "The AI returned no response for flashcard generation."
        )

    content = getattr(response, "content", None)

    if content is None:
        raise ValueError(
            "The AI response did not contain any flashcard content."
        )

    if not isinstance(content, str):
        content = str(content)

    content = content.strip()

    if not content:
        raise ValueError(
            "The AI returned an empty response. "
            "Please try generating the flashcards again."
        )

    # --------------------------------------------------------
    # Remove Markdown code fences
    # --------------------------------------------------------

    if content.startswith("```json"):
        content = content[7:].strip()

    elif content.startswith("```"):
        content = content[3:].strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:
        flashcards = json.loads(content)

    except json.JSONDecodeError as error:
        raise ValueError(
            "AI returned invalid JSON for flashcards. "
            "Please try generating the flashcards again."
        ) from error

    # --------------------------------------------------------
    # Validate overall output
    # --------------------------------------------------------

    if not isinstance(flashcards, list):
        raise ValueError(
            "Flashcard output must be a JSON list."
        )

    if not flashcards:
        raise ValueError(
            "The AI returned an empty flashcard list."
        )

    # --------------------------------------------------------
    # Validate individual flashcards
    # --------------------------------------------------------

    cleaned_flashcards = []

    for index, card in enumerate(flashcards, start=1):

        if not isinstance(card, dict):
            continue

        question = card.get("question")
        answer = card.get("answer")

        # Make sure both fields exist
        if question is None or answer is None:
            continue

        question = str(question).strip()
        answer = str(answer).strip()

        # Ignore incomplete cards
        if not question or not answer:
            continue

        cleaned_flashcards.append({
            "question": question,
            "answer": answer
        })

    # --------------------------------------------------------
    # Check final result
    # --------------------------------------------------------

    if not cleaned_flashcards:
        raise ValueError(
            "No valid flashcards were generated. "
            "Please try again with different study material."
        )

    return cleaned_flashcards