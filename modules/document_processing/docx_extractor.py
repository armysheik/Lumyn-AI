from docx import Document


def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.

    Validates the input path, checks the file type, handles
    corrupted/unreadable DOCX files, and ensures that the
    extracted document is not empty.
    """

    # Validate file path
    if not file_path:
        raise ValueError("No DOCX file was provided.")

    # Validate file extension
    if not str(file_path).lower().endswith(".docx"):
        raise ValueError("Unsupported file format. Please upload a DOCX file.")

    try:
        # Open the DOCX document
        document = Document(file_path)

    except Exception as error:
        raise ValueError(
            f"Unable to read the DOCX file. The file may be corrupted or invalid: {error}"
        ) from error

    try:
        paragraphs = []

        # Extract text from paragraphs
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        extracted_text = "\n".join(paragraphs).strip()

        # Check for empty document
        if not extracted_text:
            raise ValueError(
                "The DOCX file does not contain any readable text."
            )

        return extracted_text

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Error extracting text from the DOCX file: {error}"
        ) from error