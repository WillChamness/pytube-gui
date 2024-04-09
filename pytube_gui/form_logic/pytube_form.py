import os
import platform

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from pytube import exceptions as pytube_exceptions

from ..form_ui.pytube_form import \
    Ui_pythonYTDownloaderForm as MainFormUi  # created from pyuic
from .downloaders import *


class PyTubeForm(MainFormUi):

    def __init__(self, current_dialog: QtWidgets.QDialog):
        """Form Constructor"""
        super().__init__()
        self.thread: QThread
        # setup UI before defining logic
        self.dialog_window: QtWidgets.QDialog = current_dialog
        self.setupUi(self.dialog_window)
        # define UI logic here
        self._on_form_load()
        self.cancelButton.clicked.connect(QtWidgets.QApplication.quit)
        self.startButton.clicked.connect(self.startButton_clicked)
        self.downloadFolderBrowseButton.clicked.connect(
            self.downloadFolderBrowseButton_clicked
        )
        self.videoPlaylistSelectCombobox.currentIndexChanged.connect(
            self.videoPlaylistSelectCombobox_changed
        )
        self.downloadAllAvailableCheckbox.stateChanged.connect(
            self.downloadAllAvailableCheckbox_changed
        )

    def _on_form_load(self):
        """When the form loads, do various chores."""
        home_download_directory = os.path.join(os.path.expanduser("~"), "Downloads")
        if platform.system != "Windows":
            try:
                os.mkdir(
                    home_download_directory
                )  # might not exist in some linux distros
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
        elif user_selection == "Captions":
            self._download_captions()
        else:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not decide if 'Video' or 'Playlist' selected",
            )

    def downloadFolderBrowseButton_clicked(self):
        """
        Handler for clicking downloadFolderBrowseButton.

        Opens a file dialog to select a directory.
        """
        download_location = QFileDialog.getExistingDirectory(
            self.dialog_window, "Select folder"
        )
        download_location_transformed = os.path.abspath(
            download_location
        )  # e.g. transform "C:/my/path" to "C:\my\path"
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
            self.thread = VideoDownloaderThread(url, download_location, audio_only)
            # update UI when download starts and ends
            self.thread.initialized.connect(self.downloadStatusLabel.setText)
            self.thread.finished.connect(self._video_download_completed)

            # start the thread
            self.thread.start()

        except pytube_exceptions.RegexMatchError as rme:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not find video. Check to make sure the URL is correct.",
            )
            print(rme)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.PytubeError as pe:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not download video. Check to make sure the URL is correct.",
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
        start_index = (
            self.startRangeSpinBox.value()
            if not self.downloadAllAvailableCheckbox.isChecked()
            else -1
        )
        stop_index = (
            self.stopRangeSpinBox.value()
            if not self.downloadAllAvailableCheckbox.isChecked()
            else -1
        )

        if start_index > stop_index:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Start value is greater than stop value",
            )
            return

        self.progressBar.setValue(0)
        self.progressBar.repaint()
        # prevent user from initiating download while current download is running
        self.startButton.setEnabled(False)
        self.downloadFolderBrowseButton.setEnabled(False)

        # attempt to download videos
        try:
            assert url is not None and url != ""
            # create new thread to download videos to prevent UI from freezing
            self.thread = PlaylistDownloaderThread(
                url, download_base_path, audio_only, start_index, stop_index
            )
            # tell the main thread to update UI when progress is made
            self.thread.initialized.connect(self.progressBar.setMaximum)
            self.thread.next_video_title.connect(self.downloadStatusLabel.setText)
            self.thread.progress.connect(self.progressBar.setValue)
            self.thread.finished.connect(self._playlist_download_completed)

            # begin the download
            self.thread.start()

        except FileExistsError as fee:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "A folder already exists for the playlist",
            )
            print(fee)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.RegexMatchError as rme:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not find playlist. Check to make sure the URL is correct.",
            )
            print(rme)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.PytubeError as pe:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not download video. Check to make sure the URL is correct.",
            )
            print(pe)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except AssertionError as ae:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not find playlist. Check to make sure the URL is correct.",
            )
            print(ae)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except ValueError as ve:
            QMessageBox.critical(self.dialog_window, "Something went wrong", str(ve))
            print(ve)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)

    def _download_captions(self):
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
            self.thread = CaptionsDownloaderThread(url, download_location)
            # update UI when download starts and ends
            self.thread.initialized.connect(self.downloadStatusLabel.setText)
            self.thread.finished.connect(self._captions_download_completed)

            # start the thread
            self.thread.start()

        except pytube_exceptions.RegexMatchError as rme:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not find video. Check to make sure the URL is correct.",
            )
            print(rme)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)
        except pytube_exceptions.PytubeError as pe:
            QMessageBox.critical(
                self.dialog_window,
                "Something went wrong",
                "Could not download captions. Maybe no captions are available?",
            )
            print(pe)
            self.startButton.setEnabled(True)
            self.downloadFolderBrowseButton.setEnabled(True)

    def _video_download_completed(self):
        """Performs chores when the video download is complete"""
        self.progressBar.setValue(1)  # do this first
        QMessageBox.information(
            self.dialog_window, "Success!", "Video download complete"
        )  # this second
        self.downloadStatusLabel.setText("")  # this third
        self.downloadFolderBrowseButton.setEnabled(True)
        self.startButton.setEnabled(True)
        del self.thread

    def _playlist_download_completed(self):
        """Performs chores when the playlist download is complete"""
        QMessageBox.information(
            self.dialog_window, "Success!", "Playlist download complete"
        )  # do this first
        self.downloadStatusLabel.setText("")  # this second
        self.downloadFolderBrowseButton.setEnabled(True)
        self.startButton.setEnabled(True)
        del self.thread

    def _captions_download_completed(self):
        """Performs chores when the captions download is complete"""
        self.progressBar.setValue(1)  # do this first
        QMessageBox.information(
            self.dialog_window, "Success!", "Caption download complete"
        )  # this second
        self.downloadStatusLabel.setText("")  # this third
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
            self.downloadAllAvailableCheckbox.setEnabled(False)
            self.startRangeSpinBox.setEnabled(False)
            self.stopRangeSpinBox.setEnabled(False)
            self.audioOnlyCheckbox.setEnabled(True)
        elif user_selection == "Playlist":
            self.downloadAllAvailableCheckbox.setEnabled(True)
            self.audioOnlyCheckbox.setEnabled(True)
            if self.downloadAllAvailableCheckbox.isChecked():
                self.startRangeSpinBox.setEnabled(False)
                self.stopRangeSpinBox.setEnabled(False)
            else:
                self.startRangeSpinBox.setEnabled(True)
                self.stopRangeSpinBox.setEnabled(True)
        elif user_selection == "Captions":
            self.downloadAllAvailableCheckbox.setEnabled(False)
            self.startRangeSpinBox.setEnabled(False)
            self.stopRangeSpinBox.setEnabled(False)
            self.audioOnlyCheckbox.setEnabled(False)

    def downloadAllAvailableCheckbox_changed(self):
        if self.downloadAllAvailableCheckbox.isChecked():
            self.startRangeSpinBox.setEnabled(False)
            self.stopRangeSpinBox.setEnabled(False)
        else:
            self.startRangeSpinBox.setEnabled(True)
            self.stopRangeSpinBox.setEnabled(True)
