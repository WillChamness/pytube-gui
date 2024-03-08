@echo off
pyinstaller --onefile --windowed --name "Pytube-GUI-Onefile"  run.py
pyinstaller --windowed --name "Pytube-GUI" run.py