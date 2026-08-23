from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path):
    """
    Extract text from all pages of a PDF.
    """
    reader = PdfReader(pdf_path)
    extracted_text = ""

    for page in reader.pages:
        text = page.extract_text()

        if text:
            extracted_text += text + "\n"

    return extracted_text


if __name__ == "__main__":
    pdf_path = "data/sample_pdfs/sample.pdf"

    text = extract_text_from_pdf(pdf_path)

    print("=" * 50)
    print("EXTRACTED PDF TEXT")
    print("=" * 50)

    print(text)

    print("=" * 50)
    print("PDF EXTRACTION COMPLETED")
    print("=" * 50)