"""
This module is an internal helper module that contains classes to download YouTube content.
It should not contain anything else.

Each class inherits from the PyQt6.QtCore.QThread class. The QThread should tell the form
what is currently being downloaded and the current progress of the download. 
"""

import os

from PyQt6 import QtCore
from PyQt6.QtCore import QThread
from pytube import Playlist, YouTube
from pytube import exceptions as pytube_exceptions


class VideoDownloaderThread(QThread):
    """Downloads a single video"""

    initialized = QtCore.pyqtSignal(
        str
    )  # tells form what is currently being downloaded
    finished = QtCore.pyqtSignal()  # tells form download is done

    def __init__(self, url: str, download_location: str, audio_only: bool):
        super().__init__()
        self.video: YouTube = YouTube(url)
        self.download_location: str = download_location
        self.audio_only: bool = audio_only

    def run(self):
        self.initialized.emit(f"Downloading: {self.video.title}")
        if self.audio_only:
            audio = (
                self.video.streams.filter(only_audio=True)
                .first()
                .download(output_path=self.download_location)
            )
            # rename to .mp3
            base, ext = os.path.splitext(audio)
            try:
                os.remove(
                    base + ".mp3"
                )  # this file might exist already. if it does, can't perform rename
            except OSError:
                pass
            os.rename(audio, base + ".mp3")
        else:
            self.video.streams.get_highest_resolution().download(self.download_location)
        self.finished.emit()


class PlaylistDownloaderThread(QThread):
    """Downloads a single playlist of videos"""

    initialized = QtCore.pyqtSignal(int)  # tells form how many videos there are
    next_video_title = QtCore.pyqtSignal(
        str
    )  # tells form what is currently being downloaded
    progress = QtCore.pyqtSignal(
        int
    )  # tells form how many videos have been downloaded so far
    finished = QtCore.pyqtSignal()  # tells form download is done

    def __init__(
        self,
        url: str,
        download_base_path: str,
        audio_only: bool,
        start_index: int,
        stop_index: int,
    ):
        super().__init__()
        self.playlist: Playlist = Playlist(url)
        self.audio_only: bool = audio_only
        self.start_index: int = start_index  # 1-indexed
        self.stop_index: int = stop_index  # 1-indexed

        if (
            len(self.playlist.videos) < start_index
            or len(self.playlist.videos) < stop_index
        ):
            raise ValueError("Start or stop value is too large")

        # put all downloaded files into its own directory
        self.download_location: str = os.path.join(
            download_base_path, self.playlist.title
        )
        os.mkdir(self.download_location)

    def run(self):
        # playlist on youtube is 1-indexed, enumeration is 0-indexed.
        # to account for this, start and stop will subtract 1 from the start_index and stop_index
        start: int = self.start_index - 1 if self.start_index > 0 else 0
        stop: int = (
            self.stop_index if self.stop_index > 0 else len(self.playlist.videos)
        )
        self.initialized.emit(stop - start)
        for i, video in enumerate(self.playlist.videos[start:stop]):
            self.next_video_title.emit(f"Downloading: {video.title}")
            if self.audio_only:
                audio = (
                    video.streams.filter(only_audio=True)
                    .first()
                    .download(output_path=self.download_location)
                )
                # rename to .mp3
                base, ext = os.path.splitext(audio)
                os.rename(audio, base + ".mp3")
            else:
                video.streams.get_highest_resolution().download(self.download_location)
            self.progress.emit(i + 1)  # i+1 videos downloaded so far
        self.finished.emit()


class CaptionsDownloaderThread(QThread):
    initialized = QtCore.pyqtSignal(str)  # tells form what is being downloaded
    finished = QtCore.pyqtSignal()  # tells form download is done

    def __init__(self, url: str, download_location: str):
        super().__init__()
        self.video: YouTube = YouTube(url)
        self.download_location: str = download_location

        self.video.bypass_age_gate()
        if not self.video.captions:
            raise pytube_exceptions.PytubeError("No captions exist for video")

    def run(self):
        self.initialized.emit(f"Downloading: {self.video.title} (captions)")
        caption = (
            self.video.captions["en"]
            if "en" in self.video.captions
            else self.video.captions["a.en"]
        )  # attempt downloading captions that the creator made. if doesn't exist, use autogenerated captions
        caption.download(
            self.video.title, srt=False, output_path=self.download_location
        )  # download to XML
        self.finished.emit()
