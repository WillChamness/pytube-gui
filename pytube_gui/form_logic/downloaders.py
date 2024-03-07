import os
from pytube import YouTube, Playlist, exceptions as pytube_exceptions
from PyQt6 import QtCore 
from PyQt6.QtCore import QThread

class VideoDownloaderThread(QThread):
    """Downloads a single video"""
    initialized = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, url: str, download_location: str, audio_only: bool):
        super().__init__()
        self.video: YouTube = YouTube(url)
        self.download_location: str = download_location
        self.audio_only: bool = audio_only


    def run(self):
        self.initialized.emit(f"Downloading: {self.video.title}")
        if self.audio_only:
            audio = self.video.streams.filter(only_audio=True).first().download(output_path=self.download_location)
            # rename to .mp3
            base, ext = os.path.splitext(audio)
            try:
                os.remove(base + ".mp3") # this file might exist already. if it does, can't perform rename
            except OSError:
                pass
            os.rename(audio, base + ".mp3")
        else:
            self.video.streams.get_highest_resolution().download(self.download_location)
        self.finished.emit()


class PlaylistDownloaderThread(QThread):
    """Downloads a single playlist of videos"""
    initialized = QtCore.pyqtSignal(int)
    next_video_title = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, url: str, download_base_path: str, audio_only: bool, start_index: int, stop_index: int):
        super().__init__()
        self.playlist: Playlist = Playlist(url)
        self.audio_only: bool = audio_only
        self.start_index: int = start_index
        self.stop_index: int = stop_index

        if len(self.playlist.videos) < start_index or len(self.playlist.videos) < stop_index:
            raise ValueError("Start or stop value is too large")

        # put all downloaded files into its own directory
        self.download_location: str = os.path.join(download_base_path, self.playlist.title)
        os.mkdir(self.download_location)


    def run(self):
        # playlist on youtube is 1-indexed, enumeration is 0-indexed. 
        start: int = self.start_index - 1 if self.start_index > 0 else 0
        stop: int = self.stop_index if self.stop_index > 0 else len(self.playlist.videos)
        self.initialized.emit(stop - start)
        for i, video in enumerate(self.playlist.videos[start : stop]): 
            self.next_video_title.emit(f"Downloading: {video.title}")
            if self.audio_only:
                audio = video.streams.filter(only_audio=True).first().download(output_path=self.download_location)
                # rename to .mp3
                base, ext = os.path.splitext(audio)
                os.rename(audio, base + ".mp3")
            else:
                video.streams.get_highest_resolution().download(self.download_location)
            self.progress.emit(i+1) # i+1 videos downloaded so far
        self.finished.emit()

 
class CaptionsDownloaderThread(QThread):
    initialized = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, url: str, download_location: str):
        super().__init__()
        self.video: YouTube = YouTube(url)
        self.download_location: str = download_location

        self.video.bypass_age_gate()
        if not self.video.captions:
            raise pytube_exceptions.PytubeError("No captions exist for video")


    def run(self):
        self.initialized.emit(f"Downloading: {self.video.title} (captions)")
        caption = self.video.captions["en"] if "en" in self.video.captions else self.video.captions["a.en"]
        caption.download(self.video.title, srt=False, output_path=self.download_location) 
        self.finished.emit()

