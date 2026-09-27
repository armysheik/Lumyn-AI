from pathlib import Path

import pyttsx3


def generate_audio(text, output_file="study_summary.wav"):
    """
    Convert study material text into an audio file.
    """

    # Validate text
    if text is None:
        raise ValueError("No text was provided for audio generation.")

    if not isinstance(text, str):
        raise ValueError("Audio input must be text.")

    text = text.strip()

    if not text:
        raise ValueError(
            "The study material is empty. Please provide valid content."
        )

    # Validate output file
    if not output_file:
        raise ValueError("No output file was specified.")

    output_path = Path(output_file)

    # Create output directory if needed
    if output_path.parent != Path("."):
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    try:
        # Initialize text-to-speech engine
        engine = pyttsx3.init()

        # Set speech speed
        engine.setProperty("rate", 160)

        # Set volume
        engine.setProperty("volume", 1.0)

        # Generate audio
        engine.save_to_file(
            text,
            str(output_path)
        )

        # Wait until audio generation is complete
        engine.runAndWait()

        # Stop the engine
        engine.stop()

    except Exception as error:
        raise RuntimeError(
            f"Unable to generate audio: {error}"
        ) from error

    # Check whether audio file was created
    if not output_path.exists():
        raise RuntimeError(
            "Audio generation failed because the audio file "
            "was not created."
        )

    # Check whether audio file is empty
    if output_path.stat().st_size == 0:
        raise RuntimeError(
            "Audio generation failed because the audio file "
            "is empty."
        )

    return str(output_path)


if __name__ == "__main__":

    sample_text = (
        "Artificial Intelligence is a branch of computer science "
        "that enables computers to perform tasks that normally "
        "require human intelligence."
    )

    try:
        audio_file = generate_audio(
            sample_text,
            "sample_study_summary.wav"
        )

        print(
            f"Audio generated successfully: {audio_file}"
        )

    except Exception as error:
        print(
            f"Audio generation failed: {error}"
        )