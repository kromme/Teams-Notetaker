"""Main module."""
import datetime
import io
import os
import subprocess

from google.cloud import speech
from google.oauth2 import service_account
from summarizer import Summarizer

from .utils import get_logger, check_cmd_application_available
from .speech_recognition import setup_google_speech, transcribe_part, transcribe_all_audioparts
from .audio_utils import extract_audio, remove_silences_from_audio, split_audio_file

logger = get_logger('teams_notetaker')


class TeamsNotetaker():
    """
    A class used to take notes from teams meetings.

    From January, 11th 2021 all Teams recordings will be stored in OneDrive directly, see [here](https://docs.microsoft.com/en-gb/MicrosoftTeams/tmr-meeting-recording-change). Until then download it from [Stream](https://web.microsoftstream.com/) > My Content > video > Download video

    """

    def __init__(self,
                 filename: str,
                 key_file: str = 'key.json',
                 video_folder: str = '.',
                 audio_folder: str = 'audio',
                 transcription_folder: str = 'transcripts',
                 notes_folder: str = 'notes',
                 ):
        filename, video_extension = os.path.splitext(filename)
        self.filename = filename
        self.video_extension = video_extension
        self.key_file = key_file
        self.ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.VIDEO_FOLDER = video_folder
        self.AUDIO_FOLDER = audio_folder
        self.TRANSCRIPTION_FOLDER = transcription_folder
        self.NOTES_FOLDER = notes_folder
        self.AUDIO_PART_FOLDER = f"{self.AUDIO_FOLDER}/{self.ts}_{filename}"
        self.logfile = "log.log"

        # init
        self.video_path = ''
        self.audio_path = ''
        self.transcription_path = ''
        self.notes_path = ''
        self.config = False
        self.client = False

        # create folders
        self._setup_folder()
        self._setup_paths()
        self._setup_google_speech()

        logger.info('Teams Notetaker initialized')

    def _setup_folder(self):

        os.makedirs(self.VIDEO_FOLDER) if not os.path.exists(
            self.VIDEO_FOLDER) else True
        os.makedirs(self.AUDIO_FOLDER) if not os.path.exists(
            self.AUDIO_FOLDER) else True
        os.makedirs(self.AUDIO_PART_FOLDER) if not os.path.exists(
            self.AUDIO_PART_FOLDER) else True
        os.makedirs(self.TRANSCRIPTION_FOLDER) if not os.path.exists(
            self.TRANSCRIPTION_FOLDER) else True
        os.makedirs(self.NOTES_FOLDER) if not os.path.exists(
            self.NOTES_FOLDER) else True

    def _setup_paths(self):
        # set timestamp

        # set paths
        self.video_path = f'{self.VIDEO_FOLDER}/{self.filename}{self.video_extension}'
        self.audio_path = f'{self.AUDIO_FOLDER}/{self.ts}_{self.filename}.wav'
        self.transcription_path = f'{self.TRANSCRIPTION_FOLDER}/{self.ts}_{self.filename}.txt'
        self.notes_path = f'{self.NOTES_FOLDER}/{self.ts}_{self.filename}.txt'

    def _setup_google_speech(self):
        """Setup the config for google speech to text
        """
        self.client, self.config = setup_google_speech(self.key_file)

    def prepare_audio(self):
        """Prepare audio file by extracting the audio from the video, removing the
        silences and splitting it up in parts of 50 seconds
        """

        # extract audio from the video
        extract_audio(video_path=self.video_path, audio_path=self.audio_path)

        # remove silences and renew audio_path name
        self.audio_path = remove_silences_from_audio(
            audio_path=self.audio_path)

        # split the audio files because google can do 1 minute max
        split_audio_file(audio_path=self.audio_path,
                         audio_part_folder=self.AUDIO_PART_FOLDER)

        logger.info('Audio preprocessing done')

    def transcribe(self):
        """Transcribe all parts in the audio parts folder
        """
        self.transcription = transcribe_all_audioparts(
            audio_part_folder=self.AUDIO_PART_FOLDER, client=self.client, config=self.config)

    def summarize(self, transcription: str = None, notes_path: str = None, ratio: float = 0.2, num_sentences: int = None):

        if transcription is None:
            transcription = self.transcription
        if notes_path is None:
            notes_path = self.notes_path

        assert len(transcription.split(".")
                   ) > 1, "Transcription too short for summarization."

        # initialize the summarizer
        try:
            model = Summarizer()
            logger.info(f'Summarizer initialized')
        except Exception as e:
            logger.error('Could not init summarizer', exc_info=e)
            return

        # Summarize
        try:
            self.notes = model(transcription, ratio=ratio,
                               num_sentences=num_sentences)
            logger.info(
                f'Succesfully summarized transcription with {len(transcription.split("."))} lines to {len(self.notes.split("."))} sentences.')
        except Exception as e:
            logger.error('Could not summarise text', exc_info=e)
            return

        # save
        with open(notes_path, 'w') as f:
            f.write(self.notes)
        logger.info(f'Notes successfully saved to {notes_path}')

        return self.notes

    def run(self):

        self.prepare_audio()
        self.transcribe()
        self.summarize()
        return self.notes
