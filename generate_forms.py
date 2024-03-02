"""Genrate the Python boilerplate code for the QT form"""
import glob
from PyQt6.uic import pyuic

for ui_file in glob.glob("./qt-forms/*.ui"):
    file_name = ui_file.split("/")[-1] # e.g. from "./qt-forms/form.ui", get "form.ui"
    destination_name = file_name.split(".ui")[0] + ".py" # *.ui to *.py
    pyuic.generate(ui_file, f"./pytube_gui/form_ui/{destination_name}", 0, None) # convert *.ui to *.py

