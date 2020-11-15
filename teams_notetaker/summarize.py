from summarizer import Summarizer
from .utils import get_logger, check_cmd_application_available
logger = get_logger('summarizer')


def summarize(transcription: str = None, notes_path: str = None, ratio: float = 0.2, num_sentences: int = None):

    assert len(transcription.split(".")
               ) > 1, "Transcription too short for summarization."

    notes = ''

    # initialize the summarizer
    try:
        model = Summarizer()
        logger.info(f'Summarizer initialized')
    except Exception as e:
        logger.error('Could not init summarizer', exc_info=e)
        return

    # Summarize
    try:
        notes = model(transcription, ratio=ratio,
                      num_sentences=num_sentences)
        logger.info(
            f'Succesfully summarized transcription with {len(transcription.split("."))} lines to {len(notes.split("."))} sentences.')
    except Exception as e:
        logger.error('Could not summarise text', exc_info=e)
        return

    # save
    with open(notes_path, 'w') as f:
        f.write(notes)
    logger.info(f'Notes successfully saved to {notes_path}')

    return notes
