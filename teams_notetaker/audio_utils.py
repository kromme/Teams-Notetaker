import subprocess
import os
from .utils import get_logger, check_cmd_application_available
logger = get_logger('audio_utils')


def extract_audio(video_path: str = None, audio_path: str = None, overwrite: bool = True):
    """Extract audio file from a video using ffmpeg

    Parameters
    ----------
    video_path : str
        Path to the video file
    audio_path : str
        Path the audio file will be saved
    overwrite : bool
        Whether to overwrite the audio file when it already exists (default is True)
    """

    # checks whether ffmpeg can be found
    if not check_cmd_application_available('ffmpeg'):
        logger.error('Could not load ffmpeg')
        return

    # checks whether video file is found
    assert os.path.isfile(video_path), 'Can\'t find video'

    # add overwrite parameter to ffmpeg
    overwrite_param = '-y' if overwrite else ''
    if os.path.isfile(audio_path) and overwrite:
        logger.info(f'File already exists: overwriting {audio_path}')
    elif os.path.isfile(audio_path) and not overwrite:
        logger.info(
            f'File already exists: not overwriting {audio_path}')
        return

    # Call ffmpeg
    try:
        # -ab 160k -ac 2 -ar 44100 -vn
        command = f"ffmpeg {overwrite_param} -i {video_path} {audio_path}"
        subprocess.call(command, shell=True)
    except Exception as e:
        logger.error(
            'Could not extract audio file from video.', exc_info=e)

    # check whether file is saved
    assert os.path.isfile(
        audio_path), 'Something went wrong saving the audio file'
    logger.info(f'Audio successfully extracted to {audio_path}')


def remove_silences_from_audio(audio_path: str = None) -> str:
    """Removes silences from audio file using sox.

    Parameters
    ----------
    audio_path : str
        Path to the audio file

    Returns
    -------
    Returns new audio filename
    """

    # checks whether sox can be found
    if not check_cmd_application_available('sox'):
        logger.error('Could not load sox')
        return

    silenced_audio_path = audio_path.replace(
        ".wav", "_silence_removed.wav")

    try:
        command = f"sox {audio_path} {silenced_audio_path} silence -l 1 0.1 1% -1 2.0 1%"
        subprocess.call(command, shell=True)
    except Exception as e:
        logger.error(
            'Could not extract audio file from video.', exc_info=e)

    logger.info(f'Silences successfully removed')
    return silenced_audio_path
