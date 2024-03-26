@echo off
pyinstaller --onefile --windowed --icon=resources/pytube-logo.ico --name "Pytube-GUI-Onefile"  run.py
pyinstaller --windowed --icon=resources/pytube-logo.ico --name "Pytube-GUI" --noconfirm run.py