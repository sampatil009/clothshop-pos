import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, 
    QLabel, QFrame, QTabWidget, QGridLayout, QDialog, 
    QFormLayout, QComboBox, QTextEdit, QCheckBox, QMessageBox,
    QAbstractItemView, QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen

# Namespace handling
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import (
    PRIMARY, PRIMARY_DARK, PRIMARY_CONT, SECONDARY, SEC_LIGHT, SEC_CONTAINER,
    TERTIARY, SURFACE, SURF_LOW, SURF_CARD, SURF_HIGH, ON_SURFACE, ON_SURF_VAR,
    OUTLINE, ERROR_BG, SUCCESS_BG, WARN_BG,
    APP_STYLE, SIDEBAR_STYLE, NAV_BTN_STYLE, PRIMARY_BTN, SECONDARY_BTN, 
    GHOST_BTN, CARD_STYLE, make_label, divider, status_pill, card, spacer
)
from services.crm_service import CRMService, relative_time
from services.whatsapp_service import WhatsAppService

# ── Workers for Multi-threading ──────────────────────────────────────────────

class CRMWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# ── Components ───────────────────────────────────────────────────────────────

class AvatarWidget(QLabel):
    def __init__(self, text, size=40, bg_color=PRIMARY, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.bg_color = bg_color
        # Get initials
        parts = text.strip().split()
        if len(parts) >= 2:
            self.initials = (parts[0][0] + parts[1][0]).upper()
        elif len(parts) == 1:
            self.initials = parts[0][:2].upper()
        else:
            self.initials = "??"
        
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Circle
        painter.setBrush(QBrush(QColor(self.bg_color)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
        
        # Draw Text
        painter.setPen(QPen(Qt.white))
        font = QFont("Segoe UI", self.width() // 3, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.initials)

class AddCustomerDialog(QDialog):
    def __init__(self, service, customer=None, parent=None):
        super().__init__(parent)
        self.service = service
        self.customer = customer # If edit mode
        self.setWindowTitle("Add New Customer" if not customer else "Edit Customer")
        self.setFixedSize(480, 600)
        self.setStyleSheet(f"background: {SURF_CARD}; border-radius: 12px;")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
        self._build()
        if self.customer:
            self._fill_data()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = make_label("Customer Profile", 18, PRIMARY, bold=True)
        layout.addWidget(title)
        layout.addWidget(divider())

        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignLeft)

        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("Full Name")
        self.err_name = make_label("", 10, TERTIARY)
        vn = QVBoxLayout(); vn.addWidget(self.name_in); vn.addWidget(self.err_name)
        form.addRow(make_label("Name*", 11, ON_SURF_VAR, bold=True), vn)

        self.phone_in = QLineEdit()
        self.phone_in.setPlaceholderText("10 Digit Mobile")
        self.err_phone = make_label("", 10, TERTIARY)
        vp = QVBoxLayout(); vp.addWidget(self.phone_in); vp.addWidget(self.err_phone)
        form.addRow(make_label("Phone*", 11, ON_SURF_VAR, bold=True), vp)

        self.email_in = QLineEdit()
        form.addRow(make_label("Email", 11, ON_SURF_VAR, bold=True), self.email_in)

        self.addr_in = QTextEdit()
        self.addr_in.setFixedHeight(60)
        form.addRow(make_label("Address", 11, ON_SURF_VAR, bold=True), self.addr_in)

        self.dob_in = QLineEdit()
        self.dob_in.setPlaceholderText("DD-MM-YYYY")
        form.addRow(make_label("DOB", 11, ON_SURF_VAR, bold=True), self.dob_in)

        self.gender_in = QComboBox()
        self.gender_in.addItems(["", "Female", "Male", "Other"])
        form.addRow(make_label("Gender", 11, ON_SURF_VAR, bold=True), self.gender_in)

        # Tags
        tag_lay = QHBoxLayout()
        self.tag_boxes = {}
        for tname in ["VIP", "Regular", "New", "Bridal", "Wholesale"]:
            cb = QCheckBox(tname)
            self.tag_boxes[tname] = cb
            tag_lay.addWidget(cb)
        form.addRow(make_label("Tags", 11, ON_SURF_VAR, bold=True), tag_lay)

        self.notes_in = QTextEdit()
        self.notes_in.setFixedHeight(60)
        form.addRow(make_label("Notes", 11, ON_SURF_VAR, bold=True), self.notes_in)

        layout.addLayout(form)
        layout.addStretch()

        btns = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(GHOST_BTN)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save Customer")
        self.save_btn.setStyleSheet(PRIMARY_BTN)
        self.save_btn.clicked.connect(self._save)
        
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        layout.addLayout(btns)

    def _fill_data(self):
        c = self.customer
        self.name_in.setText(c.name)
        self.phone_in.setText(c.phone)
        self.email_in.setText(c.email or "")
        self.addr_in.setPlainText(c.address or "")
        self.dob_in.setText(c.dob or "")
        self.gender_in.setCurrentText(c.gender or "")
        self.notes_in.setPlainText(c.notes or "")
        
        current_tags = [t.name for t in c.tags]
        for tname, cb in self.tag_boxes.items():
            cb.setChecked(tname in current_tags)

    def _save(self):
        name = self.name_in.text().strip()
        phone = self.phone_in.text().strip()
        
        # Validation
        valid = True
        if not name:
            self.err_name.setText("Name is required")
            valid = False
        else: self.err_name.setText("")
        
        if not phone or len(phone) < 10:
            self.err_phone.setText("Valid 10-digit phone required")
            valid = False
        else: self.err_phone.setText("")
        
        if not valid: return

        tags = [t for t, cb in self.tag_boxes.items() if cb.isChecked()]
        
        data = {
            "name": name, "phone": phone, "email": self.email_in.text(),
            "address": self.addr_in.toPlainText(), "dob": self.dob_in.text(),
            "gender": self.gender_in.currentText(), "notes": self.notes_in.toPlainText(),
            "tags": tags
        }

        try:
            if self.customer:
                self.service.update_customer(self.customer.id, **data)
            else:
                self.service.add_customer(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class WhatsAppDialog(QDialog):
    def __init__(self, name, phone, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"WhatsApp to {name}")
        self.setFixedSize(400, 300)
        self.setStyleSheet(f"background: {SURF_CARD};")
        self.name = name
        self.phone = phone
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.addWidget(make_label(f"Sending to: {name} ({phone})", 12, ON_SURF_VAR))
        
        self.msg_in = QTextEdit()
        self.msg_in.setPlaceholderText("Type your message here...")
        lay.addWidget(self.msg_in)
        
        btns = QHBoxLayout()
        send = QPushButton("Send Message")
        send.setStyleSheet(SECONDARY_BTN)
        send.clicked.connect(self._send)
        btns.addWidget(send)
        lay.addLayout(btns)

    def _send(self):
        body = self.msg_in.toPlainText().strip()
        if not body: return
        
        svc = WhatsAppService()
        res = svc.send_custom(self.phone, body, self.name)
        if res["success"]:
            QMessageBox.information(self, "Success", "Message sent via WhatsApp!")
            self.accept()
        else:
            QMessageBox.critical(self, "Failed", res["message"])

class CustomerListPanel(QWidget):
    row_clicked = pyqtSignal(object)
    refreshed = pyqtSignal()

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.all_customers = []
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        head = QHBoxLayout()
        self.title_lbl = make_label("Customers (0)", 15, ON_SURFACE, bold=True)
        head.addWidget(self.title_lbl)
        head.addStretch()

        self.search_in = QLineEdit()
        self.search_in.setPlaceholderText("Search by name, phone...")
        self.search_in.setFixedWidth(250)
        self.search_in.textChanged.connect(self.refresh)
        head.addWidget(self.search_in)

        filter_btn = QPushButton("Filters")
        filter_btn.setStyleSheet(GHOST_BTN)
        head.addWidget(filter_btn)

        add_btn = QPushButton("+ Add Customer")
        add_btn.setStyleSheet(PRIMARY_BTN)
        add_btn.clicked.connect(self._on_add)
        head.addWidget(add_btn)
        layout.addLayout(head)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "", "NAME", "PHONE", "TOTAL PURCHASE", "LAST VISIT", "LOYALTY", "TAGS", "ACTIONS"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_table_click)
        layout.addWidget(self.table)
        
        # Pagination Placeholder
        pag_lay = QHBoxLayout()
        self.stats_lbl = make_label("Showing 0 to 0 of 0", 11, ON_SURF_VAR)
        pag_lay.addWidget(self.stats_lbl)
        pag_lay.addStretch()
        layout.addLayout(pag_lay)

    def refresh(self):
        search = self.search_in.text()
        self.worker = CRMWorker(self.service.get_all_customers, search=search)
        self.worker.finished.connect(self._populate)
        self.worker.start()

    def _populate(self, customers):
        self.all_customers = customers
        self.title_lbl.setText(f"Customers ({len(customers)})")
        self.table.setRowCount(len(customers))
        
        for i, c in enumerate(customers):
            self.table.setRowHeight(i, 60)
            
            # Avatar
            tag_name = c.tags[0].name if c.tags else "Regular"
            color = self.service.TAG_COLORS.get(tag_name, PRIMARY)
            av = AvatarWidget(c.name, 40, color)
            av_wrap = QWidget(); avl = QHBoxLayout(av_wrap); avl.addWidget(av); avl.setAlignment(Qt.AlignCenter); avl.setContentsMargins(0,0,0,0)
            self.table.setCellWidget(i, 0, av_wrap)
            
            # Name & Phone
            self.table.setItem(i, 1, QTableWidgetItem(c.name))
            self.table.setItem(i, 2, QTableWidgetItem(c.phone))
            
            # Purchase Stats
            stats = self.service.get_customer_stats(c.id)
            purch = QTableWidgetItem(f"₹{stats['total_purchase']:,.2f}")
            purch.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 3, purch)
            
            self.table.setItem(i, 4, QTableWidgetItem(relative_time(stats['last_visit'])))
            
            # Loyalty
            points = c.loyalty.available_points if c.loyalty else 0
            loy = QTableWidgetItem(f"{points} ★")
            loy.setForeground(QColor("#ffb300"))
            loy.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 5, loy)
            
            # Tags
            tag_wrap = QWidget(); tgl = QHBoxLayout(tag_wrap); tgl.setContentsMargins(5,0,5,0)
            if c.tags:
                for t in c.tags:
                    tgl.addWidget(status_pill(t.name.upper(), self.service.TAG_COLORS.get(t.name, ON_SURFACE), SEC_CONTAINER))
            else:
                tgl.addWidget(status_pill("REGULAR", ON_SURF_VAR, SURF_HIGH))
            self.table.setCellWidget(i, 6, tag_wrap)
            
            # Actions
            act_wrap = QWidget(); acl = QHBoxLayout(act_wrap); acl.setContentsMargins(5,0,5,0); acl.setSpacing(5)
            view_btn = QPushButton("👁")
            view_btn.setFixedSize(28, 28); view_btn.setStyleSheet(GHOST_BTN); view_btn.clicked.connect(lambda _, cust=c: self.row_clicked.emit(cust))
            wa_btn = QPushButton("💬")
            wa_btn.setFixedSize(28, 28); wa_btn.setStyleSheet("color: #25D366; background: transparent; border: none; font-size: 16px;"); wa_btn.clicked.connect(lambda _, cust=c: self._on_whatsapp(cust))
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 28); edit_btn.setStyleSheet(GHOST_BTN); edit_btn.clicked.connect(lambda _, cust=c: self._on_edit(cust))
            
            acl.addWidget(view_btn); acl.addWidget(wa_btn); acl.addWidget(edit_btn)
            self.table.setCellWidget(i, 7, act_wrap)

    def _on_table_click(self, row, col):
        self.row_clicked.emit(self.all_customers[row])

    def _on_add(self):
        dlg = AddCustomerDialog(self.service)
        if dlg.exec_(): self.refresh(); self.refreshed.emit()

    def _on_edit(self, cust):
        dlg = AddCustomerDialog(self.service, customer=cust)
        if dlg.exec_(): self.refresh(); self.refreshed.emit()

    def _on_whatsapp(self, cust):
        WhatsAppDialog(cust.name, cust.phone, self).exec_()
        self.service.log_interaction(cust.id, "WhatsApp", "WhatsApp", "Manual WhatsApp message sent")

