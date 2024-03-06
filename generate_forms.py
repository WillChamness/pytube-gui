"""Genrate the Python boilerplate code for the QT form"""
import glob
import platform
import os
from PyQt6.uic import pyuic

try:
    os.mkdir("./pytube_gui/form_ui")
except FileExistsError:
    pass

with open("./pytube_gui/form_ui/__init__.py", "w") as f:
    f.write("")

for ui_file in glob.glob("./qt-forms/*.ui"):
    file_name = ui_file.split("\\" if platform.system() == "Windows" else "/")[-1] # e.g. from "./qt-forms/form.ui", get "form.ui"
    destination_name = file_name.split(".ui")[0] + ".py" # *.ui to *.py
    pyuic.generate(ui_file, os.path.join(".", "pytube_gui", "form_ui", destination_name), 0, None) # convert *.ui to *.py

