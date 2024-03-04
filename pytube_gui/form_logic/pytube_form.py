import os
import platform
import time
from typing import Union
from pytube import YouTube, Playlist, exceptions as pytube_exceptions
from ..form_ui.pytube_form import Ui_pythonYTDownloaderForm as MainFormUi # created from pyuic
from PyQt6 import QtWidgets, QtCore 
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QMessageBox, QFileDialog 

class PyTubeForm(MainFormUi):
    def __init__(self, current_dialog: QtWidgets.QDialog):
        """Form Constructor"""
        super().__init__()
        self.thread: Union[_VideoDownloaderThread, _PlaylistDownloaderThread] = None
        # setup UI before defining logic
        self.dialog_window: QtWidgets.QDialog = current_dialog
        self.setupUi(self.dialog_window)
        # define UI logic here
        self._on_form_load()
        self.cancelButton.clicked.connect(QtWidgets.QApplication.quit)
        self.startButton.clicked.connect(self.startButton_clicked)
        self.downloadFolderBrowseButton.clicked.connect(self.downloadFolderBrowseButton_clicked)
        self.videoPlaylistSelectCombobox.currentIndexChanged.connect(self.videoPlaylistSelectCombobox_changed)


    def _on_form_load(self):
        """When the form loads, do various chores."""
        home_download_directory = os.path.join(os.path.expanduser("~"), "Downloads")
        if platform.system != "Windows":
            try:
                os.mkdir(home_download_directory) # might not exist in some linux distros
            except FileExistsError:
                pass
        self.downloadFolderTextbox.setText(home_download_directory)
        self.downloadStatusLabel.setText("")


    def startButton_clicked(self):
        """
        Handler for clicking startButton.

        Downloads a video or playlist depending on user's inputs.
        """
        user_selection: str = self.videoPlaylistSelectCombobox.currentText()
        if user_selection == "Video":
            self._download_video()
        elif user_selection == "Playlist":
            self._download_playlist()
        else: 
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Could not decide if 'Video' or 'Playlist' selected")
        

    def downloadFolderBrowseButton_clicked(self):
        """
        Handler for clicking downloadFolderBrowseButton.

        Opens a file dialog to select a directory.
        """
        download_location = QFileDialog.getExistingDirectory(self.dialog_window, "Select folder")
        download_location_transformed = os.path.abspath(download_location) # e.g. transform "C:/my/path" to "C:\my\path"
        self.downloadFolderTextbox.setText(download_location_transformed)
  

    def _download_video(self):
        """Downloads a single video and saves it to the destination directory."""
        audio_only: bool = self.audioOnlyCheckbox.isChecked()
        download_location: str = self.downloadFolderTextbox.text()
        url: str = self.urlTextbox.text()

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)
        # prevent user from initiating download while current download is running
        self.startButton.setEnabled(False)
        self.downloadFolderBrowseButton.setEnabled(False)

        # attempt download
        try:
            # create new thread to download videos to prevent UI from freezing
            self.thread = _VideoDownloaderThread(url, download_location, audio_only)
            # update UI when download starts and ends
            self.thread.initialized.connect(self.downloadStatusLabel.setText)
            self.thread.finished.connect(self._video_download_completed)

            # start the thread
            self.thread.start()
            
        except pytube_exceptions.RegexMatchError as rme:
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Could not find video. Check to make sure the URL is correct.")
            print(rme)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.PytubeError as pe:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not download video. Check to make sure the URL is correct."
            )
            print(pe)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)


    def _download_playlist(self):
        """
        Downloads an entire playlist or part of a playlist, 
        creating a new directory to contain all videos from the playlist.
        """
        audio_only: bool = self.audioOnlyCheckbox.isChecked()
        download_base_path: str = self.downloadFolderTextbox.text()
        url: str = self.urlTextbox.text()
        # indexes are 1-based on YouTube, so these are also 1-based for the user
        start_index = self.startRangeSpinBox.value()
        stop_index = self.stopRangeSpinBox.value()

        if start_index > stop_index:
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Start value is greater than stop value")
            return

        self.progressBar.setMaximum(stop_index - start_index + 1)
        self.progressBar.setValue(0)
        self.progressBar.repaint()
        # prevent user from initiating download while current download is running
        self.startButton.setEnabled(False)
        self.downloadFolderBrowseButton.setEnabled(False)

        # attempt to download videos
        try:
            # create new thread to download videos to prevent UI from freezing
            self.thread = _PlaylistDownloaderThread(url, download_base_path, audio_only, start_index, stop_index)
            # tell the main thread to update UI when progress is made
            self.thread.next_video_title.connect(self.downloadStatusLabel.setText)
            self.thread.progress.connect(self.progressBar.setValue)
            self.thread.finished.connect(self._playlist_download_completed)

            # begin the download
            self.thread.start()
        except FileExistsError as fee: 
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "A folder already exists for the playlist")
            print(fee)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.RegexMatchError as rme:
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Could not find playlist. Check to make sure the URL is correct.")
            print(rme)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.PytubeError as pe:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not download video. Check to make sure the URL is correct."
            )
            print(pe)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except ValueError as ve:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                str(ve)
            )
            print(ve)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)


    def _video_download_completed(self):
        """Performs chores when the video download is complete"""
        self.progressBar.setValue(1) # do this first
        QMessageBox.about(self.dialog_window, "Success!", "Video download complete") # this second
        self.downloadStatusLabel.setText("") # this third
        self.downloadFolderBrowseButton.setEnabled(True)
        self.startButton.setEnabled(True)
        del self.thread

    
    def _playlist_download_completed(self):
        """Performs chores when the playlist download is complete"""
        QMessageBox.about(self.dialog_window, "Success!", "Playlist download complete")  # do this first
        self.downloadStatusLabel.setText("") # this second
        self.downloadFolderBrowseButton.setEnabled(True)
        self.startButton.setEnabled(True)
        del self.thread

   
    def videoPlaylistSelectCombobox_changed(self):
        """
        Handler for changing videoPlaylistSelectCombobox.

        Enables/disables the playlist range fields depending
        on whether or not a video or playlist is being downloaded.
        """
        user_selection: str = self.videoPlaylistSelectCombobox.currentText()
        if user_selection == "Video":
            self.startRangeSpinBox.setEnabled(False)
            self.stopRangeSpinBox.setEnabled(False)
        elif user_selection == "Playlist":
            self.startRangeSpinBox.setEnabled(True)
            self.stopRangeSpinBox.setEnabled(True)


class _VideoDownloaderThread(QThread):
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
            os.rename(audio, base + ".mp3")
        else:
            self.video.streams.get_highest_resolution().download(self.download_location)
        self.finished.emit()


class _PlaylistDownloaderThread(QThread):
    """Downloads a single playlist of videos"""
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
        for i, video in enumerate(self.playlist.videos[self.start_index-1 : self.stop_index]): 
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

            