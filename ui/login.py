from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLineEdit, 
                             QLabel, QFrame, QMessageBox, QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from ui.theme import (PRIMARY, PRIMARY_DARK, PRIMARY_CONT, SECONDARY, ON_SURFACE, 
                        ON_SURF_VAR, SURFACE, SURF_LOW, SURF_CARD, SURF_HIGH, 
                        PRIMARY_BTN, CARD_STYLE, make_label, divider)

class LoginScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        # Using the same professional slate background as the POS
        self.setStyleSheet("background: #f8fafc;")
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # Center Login Card
        self.frame = QFrame()
        self.frame.setObjectName("LoginCard")
        self.frame.setFixedWidth(400)
        self.frame.setStyleSheet("QFrame#LoginCard { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; }")
        
        # Premium Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(12)
        shadow.setColor(QColor(15, 23, 42, 30)) # Slate 900 tint
        self.frame.setGraphicsEffect(shadow)

        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(40, 45, 40, 45)
        self.frame_layout.setSpacing(0)
        
        # 1. Branding Header
        # Logo Icon (Clean Slate look)
        logo_icon = QLabel("F")
        logo_icon.setFixedSize(54, 54)
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setFont(QFont("Segoe UI", 24, QFont.Bold))
        logo_icon.setStyleSheet(f"background: #0f172a; color: #ffffff; border-radius: 12px;")
        
        self.frame_layout.addWidget(logo_icon, 0, Qt.AlignCenter)
        self.frame_layout.addSpacing(20)
        
        title = QLabel("Welcome Back")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #011627; background: transparent; border: none;")
        title.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(title)
        
        subtitle = QLabel("Sign in to manage your boutique")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; background: transparent; border: none;")
        subtitle.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(subtitle)
        
        self.frame_layout.addSpacing(35)
        
        # 2. Form Fields (Compact Label-Field groups)
        def add_input_group(label, placeholder, is_pass=False):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #475569; font-size: 11px; text-transform: uppercase; margin-bottom: 4px;")
            self.frame_layout.addWidget(lbl)
            
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setFixedHeight(46)
            if is_pass:
                field.setEchoMode(QLineEdit.Password)
            field.setStyleSheet("""
                QLineEdit {
                    padding: 8px 15px; 
                    background: #f8fafc; 
                    border: 1px solid #e2e8f0; 
                    border-radius: 8px;
                    font-size: 14px;
                    color: #1e293b;
                }
                QLineEdit:focus {
                    border: 2px solid #0f172a;
                    background: #ffffff;
                }
            """)
            self.frame_layout.addWidget(field)
            self.frame_layout.addSpacing(18)
            return field

        self.username = add_input_group("Username", "Enter username")
        self.password = add_input_group("Password", "••••••••", is_pass=True)
        
        self.frame_layout.addSpacing(10)
        
        # 3. Actions
        self.login_btn = QPushButton("SIGN IN")
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: #0f172a; 
                color: white; 
                border-radius: 8px; 
                font-weight: bold; 
                font-size: 14px;
            }
            QPushButton:hover {
                background: #1e293b;
            }
            QPushButton:pressed {
                background: #000000;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        self.frame_layout.addWidget(self.login_btn)
        
        # 4. Footer
        self.frame_layout.addSpacing(30)
        footer = QLabel("FabricPOS Dashboard v1.0.0")
        footer.setStyleSheet("font-size: 11px; color: #94a3b8;")
        footer.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(footer)
        
        self.layout.addWidget(self.frame)

    def handle_login(self):
        if self.username.text() == "admin" and self.password.text() == "admin":
            self.main_window.show_dashboard()
        else:
            QMessageBox.warning(self, "Failed", "Invalid username or password")
