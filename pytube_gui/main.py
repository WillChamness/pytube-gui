import sys
import platform
from PyQt6 import QtWidgets, QtGui
from .form_logic.pytube_form import PyTubeForm 
from .form_ui import resources

def main():
    if platform.system() == "Windows":
        import ctypes
        app_id = "pytube-gui"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    app = QtWidgets.QApplication(sys.argv)
    pythonYTDownloaderDialog = QtWidgets.QDialog()
    pythonYTDownloaderDialog.setWindowIcon(QtGui.QIcon(":/icons/application-icon.ico"))
    ui = PyTubeForm(pythonYTDownloaderDialog)
    pythonYTDownloaderDialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
