from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QFrame, QMessageBox, QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from fabricpos.ui.theme import (PRIMARY, SURFACE, SURF_CARD, PRIMARY_BTN, 
                                ON_SURFACE, ON_SURF_VAR, SECONDARY, make_label)

class LoginScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background: {SURFACE};")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # Center Card
        self.frame = QFrame()
        self.frame.setFixedSize(400, 480)
        self.frame.setStyleSheet(f"background-color: {SURF_CARD}; border-radius: 16px; border: 1px solid #e2e8f0;")
        
        # Add Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.frame.setGraphicsEffect(shadow)

        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(40, 50, 40, 50)
        self.frame_layout.setSpacing(12)
        
        # Logo Icon
        logo_icon = QLabel("F")
        logo_icon.setFixedSize(50, 50)
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setFont(QFont("Segoe UI", 20, QFont.Bold))
        logo_icon.setStyleSheet(f"background: {PRIMARY}; color: #ffffff; border-radius: 12px; margin-bottom: 5px;")
        
        self.frame_layout.addWidget(logo_icon, 0, Qt.AlignCenter)
        
        # Title
        title = make_label("Welcome Back", 20, ON_SURFACE, bold=True)
        title.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(title)
        
        subtitle = make_label("Sign in to manage your boutique", 12, ON_SURF_VAR)
        subtitle.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(subtitle)
        
        self.frame_layout.addSpacing(20)
        
        # Inputs
        self.frame_layout.addWidget(make_label("Username", 11, ON_SURF_VAR, bold=True))
        self.username = QLineEdit()
        self.username.setPlaceholderText("admin")
        self.username.setFixedHeight(45)
        self.frame_layout.addWidget(self.username)
        
        self.frame_layout.addSpacing(8)
        
        self.frame_layout.addWidget(make_label("Password", 11, ON_SURF_VAR, bold=True))
        self.password = QLineEdit()
        self.password.setPlaceholderText("••••••••")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setFixedHeight(45)
        self.frame_layout.addWidget(self.password)
        
        self.frame_layout.addSpacing(20)
        
        self.login_btn = QPushButton("SIGN IN")
        self.login_btn.setFixedHeight(48)
        self.login_btn.setStyleSheet(PRIMARY_BTN)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        self.frame_layout.addWidget(self.login_btn)
        
        # Footer
        footer = make_label("FabricPOS v1.0.0", 10, "#94a3b8")
        footer.setAlignment(Qt.AlignCenter)
        self.frame_layout.addStretch()
        self.frame_layout.addWidget(footer)
        
        self.layout.addWidget(self.frame)

    def handle_login(self):
        if self.username.text() == "admin" and self.password.text() == "admin":
            self.main_window.show_dashboard()
        else:
            QMessageBox.warning(self, "Failed", "Invalid username or password")
