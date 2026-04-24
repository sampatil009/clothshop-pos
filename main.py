import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QTextEdit, QTableWidget, QAbstractItemView, QListWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject, QEvent, Qt

from services.db import init_db
from ui.main_window import MainWindow
from ui.theme import APP_STYLE

class GlobalKeyboardNavigation(QObject):
    """
    Globally translates Enter and Up/Down arrow keys into Tab/Shift+Tab focus navigation
    while respecting native uses in ComboBoxes, Tables, and Multiline inputs.
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            
            # Identify widget type to preserve native navigation
            parent = obj.parent() if hasattr(obj, "parent") else None
            is_table = isinstance(obj, QTableWidget) or isinstance(parent, QTableWidget)
            is_textedit = isinstance(obj, QTextEdit)
            is_button = isinstance(obj, QPushButton)
            is_popup = isinstance(obj, QAbstractItemView) or isinstance(obj, QListWidget)
            has_dropdown = obj.property("has_dropdown") is True  # Custom search fields handle own nav

            if key in (Qt.Key_Return, Qt.Key_Enter):
                if is_button:
                    obj.click()
                    return True
                elif not is_textedit and not has_dropdown and hasattr(obj, "focusNextChild"):
                    obj.focusNextChild()
                    return True
                    
            elif key == Qt.Key_Down:
                if not (is_table or is_textedit or is_popup or has_dropdown) and hasattr(obj, "focusNextChild"):
                    obj.focusNextChild()
                    return True
                    
            elif key == Qt.Key_Up:
                if not (is_table or is_textedit or is_popup or has_dropdown) and hasattr(obj, "focusPreviousChild"):
                    obj.focusPreviousChild()
                    return True

        return super().eventFilter(obj, event)

def main():
    # Initialize Database
    init_db()
    
    # Start App
    app = QApplication(sys.argv)
    
    # Set Global Font
    app.setFont(QFont("Segoe UI", 10))
    
    # Set App-wide Style (Premium Atrium Theme)
    app.setStyleSheet(APP_STYLE)
    
    # Install Keyboard Navigation
    nav_filter = GlobalKeyboardNavigation(app)
    app.installEventFilter(nav_filter)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
