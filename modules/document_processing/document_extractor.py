from pathlib import Path

from PyPDF2 import PdfReader
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file.
    """

    if not file_path:
        raise ValueError("No PDF file was provided.")

    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError("The PDF file could not be found.")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("Invalid file format. Please provide a PDF file.")

    try:
        reader = PdfReader(str(file_path))

        if not reader.pages:
            raise ValueError("The PDF file does not contain any pages.")

        extracted_text = []

        for page in reader.pages:
            try:
                text = page.extract_text()

                if text and text.strip():
                    extracted_text.append(text.strip())

            except Exception as error:
                raise ValueError(
                    f"Unable to extract text from a PDF page: {error}"
                ) from error

        result = "\n".join(extracted_text).strip()

        if not result:
            raise ValueError(
                "The PDF file does not contain any readable text."
            )

        return result

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Unable to read the PDF file. The file may be corrupted or invalid: {error}"
        ) from error


def extract_text_from_txt(file_path):
    """
    Extract text from a TXT file.
    """

    if not file_path:
        raise ValueError("No TXT file was provided.")

    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError("The TXT file could not be found.")

    if file_path.suffix.lower() != ".txt":
        raise ValueError("Invalid file format. Please provide a TXT file.")

    try:
        # Try UTF-8 first
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                text = file.read()

        except UnicodeDecodeError:
            # Fall back to Latin-1
            with open(file_path, "r", encoding="latin-1") as file:
                text = file.read()

        text = text.strip()

        if not text:
            raise ValueError(
                "The TXT file does not contain any readable text."
            )

        return text

    except ValueError:
        raise

    except FileNotFoundError:
        raise ValueError("The TXT file could not be found.")

    except PermissionError:
        raise ValueError(
            "Permission denied while reading the TXT file."
        )

    except Exception as error:
        raise ValueError(
            f"Unable to read the TXT file: {error}"
        ) from error


def extract_text_from_docx(file_path):
    """
    Extract text from a DOCX file.
    """

    if not file_path:
        raise ValueError("No DOCX file was provided.")

    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError("The DOCX file could not be found.")

    if file_path.suffix.lower() != ".docx":
        raise ValueError("Invalid file format. Please provide a DOCX file.")

    try:
        document = Document(str(file_path))

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        result = "\n".join(paragraphs).strip()

        if not result:
            raise ValueError(
                "The DOCX file does not contain any readable text."
            )

        return result

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Unable to read the DOCX file. The file may be corrupted or invalid: {error}"
        ) from error


def extract_text(file_path):
    """
    Detect the document type and extract text accordingly.

    Supported formats:
    PDF
    TXT
    DOCX
    """

    if not file_path:
        raise ValueError("No file was provided.")

    file_path = Path(file_path)

    if not file_path.exists():
        raise ValueError("The uploaded file could not be found.")

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file format. "
            "Please upload a PDF, TXT, or DOCX file."
        )

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".txt":
        return extract_text_from_txt(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError(
        "Unsupported file format. "
        "Please upload a PDF, TXT, or DOCX file."
    )


def extract_text_from_uploaded_file(uploaded_file):
    """
    Save a Streamlit uploaded file temporarily and extract its text.
    """

    if uploaded_file is None:
        raise ValueError("No file was uploaded.")

    file_name = getattr(uploaded_file, "name", "")

    if not file_name:
        raise ValueError("The uploaded file does not have a valid file name.")

    extension = Path(file_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported file format. "
            "Please upload PDF, TXT, or DOCX."
        )

    temp_file = Path("uploaded_temp" + extension)

    try:
        file_data = uploaded_file.getbuffer()

        if not file_data:
            raise ValueError("The uploaded file is empty.")

        with open(temp_file, "wb") as file:
            file.write(file_data)

        text = extract_text(temp_file)

        if not text or not text.strip():
            raise ValueError(
                "No readable content was found in the uploaded file."
            )

        return text

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Error processing the uploaded file: {error}"
        ) from error

    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass