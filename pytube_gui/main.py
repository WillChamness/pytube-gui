from PyQt6 import QtWidgets 
from .form_logic.pytube_form import PyTubeForm 

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    pythonYTDownloaderForm = QtWidgets.QDialog()
    ui = PyTubeForm(pythonYTDownloaderForm)
    pythonYTDownloaderForm.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
