import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Add parent directory of 'fabricpos' to path to resolve absolute imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from fabricpos.services.db import init_db
from fabricpos.ui.main_window import MainWindow
from fabricpos.ui.theme import APP_STYLE

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
