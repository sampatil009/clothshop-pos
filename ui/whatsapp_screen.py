"""
ui/whatsapp_screen.py
──────────────────────
WhatsApp messaging screen for FabricPOS.
Features:
  • Send invoice message to any party
  • Send payment due reminders (bulk or single)
  • Compose custom message
  • View full send history
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QComboBox, QMessageBox, QDialog,
    QFormLayout, QAbstractItemView, QScrollArea, QTabWidget, QListView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import get_db, PartyModel, InvoiceModel
from services.whatsapp_service import WhatsAppService
from ui.theme import (
    PRIMARY, SECONDARY, TERTIARY, ON_SURFACE, ON_SURF_VAR,
    SURFACE, SURF_CARD, SURF_LOW, SURF_HIGH, ERROR_BG, SUCCESS_BG,
    WARN_BG, SEC_CONTAINER, PRIMARY_BTN, GHOST_BTN, CARD_STYLE,
    make_label, divider, status_pill
)


# ── Background thread for sending (keeps UI responsive) ──────────────────────
class SendThread(QThread):
    result = pyqtSignal(dict)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn     = fn
        self.args   = args
        self.kwargs = kwargs

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.result.emit(res)
        except Exception as e:
            self.result.emit({"success": False, "message": str(e)})


# ── Dialog: Contact Selection ────────────────────────────────────────────────
class ContactSelectionDialog(QDialog):
    def __init__(self, contacts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Contact from History")
        self.setFixedSize(600, 700)
        self.setStyleSheet(f"background: {SURFACE};")
        self.selected_contacts = []
        self.all_contacts = contacts
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        hdr = QHBoxLayout()
        hdr.addWidget(make_label("Search Contacts", 15, ON_SURFACE, bold=True))
        hdr.addStretch()
        
        self.sel_all_btn = QPushButton("Select All")
        self.sel_all_btn.setFixedWidth(100)
        self.sel_all_btn.setStyleSheet(GHOST_BTN)
        self.sel_all_btn.clicked.connect(self._select_all)
        hdr.addWidget(self.sel_all_btn)
        lay.addLayout(hdr)
        
        # Search box
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or phone...")
        self.search.setFixedHeight(40)
        self.search.textChanged.connect(self._filter_table)
        lay.addWidget(self.search)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["NAME", "PHONE", "SOURCE"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        lay.addWidget(self.table)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setFixedSize(100, 36)
        cancel.setStyleSheet(GHOST_BTN)
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)

        self.pick_btn = QPushButton("Confirm Selection")
        self.pick_btn.setFixedSize(160, 36)
        self.pick_btn.setStyleSheet(PRIMARY_BTN)
        self.pick_btn.clicked.connect(self._on_select)
        btns.addWidget(self.pick_btn)
        lay.addLayout(btns)

        self._populate_table(self.all_contacts)

    def _populate_table(self, contacts):
        self.table.setRowCount(len(contacts))
        for i, c in enumerate(contacts):
            self.table.setRowHeight(i, 45)
            # Create a checkable item for the Name column
            name_item = QTableWidgetItem(c['name'])
            name_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            name_item.setCheckState(Qt.Unchecked)
            
            self.table.setItem(i, 0, name_item)
            self.table.setItem(i, 1, QTableWidgetItem(c['phone']))
            self.table.setItem(i, 2, QTableWidgetItem(c['source']))

    def _select_all(self):
        is_checking = self.sel_all_btn.text() == "Select All"
        state = Qt.Checked if is_checking else Qt.Unchecked
        for i in range(self.table.rowCount()):
            self.table.item(i, 0).setCheckState(state)
        self.sel_all_btn.setText("Deselect All" if is_checking else "Select All")

    def _filter_table(self, text):
        filtered = [c for c in self.all_contacts if text.lower() in c['name'].lower() or text.lower() in c['phone']]
        self._populate_table(filtered)

    def _on_select(self):
        self.selected_contacts = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 0).checkState() == Qt.Checked:
                name = self.table.item(i, 0).text()
                phone = self.table.item(i, 1).text()
                self.selected_contacts.append({"name": name, "phone": phone})
        
        if not self.selected_contacts:
            QMessageBox.warning(self, "Selection Empty", "Please select at least one contact.")
            return
            
        self.accept()

# ── Main Screen ───────────────────────────────────────────────────────────────
class WhatsAppScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.svc = WhatsAppService()
        self.selected_recipients = [] # list of contacts for bulk send
        self._build()

    def _build(self):
        self.setStyleSheet(f"background: {SURFACE};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # Page header
        hdr = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(make_label("WhatsApp Messaging", 20, ON_SURFACE, bold=True))
        title_col.addWidget(make_label("Send invoices and payment reminders directly to customers", 12, ON_SURF_VAR))
        hdr.addLayout(title_col)
        hdr.addStretch()

        refresh_btn = QPushButton("↻  Refresh History")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(GHOST_BTN)
        refresh_btn.clicked.connect(self._load_history)
        hdr.addWidget(refresh_btn)
        root.addLayout(hdr)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: transparent; }}
            QTabBar::tab {{
                background: {SURF_LOW}; color: {ON_SURF_VAR};
                padding: 9px 20px; border: none; border-radius: 0px;
                font-size: 13px; font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {SURF_CARD}; color: {PRIMARY};
                border-bottom: 2px solid {SECONDARY};
            }}
            QTabBar::tab:hover:!selected {{ background: {SURF_HIGH}; }}
        """)

        tabs.addTab(self._build_invoice_tab(),  "📄  Send Invoice")
        tabs.addTab(self._build_reminder_tab(), "🔔  Due Reminder")
        tabs.addTab(self._build_custom_tab(),   "✏️  Custom Message")
        tabs.addTab(self._build_history_tab(),  "📋  Message History")
        root.addWidget(tabs)

    # ── Tab 1: Send Invoice ──────────────────────────────────────────────────
    def _build_invoice_tab(self):
        w = QWidget()
        w.setStyleSheet(f"background: {SURFACE};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(16)

        # Two-column layout
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # Left: form
        form_card = QFrame()
        form_card.setStyleSheet(CARD_STYLE)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(14)
        fl.addWidget(make_label("Invoice Details", 14, ON_SURFACE, bold=True))
        fl.addWidget(divider())

        fl.addWidget(make_label("Invoice Number", 11, ON_SURF_VAR))
        self.inv_inv_combo = QComboBox()
        self.inv_inv_combo.setView(QListView())
        self.inv_inv_combo.view().setStyleSheet("QListView::item { height: 50px; padding: 10px; }")
        self.inv_inv_combo.setFixedHeight(45)
        self.inv_inv_combo.currentIndexChanged.connect(self._on_invoice_selected)
        fl.addWidget(self.inv_inv_combo)

        fl.addWidget(make_label("Customer Phone", 11, ON_SURF_VAR))
        self.inv_phone = QLineEdit()
        self.inv_phone.setPlaceholderText("9876543210")
        self.inv_phone.setFixedHeight(45)
        fl.addWidget(self.inv_phone)

        fl.addWidget(make_label("Message Language", 11, ON_SURF_VAR))
        self.inv_lang_combo = QComboBox()
        self.inv_lang_combo.addItems(["English", "Marathi"])
        self.inv_lang_combo.setView(QListView())
        self.inv_lang_combo.view().setStyleSheet("QListView::item { height: 40px; padding: 8px 12px; }")
        self.inv_lang_combo.setFixedHeight(45)
        self.inv_lang_combo.currentIndexChanged.connect(self._on_invoice_selected)
        fl.addWidget(self.inv_lang_combo)

        fl.addWidget(make_label("Preview Message", 11, ON_SURF_VAR))
        self.inv_preview = QTextEdit()
        self.inv_preview.setFixedHeight(140)
        self.inv_preview.setStyleSheet(f"""
            background: {SURF_LOW}; border: none; border-radius: 6px;
            padding: 10px; font-size: 12px; color: {ON_SURFACE};
        """)
        self.inv_preview.setReadOnly(True)
        fl.addWidget(self.inv_preview)
        fl.addStretch()

        self.inv_send_btn = QPushButton("Send via WhatsApp  →")
        self.inv_send_btn.setFixedHeight(44)
        self.inv_send_btn.setStyleSheet(PRIMARY_BTN)
        self.inv_send_btn.setCursor(Qt.PointingHandCursor)
        self.inv_send_btn.clicked.connect(self._send_invoice_msg)
        fl.addWidget(self.inv_send_btn)
        cols.addWidget(form_card, 1)

        # Right: recent invoices list
        recent_card = QFrame()
        recent_card.setStyleSheet(CARD_STYLE)
        rl = QVBoxLayout(recent_card)
        rl.setContentsMargins(20, 20, 20, 20)
        rl.setSpacing(10)
        rl.addWidget(make_label("Recent Invoices", 14, ON_SURFACE, bold=True))
        rl.addWidget(divider())

        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(4)
        self.inv_table.setHorizontalHeaderLabels(["INVOICE", "CUSTOMER", "AMOUNT", "STATUS"])
        self.inv_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.inv_table.verticalHeader().setVisible(False)
        self.inv_table.setShowGrid(False)
        self.inv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.inv_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inv_table.doubleClicked.connect(self._on_invoice_table_click)
        rl.addWidget(self.inv_table)
        cols.addWidget(recent_card, 1)

        lay.addLayout(cols)
        self._load_invoices()
        return w

    # ── Tab 2: Due Reminder ──────────────────────────────────────────────────
    def _build_reminder_tab(self):
        w = QWidget()
        w.setStyleSheet(f"background: {SURFACE};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(16)

        cols = QHBoxLayout()
        cols.setSpacing(16)

        # Left: single reminder form
        form_card = QFrame()
        form_card.setStyleSheet(CARD_STYLE)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(14)
        fl.addWidget(make_label("Send Reminder", 14, ON_SURFACE, bold=True))
        fl.addWidget(divider())

        fl.addWidget(make_label("Select Party", 11, ON_SURF_VAR))
        self.rem_party_combo = QComboBox()
        self.rem_party_combo.setView(QListView())
        self.rem_party_combo.view().setStyleSheet("QListView::item { height: 50px; padding: 10px; }")
        self.rem_party_combo.setFixedHeight(45)
        self.rem_party_combo.currentIndexChanged.connect(self._on_party_selected)
        fl.addWidget(self.rem_party_combo)

        fl.addWidget(make_label("Phone Number", 11, ON_SURF_VAR))
        self.rem_phone = QLineEdit()
        self.rem_phone.setPlaceholderText("9876543210")
        self.rem_phone.setFixedHeight(38)
        fl.addWidget(self.rem_phone)

        fl.addWidget(make_label("Outstanding Amount (₹)", 11, ON_SURF_VAR))
        self.rem_amount = QLineEdit()
        self.rem_amount.setPlaceholderText("0.00")
        self.rem_amount.setFixedHeight(38)
        fl.addWidget(self.rem_amount)

        fl.addWidget(make_label("Message Preview", 11, ON_SURF_VAR))
        self.rem_preview = QTextEdit()
        self.rem_preview.setFixedHeight(120)
        self.rem_preview.setStyleSheet(f"""
            background: {SURF_LOW}; border: none; border-radius: 6px;
            padding: 10px; font-size: 12px; color: {ON_SURFACE};
        """)
        self.rem_preview.setReadOnly(True)
        fl.addWidget(self.rem_preview)
        fl.addStretch()

        self.rem_send_btn = QPushButton("Send Reminder  →")
        self.rem_send_btn.setFixedHeight(44)
        self.rem_send_btn.setStyleSheet(f"""
            QPushButton {{ background: {SECONDARY}; color: white; border: none;
                          border-radius: 6px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background: #155c43; }}
        """)
        self.rem_send_btn.setCursor(Qt.PointingHandCursor)
        self.rem_send_btn.clicked.connect(self._send_reminder)
        fl.addWidget(self.rem_send_btn)
        cols.addWidget(form_card, 1)

        # Right: parties with dues
        dues_card = QFrame()
        dues_card.setStyleSheet(CARD_STYLE)
        dl = QVBoxLayout(dues_card)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(10)

        dues_hdr = QHBoxLayout()
        dues_hdr.addWidget(make_label("Parties with Dues", 14, ON_SURFACE, bold=True))
        dues_hdr.addStretch()
        bulk_btn = QPushButton("Send All Reminders")
        bulk_btn.setFixedHeight(32)
        bulk_btn.setStyleSheet(f"""
            QPushButton {{ background: {WARN_BG}; color: #92400e;
                          border: none; border-radius: 4px;
                          font-size: 12px; padding: 0 12px; }}
            QPushButton:hover {{ background: #fde68a; }}
        """)
        bulk_btn.clicked.connect(self._send_bulk_reminders)
        dues_hdr.addWidget(bulk_btn)
        dl.addLayout(dues_hdr)
        dl.addWidget(divider())

        self.dues_table = QTableWidget()
        self.dues_table.setColumnCount(4)
        self.dues_table.setHorizontalHeaderLabels(["PARTY", "PHONE", "BALANCE", "ACTION"])
        self.dues_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.dues_table.verticalHeader().setVisible(False)
        self.dues_table.setShowGrid(False)
        self.dues_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        dl.addWidget(self.dues_table)
        cols.addWidget(dues_card, 1)

        lay.addLayout(cols)
        self._load_parties()
        return w

    # ── Tab 3: Custom Message ────────────────────────────────────────────────
    def _build_custom_tab(self):
        w = QWidget()
        w.setStyleSheet(f"background: {SURFACE};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 16, 0, 0)
        lay.setSpacing(16)

        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(14)
        cl.addWidget(make_label("Compose Custom Message", 14, ON_SURFACE, bold=True))
        cl.addWidget(divider())

        row = QHBoxLayout()
        row.setSpacing(16)

        phone_col = QVBoxLayout()
        phone_hdr = QHBoxLayout()
        phone_hdr.addWidget(make_label("Phone Number", 11, ON_SURF_VAR))
        phone_hdr.addStretch()
        
        pick_btn = QPushButton("📋 Pick from History")
        pick_btn.setCursor(Qt.PointingHandCursor)
        pick_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {SECONDARY}; border: none; font-size: 11px; font-weight: 600; text-decoration: underline; }}
            QPushButton:hover {{ color: {PRIMARY}; }}
        """)
        pick_btn.clicked.connect(self._open_contact_picker)
        phone_hdr.addWidget(pick_btn)
        
        phone_col.addLayout(phone_hdr)
        self.cust_phone = QLineEdit()
        self.cust_phone.setPlaceholderText("9876543210")
        self.cust_phone.setFixedHeight(38)
        phone_col.addWidget(self.cust_phone)
        row.addLayout(phone_col)

        name_col = QVBoxLayout()
        name_col.addWidget(make_label("Party Name (optional)", 11, ON_SURF_VAR))
        self.cust_name = QLineEdit()
        self.cust_name.setPlaceholderText("Priya Sharma")
        self.cust_name.setFixedHeight(38)
        name_col.addWidget(self.cust_name)
        row.addLayout(name_col)
        cl.addLayout(row)

        cl.addWidget(make_label("Message", 11, ON_SURF_VAR))
        self.cust_body = QTextEdit()
        self.cust_body.setPlaceholderText(
            "Type your message here...\n\n"
            "Tip: Use *bold text* in WhatsApp by wrapping with asterisks."
        )
        self.cust_body.setFixedHeight(180)
        self.cust_body.setStyleSheet(f"""
            background: {SURF_LOW}; border: none; border-radius: 6px;
            padding: 10px; font-size: 13px; color: {ON_SURFACE};
        """)
        cl.addWidget(self.cust_body)

        self.cust_send_btn = QPushButton("Send Message  →")
        self.cust_send_btn.setFixedHeight(44)
        self.cust_send_btn.setStyleSheet(PRIMARY_BTN)
        self.cust_send_btn.setCursor(Qt.PointingHandCursor)
        self.cust_send_btn.clicked.connect(self._send_custom)
        cl.addWidget(self.cust_send_btn, alignment=Qt.AlignRight)

        lay.addWidget(card)
        lay.addStretch()
        return w

    # ── Tab 4: History ───────────────────────────────────────────────────────
    def _build_history_tab(self):
        w = QWidget()
        w.setStyleSheet(f"background: {SURFACE};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 16, 0, 0)

        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)

        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(6)
        self.hist_table.setHorizontalHeaderLabels([
            "SENT AT", "PARTY", "PHONE", "TYPE", "INVOICE", "STATUS"
        ])
        self.hist_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.setShowGrid(False)
        self.hist_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        cl.addWidget(self.hist_table)

        lay.addWidget(card)
        self._load_history()
        return w

    # ── Data Loaders ─────────────────────────────────────────────────────────
    def _load_invoices(self):
        db = get_db()
        try:
            invoices = db.query(InvoiceModel)\
                         .order_by(InvoiceModel.date.desc())\
                         .limit(30).all()
            self.inv_inv_combo.clear()
            self.inv_inv_combo.addItem("Select invoice...", None)
            self._all_invoices = invoices

            self.inv_table.setRowCount(len(invoices))
            for i, inv in enumerate(invoices):
                self.inv_table.setRowHeight(i, 50)
                self.inv_table.setItem(i, 0, QTableWidgetItem(inv.invoice_number))
                self.inv_table.setItem(i, 1, QTableWidgetItem(inv.party_name or "Walk-in"))
                amt = QTableWidgetItem(f"₹{inv.grand_total:,.2f}")
                amt.setFont(QFont("Segoe UI", 12, QFont.Bold))
                self.inv_table.setItem(i, 2, amt)

                s_color = SECONDARY if inv.status == "Paid" else TERTIARY
                s_bg    = SUCCESS_BG if inv.status == "Paid" else ERROR_BG
                pill_w  = QWidget()
                pl      = QHBoxLayout(pill_w)
                pl.setContentsMargins(8, 0, 8, 0)
                pl.addWidget(status_pill(inv.status, s_color, s_bg))
                self.inv_table.setCellWidget(i, 3, pill_w)

                self.inv_inv_combo.addItem(inv.invoice_number, inv)
        finally:
            db.close()

    def _load_parties(self):
        db = get_db()
        try:
            parties = db.query(PartyModel)\
                        .filter(PartyModel.party_type == "Customer")\
                        .filter(PartyModel.balance > 0)\
                        .all()
            self.rem_party_combo.clear()
            self.rem_party_combo.addItem("Select party...", None)

            self.dues_table.setRowCount(len(parties))
            for i, p in enumerate(parties):
                self.dues_table.setRowHeight(i, 50)
                self.dues_table.setItem(i, 0, QTableWidgetItem(p.name))
                self.dues_table.setItem(i, 1, QTableWidgetItem(p.phone or "—"))
                bal = QTableWidgetItem(f"₹{p.balance:,.2f}")
                bal.setFont(QFont("Segoe UI", 12, QFont.Bold))
                bal.setForeground(__import__("PyQt5.QtGui", fromlist=["QColor"]).QColor(TERTIARY))
                self.dues_table.setItem(i, 2, bal)

                send_btn = QPushButton("Send")
                send_btn.setFixedHeight(28)
                send_btn.setStyleSheet(f"""
                    QPushButton {{ background: {SUCCESS_BG}; color: {SECONDARY};
                                  border: none; border-radius: 4px;
                                  font-size: 11px; padding: 0 12px; }}
                    QPushButton:hover {{ background: {SECONDARY}; color: white; }}
                """)
                send_btn.clicked.connect(lambda _, party=p: self._quick_remind(party))
                self.dues_table.setCellWidget(i, 3, send_btn)

                self.rem_party_combo.addItem(p.name, p)
        finally:
            db.close()

    def _load_history(self):
        logs = self.svc.get_history(100)
        self.hist_table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            self.hist_table.setRowHeight(i, 50)
            self.hist_table.setItem(i, 0, QTableWidgetItem(
                log.sent_at.strftime("%d %b %y  %H:%M") if log.sent_at else "—"
            ))
            self.hist_table.setItem(i, 1, QTableWidgetItem(log.party_name or "—"))
            self.hist_table.setItem(i, 2, QTableWidgetItem(log.phone))
            self.hist_table.setItem(i, 3, QTableWidgetItem(log.message_type.title()))
            self.hist_table.setItem(i, 4, QTableWidgetItem(log.invoice_no or "—"))
            s_color = SECONDARY if log.status == "sent" else TERTIARY
            s_bg    = SUCCESS_BG if log.status == "sent" else ERROR_BG
            sw = QWidget()
            sl = QHBoxLayout(sw)
            sl.setContentsMargins(8,0,8,0)
            sl.addWidget(status_pill(log.status.upper(), s_color, s_bg))
            self.hist_table.setCellWidget(i, 5, sw)

    # ── Event Handlers ────────────────────────────────────────────────────────
    def _on_invoice_selected(self, idx):
        inv = self.inv_inv_combo.currentData()
        if not inv:
            return
        
        # Only update phone if we actually selected a new invoice (not just triggered by lang change)
        import inspect
        caller = inspect.stack()[1].function
        if caller != "_on_invoice_selected" and caller != "<lambda>": # Standard currentIndexChanged trigger
             self.inv_phone.setText(inv.party_phone or "")
             
        from services.whatsapp_service import WhatsAppService
        
        # Pick template based on language selection
        if hasattr(self, 'inv_lang_combo') and self.inv_lang_combo.currentText() == "Marathi":
            template = WhatsAppService.INVOICE_MSG_MARATHI
        else:
            template = WhatsAppService.INVOICE_MSG
            
        body = template.format(
            customer=inv.party_name or "Customer",
            invoice_no=inv.invoice_number,
            shop=__import__("fabricpos.config", fromlist=["SHOP_NAME"]).SHOP_NAME,
            amount=inv.grand_total,
            date=inv.date.strftime("%d %b %Y"),
        )
        self.inv_preview.setPlainText(body)

    def _on_invoice_table_click(self, index):
        row = index.row()
        if row < len(self._all_invoices):
            inv = self._all_invoices[row]
            combo_idx = self.inv_inv_combo.findText(inv.invoice_number)
            if combo_idx >= 0:
                self.inv_inv_combo.setCurrentIndex(combo_idx)

    def _on_party_selected(self, idx):
        party = self.rem_party_combo.currentData()
        if not party:
            return
        self.rem_phone.setText(party.phone or "")
        self.rem_amount.setText(f"{party.balance:.2f}")
        from services.whatsapp_service import WhatsAppService
        from config import SHOP_NAME, PHONE
        body = WhatsAppService.REMINDER_MSG.format(
            name=party.name, due=party.balance,
            shop=SHOP_NAME, phone=PHONE
        )
        self.rem_preview.setPlainText(body)

    # ── Send Actions ─────────────────────────────────────────────────────────
    def _send_invoice_msg(self):
        inv = self.inv_inv_combo.currentData()
        phone = self.inv_phone.text().strip()
        if not inv or not phone:
            QMessageBox.warning(self, "Missing Info", "Please select an invoice and enter a phone number.")
            return
        self._set_loading(self.inv_send_btn, True)
        self._thread = SendThread(
            self.svc.send_invoice_message,
            phone=phone,
            invoice_no=inv.invoice_number,
            customer=inv.party_name or "Customer",
            amount=inv.grand_total,
        )
        self._thread.result.connect(lambda r: self._on_send_result(r, self.inv_send_btn, "Send via WhatsApp  →"))
        self._thread.start()

    def _send_reminder(self):
        phone  = self.rem_phone.text().strip()
        name   = self.rem_party_combo.currentText()
        try:
            due = float(self.rem_amount.text() or 0)
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Enter a valid amount.")
            return
        if not phone:
            QMessageBox.warning(self, "Missing", "Enter a phone number.")
            return
        self._set_loading(self.rem_send_btn, True)
        self._thread = SendThread(self.svc.send_due_reminder, phone=phone, name=name, due=due)
        self._thread.result.connect(lambda r: self._on_send_result(r, self.rem_send_btn, "Send Reminder  →"))
        self._thread.start()

    def _send_custom(self):
        phone_input = self.cust_phone.text().strip()
        body = self.cust_body.toPlainText().strip()
        
        if not body:
            QMessageBox.warning(self, "Missing", "Message body is required.")
            return

        # Check if we have bulk recipients stored
        if self.selected_recipients:
            recipients = self.selected_recipients
        elif phone_input:
            recipients = [{"phone": phone_input, "name": self.cust_name.text().strip()}]
        else:
            QMessageBox.warning(self, "Missing", "Please select recipients or enter a phone number.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Send",
            f"Send message to {len(recipients)} contact(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        self._set_loading(self.cust_send_btn, True)
        
        # We'll use a wrapper to send everything in the thread
        def bulk_send_wrapper():
            from time import sleep
            from config import WHATSAPP_BACKEND
            
            success, failed = 0, 0
            for i, r in enumerate(recipients):
                res = self.svc.send_custom(phone=r['phone'], body=body, party_name=r.get('name', ''))
                if res["success"]:
                    success += 1
                else:
                    failed += 1
                
                # Add delay between messages for pywhatkit to prevent ban/crash
                if WHATSAPP_BACKEND == "pywhatkit" and i < len(recipients) - 1:
                    sleep(15) 
            
            return {"success": True, "message": f"Bulk Send Complete\n✅ Sent: {success}\n❌ Failed: {failed}"}

        self._thread = SendThread(bulk_send_wrapper)
        self._thread.result.connect(lambda r: self._on_send_result(r, self.cust_send_btn, "Send Message  →"))
        self._thread.start()

    def _quick_remind(self, party):
        if not party.phone:
            QMessageBox.warning(self, "No Phone", f"{party.name} has no phone number on record.")
            return
        res = self.svc.send_due_reminder(phone=party.phone, name=party.name, due=party.balance)
        if res["success"]:
            QMessageBox.information(self, "Sent", f"Reminder sent to {party.name}")
        else:
            QMessageBox.critical(self, "Failed", res["message"])
        self._load_history()

    def _send_bulk_reminders(self):
        db = get_db()
        try:
            parties = db.query(PartyModel)\
                        .filter(PartyModel.party_type == "Customer")\
                        .filter(PartyModel.balance > 0)\
                        .filter(PartyModel.phone != None)\
                        .filter(PartyModel.phone != "")\
                        .all()
        finally:
            db.close()

        if not parties:
            QMessageBox.information(self, "No Dues", "No customers with outstanding dues and phone numbers.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Bulk Send",
            f"Send reminders to {len(parties)} customers with outstanding dues?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        success, failed = 0, 0
        for party in parties:
            res = self.svc.send_due_reminder(phone=party.phone, name=party.name, due=party.balance)
            if res["success"]:
                success += 1
            else:
                failed += 1

        QMessageBox.information(self, "Bulk Send Complete",
                                f"✅ Sent: {success}\n❌ Failed: {failed}")
        self._load_history()

    def _on_send_result(self, result: dict, btn: QPushButton, original_text: str):
        self._set_loading(btn, False, original_text)
        if result["success"]:
            QMessageBox.information(self, "✅ Sent", "Message sent successfully!")
        else:
            QMessageBox.critical(self, "❌ Failed", result["message"])
        self._load_history()

    def _set_loading(self, btn: QPushButton, loading: bool, original: str = ""):
        if loading:
            btn.setText("Sending...")
            btn.setEnabled(False)
        else:
            btn.setText(original)
            btn.setEnabled(True)

    def _open_contact_picker(self):
        """Open history dialog and fill the form with selection."""
        contacts = self.svc.get_contact_list()
        if not contacts:
            QMessageBox.information(self, "No History", "No contact history found in your database yet.")
            return
            
        dlg = ContactSelectionDialog(contacts, self)
        if dlg.exec_():
            self.selected_recipients = dlg.selected_contacts
            if len(self.selected_recipients) == 1:
                sel = self.selected_recipients[0]
                self.cust_phone.setText(sel['phone'])
                self.cust_name.setText(sel['name'] if sel['name'] != "Unknown" else "")
            else:
                self.cust_phone.setText(f"Multiple ({len(self.selected_recipients)} contacts selected)")
                self.cust_phone.setReadOnly(True)
                self.cust_name.setEnabled(False)
