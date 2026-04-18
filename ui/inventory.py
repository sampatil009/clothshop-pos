from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, 
                             QFormLayout, QDialog, QMessageBox, QLabel, QFrame,
                             QAbstractItemView, QProgressBar)
from PyQt5.QtCore import Qt
from services.db import get_db, ProductModel
from ui.theme import (PRIMARY, SECONDARY, TERTIARY, ON_SURFACE, 
                                ON_SURF_VAR, SURFACE, SURF_CARD, SURF_HIGH, 
                                SURF_LOW, SUCCESS_BG, WARN_BG, ERROR_BG, SEC_CONTAINER, PRIMARY_BTN,
                                GHOST_BTN, CARD_STYLE, make_label, status_pill)

class InventoryScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        self.setStyleSheet(f"background: {SURFACE};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(20)

        # Metric row
        m_row = QHBoxLayout()
        m_row.setSpacing(14)

        # 1. Total Value Card
        self.total_val_card = QFrame()
        self.total_val_card.setStyleSheet(CARD_STYLE)
        inv_lay = QHBoxLayout(self.total_val_card)
        inv_lay.setContentsMargins(20,18,20,18)
        left_v = QVBoxLayout()
        left_v.setSpacing(4)
        left_v.addWidget(make_label("TOTAL INVENTORY VALUE", 10, ON_SURF_VAR))
        self.total_val_lbl = make_label("₹0", 26, ON_SURFACE, bold=True)
        left_v.addWidget(self.total_val_lbl)
        left_v.addWidget(make_label("Live Valuation", 11, SECONDARY))
        inv_lay.addLayout(left_v)
        inv_lay.addStretch()
        m_row.addWidget(self.total_val_card, 2)

        # 2. Stock Alerts Card
        self.alerts_card = QFrame()
        self.alerts_card.setStyleSheet(f"background: {WARN_BG}; border-radius: 8px;")
        al_lay = QVBoxLayout(self.alerts_card)
        al_lay.setContentsMargins(20,18,20,18)
        al_lay.addWidget(make_label("STOCK ALERTS", 10, TERTIARY))
        self.alerts_lbl = make_label("0", 28, TERTIARY, bold=True)
        al_lay.addWidget(self.alerts_lbl)
        al_lay.addWidget(make_label("LOW STOCK ITEMS", 11, TERTIARY))
        m_row.addWidget(self.alerts_card, 1)

        # 3. New Arrivals Card (Placeholder for logic)
        self.count_card = QFrame()
        self.count_card.setStyleSheet(f"background: {SUCCESS_BG}; border-radius: 8px;")
        cl_lay = QVBoxLayout(self.count_card)
        cl_lay.setContentsMargins(20,18,20,18)
        cl_lay.addWidget(make_label("UNIQUE SKUS", 10, SECONDARY))
        self.sku_count_lbl = make_label("0", 28, SECONDARY, bold=True)
        cl_lay.addWidget(self.sku_count_lbl)
        cl_lay.addWidget(make_label("ACTIVE PRODUCTS", 11, SECONDARY))
        m_row.addWidget(self.count_card, 1)
        
        lay.addLayout(m_row)

        # Toolbar
        tool_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by product name or SKU...")
        self.search_input.setFixedWidth(350)
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self.filter_data)
        tool_row.addWidget(self.search_input)
        tool_row.addStretch()

        self.add_btn = QPushButton("+ Add New Product")
        self.add_btn.setFixedHeight(38)
        self.add_btn.setStyleSheet(PRIMARY_BTN)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.show_add_product_dialog)
        tool_row.addWidget(self.add_btn)
        lay.addLayout(tool_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["PRODUCT DETAILS", "SKU", "HSN", "PRICE", "STOCK", "STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        lay.addWidget(self.table)

    def load_data(self):
        db = get_db()
        try:
            products = db.query(ProductModel).all()
            
            total_val = 0
            low_stock = 0
            
            self.table.setRowCount(0)
            for i, prod in enumerate(products):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setRowHeight(row, 60)
                
            total_val = 0
            low_stock = 0
            
            self.table.setRowCount(0)
            for i, prod in enumerate(products):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setRowHeight(row, 60)
                
                # Data calc
                total_val += (prod.price * prod.stock_quantity)
                if prod.stock_quantity < 10: low_stock += 1
                
                # Product details (Column 0)
                self.table.setItem(row, 0, QTableWidgetItem(prod.name))
                self.table.setItem(row, 1, QTableWidgetItem(prod.sku))
                self.table.setItem(row, 2, QTableWidgetItem(prod.hsn or "---"))
                self.table.setItem(row, 3, QTableWidgetItem(f"₹{prod.price:,.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(str(prod.stock_quantity)))
                
                # Status Pill (Column 5)
                badge_container = QWidget()
                bcl = QHBoxLayout(badge_container)
                if prod.stock_quantity <= 0:
                    pill = status_pill("OUT OF STOCK", TERTIARY, ERROR_BG)
                elif prod.stock_quantity < 10:
                    pill = status_pill("LOW STOCK", "#b45309", "#fef3c7")
                else:
                    pill = status_pill("IN STOCK", SECONDARY, SEC_CONTAINER)
                bcl.addWidget(pill)
                bcl.setAlignment(Qt.AlignCenter)
                bcl.setContentsMargins(0,0,0,0)
                self.table.setCellWidget(row, 5, badge_container)

            # Update stats
            self.total_val_lbl.setText(f"₹{total_val:,.2f}")
            self.alerts_lbl.setText(str(low_stock))
            self.sku_count_lbl.setText(str(len(products)))
        finally:
            db.close()

    def filter_data(self, text):
        for i in range(self.table.rowCount()):
            match = False
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(i, not match)

    def show_add_product_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Product")
        dialog.setFixedWidth(400)
        dialog_layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        name_in = QLineEdit()
        sku_in = QLineEdit()
        hsn_in = QLineEdit()
        price_in = QLineEdit()
        stock_in = QLineEdit()
        stock_in.setText("0")
        
        form.addRow("Product Name:", name_in)
        form.addRow("SKU/Barcode:", sku_in)
        form.addRow("HSN Code:", hsn_in)
        form.addRow("Price:", price_in)
        form.addRow("Initial Stock:", stock_in)
        
        dialog_layout.addLayout(form)
        
        save_btn = QPushButton("Save Product")
        save_btn.setStyleSheet(PRIMARY_BTN)
        save_btn.clicked.connect(lambda: self.save_product(dialog, name_in, sku_in, hsn_in, price_in, stock_in))
        dialog_layout.addWidget(save_btn)
        
        dialog.exec_()

    def save_product(self, dialog, name_in, sku_in, hsn_in, price_in, stock_in):
        try:
            db = get_db()
            new_prod = ProductModel(
                name=name_in.text(),
                sku=sku_in.text(),
                hsn=hsn_in.text(),
                price=float(price_in.text() or 0),
                stock_quantity=int(stock_in.text() or 0)
            )
            db.add(new_prod)
            db.commit()
            dialog.accept()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save product: {str(e)}")
