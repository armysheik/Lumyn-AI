import json
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from pdf_extractor import extract_text_from_pdf


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
# Quiz Generation Prompt
# ============================================================

prompt = ChatPromptTemplate.from_template("""
You are an expert educational quiz generator.

Read the PDF text provided below and create exactly
{num_questions} multiple-choice questions.

IMPORTANT:
- Questions must be based ONLY on the provided text.
- Each question must have exactly 4 options.
- Options must be labelled A, B, C and D.
- There must be exactly one correct answer.
- Do not add explanations.
- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT include ```json or ```.

Use EXACTLY this JSON format:

[
    {{
        "question": "Question text",
        "options": {{
            "A": "Option A",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D"
        }},
        "answer": "B"
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
# Generate Quiz
# ============================================================

def generate_quiz(text, num_questions=5):
    """
    Generate structured quiz data from extracted PDF text.
    """

    response = chain.invoke({
        "text": text,
        "num_questions": num_questions
    })

    # Remove accidental Markdown code blocks
    response = response.strip()

    if response.startswith("```json"):
        response = response[7:]

    if response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    # Convert JSON text into Python object
    quiz = json.loads(response)

    return quiz


# ============================================================
# Main Program
# ============================================================

if __name__ == "__main__":

    # Path to sample PDF
    pdf_path = "data/sample_pdfs/sample.pdf"

    print("=" * 60)
    print("           LUMYN-AI PDF QUIZ GENERATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Step 1: Read PDF
    # --------------------------------------------------------

    print("\n📖 Reading PDF...")
    print(f"PDF: {pdf_path}")

    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        print("\n❌ No text could be extracted from the PDF.")
        exit()

    print("✅ PDF text extracted successfully.")

    # --------------------------------------------------------
    # Step 2: Generate Quiz
    # --------------------------------------------------------

    print("\n🤖 Generating quiz using AI...")

    quiz = generate_quiz(text, 3)

    # --------------------------------------------------------
    # Step 3: Display Structured Quiz
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("                 GENERATED QUIZ")
    print("=" * 60)

    for index, question in enumerate(quiz, start=1):

        print(f"\nQuestion {index}:")
        print(question["question"])

        print(f"A. {question['options']['A']}")
        print(f"B. {question['options']['B']}")
        print(f"C. {question['options']['C']}")
        print(f"D. {question['options']['D']}")

        print(f"Correct Answer: {question['answer']}")

    # --------------------------------------------------------
    # Step 4: Show JSON
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("             STRUCTURED JSON DATA")
    print("=" * 60)

    print(json.dumps(quiz, indent=4))

    print("\n" + "=" * 60)
    print("✅ QUIZ GENERATION COMPLETED")
    print("=" * 60)