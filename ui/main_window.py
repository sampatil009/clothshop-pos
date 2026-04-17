from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QStackedWidget, QFrame, QLineEdit, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from fabricpos.ui.inventory import InventoryScreen
from fabricpos.ui.pos_screen import POSScreen
from fabricpos.ui.login import LoginScreen
from fabricpos.ui.theme import (PRIMARY, PRIMARY_CONT, SECONDARY, ON_SURFACE, 
                                ON_SURF_VAR, SURF_CARD, SURF_HIGH, SURF_LOW, 
                                NAV_BTN_STYLE, PRIMARY_BTN, SECONDARY_BTN, SIDEBAR_STYLE,
                                make_label, divider)

class Sidebar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("Sidebar")
        self.setFixedWidth(240) # Slightly wider for better breathing room
        self.setStyleSheet(SIDEBAR_STYLE)
        self.nav_buttons = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 24, 0, 24)
        lay.setSpacing(4)

        # Logo area
        logo_w = QWidget()
        logo_w.setStyleSheet("background: transparent; margin-bottom: 20px;")
        logo_lay = QHBoxLayout(logo_w)
        logo_lay.setContentsMargins(24, 0, 24, 0)
        logo_lay.setSpacing(12)

        logo_box = QLabel("F")
        logo_box.setFixedSize(40, 40)
        logo_box.setAlignment(Qt.AlignCenter)
        logo_box.setFont(QFont("Segoe UI", 16, QFont.Bold))
        logo_box.setStyleSheet(f"background: {SECONDARY}; color: #ffffff; border-radius: 10px;")

        logo_text = QWidget()
        logo_text.setStyleSheet("background: transparent;")
        lt_lay = QVBoxLayout(logo_text)
        lt_lay.setContentsMargins(0,0,0,0)
        lt_lay.setSpacing(0)
        
        # Explicitly set color for logo text to ensure visibility
        l1 = make_label("FabricPOS", 15, "#ffffff", bold=True)
        l2 = make_label("Cloth & Apparel", 10, "#94a3b8")
        lt_lay.addWidget(l1)
        lt_lay.addWidget(l2)

        logo_lay.addWidget(logo_box)
        logo_lay.addWidget(logo_text)
        lay.addWidget(logo_w)

        # Nav items (Using Segoe UI Symbol codes)
        # \ue149: Calculator, \ue188: Box, \ue161: Contact, \ue125: People, \ue19d: Graph, \ue115: Gear
        nav_items = [
            ("\ue149", "POS Dashboard", 0),
            ("\ue188", "Inventory", 1),
            ("\ue12a", "Accounting", 2), # Using \ue12a for Journal/Book
            ("\ue125", "CRM / Parties", 3),
            ("\ue19d", "Reports", 4),
            ("\ue115", "Settings", 5),
        ]
        
        icon_font = QFont("Segoe UI Symbol", 12)
        
        for icon_code, label, idx in nav_items:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setStyleSheet(NAV_BTN_STYLE)
            btn.setFixedHeight(48)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Create horizontal layout for button content
            btn_lay = QHBoxLayout(btn)
            btn_lay.setContentsMargins(16, 0, 16, 0)
            btn_lay.setSpacing(12)
            
            icon_lbl = QLabel(icon_code)
            icon_lbl.setFont(icon_font)
            icon_lbl.setStyleSheet("color: inherit; background: transparent;")
            
            text_lbl = QLabel(label)
            text_lbl.setStyleSheet("color: inherit; background: transparent; font-weight: inherit;")
            
            btn_lay.addWidget(icon_lbl)
            btn_lay.addWidget(text_lbl)
            btn_lay.addStretch()
            
            btn.clicked.connect(lambda checked, i=idx: self.main_window.switch_view(i))
            lay.addWidget(btn)
            self.nav_buttons.append(btn)

        lay.addStretch()
        
        # Bottom CTA Container
        bottom_w = QWidget()
        bottom_w.setStyleSheet("background: transparent; padding: 12px;")
        bottom_lay = QVBoxLayout(bottom_w)
        
        take_pay = QPushButton("Take Payment")
        take_pay.setFixedHeight(46)
        take_pay.setStyleSheet(SECONDARY_BTN)
        bottom_lay.addWidget(take_pay)
        
        lay.addWidget(bottom_w)
        
        # Set first active by default
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

