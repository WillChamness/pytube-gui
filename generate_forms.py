"""Genrate the Python boilerplate code for the QT form"""
import glob
import platform
import os
from PyQt6.uic import pyuic

try:
    os.mkdir("./pytube_gui/form_ui")
except FileExistsError:
    pass

try:
    os.remove("./pytube_gui/form_ui/resources.py")
except FileNotFoundError:
    pass

try:    
    os.chdir("./resources")
    os.system("pyside6-rcc -o resources.py resources.qrc") # PyQt6 doesn't have rcc, use pyside instead
    os.chdir("..")
    os.rename("./resources/resources.py", "./pytube_gui/form_ui/resources.py")
    with open("./pytube_gui/form_ui/resources.py", "r") as f:
        lines = f.readlines()
    with open("./pytube_gui/form_ui/resources.py", "w") as f:
        for line in lines:
            if "from PySide6 import QtCore" in line:
                f.write("from PyQt6 import QtCore # auto changed to import PyQt6 instead of PySide6\n")
            else:
                f.write(line)
except FileNotFoundError:
    print("File not found. Exiting...")
    exit()

for ui_file in glob.glob("./qt-forms/*.ui"):
    file_name = ui_file.split("\\" if platform.system() == "Windows" else "/")[-1] # e.g. from "./qt-forms/form.ui", get "form.ui"
    destination_name = file_name.split(".ui")[0] + ".py" # *.ui to *.py
    pyuic.generate(ui_file, os.path.join(".", "pytube_gui", "form_ui", destination_name), 0, None) # convert *.ui to *.py

