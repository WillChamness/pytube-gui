from PyQt6 import QtWidgets, QtGui
from .form_logic.pytube_form import PyTubeForm 

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    pythonYTDownloaderDialog = QtWidgets.QDialog()
    pythonYTDownloaderDialog.setWindowIcon(QtGui.QIcon("./pytube_gui/form_ui/pytube-logo.ico"))
    ui = PyTubeForm(pythonYTDownloaderDialog)
    pythonYTDownloaderDialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
