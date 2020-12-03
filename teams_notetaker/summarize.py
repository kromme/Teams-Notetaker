from summarizer import Summarizer
from .utils import get_logger, check_cmd_application_available

logger = get_logger("summarizer")


def summarize(
    transcription: str, notes_path: str, ratio: float = 0.2, num_sentences: int = None
) -> str:
    """Uses BERT for extractive summarization

    Parameters
    ----------
    transcription : str
        The transcription to be summarized
    notes_path : str
        Path to where the notes should be saved
    ratio : float
        Determine the length of the summarization in ratio of length transcription
    num_sentences : int
        Determine the length of the summarization in number of sentences

    Returns
    -------
    The summarized notes
    """

    assert (
        len(transcription.split(".")) > 1
    ), "Transcription too short for summarization."

    notes = ""

    # initialize the summarizer
    try:
        model = Summarizer()
        logger.info(f"Summarizer initialized")
    except Exception as e:
        logger.error("Could not init summarizer", exc_info=e)
        return

    # Summarize
    try:
        notes = model(transcription, ratio=ratio, num_sentences=num_sentences)
        logger.info(
            f'Succesfully summarized transcription with {len(transcription.split("."))} lines to {len(notes.split("."))} sentences.'
        )
    except Exception as e:
        logger.error("Could not summarise text", exc_info=e)
        return

    # save
    with open(notes_path, "w") as f:
        f.write(notes)
    logger.info(f"Notes successfully saved to {notes_path}")

    return notes
