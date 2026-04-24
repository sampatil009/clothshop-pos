import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QGridLayout, QPushButton, QLineEdit, QLabel, 
                             QFrame, QMessageBox, QSizePolicy, 
                             QGraphicsDropShadowEffect, QInputDialog, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QDateEdit, QTextEdit, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer
from PyQt5.QtGui import QColor, QFont
from services.db import get_db, ProductModel
from services.sales_service import SalesService
from services.print_service import PrintService
from services.whatsapp_service import WhatsAppService
from models.data_models import Invoice, InvoiceItem
from ui.theme import (PRIMARY, SECONDARY, TERTIARY, ON_SURFACE, 
                                 ON_SURF_VAR, SURFACE, SURF_LOW, SURF_CARD, 
                                 SURF_HIGH, ERROR_BG, WARN_BG, SEC_CONTAINER, 
                                 PRIMARY_BTN, GHOST_BTN, CARD_STYLE,
                                 make_label, divider, status_pill, card)

class POSScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.cart_items = []
        self.products = []
        self.init_ui()
        self.load_products()

    def init_ui(self):
        # Professional background: neutral gray
        self.setObjectName("POSScreen")
        self.setStyleSheet("QWidget#POSScreen { background: #f8fafc; }")
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("background: transparent; border: none;")
        main_lay.addWidget(self._scroll)

        # Main Container
        container = QWidget()
        container.setObjectName("MainContainer")
        container.setStyleSheet("QWidget#MainContainer { background: white; border-radius: 8px; }")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(30, 20, 30, 30)
        lay.setSpacing(25)
        
        centering_lay = QHBoxLayout()
        centering_lay.addStretch()
        centering_lay.addWidget(container, 6)
        centering_lay.addStretch()
        
        centering_w = QWidget()
        centering_w.setLayout(centering_lay)
        self._scroll.setWidget(centering_w)

        # 1. Professional Header
        head_lay = QHBoxLayout()
        title = QLabel("Billing Dashboard")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0f172a;") # Slate 900
        head_lay.addWidget(title)
        head_lay.addStretch()
        lay.addLayout(head_lay)

        # 2. Top Info Grid (Compact)
        info_card = QFrame()
        info_card.setObjectName("InfoCard")
        info_card.setStyleSheet("QFrame#InfoCard { background: #f1f5f9; border-radius: 8px; border: 1px solid #e2e8f0; }")
        info_lay = QGridLayout(info_card)
        info_lay.setContentsMargins(20, 15, 20, 15)
        info_lay.setSpacing(15)

        # Labels above fields
        def add_field(label, row, col, widget=None):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #64748b; font-size: 13px; text-transform: uppercase;")
            info_lay.addWidget(lbl, row, col)
            if widget:
                widget.setStyleSheet("padding: 10px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
                info_lay.addWidget(widget, row + 1, col)
            return widget

        self.cust_name = QLineEdit()
        add_field("Customer Name", 0, 0, self.cust_name)

        self.cust_phone = QLineEdit()
        add_field("Mobile / Phone", 0, 1, self.cust_phone)

        # Invoice Info (Read-only values)
        inv_no_box = QVBoxLayout()
        add_field("Invoice No", 0, 2)
        self.order_id_lbl = QLabel("#INV-000")
        self.order_id_lbl.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: bold; padding: 5px 0;")
        info_lay.addWidget(self.order_id_lbl, 1, 2)

        add_field("Invoice Date", 0, 3)
        self.date_lbl = QLabel(datetime.now().strftime('%d-%b-%Y'))
        self.date_lbl.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: bold; padding: 5px 0;")
        info_lay.addWidget(self.date_lbl, 1, 3)

        lay.addWidget(info_card)

        # 3. Add Item Bar (Flush labels)
        bar_card = QFrame()
        bar_card.setObjectName("AddBar")
        bar_card.setStyleSheet("QFrame#AddBar { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; }")
        bar_lay = QHBoxLayout(bar_card)
        bar_lay.setContentsMargins(15, 10, 15, 10)
        bar_lay.setSpacing(10)

        # Product Selector - QLineEdit + inline QListWidget dropdown
        prod_v = QVBoxLayout()
        prod_v.setSpacing(0)
        prod_lbl = QLabel("SELECT PRODUCT")
        prod_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold; margin-bottom: 4px;")
        prod_v.addWidget(prod_lbl)
        
        self._selected_product = None
        self.prod_search = QLineEdit()
        self.prod_search.setPlaceholderText("Click to search products...")
        self.prod_search.setStyleSheet("padding: 8px 12px; background: white; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px;")
        self.prod_search.textChanged.connect(self._filter_products)
        self.prod_search.setProperty("has_dropdown", True)  # Exempts from global nav filter
        self.prod_search.installEventFilter(self)
        prod_v.addWidget(self.prod_search)
        
        # Floating overlay dropdown list — child of scroll viewport so it overlays without shifting layout
        self.prod_list = QListWidget(self._scroll.viewport())
        self.prod_list.setFocusPolicy(Qt.NoFocus)
        self.prod_list.setFont(QFont("Segoe UI", 13))
        self.prod_list.setVisible(False)
        self.prod_list.setStyleSheet("""
            QListWidget { background: white; border: 1px solid #cbd5e1; border-radius: 0 0 6px 6px; outline: none; }
            QListWidget::item { padding: 10px 15px; min-height: 38px; font-size: 14px; border-bottom: 1px solid #f1f5f9; }
            QListWidget::item:selected { background: #e2e8f0; color: #0f172a; }
            QListWidget::item:hover { background: #f8fafc; }
        """)
        self.prod_list.itemClicked.connect(self.on_product_selected)
        
        bar_lay.addLayout(prod_v, 4)

        # Qty
        qty_v = QVBoxLayout()
        qty_lbl = QLabel("QTY")
        qty_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold;")
        qty_v.addWidget(qty_lbl)
        self.qty_input = QLineEdit()
        self.qty_input.setFixedWidth(80)
        self.qty_input.setStyleSheet("padding: 8px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        qty_v.addWidget(self.qty_input)
        bar_lay.addLayout(qty_v, 1)

        # Rate
        rate_v = QVBoxLayout()
        rate_lbl = QLabel("RATE")
        rate_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: bold;")
        rate_v.addWidget(rate_lbl)
        self.rate_input = QLineEdit()
        self.rate_input.setFixedWidth(100)
        self.rate_input.setStyleSheet("padding: 8px; background: white; border: 1px solid #cbd5e1; border-radius: 6px;")
        rate_v.addWidget(self.rate_input)
        bar_lay.addLayout(rate_v, 1)

        # Add Button
        add_btn = QPushButton("+ ADD ITEM")
        add_btn.setStyleSheet("background: #10b981; color: white; font-weight: bold; border-radius: 6px; padding: 12px 20px; margin-top: 15px;")
        add_btn.clicked.connect(self.add_from_selector)
        bar_lay.addWidget(add_btn)

        lay.addWidget(bar_card)

        # 4. Table
        self.table = QTableWidget(0, 5)
        self.table.setFont(QFont("Segoe UI", 12))
        self.table.setHorizontalHeaderLabels(["Item", "Qty", "Rate", "Amount", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setColumnWidth(4, 70)
        self.table.setStyleSheet("""
            QTableWidget { font-size: 14px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; gridline-color: #f1f5f9; }
            QHeaderView::section { background: #1e293b; color: white; padding: 12px; border: none; font-weight: bold; font-size: 13px; }
            QTableWidget::item { padding: 8px 15px; border-bottom: 1px solid #f1f5f9; }
        """)
        self.table.setMinimumHeight(350)
        lay.addWidget(self.table)

        # 5. Bottom Section: Notes & Finisher
        footer_lay = QHBoxLayout()
        footer_lay.setSpacing(40)

        # Notes (Left)
        notes_v = QVBoxLayout()
        notes_v.addWidget(make_label("CUSTOMER NOTES", 13, "#64748b", bold=True))
        self.cust_notes = QLineEdit()
        self.cust_notes.setPlaceholderText("Optional notes for the invoice...")
        self.cust_notes.setStyleSheet("padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px;")
        notes_v.addWidget(self.cust_notes)
        notes_v.addStretch()
        footer_lay.addLayout(notes_v, 2)

        checkout_v = QVBoxLayout()
        checkout_v.setSpacing(5)
        
        summary_card = QFrame()
        summary_card.setObjectName("SummaryCard")
        summary_card.setStyleSheet("QFrame#SummaryCard { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; }")
        summ_lay = QVBoxLayout(summary_card)
        self.subtotal_lbl = self._add_pro_row(summ_lay, "SUBTOTAL")
        
        # Discount row
        disc_row = QHBoxLayout()
        disc_row.setSpacing(8)
        
        disc_lbl = QLabel("DISCOUNT")
        disc_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold;")
        
        # Input + % suffix wrapped together
        disc_input_wrap = QFrame()
        disc_input_wrap.setStyleSheet("QFrame { background: white; border: 1px solid #cbd5e1; border-radius: 6px; }")
        disc_input_inner = QHBoxLayout(disc_input_wrap)
        disc_input_inner.setContentsMargins(8, 0, 8, 0)
        disc_input_inner.setSpacing(4)
        
        self.discount_input = QLineEdit()
        self.discount_input.setText("0")
        self.discount_input.setFixedWidth(55)
        self.discount_input.setAlignment(Qt.AlignCenter)
        self.discount_input.setStyleSheet("border: none; background: transparent; font-size: 15px; font-weight: bold; color: #0f172a; padding: 8px 0;")
        self.discount_input.textChanged.connect(self.render_table)
        
        disc_suffix = QLabel("%")
        disc_suffix.setStyleSheet("color: #64748b; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        
        disc_input_inner.addWidget(self.discount_input)
        disc_input_inner.addWidget(disc_suffix)
        
        self.discount_amt_lbl = QLabel("- ₹0.00")
        self.discount_amt_lbl.setStyleSheet("font-weight: bold; color: #10b981; font-size: 14px;")
        
        disc_row.addWidget(disc_lbl)
        disc_row.addWidget(disc_input_wrap)
        disc_row.addStretch()
        disc_row.addWidget(self.discount_amt_lbl)
        summ_lay.addLayout(disc_row)
        
        summ_lay.addWidget(divider())
        self.grand_total_lbl = self._add_pro_row(summ_lay, "GRAND TOTAL", grand=True)
        checkout_v.addWidget(summary_card)
        
        actions_lay = QHBoxLayout()
        self.btn_print = QPushButton("PRINT")
        self.btn_print.setStyleSheet("background: #334155; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
        
        self.btn_save = QPushButton("SAVE INVOICE")
        self.btn_save.setStyleSheet("background: #10b981; color: white; padding: 12px 30px; border-radius: 6px; font-weight: bold;")
        self.btn_save.clicked.connect(self.checkout)
        
        actions_lay.addWidget(self.btn_print)
        actions_lay.addWidget(self.btn_save)
        checkout_v.addLayout(actions_lay)
        
        footer_lay.addLayout(checkout_v, 1)
        lay.addLayout(footer_lay)

        self.update_order_id()

    def _add_pro_row(self, layout, label, grand=False):
        row = QHBoxLayout()
        lbl = QLabel(label)
        v_lbl = QLabel("₹0.00")
        if grand:
            lbl.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 14px;")
            v_lbl.setStyleSheet("font-weight: bold; color: #ef4444; font-size: 20px;")
        else:
            lbl.setStyleSheet("color: #64748b; font-size: 13px;")
            v_lbl.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 14px;")
        
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(v_lbl)
        layout.addLayout(row)
        return v_lbl

    def update_order_id(self):
        next_num = SalesService.get_next_invoice_number()
        self.order_id_lbl.setText(f"<b>Invoice No:</b> #{next_num}")

    def eventFilter(self, obj, event):
        """Handle keyboard navigation for product search dropdown."""
        if obj == self.prod_search and event.type() == QEvent.KeyPress:
            key = event.key()
            
            if key == Qt.Key_Down:
                if not self.prod_list.isVisible():
                    self._show_product_popup()
                count = self.prod_list.count()
                if count > 0:
                    cur = self.prod_list.currentRow()
                    self.prod_list.setCurrentRow(min(cur + 1, count - 1) if cur >= 0 else 0)
                return True
            
            elif key == Qt.Key_Up:
                if self.prod_list.isVisible():
                    cur = self.prod_list.currentRow()
                    if cur > 0:
                        self.prod_list.setCurrentRow(cur - 1)
                return True
            
            elif key in (Qt.Key_Return, Qt.Key_Enter):
                if self.prod_list.isVisible():
                    item = self.prod_list.currentItem()
                    if item:
                        self.on_product_selected(item)
                        return True
                # Dropdown closed but product selected — trigger add
                if self._selected_product:
                    self.add_from_selector()
                    return True
                return False
            
            elif key == Qt.Key_Escape:
                self._hide_product_popup()
                return True
        
        elif obj == self.prod_search:
            if event.type() == QEvent.FocusIn:
                self._show_product_popup()
            elif event.type() == QEvent.FocusOut:
                QTimer.singleShot(150, self._hide_product_popup)
        
        return super().eventFilter(obj, event)

    def _show_product_popup(self):
        if self.prod_list.count() == 0:
            return
        # Map prod_search bottom-left to the scroll viewport coordinate space
        vp = self._scroll.viewport()
        pos = self.prod_search.mapTo(vp, self.prod_search.rect().bottomLeft())
        w = self.prod_search.width()
        h = min(self.prod_list.count() * 48 + 8, 220)
        self.prod_list.setGeometry(pos.x(), pos.y(), w, h)
        self.prod_list.show()
        self.prod_list.raise_()

    def _hide_product_popup(self):
        self.prod_list.setVisible(False)

    def _filter_products(self, text):
        """Filter the dropdown list as the user types."""
        # Only clear selected product if user is actually typing something different
        if self._selected_product and text == self._selected_product.name:
            return  # Text was set by on_product_selected, don't re-filter
        self._selected_product = None
        self.prod_list.clear()
        text = text.strip().lower()
        matches = [p for p in self.products if text in p.name.lower()] if text else self.products
        for p in matches:
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, p)
            self.prod_list.addItem(item)
        self._show_product_popup()

    def load_products(self):
        db = get_db()
        try:
            self.products = db.query(ProductModel).all()
            self.prod_list.clear()
            for p in self.products:
                item = QListWidgetItem(p.name)
                item.setData(Qt.UserRole, p)
                self.prod_list.addItem(item)
        finally:
            db.close()

    def on_product_selected(self, list_item):
        """Called when a product is clicked or activated in the popup list."""
        p = list_item.data(Qt.UserRole)
        if p:
            self._selected_product = p
            # Block signals so setText doesn't trigger _filter_products and wipe _selected_product
            self.prod_search.blockSignals(True)
            self.prod_search.setText(p.name)
            self.prod_search.blockSignals(False)
            self.rate_input.setText(str(p.price))
            self.qty_input.setText("1")
            self._hide_product_popup()
            self.qty_input.setFocus()

    def add_from_selector(self):
        p = self._selected_product
        if not p:
            return
        try:
            qty = float(self.qty_input.text() or 1)
            rate = float(self.rate_input.text() or p.price)
            self.add_to_cart(p, qty, rate)
            
            self._selected_product = None
            self.prod_search.clear()
            self.rate_input.clear()
            self.qty_input.clear()
            self._hide_product_popup()
            self.prod_search.setFocus()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for quantity and rate.")



    def add_to_cart(self, product, qty=1, rate=None):
        if rate is None: rate = product.price
        
        found = False
        for item in self.cart_items:
            if item['id'] == product.id and item['price'] == rate:
                item['qty'] += qty
                found = True
                break
        
        if not found:
            self.cart_items.append({
                'id': product.id,
                'name': product.name,
                'hsn': product.hsn,
                'qty': qty,
                'price': rate,
                'gst_rate': product.gst_rate,
                'unit': product.unit
            })
        
        self.render_table()

    def render_table(self):
        self.table.setRowCount(0)
        subtotal = 0
        
        for i, item in enumerate(self.cart_items):
            self.table.insertRow(i)
            
            # Item
            item_lbl = QTableWidgetItem(item['name'])
            item_lbl.setForeground(QColor("#0f172a"))
            self.table.setItem(i, 0, item_lbl)
            
            # Qty
            qty_item = QTableWidgetItem(str(item['qty']))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, qty_item)
            
            # Rate
            rate_item = QTableWidgetItem(f"₹{item['price']:,.2f}")
            rate_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, rate_item)
            
            # Amount
            amt = item['qty'] * item['price']
            amt_item = QTableWidgetItem(f"₹{amt:,.2f}")
            amt_item.setTextAlignment(Qt.AlignCenter)
            amt_item.setForeground(QColor("#0f172a"))
            self.table.setItem(i, 3, amt_item)
            
            # Delete Btn Container
            cell_widget = QWidget()
            cell_lay = QHBoxLayout(cell_widget)
            cell_lay.setContentsMargins(0, 0, 0, 0)
            cell_lay.setAlignment(Qt.AlignCenter)
            
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(30, 30)
            del_btn.setStyleSheet("QPushButton { background: #fee2e2; color: #ef4444; border: 1px solid #fca5a5; border-radius: 6px; font-size: 16px; font-weight: bold; } QPushButton:hover { background: #ef4444; color: white; }")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            
            cell_lay.addWidget(del_btn)
            self.table.setCellWidget(i, 4, cell_widget)
            
            subtotal += amt
            
        # Discount
        try:
            disc_pct = float(self.discount_input.text() or 0)
        except ValueError:
            disc_pct = 0
        disc_pct = max(0, min(disc_pct, 100))
        discount_amt = subtotal * (disc_pct / 100)
        total = subtotal - discount_amt
        
        self.subtotal_lbl.setText(f"₹{subtotal:,.2f}")
        self.discount_amt_lbl.setText(f"- ₹{discount_amt:,.2f}")
        self.grand_total_lbl.setText(f"₹{total:,.2f}")

    def remove_item(self, index):
        if 0 <= index < len(self.cart_items):
            self.cart_items.pop(index)
            self.render_table()

    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Bill", "Please add items to the bill first.")
            return
            
        try:
            invoice_items = []
            subtotal = 0
            
            for item in self.cart_items:
                item_amt = item['qty'] * item['price']
                invoice_items.append(InvoiceItem(
                    product_id=item['id'],
                    product_name=item['name'],
                    hsn_code=item['hsn'],
                    quantity=item['qty'],
                    unit_price=item['price'],
                    gst_rate=5.0, # HTML spec
                    total=item_amt * 1.05
                ))
                subtotal += item_amt
            
            try:
                disc_pct = float(self.discount_input.text() or 0)
            except ValueError:
                disc_pct = 0
            disc_pct = max(0, min(disc_pct, 100))
            discount_amt = subtotal * (disc_pct / 100)
            grand_total = subtotal - discount_amt
                
            inv = Invoice(
                invoice_number=SalesService.get_next_invoice_number(),
                party_name=self.cust_name.text() or "Walk-in Customer",
                party_phone=self.cust_phone.text(),
                customer_address="",
                customer_notes=self.cust_notes.text(),
                due_date=datetime.now(),
                items=invoice_items,
                subtotal=subtotal,
                gst_total=0.0,
                cgst=0.0,
                sgst=0.0,
                grand_total=grand_total,
                status="Paid"
            )
            
            SalesService.create_invoice(inv)
            pdf_path = f"invoice_{inv.invoice_number.replace('-', '_')}.pdf"
            PrintService.generate_invoice_pdf(inv, pdf_path)
            
            # QMessageBox.information(self, "Success", f"Invoice created: {inv.invoice_number}")
                # Show success + offer WhatsApp send
            reply = QMessageBox.question(
                self, "Invoice Created",
                f"Invoice {inv.invoice_number} created!\n\nSend via WhatsApp?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                phone = self.cust_phone.text().strip()
                if not phone:
                    phone, ok = QInputDialog.getText(
                        self, "Customer Phone",
                        "Enter customer's WhatsApp number (10 digits):"
                    )
                    if not ok or not phone.strip():
                        return
                    phone = phone.strip()
                
                from services.whatsapp_service import WhatsAppService
                svc = WhatsAppService()
                result = svc.send_invoice_message(
                    phone=phone.strip(),
                    invoice_no=inv.invoice_number,
                    customer=inv.party_name,
                    amount=inv.grand_total,
                )
                if result["success"]:
                    QMessageBox.information(self, "WhatsApp Sent", "Invoice sent via WhatsApp!")
                else:
                    QMessageBox.warning(self, "WhatsApp Failed", result["message"])
            
            if sys.platform == "win32":
                os.startfile(pdf_path)
            
            self.clear_form()
            self.load_products() 
            self.update_order_id()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save invoice: {str(e)}")

    def clear_form(self):
        self.cart_items = []
        self.cust_name.clear()
        self.cust_phone.clear()
        self.cust_notes.clear()
        self.qty_input.clear()
        self.rate_input.clear()
        self.table.setRowCount(0)
        self.render_table()
        self.update_order_id()
