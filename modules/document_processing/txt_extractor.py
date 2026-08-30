def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as file:
            return file.read()

    except Exception as error:
        raise Exception(f"Error reading TXT file: {error}")