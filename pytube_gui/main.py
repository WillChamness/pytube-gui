from PyQt6 import QtWidgets 
from .form_logic.pytube_form import PyTubeForm 

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    pythonYTDownloaderDialog = QtWidgets.QDialog()
    ui = PyTubeForm(pythonYTDownloaderDialog)
    pythonYTDownloaderDialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
