import os
from pytube import YouTube, Playlist
from ..form_ui.pytube_form import Ui_pythonYTDownloaderForm as MainFormUi # created from pyuic
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox, QFileDialog

class PyTubeForm(MainFormUi):
    def __init__(self, current_dialog: QtWidgets.QDialog):
        """Form Constructor"""
        super().__init__()
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
        self.downloadFolderTextbox.setText(os.path.expanduser("~/Downloads"))
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
        self.downloadFolderTextbox.setText(download_location)
        
  
    def _download_video(self):
        """Downloads a single video and saves it to the destination directory."""
        audio_only: bool = self.audioOnlyCheckbox.isChecked()
        download_location: str = self.downloadFolderTextbox.text()
        url: str = self.urlTextbox.text()

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1)
        self.progressBar.setValue(0)

        try:
            video: YouTube = YouTube(url)
            self.downloadStatusLabel.setText(f"Downloading: {video.title}")
            self.downloadStatusLabel.repaint()
            if audio_only:
                audio = video.streams.filter(only_audio=True).first().download(output_path=download_location)
                # rename to .mp3
                base, ext = os.path.splitext(audio)
                os.rename(audio, base + ".mp3")
            else:
                video.streams.get_highest_resolution().download(download_location)
        except Exception as e:
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Could not download video. Check to make sure the URL is correct.")
            print(e)
            return

        self.progressBar.setValue(1)
        QMessageBox.about(self.dialog_window, "Success!", "Video download complete!")
        self.downloadStatusLabel.setText("")
        self.downloadStatusLabel.repaint()


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

        self.progressBar.setMaximum(stop_index - start_index + 1)
        self.progressBar.setValue(0)
        self.progressBar.repaint()

        if start_index > stop_index:
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Start value is greater than stop value")
            return

        # attempt to download videos
        try:
            playlist = Playlist(url)
            if start_index > len(playlist.videos) or stop_index > len(playlist.videos):
                QMessageBox.critical(
                    self.dialog_window, 
                    "Something went wrong", 
                    "Start or stop value is too big")
                return
            download_location: str = os.path.join(download_base_path, playlist.title)
            os.mkdir(download_location)

            for i, video in enumerate(playlist.videos):
                if i+1 < start_index:
                    continue
                if i+1 > stop_index: 
                    break

                self.downloadStatusLabel.setText(f"Downloading: {video.title}")
                self.downloadStatusLabel.repaint()

                if audio_only:
                    audio = video.streams.filter(only_audio=True).first().download(output_path=download_location)
                    # rename to .mp3
                    base, ext = os.path.splitext(audio)
                    os.rename(audio, base + ".mp3")
                else:
                    video.streams.get_highest_resolution().download(download_location)
                self.progressBar.setValue(self.progressBar.value() + 1)
                self.progressBar.repaint()
        except FileExistsError as fee: # directory already exists
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "A folder already exists for the playlist")
            print(fee)
            return
        except Exception as e:
            QMessageBox.critical(
                self.dialog_window, 
                "Something went wrong", 
                "Could not download video. Check to make sure the URL is correct.")
            print(e)
            return

        QMessageBox.about(self.dialog_window, "Success!", "Playlist download complete!")
        self.downloadStatusLabel.setText("")
        self.downloadStatusLabel.repaint()


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

