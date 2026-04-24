from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QStackedWidget, QFrame, QLineEdit, 
                             QListWidget, QListWidgetItem, QGridLayout, 
                             QComboBox, QTextEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
from ui.theme import (PRIMARY, SECONDARY, ON_SURFACE, ON_SURF_VAR, 
                        SURF_CARD, SURF_HIGH, SURF_LOW, OUTLINE, 
                        NAV_BTN_STYLE, PRIMARY_BTN, SECONDARY_BTN, GHOST_BTN, CARD_STYLE,
                        make_label, divider, card)
from services.db import (get_db, BusinessProfileModel, UserModel, RoleModel, 
                         PrinterSettingsModel, InvoiceSettingsModel, WhatsAppLogModel)
from datetime import datetime

class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("SettingsScreen")
        self.db = get_db()
        self._build_ui()
        self.load_all_data()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(f"background: {SURF_CARD}; border-right: 1px solid {SURF_HIGH};")
        sidebar_lay = QVBoxLayout(self.sidebar)
        sidebar_lay.setContentsMargins(12, 24, 12, 24)
        sidebar_lay.setSpacing(8)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(f"""
            QListWidget {{ border: none; background: transparent; outline: none; }}
            QListWidget::item {{ padding: 12px 16px; border-radius: 8px; color: {ON_SURF_VAR}; font-weight: 500; margin-bottom: 4px; }}
            QListWidget::item:selected {{ background: {SURF_LOW}; color: {PRIMARY}; font-weight: 600; }}
            QListWidget::item:hover {{ background: {SURF_LOW}; }}
        """)

        categories = [
            ("Business Profile", "\ue115"),
            ("Administration", "\ue125"),
            ("Printer Settings", "\ue149"),
            ("WhatsApp Settings", "\ue170"),
            ("Invoice Settings", "\ue12a")
        ]

        for text, icon in categories:
            item = QListWidgetItem(text)
            item.setFont(QFont("Segoe UI", 10))
            self.nav_list.addItem(item)

        sidebar_lay.addWidget(make_label("CATEGORIES", 10, ON_SURF_VAR, bold=True))
        sidebar_lay.addWidget(self.nav_list)
        sidebar_lay.addStretch()

        main_layout.addWidget(self.sidebar)

        # Right Content Area
        self.content_stack = QStackedWidget()
        
        # Add Pages
        self.content_stack.addWidget(self._create_business_page())
        self.content_stack.addWidget(self._create_admin_page())
        self.content_stack.addWidget(self._create_printer_page())
        self.content_stack.addWidget(self._create_whatsapp_page())
        self.content_stack.addWidget(self._create_invoice_page())

        main_layout.addWidget(self.content_stack)

        self.nav_list.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    def _create_business_page(self):
        page = QScrollArea()
        page.setWidgetResizable(True)
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(24)

        lay.addWidget(make_label("Business Profile", 22, PRIMARY, bold=True))
        lay.addWidget(make_label("Manage your shop details and contact information.", 11, ON_SURF_VAR))
        
        form_card = card()
        form_lay = QGridLayout(form_card)
        form_lay.setContentsMargins(24, 24, 24, 24)
        form_lay.setSpacing(20)

        # Business Name
        form_lay.addWidget(make_label("Business Name", 10, bold=True), 0, 0)
        self.biz_name = QLineEdit()
        form_lay.addWidget(self.biz_name, 1, 0)

        # Contact Number
        form_lay.addWidget(make_label("Contact Number", 10, bold=True), 0, 1)
        self.biz_phone = QLineEdit()
        form_lay.addWidget(self.biz_phone, 1, 1)

        # Email
        form_lay.addWidget(make_label("Business Email", 10, bold=True), 2, 0)
        self.biz_email = QLineEdit()
        form_lay.addWidget(self.biz_email, 3, 0)

        # Website
        form_lay.addWidget(make_label("Website", 10, bold=True), 2, 1)
        self.biz_web = QLineEdit()
        form_lay.addWidget(self.biz_web, 3, 1)

        # Address
        form_lay.addWidget(make_label("Address", 10, bold=True), 4, 0, 1, 2)
        self.biz_addr = QTextEdit()
        self.biz_addr.setMaximumHeight(80)
        self.biz_addr.setStyleSheet(f"border: 1px solid {OUTLINE}; border-radius: 4px; padding: 8px;")
        form_lay.addWidget(self.biz_addr, 5, 0, 1, 2)

        lay.addWidget(form_card)

        # Buttons
        btn_lay = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet(SECONDARY_BTN)
        save_btn.setFixedWidth(150)
        save_btn.clicked.connect(self.save_business_profile)
        btn_lay.addStretch()
        btn_lay.addWidget(save_btn)
        lay.addLayout(btn_lay)
        
        lay.addStretch()
        page.setWidget(container)
        return page

    def _create_admin_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(24)

        lay.addWidget(make_label("Administration", 22, PRIMARY, bold=True))
        
        # User Table Card
        user_card = card()
        user_lay = QVBoxLayout(user_card)
        user_lay.setContentsMargins(0,0,0,0)
        
        self.user_table = QTableWidget(0, 4)
        self.user_table.setHorizontalHeaderLabels(["Username", "Role", "Last Login", "Action"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        user_lay.addWidget(self.user_table)
        lay.addWidget(user_card)
        
        add_user_btn = QPushButton("+ Add New User")
        add_user_btn.setStyleSheet(PRIMARY_BTN)
        add_user_btn.setFixedWidth(150)
        lay.addWidget(add_user_btn)

        lay.addStretch()
        return page

    def _create_printer_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(24)

        lay.addWidget(make_label("Printer Settings", 22, PRIMARY, bold=True))
        
        printer_card = card()
        pc_lay = QVBoxLayout(printer_card)
        pc_lay.setContentsMargins(24, 24, 24, 24)
        pc_lay.setSpacing(20)

        pc_lay.addWidget(make_label("Default Printer", 10, bold=True))
        self.printer_combo = QComboBox()
        # In a real app, we'd list actual system printers here
        self.printer_combo.addItems(["Microsoft Print to PDF", "OneNote", "EPSON TM-T88VI", "Brother QL-800"])
        pc_lay.addWidget(self.printer_combo)

        pc_lay.addWidget(make_label("Paper Size", 10, bold=True))
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["80mm Thermal", "58mm Thermal", "A4", "A5"])
        pc_lay.addWidget(self.paper_combo)

        save_btn = QPushButton("Save Printer Settings")
        save_btn.setStyleSheet(SECONDARY_BTN)
        save_btn.clicked.connect(self.save_printer_settings)
        pc_lay.addWidget(save_btn)

        lay.addWidget(printer_card)
        lay.addStretch()
        return page

    def _create_whatsapp_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(24)

        lay.addWidget(make_label("WhatsApp Settings", 22, PRIMARY, bold=True))
        
        # Stats Dashboard
        stats_lay = QHBoxLayout()
        stats_lay.setSpacing(20)
        
        self.stat_msg_sent = make_label("0", 20, PRIMARY, bold=True)
        self.stat_campaigns = make_label("0", 20, SECONDARY, bold=True)
        
        def create_stat_card(title, label_obj):
            c = card()
            c_lay = QVBoxLayout(c)
            c_lay.addWidget(make_label(title, 10, ON_SURF_VAR))
            c_lay.addWidget(label_obj)
            return c

        stats_lay.addWidget(create_stat_card("Messages Sent", self.stat_msg_sent))
        stats_lay.addWidget(create_stat_card("Successful Deliveries", self.stat_campaigns))
        lay.addLayout(stats_lay)

        # Options
        options_card = card()
        opt_lay = QVBoxLayout(options_card)
        opt_lay.setContentsMargins(0, 0, 0, 0)
        
        opts = ["Message Templates", "Campaign History", "Auto-Responder Settings"]
        for opt in opts:
            btn = QPushButton(opt)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; border-bottom: 1px solid {SURF_HIGH}; padding: 16px 24px; text-align: left; color: {ON_SURFACE}; font-size: 14px; }}
                QPushButton:hover {{ background: {SURF_LOW}; }}
            """)
            opt_lay.addWidget(btn)
            
        lay.addWidget(options_card)
        lay.addStretch()
        return page

    def _create_invoice_page(self):
        page = QScrollArea()
        page.setWidgetResizable(True)
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(24)

        lay.addWidget(make_label("Invoice Settings", 22, PRIMARY, bold=True))
        
        format_card = card()
        f_lay = QVBoxLayout(format_card)
        f_lay.setContentsMargins(24, 24, 24, 24)
        f_lay.setSpacing(16)

        f_lay.addWidget(make_label("Header Text", 10, bold=True))
        self.inv_header = QTextEdit()
        self.inv_header.setMaximumHeight(60)
        f_lay.addWidget(self.inv_header)

        f_lay.addWidget(make_label("Footer Text", 10, bold=True))
        self.inv_footer = QTextEdit()
        self.inv_footer.setMaximumHeight(60)
        f_lay.addWidget(self.inv_footer)

        f_lay.addWidget(make_label("Font Size", 10, bold=True))
        self.inv_font = QComboBox()
        self.inv_font.addItems(["Small (8pt)", "Normal (10pt)", "Large (12pt)"])
        f_lay.addWidget(self.inv_font)

        lay.addWidget(format_card)
        
        save_btn = QPushButton("Save Bill Format")
        save_btn.setStyleSheet(SECONDARY_BTN)
        save_btn.clicked.connect(self.save_invoice_settings)
        lay.addWidget(save_btn)

        lay.addStretch()
        page.setWidget(container)
        return page

    # --- DATA LOADING ---
    def load_all_data(self):
        self.load_business_profile()
        self.load_users()
        self.load_printer_settings()
        self.load_whatsapp_stats()
        self.load_invoice_settings()

    def load_business_profile(self):
        profile = self.db.query(BusinessProfileModel).first()
        if profile:
            self.biz_name.setText(profile.name or "")
            self.biz_phone.setText(profile.phone or "")
            self.biz_email.setText(profile.email or "")
            self.biz_web.setText(profile.website or "")
            self.biz_addr.setText(profile.address or "")

    def load_users(self):
        users = self.db.query(UserModel).all()
        self.user_table.setRowCount(len(users))
        for i, user in enumerate(users):
            self.user_table.setItem(i, 0, QTableWidgetItem(user.username))
            self.user_table.setItem(i, 1, QTableWidgetItem(user.role.name if user.role else "N/A"))
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
            self.user_table.setItem(i, 2, QTableWidgetItem(last_login))
            self.user_table.setItem(i, 3, QTableWidgetItem("Edit"))

    def load_printer_settings(self):
        settings = self.db.query(PrinterSettingsModel).first()
        if settings:
            idx = self.printer_combo.findText(settings.printer_name)
            if idx >= 0: self.printer_combo.setCurrentIndex(idx)
            
            idx = self.paper_combo.findText(settings.paper_size)
            if idx >= 0: self.paper_combo.setCurrentIndex(idx)

    def load_whatsapp_stats(self):
        total = self.db.query(WhatsAppLogModel).count()
        success = self.db.query(WhatsAppLogModel).filter_by(status="sent").count()
        self.stat_msg_sent.setText(str(total))
        self.stat_campaigns.setText(str(success))

    def load_invoice_settings(self):
        settings = self.db.query(InvoiceSettingsModel).first()
        if settings:
            self.inv_header.setText(settings.header_text or "")
            self.inv_footer.setText(settings.footer_text or "")
            idx = self.inv_font.findText(settings.font_size)
            if idx >= 0: self.inv_font.setCurrentIndex(idx)

    # --- SAVE LOGIC ---
    def save_business_profile(self):
        profile = self.db.query(BusinessProfileModel).first()
        if not profile:
            profile = BusinessProfileModel()
            self.db.add(profile)
        
        profile.name = self.biz_name.text()
        profile.phone = self.biz_phone.text()
        profile.email = self.biz_email.text()
        profile.website = self.biz_web.text()
        profile.address = self.biz_addr.toPlainText()
        
        self.db.commit()
        QMessageBox.information(self, "Success", "Business profile updated successfully!")

    def save_printer_settings(self):
        settings = self.db.query(PrinterSettingsModel).first()
        if not settings:
            settings = PrinterSettingsModel()
            self.db.add(settings)
            
        settings.printer_name = self.printer_combo.currentText()
        settings.paper_size = self.paper_combo.currentText()
        
        self.db.commit()
        QMessageBox.information(self, "Success", "Printer settings updated!")

    def save_invoice_settings(self):
        settings = self.db.query(InvoiceSettingsModel).first()
        if not settings:
            settings = InvoiceSettingsModel()
            self.db.add(settings)
            
        settings.header_text = self.inv_header.toPlainText()
        settings.footer_text = self.inv_footer.toPlainText()
        settings.font_size = self.inv_font.currentText()
        
        self.db.commit()
        QMessageBox.information(self, "Success", "Invoice format saved!")
        
    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
