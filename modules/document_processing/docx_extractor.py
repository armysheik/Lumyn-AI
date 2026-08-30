from docx import Document


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""

    try:
        document = Document(file_path)

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n".join(paragraphs)

    except Exception as error:
        raise Exception(f"Error reading DOCX file: {error}")