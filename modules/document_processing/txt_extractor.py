def extract_text_from_txt(file_path):
    """
    Extract text from a TXT file.

    Validates the input, checks the file format,
    handles different text encodings, and ensures
    that the file contains readable content.
    """

    # Validate file path
    if not file_path:
        raise ValueError("No TXT file was provided.")

    # Validate file extension
    if not str(file_path).lower().endswith(".txt"):
        raise ValueError("Unsupported file format. Please upload a TXT file.")

    try:
        # Try UTF-8 first
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

    except UnicodeDecodeError:
        # Try Latin-1 if UTF-8 decoding fails
        try:
            with open(file_path, "r", encoding="latin-1") as file:
                text = file.read()

        except Exception as error:
            raise ValueError(
                f"Unable to read the TXT file: {error}"
            ) from error

    except FileNotFoundError:
        raise ValueError(
            "The TXT file could not be found."
        )

    except PermissionError:
        raise ValueError(
            "Permission denied while reading the TXT file."
        )

    except Exception as error:
        raise ValueError(
            f"Error reading TXT file: {error}"
        ) from error

    # Remove unnecessary whitespace
    text = text.strip()

    # Check for empty content
    if not text:
        raise ValueError(
            "The TXT file does not contain any readable text."
        )

    return text