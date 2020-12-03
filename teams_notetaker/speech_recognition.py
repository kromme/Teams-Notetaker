from .utils import get_logger
from google.cloud import speech
from google.oauth2 import service_account
import tqdm
import os
import io

logger = get_logger("speech_recognition")


def setup_google_speech(key_file):
    """Setup the config for google speech to text
    """

    assert os.path.isfile(
        key_file
    ), "Could not find key file, please visit https://codelabs.developers.google.com/codelabs/cloud-speech-text-python3#0"

    # create credentials
    credentials = service_account.Credentials.from_service_account_file(key_file)

    # setup the client and config
    client = speech.SpeechClient(credentials=credentials)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        # sample_rate_hertz=16000,
        language_code="en-US",
        # Enable automatic punctuation
        enable_automatic_punctuation=True,
    )
    logger.info("Initialized Google Speech")
    return client, config


def transcribe_part(audio_path: str, client, config) -> str:
    """Transcribes an audio file
    """
    assert client, "Google Client not set, run _setup_google_speech()"
    assert config, "Google Config not set, run _setup_google_speech()"

    # init transcription for path
    transcription = ""

    # open audio
    with io.open(audio_path, "rb") as f:
        content = f.read()

    # transcribe by sending to google
    audio = speech.RecognitionAudio(content=content)
    response = client.recognize(config=config, audio=audio)

    # collecting results
    for _, result in enumerate(response.results):
        alternative = result.alternatives[0]
        transcription += " " + alternative.transcript

    return transcription


def transcribe_all_audioparts(audio_part_folder: str, client, config) -> str:
    """Transcribe all parts of the audio and concat them
    """
    # init transcription
    transcription = ""

    # collect files to transcribe
    files = os.listdir(audio_part_folder)

    logger.info(f"Transcribing {len(files)} parts")

    # loop and transcribe
    for _, audio_part in tqdm.tqdm(enumerate(files)):
        audio_part_path = f"{audio_part_folder}/{audio_part}"
        transcription += transcribe_part(
            audio_path=audio_part_path, client=client, config=config
        )

    return transcription
