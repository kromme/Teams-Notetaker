"""Main module."""
import datetime
import io
import os
import subprocess

from google.cloud import speech
from google.oauth2 import service_account
from summarizer import Summarizer

from utils import get_logger, check_cmd_application_available


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
        self.audio_part_path = ''
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
        self.audio_part_path = f'{self.AUDIO_PART_FOLDER}/%03d.wav'
        self.transcription_path = f'{self.TRANSCRIPTION_FOLDER}/{self.ts}_{self.filename}.txt'
        self.notes_path = f'{self.NOTES_FOLDER}/{self.ts}_{self.filename}.txt'

    def extract_audio(self, video_path: str = None, audio_path: str = None, overwrite: bool = True):
        """Extract audio file from a video using ffmpeg

        Parameters
        ----------
        video_path : str
            Path to the video file, default is set in class
        audio_path : str
            Path the audio file will be saved, default is set in class
        overwrite : bool
            Whether to overwrite the audio file when it already exists (default is True)
        """
        if video_path is None:
            video_path = self.video_path
        if audio_path is None:
            audio_path = self.audio_path

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

    def remove_silences_from_audio(self, audio_path: str = None):
        """Removes silences from audio file using sox
        """

        if audio_path is None:
            audio_path = self.audio_path

        # checks whether sox can be found
        if not check_cmd_application_available('sox'):
            logger.error('Could not load sox')
            return

        silenced_audio_path = audio_path.replace(
            ".wav", "_silence_removed.wav")

        try:
            command = f"sox {audio_path} {silenced_audio_path} silence -l 1 0.1 1% -1 2.0 1%"
            subprocess.call(command, shell=True)
            self.audio_path = silenced_audio_path
        except Exception as e:
            logger.error(
                'Could not extract audio file from video.', exc_info=e)

        logger.info(f'Silences successfully removed')

    def split_audio_file(self, audio_path: str = None):
        """Split up the audio in parts of 50 seconds
        """

        if audio_path is None:
            audio_path = self.audio_path

        # checks whether ffmpeg can be found
        output = subprocess.run('ffmpeg', shell=True, capture_output=True)
        assert 'not recognized' not in str(output.stderr), 'ffmpeg not found'

        # split up
        try:
            command = f"""ffmpeg -i "{audio_path}" -f segment -segment_time 50 -c copy -reset_timestamps 1 "{self.audio_part_path}" """
            subprocess.call(command, shell=True)
        except Exception as e:
            logger.error(
                'Could not extract audio file from video.', exc_info=e)

        logger.info(
            f'Audio successfully split into {len(os.listdir(self.AUDIO_PART_FOLDER))} parts')

    def _setup_google_speech(self):
        """Setup the config for google speech to text
        """

        assert os.path.isfile(
            self.key_file), 'Could not find key file, please visit https://codelabs.developers.google.com/codelabs/cloud-speech-text-python3#0'

        # create credentials
        credentials = service_account.Credentials.from_service_account_file(
            self.key_file)

        # setup the client and config
        self.client = speech.SpeechClient(credentials=credentials)
        self.config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            # Enable automatic punctuation
            enable_automatic_punctuation=True,
        )
        logger.info('Initialized Google Speech')

    def transcribe_part(self, audio_path: str) -> str:
        """Transcribes an audio file
        """
        assert self.client, 'Google Client not set, run _setup_google_speech()'
        assert self.config, 'Google Config not set, run _setup_google_speech()'

        # init transcription for path
        transcription = ""

        # open audio
        with io.open(audio_path, "rb") as f:
            content = f.read()

        # transcribe by sending to google
        audio = speech.RecognitionAudio(content=content)
        response = self.client.recognize(config=self.config, audio=audio)

        # collecting results
        for _, result in enumerate(response.results):
            alternative = result.alternatives[0]
            transcription += ' ' + alternative.transcript

        return transcription

    def transcribe(self):
        """Transcribe all parts of the audio and concat them
        """
        # init transcription
        self.transcription = ""

        # collect files to transcribe
        files = os.listdir(self.AUDIO_PART_FOLDER)

        # loop and transcribe
        for i, audio_part in enumerate(files):
            audio_part_path = f"{self.AUDIO_PART_FOLDER}/{audio_part}"
            self.transcription += self.transcribe_part(audio_part_path)
            logger.info(f'Transcribed {i+1} out of {len(files)}')

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

        self.extract_audio()
        self.remove_silences_from_audio()
        self.split_audio_file()
        self.transcribe()
        self.summarize()
        return self.notes
