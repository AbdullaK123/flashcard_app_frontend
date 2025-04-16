import sys
from PyQt6.QtWidgets import QApplication
from src.core.app import FlashCardApp

def main():

    # create the QApplication instance (the beating heart of the app)
    q_app = QApplication(sys.argv)

    # create the mainwindow
    app = FlashCardApp()
    app.show()

    # run the app until its closed 
    sys.exit(q_app.exec())


if __name__ == "__main__":
    main()