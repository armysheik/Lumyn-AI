import json
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()


# ============================================================
# Initialize Groq LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)


# ============================================================
# Flashcard Generation Prompt
# ============================================================

prompt = ChatPromptTemplate.from_template("""
You are an expert educational flashcard generator.

Read the PDF text provided below and create exactly
{num_flashcards} flashcards.

IMPORTANT:
- Flashcards must be based ONLY on the provided text.
- Each flashcard must have a question and answer.
- Questions should test important concepts.
- Answers should be clear and concise.
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT include ```json or ```.

Use EXACTLY this JSON format:

[
    {{
        "question": "Question text",
        "answer": "Answer text"
    }}
]

PDF TEXT:
{text}
""")


# ============================================================
# Create LangChain Chain
# ============================================================

chain = prompt | llm | StrOutputParser()


# ============================================================
# Generate Flashcards
# ============================================================

def generate_flashcards(text, num_flashcards=5):

    response = chain.invoke({
        "text": text,
        "num_flashcards": num_flashcards
    })

    response = response.strip()

    # Remove accidental Markdown code blocks
    if response.startswith("```json"):
        response = response[7:]

    if response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    # Convert JSON text into Python object
    flashcards = json.loads(response)

    return flashcards


# ============================================================
# Main Program - Testing
# ============================================================

if __name__ == "__main__":

    sample_text = """
    Python is a high-level programming language.
    Artificial Intelligence is the simulation of human intelligence
    by machines.
    Machine Learning is a subset of Artificial Intelligence.
    """

    print("Generating flashcards...")

    flashcards = generate_flashcards(sample_text, 3)

    print("\nGenerated Flashcards:")

    for index, card in enumerate(flashcards, start=1):

        print(f"\nFlashcard {index}")
        print("Question:", card["question"])
        print("Answer:", card["answer"])