class TopBar(QWidget):
    def __init__(self, title="POS Dashboard"):
        super().__init__()
        self.setFixedHeight(70) # Slightly taller for a more airy feel
        self.setStyleSheet(f"background: {SURF_CARD}; border-bottom: 1px solid {SURF_HIGH};")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(20)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold)) # Slightly larger
        self.title_lbl.setStyleSheet(f"color: {ON_SURFACE}; background: transparent;")
        lay.addWidget(self.title_lbl)
        lay.addStretch()

        # Modern Search bar with icon
        search_container = QWidget()
        search_container.setFixedWidth(260)
        search_container.setFixedHeight(40)
        search_container.setStyleSheet(f"background: {SURF_LOW}; border-radius: 20px;")
        s_lay = QHBoxLayout(search_container)
        s_lay.setContentsMargins(15, 0, 15, 0)
        
        search_icon = QLabel("\ue11a") # Search icon
        search_icon.setFont(QFont("Segoe UI Symbol", 10))
        search_icon.setStyleSheet(f"color: {ON_SURF_VAR};")
        s_lay.addWidget(search_icon)

        search = QLineEdit()
        search.setPlaceholderText("Search...")
        search.setStyleSheet(f"background: transparent; border: none; padding: 0; color: {ON_SURFACE};")
        s_lay.addWidget(search)
        lay.addWidget(search_container)

        # Notification button
        notif = QPushButton("\ue119") # Bell icon
        notif.setFixedSize(40, 40)
        notif.setFont(QFont("Segoe UI Symbol", 12))
        notif.setCursor(Qt.PointingHandCursor)
        notif.setStyleSheet(f"""
            QPushButton {{ 
                background: {SURF_LOW}; border-radius: 20px; color: {ON_SURF_VAR}; border: none; 
            }}
            QPushButton:hover {{ background: {SURF_HIGH}; color: {ON_SURFACE}; }}
        """)
        lay.addWidget(notif)

        # User Profile / Avatar
        self.avatar = QLabel("AD")
        self.avatar.setFixedSize(40, 40)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.avatar.setStyleSheet(f"background: {PRIMARY}; color: #ffffff; border-radius: 20px;")
        lay.addWidget(self.avatar)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FabricPOS | Atrium Boutique")
        self.setMinimumSize(1200, 800)
        
        self.wrapper_stack = QStackedWidget()
        self.setCentralWidget(self.wrapper_stack)
        
        # Dashboard Layer
        self.dashboard_widget = QWidget()
        dash_root = QHBoxLayout(self.dashboard_widget)
        dash_root.setContentsMargins(0, 0, 0, 0)
        dash_root.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = Sidebar(self)
        dash_root.addWidget(self.sidebar)
        
        # 2. Right Side Content
        right_container = QWidget()
        right_lay = QVBoxLayout(right_container)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)
        
        self.top_bar = TopBar()
        right_lay.addWidget(self.top_bar)
        
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(POSScreen())
        self.content_stack.addWidget(InventoryScreen())
        self.content_stack.addWidget(self.create_placeholder("Parties & Ledger"))
        self.content_stack.addWidget(self.create_placeholder("CRM / CRM Explorer"))
        self.content_stack.addWidget(self.create_placeholder("Reports Dashboard"))
        self.content_stack.addWidget(self.create_placeholder("Settings"))
        
        right_lay.addWidget(self.content_stack)
        dash_root.addWidget(right_container)
        
        # Add Layers to Root
        self.login_screen = LoginScreen(self)
        self.wrapper_stack.addWidget(self.login_screen)
        self.wrapper_stack.addWidget(self.dashboard_widget)
        
        self.wrapper_stack.setCurrentIndex(0) # Start with login

    def show_dashboard(self):
        self.wrapper_stack.setCurrentIndex(1)

    def switch_view(self, index):
        # Update sidebar buttons
        for i, btn in enumerate(self.sidebar.nav_buttons):
            btn.setChecked(i == index)
        
        # Update stack
        self.content_stack.setCurrentIndex(index)
        
        # Update TopBar title
        titles = ["POS Dashboard", "Inventory Management", "Accounting & Ledger", "CRM Explorer", "Performance Reports", "System Settings"]
        if index < len(titles):
            self.top_bar.title_lbl.setText(titles[index])

    def create_placeholder(self, text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 24px; color: {ON_SURF_VAR}; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return widget
