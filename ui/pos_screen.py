import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QGridLayout, QPushButton, QLineEdit, QLabel, 
                             QFrame, QMessageBox, QComboBox, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from fabricpos.services.db import get_db, ProductModel
from fabricpos.services.sales_service import SalesService
from fabricpos.services.print_service import PrintService
from fabricpos.models.data_models import Invoice, InvoiceItem
from fabricpos.ui.theme import (PRIMARY, SECONDARY, TERTIARY, ON_SURFACE, 
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
        self.setStyleSheet(f"background: {SURFACE};")
        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # ── Left: product area ──
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("background: transparent; border: none;")

        left_w = QWidget()
        left_w.setStyleSheet(f"background: {SURFACE};")
        self.left_lay = QVBoxLayout(left_w)
        self.left_lay.setContentsMargins(24, 24, 16, 24)
        self.left_lay.setSpacing(20)

        # Search / Category bar
        hdr = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Product / SKU...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.filter_products)
        hdr.addWidget(self.search_input)
        hdr.addStretch()
        self.left_lay.addLayout(hdr)

        # Product grid
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setSpacing(14)
        self.left_lay.addWidget(self.grid_container)
        self.left_lay.addStretch()

        left_scroll.setWidget(left_w)
        root.addWidget(left_scroll, 3)

        # ── Right: cart/order panel ──
        right_w = QWidget()
        right_w.setFixedWidth(360)
        right_w.setStyleSheet(f"background: {SURF_CARD}; border-left: 1px solid {SURF_HIGH};")
        right_lay = QVBoxLayout(right_w)
        right_lay.setContentsMargins(20, 20, 20, 20)
        right_lay.setSpacing(14)

        # Order header
        ord_hdr = QHBoxLayout()
        ord_hdr.addWidget(make_label("Current Order", 15, ON_SURFACE, bold=True))
        ord_hdr.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet(f"background: {ERROR_BG}; color: {TERTIARY}; border: none; border-radius: 4px; font-size: 11px; padding: 0 10px;")
        clear_btn.clicked.connect(self.clear_cart)
        ord_hdr.addWidget(clear_btn)
        right_lay.addLayout(ord_hdr)

        self.order_id_lbl = make_label("Order ID: #INV-LOADING", 11, ON_SURF_VAR)
        right_lay.addWidget(self.order_id_lbl)
        right_lay.addWidget(divider())

        # Customer selector
        right_lay.addWidget(make_label("Customer", 11, ON_SURF_VAR))
        self.cust_sel = QComboBox()
        self.cust_sel.addItems(["Walk-in Customer", "Regular Party"])
        right_lay.addWidget(self.cust_sel)

        # Cart items scroll
        cart_scroll = QScrollArea()
        cart_scroll.setWidgetResizable(True)
        cart_scroll.setStyleSheet("background: transparent; border: none;")
        
        cart_w = QWidget()
        cart_w.setStyleSheet("background: transparent;")
        self.cart_list_lay = QVBoxLayout(cart_w)
        self.cart_list_lay.setContentsMargins(0,0,0,0)
        self.cart_list_lay.setSpacing(8)
        self.cart_list_lay.addStretch()
        
        cart_scroll.setWidget(cart_w)
        right_lay.addWidget(cart_scroll, 1)
        right_lay.addWidget(divider())

        # Totals
        self.subtotal_lbl = self._add_stat_row(right_lay, "Subtotal", "₹0")
        self.gst_lbl = self._add_stat_row(right_lay, "Tax (GST)", "₹0")
        right_lay.addWidget(divider())
        
        total_row = QHBoxLayout()
        total_row.addWidget(make_label("Total", 15, ON_SURFACE, bold=True))
        total_row.addStretch()
        self.grand_total_lbl = make_label("₹0", 18, PRIMARY, bold=True)
        total_row.addWidget(self.grand_total_lbl)
        right_lay.addLayout(total_row)
        
        # Actions
        right_lay.addWidget(make_label("PAYMENT MODE", 10, ON_SURF_VAR))
        pay_row = QHBoxLayout()
        self.pay_mode = QComboBox()
        self.pay_mode.addItems(["Cash", "Card", "UPI", "Credit"])
        self.pay_mode.setFixedHeight(38)
        pay_row.addWidget(self.pay_mode)
        right_lay.addLayout(pay_row)

        self.checkout_btn = QPushButton("PROCESS & PRINT RECEIPT")
        self.checkout_btn.setFixedHeight(46)
        self.checkout_btn.setStyleSheet(PRIMARY_BTN)
        self.checkout_btn.clicked.connect(self.checkout)
        right_lay.addWidget(self.checkout_btn)

        root.addWidget(right_w)
        self.update_order_id()

    def _add_stat_row(self, layout, label, val):
        row = QHBoxLayout()
        row.addWidget(make_label(label, 13, ON_SURF_VAR))
        row.addStretch()
        v_lbl = make_label(val, 13, ON_SURFACE)
        row.addWidget(v_lbl)
        layout.addLayout(row)
        return v_lbl

    def update_order_id(self):
        self.order_id_lbl.setText(f"Order ID: #INV-{datetime.now().strftime('%m%d%H%M')}")

    def load_products(self):
        db = get_db()
        try:
            self.products = db.query(ProductModel).all()
            self.update_grid(self.products)
        finally:
            db.close()

    def update_grid(self, products):
        # Clear existing grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, p in enumerate(products):
            card = self._make_product_card(p)
            self.grid.addWidget(card, i // 3, i % 3)

    def filter_products(self, text):
        filtered = [p for p in self.products if text.lower() in p.name.lower() or text.lower() in p.sku.lower()]
        self.update_grid(filtered)

    def _make_product_card(self, p):
        f = QFrame()
        f.setObjectName("ProductCard")
        f.setMinimumHeight(140)
        
        # Modern Card Style with hover transition effect (via QSS)
        f.setStyleSheet(f"""
            QFrame#ProductCard {{ 
                background: {SURF_CARD}; 
                border-radius: 12px; 
                border: 1px solid {SURF_HIGH};
            }}
            QFrame#ProductCard:hover {{ 
                background: #ffffff; 
                border: 1px solid {SECONDARY};
            }}
        """)
        
        # Add Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 20)) # Very subtle shadow
        f.setGraphicsEffect(shadow)

        lay = QVBoxLayout(f)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        # Status Badge
        badge_row = QHBoxLayout()
        if p.stock_quantity <= 0:
            badge = status_pill("OUT OF STOCK", TERTIARY, ERROR_BG)
        elif p.stock_quantity < 10:
            badge = status_pill("LOW STOCK", "#b45309", "#fef3c7")
        else:
            badge = status_pill("IN STOCK", SECONDARY, SEC_CONTAINER)
        badge_row.addWidget(badge)
        badge_row.addStretch()
        lay.addLayout(badge_row)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(2)
        info_lay.addWidget(make_label(p.name, 14, ON_SURFACE, bold=True))
        info_lay.addWidget(make_label(f"SKU: {p.sku}", 10, ON_SURF_VAR))
        lay.addLayout(info_lay)

        price_row = QHBoxLayout()
        price_row.addWidget(make_label(f"₹{p.price:,.2f}", 16, PRIMARY, bold=True))
        price_row.addStretch()
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {PRIMARY}; color: white; border-radius: 16px; 
                font-size: 18px; font-weight: bold; border: none;
            }}
            QPushButton:hover {{ background: {SECONDARY}; }}
        """)
        add_btn.clicked.connect(lambda _, prod=p: self.add_to_cart(prod))
        price_row.addWidget(add_btn)
        lay.addLayout(price_row)
        
        return f

    def add_to_cart(self, product):
        if product.stock_quantity <= 0:
            QMessageBox.warning(self, "Out of Stock", "This item is currently out of stock.")
            return

        found = False
        for item in self.cart_items:
            if item['id'] == product.id:
                item['qty'] += 1
                found = True
                break
        
        if not found:
            self.cart_items.append({
                'id': product.id,
                'name': product.name,
                'qty': 1,
                'price': product.price,
                'gst_rate': product.gst_rate
            })
        
        self.render_cart()

    def render_cart(self):
        # Clear list layout (except stretch at the bottom)
        while self.cart_list_lay.count() > 1:
            item = self.cart_list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        subtotal = 0
        gst_total = 0
        
        for i, item in enumerate(self.cart_items):
            row_w = QWidget()
            row_w.setStyleSheet(f"background: {SURF_LOW}; border-radius: 6px;")
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(10, 8, 10, 8)
            
            info = QVBoxLayout()
            info.addWidget(make_label(item['name'], 12, ON_SURFACE, bold=True))
            info.addWidget(make_label(f"Qty: {item['qty']} x ₹{item['price']:.2f}", 10, ON_SURF_VAR))
            row_lay.addLayout(info)
            row_lay.addStretch()

            item_total = item['qty'] * item['price']
            item_gst = item_total * (item['gst_rate'] / 100)
            row_lay.addWidget(make_label(f"₹{item_total + item_gst:.2f}", 13, PRIMARY, bold=True))
            
            self.cart_list_lay.insertWidget(i, row_w)
            subtotal += item_total
            gst_total += item_gst
            
        grand_total = subtotal + gst_total
        self.subtotal_lbl.setText(f"₹{subtotal:.2f}")
        self.gst_lbl.setText(f"₹{gst_total:.2f}")
        self.grand_total_lbl.setText(f"₹{grand_total:.2f}")

    def clear_cart(self):
        self.cart_items = []
        self.render_cart()

    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "Please add products to the cart first.")
            return
            
        try:
            invoice_items = []
            subtotal = 0
            gst_total = 0
            
            for item in self.cart_items:
                item_sub = item['qty'] * item['price']
                item_gst = item_sub * (item['gst_rate'] / 100)
                invoice_items.append(InvoiceItem(
                    product_id=item['id'],
                    product_name=item['name'],
                    quantity=item['qty'],
                    unit_price=item['price'],
                    gst_rate=item['gst_rate'],
                    total=item_sub + item_gst
                ))
                subtotal += item_sub
                gst_total += item_gst
                
            inv = Invoice(
                invoice_number=f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                party_name=self.cust_sel.currentText(),
                items=invoice_items,
                subtotal=subtotal,
                gst_total=gst_total,
                grand_total=subtotal + gst_total,
                payment_mode=self.pay_mode.currentText()
            )
            
            SalesService.create_invoice(inv)
            pdf_path = f"invoice_{inv.invoice_number}.pdf"
            PrintService.generate_invoice_pdf(inv, pdf_path)
            
            QMessageBox.information(self, "Success", f"Invoice created: {inv.invoice_number}")
            
            if sys.platform == "win32":
                os.startfile(pdf_path)
            
            self.clear_cart()
            self.load_products() 
            self.update_order_id()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Checkout failed: {str(e)}")
