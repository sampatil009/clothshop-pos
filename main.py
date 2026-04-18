import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from services.db import init_db
from ui.main_window import MainWindow
from ui.theme import APP_STYLE

def main():
    # Initialize Database
    init_db()
    
    # Start App
    app = QApplication(sys.argv)
    
    # Set Global Font
    app.setFont(QFont("Segoe UI", 10))
    
    # Set App-wide Style (Premium Atrium Theme)
    app.setStyleSheet(APP_STYLE)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