class CustomerOverviewPanel(QFrame):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.setFixedWidth(280)
        self.setStyleSheet(f"background: {SURF_CARD}; border-left: 1px solid {SURF_HIGH};")
        self._build()
        self.refresh()

    def _build(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        self.layout.addWidget(make_label("Customer Overview", 14, ON_SURFACE, bold=True))
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.cards = {}
        metrics = [
            ("TOTAL CUSTOMERS", "0", "👥"),
            ("ACTIVE THIS MONTH", "0", "⚡"),
            ("TOTAL SALES", "₹0.00", "💰"),
            ("AVG SPEND / CUST", "₹0.00", "📈")
        ]
        
        for i, (label, val, icon) in enumerate(metrics):
            f = QFrame()
            f.setStyleSheet(f"background: {SURF_LOW}; border-radius: 8px; padding: 10px;")
            l = QVBoxLayout(f)
            l.addWidget(make_label(label, 9, ON_SURF_VAR, bold=True))
            
            val_lay = QHBoxLayout()
            v_lbl = make_label(val, 18, ON_SURFACE, bold=True)
            self.cards[label] = v_lbl
            val_lay.addWidget(v_lbl)
            val_lay.addWidget(make_label(icon, 14, ON_SURF_VAR))
            l.addLayout(val_lay)
            
            grid.addWidget(f, i // 2, i % 2)
            
        self.layout.addLayout(grid)
        self.layout.addStretch()

    def refresh(self):
        self.worker = CRMWorker(self.service.get_overview_stats)
        self.worker.finished.connect(self._update_metrics)
        self.worker.start()

    def _update_metrics(self, stats):
        self.cards["TOTAL CUSTOMERS"].setText(str(stats["total_customers"]))
        self.cards["ACTIVE THIS MONTH"].setText(str(stats["active_this_month"]))
        self.cards["TOTAL SALES"].setText(f"₹{stats['total_sales']:,.0f}")
        self.cards["AVG SPEND / CUST"].setText(f"₹{stats['avg_spend']:,.0f}")

class CustomerProfilePanel(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.customer = None
        self._build()

    def set_customer(self, customer):
        self.customer = customer
        self._load_data()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with Back button
        head_container = QFrame()
        head_container.setFixedHeight(60)
        head_container.setStyleSheet(f"background: {SURF_CARD}; border-bottom: 1px solid {SURF_HIGH};")
        head = QHBoxLayout(head_container)
        head.setContentsMargins(20, 0, 20, 0)
        
        back = QPushButton("← Back to List")
        back.setStyleSheet(GHOST_BTN)
        back.clicked.connect(self.back_requested.emit)
        head.addWidget(back)
        head.addStretch()
        layout.addWidget(head_container)

        content = QHBoxLayout()
        
        # Left Column
        left = QFrame()
        left.setFixedWidth(320)
        left.setStyleSheet(f"background: {SURF_CARD}; border-right: 1px solid {SURF_HIGH};")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(30, 30, 30, 30)
        ll.setSpacing(15)
        
        # Profile Header
        self.av_big = AvatarWidget("??", 64, PRIMARY)
        av_wrap = QHBoxLayout(); av_wrap.addWidget(self.av_big); av_wrap.addStretch(); ll.addLayout(av_wrap)
        
        self.name_lbl = make_label("Customer Name", 20, ON_SURFACE, bold=True)
        ll.addWidget(self.name_lbl)
        
        tag_lay = QHBoxLayout()
        self.tag_pill = status_pill("REGULAR", ON_SURF_VAR, SURF_HIGH)
        tag_lay.addWidget(self.tag_pill); tag_lay.addStretch(); ll.addLayout(tag_lay)
        
        ll.addWidget(divider())
        
        # Info items
        def info_row(lbl, icon=""):
            row = QHBoxLayout()
            l = make_label(lbl, 12, ON_SURF_VAR)
            row.addWidget(l); row.addStretch()
            return l

        self.phone_lbl = info_row("Phone")
        self.email_lbl = info_row("Email")
        self.addr_lbl = info_row("Address")
        self.addr_lbl.setWordWrap(True)
        self.dob_lbl = info_row("DOB")
        self.joined_lbl = info_row("Joined")
        
        ll.addWidget(divider())
        
        self.points_lbl = make_label("0 ★ Points", 16, "#ffb300", bold=True)
        ll.addWidget(self.points_lbl)
        
        ll.addStretch()
        
        edit_btn = QPushButton("Edit Profile")
        edit_btn.setStyleSheet(GHOST_BTN)
        edit_btn.clicked.connect(self._on_edit)
        ll.addWidget(edit_btn)
        
        pay_btn = QPushButton("Take Payment")
        pay_btn.setStyleSheet(PRIMARY_BTN)
        ll.addWidget(pay_btn)
        
        content.addWidget(left)
        
        # Center Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: white; }
            QTabBar::tab { padding: 15px 25px; background: transparent; color: #64748b; font-weight: bold; }
            QTabBar::tab:selected { color: #002045; border-bottom: 3px solid #002045; }
        """)
        
        content.addWidget(self.tabs, 1)
        
        # Right Sidebar (Recent Interactions)
        right = QFrame()
        right.setFixedWidth(260)
        right.setStyleSheet(f"background: {SURF_CARD}; border-left: 1px solid {SURF_HIGH};")
        rl = QVBoxLayout(right)
        rl.addWidget(make_label("Recent Interactions", 13, ON_SURFACE, bold=True))
        
        self.quick_inter_lay = QVBoxLayout()
        rl.addLayout(self.quick_inter_lay)
        rl.addStretch()
        
        view_all = QPushButton("View All Interactions →")
        view_all.setStyleSheet(f"color: {PRIMARY}; border: none; text-align: left; font-weight: 600;")
        rl.addWidget(view_all)
        
        content.addWidget(right)
        layout.addLayout(content)

        # Tab Setup (Lazy init later or placeholders)
        self._init_tabs()

    def _init_tabs(self):
        self.tab_ov = QWidget(); self.tabs.addTab(self.tab_ov, "Overview")
        self.tab_hist = QWidget(); self.tabs.addTab(self.tab_hist, "History")
        self.tab_an = QWidget(); self.tabs.addTab(self.tab_an, "Analytics")
        self.tab_pref = QWidget(); self.tabs.addTab(self.tab_pref, "Preferences")
        self.tab_inter = QWidget(); self.tabs.addTab(self.tab_inter, "Interactions")
        self.tab_loy = QWidget(); self.tabs.addTab(self.tab_loy, "Loyalty")

    def _load_data(self):
        c = self.customer
        self.name_lbl.setText(c.name)
        self.av_big.initials = (c.name[0] + (c.name.split()[-1][0] if ' ' in c.name else "")).upper()
        
        tag_name = c.tags[0].name if c.tags else "Regular"
        self.tag_pill.setText(tag_name.upper())
        self.tag_pill.setStyleSheet(f"color: {self.service.TAG_COLORS.get(tag_name, PRIMARY)}; background: {SEC_CONTAINER}; border-radius: 4px; padding: 3px 10px;")
        
        self.phone_lbl.setText(f"📞  {c.phone}")
        self.email_lbl.setText(f"✉  {c.email or 'No Email'}")
        self.addr_lbl.setText(f"📍  {c.address or 'No Address'}")
        self.dob_lbl.setText(f"🎂  {c.dob or 'Not set'}")
        self.joined_lbl.setText(f"🗓  Joined {c.created_at.strftime('%d %b %Y') if c.created_at else '—'}")
        
        points = c.loyalty.available_points if c.loyalty else 0
        self.points_lbl.setText(f"{points} ★ Points")
        
        self._refresh_quick_interactions()
        self._render_overview_tab()

    def _refresh_quick_interactions(self):
        # Clear
        while self.quick_inter_lay.count():
            item = self.quick_inter_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        inters = self.service.get_interactions(self.customer.id, limit=5)
        for inter in inters:
            row = QFrame()
            row.setStyleSheet(f"border-bottom: 1px solid {SURF_HIGH}; padding: 8px 0;")
            l = QVBoxLayout(row)
            title = make_label(inter.type, 11, ON_SURFACE, bold=True)
            desc = make_label(inter.content[:30] + "...", 10, ON_SURF_VAR)
            l.addWidget(title); l.addWidget(desc)
            self.quick_inter_lay.addWidget(row)

    def _render_overview_tab(self):
        # Implementation of Tab 1
        lay = QVBoxLayout(self.tab_ov)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(20)
        
        stats = self.service.get_customer_stats(self.customer.id)
        
        grid = QGridLayout()
        stat_data = [
            ("TOTAL PURCHASE", f"₹{stats['total_purchase']:,.2f}"),
            ("TOTAL ORDERS", str(stats['total_orders'])),
            ("AVG BILL VALUE", f"₹{stats['avg_bill']:,.2f}"),
            ("LAST VISIT", relative_time(stats['last_visit']))
        ]
        
        for i, (l, v) in enumerate(stat_data):
            f = card()
            fv = QVBoxLayout(f)
            fv.addWidget(make_label(l, 9, ON_SURF_VAR, bold=True))
            fv.addWidget(make_label(v, 16, ON_SURFACE, bold=True))
            grid.addWidget(f, 0, i)
        lay.addLayout(grid)
        
        # Recent Invoices Placeholder
        lay.addWidget(make_label("Recent Invoices", 13, ON_SURFACE, bold=True))
        table = QTableWidget(5, 5)
        table.setHorizontalHeaderLabels(["ID", "DATE", "ITEMS", "TOTAL", "STATUS"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lay.addWidget(table)
        
        # Actions
        btns = QHBoxLayout()
        wa = QPushButton("Send WhatsApp")
        wa.setStyleSheet(SECONDARY_BTN); wa.clicked.connect(lambda: WhatsAppDialog(self.customer.name, self.customer.phone, self).exec_())
        offer = QPushButton("Send Offer / Message")
        offer.setStyleSheet(PRIMARY_BTN)
        btns.addWidget(wa); btns.addWidget(offer); btns.addStretch()
        lay.addLayout(btns)
        lay.addStretch()

    def _on_edit(self):
        dlg = AddCustomerDialog(self.service, customer=self.customer)
        if dlg.exec_():
            self.customer = self.service.get_customer_by_id(self.customer.id)
            self._load_data()

class CRMScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.service = CRMService()
        self._build()

    def _build(self):
        self.setContentsMargins(0, 0, 0, 0)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Content Wrapper
        self.stack = QStackedWidget()
        
        # Page 1: List View
        self.page_list = QWidget()
        self.list_layout = QHBoxLayout(self.page_list)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        
        self.customer_list = CustomerListPanel(self.service)
        self.customer_list.row_clicked.connect(self._show_profile)
        self.list_layout.addWidget(self.customer_list, 2)
        
        self.overview = CustomerOverviewPanel(self.service)
        self.list_layout.addWidget(self.overview, 0)
        
        self.stack.addWidget(self.page_list)
        
        # Page 2: Profile View
        self.profile = CustomerProfilePanel(self.service)
        self.profile.back_requested.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.profile)
        
        self.main_layout.addWidget(self.stack)

    def _show_profile(self, customer):
        self.profile.set_customer(customer)
        self.stack.setCurrentIndex(1)
        
    def refresh_all(self):
        self.customer_list.refresh()
        self.overview.refresh()
