import os
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QLineEdit, 
    QLabel, QFrame, QGridLayout, QDateEdit, QComboBox, 
    QAbstractItemView, QGraphicsDropShadowEffect, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QPolygonF

# Namespace handling
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.theme import (
    PRIMARY, PRIMARY_DARK, PRIMARY_CONT, SECONDARY, SEC_LIGHT, SEC_CONTAINER,
    TERTIARY, SURFACE, SURF_LOW, SURF_CARD, SURF_HIGH, ON_SURFACE, ON_SURF_VAR,
    OUTLINE, ERROR_BG, SUCCESS_BG, WARN_BG,
    APP_STYLE, PRIMARY_BTN, SECONDARY_BTN, GHOST_BTN, CARD_STYLE, 
    make_label, divider, status_pill, card, spacer
)
from services.report_service import ReportService
from services.export_service import ExportService

# ─── CUSTOM CHART WIDGETS ─────────────────────────────────────────────────────

class BaseChartWidget(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self.setMinimumHeight(280)
        self.setStyleSheet(CARD_STYLE)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Title
        painter.setPen(QColor(ON_SURFACE))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(20, 30, self.title)

class DonutChart(BaseChartWidget):
    def __init__(self, title, colors=None):
        super().__init__(title)
        self.colors = colors or [SECONDARY, PRIMARY, TERTIARY, "#ffb300", "#9c27b0", "#607d8b"]

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.data: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Donut dimensions
        margin = 60
        rect_size = min(self.width() // 2, self.height() - 100)
        rect = QRectF(40, 60, rect_size, rect_size)
        
        total = sum(d['value'] for d in self.data) or 1
        start_angle = 90 * 16
        
        for i, d in enumerate(self.data):
            span_angle = -int((d['value'] / total) * 360 * 16)
            
            painter.setBrush(QBrush(QColor(self.colors[i % len(self.colors)])))
            painter.setPen(Qt.NoPen)
            painter.drawPie(rect, start_angle, span_angle)
            
            # Legend
            lx = rect_size + 80
            ly = 80 + (i * 25)
            painter.drawEllipse(lx, ly, 10, 10)
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(ON_SURF_VAR))
            painter.drawText(lx + 20, ly + 10, f"{d.get('mode') or d.get('category')}: {d.get('percent', 0)}%")
            
            start_angle += span_angle
            
        # Draw Inner Hole
        painter.setBrush(QBrush(QColor(SURF_CARD)))
        painter.drawEllipse(rect.adjusted(rect_size/4, rect_size/4, -rect_size/4, -rect_size/4))

class LineChart(BaseChartWidget):
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.data: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Grid area
        gx, gy = 50, 60
        gw, gh = self.width() - 100, self.height() - 120
        
        max_val = max(d['value'] for d in self.data) or 1
        points = []
        for i, d in enumerate(self.data):
            px = gx + (i * (gw / (len(self.data) - 1 if len(self.data) > 1 else 1)))
            py = gy + gh - (d['value'] / max_val * gh)
            points.append(QPointF(px, py))
            
        # Draw Area Gradient
        path = QPolygonF(points)
        path.append(QPointF(points[-1].x(), gy + gh))
        path.append(QPointF(points[0].x(), gy + gh))
        
        grad = QLinearGradient(0, gy, 0, gy + gh)
        grad.setColorAt(0, QColor(SEC_LIGHT))
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(path)
        
        # Draw Line
        painter.setPen(QPen(QColor(SECONDARY), 2.5))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])
            
        # X-Axis Labels (Every 5th if many)
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(QColor(ON_SURF_VAR))
        for i, d in enumerate(self.data):
            if len(self.data) > 10 and i % 5 != 0: continue
            px = gx + (i * (gw / (len(self.data) - 1 if len(self.data) > 1 else 1)))
            painter.drawText(int(px - 15), gy + gh + 20, d['label'][-5:])

class BarChart(BaseChartWidget):
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.data: return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gx, gy = 50, 60
        gw, gh = self.width() - 100, self.height() - 120
        
        max_val = max(d['value'] for d in self.data) or 1
        bar_w = (gw / len(self.data)) * 0.6
        spacing = (gw / len(self.data)) * 0.4
        
        for i, d in enumerate(self.data):
            bh = (d['value'] / max_val) * gh
            bx = gx + (i * (bar_w + spacing)) + (spacing / 2)
            by = gy + gh - bh
            
            painter.setBrush(QBrush(QColor(SECONDARY)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 4, 4)
            
            # Label
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(ON_SURF_VAR))
            painter.drawText(int(bx), gy + gh + 20, d['label'])

# ─── KPI CARD ─────────────────────────────────────────────────────────────────

class KPICard(QFrame):
    def __init__(self, title, value, trend, icon_char, color=PRIMARY):
        super().__init__()
        self.setStyleSheet(CARD_STYLE)
        self.setMinimumHeight(110)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 15, 15, 15)
        
        header = QHBoxLayout()
        header.addWidget(make_label(title, 10, ON_SURF_VAR, bold=True))
        header.addStretch()
        icon = make_label(icon_char, 14, color)
        icon.setFont(QFont("Segoe UI Symbol", 14))
        header.addWidget(icon)
        lay.addLayout(header)
        
        self.val_lbl = make_label(value, 18, ON_SURFACE, bold=True)
        lay.addWidget(self.val_lbl)
        
        trend_lay = QHBoxLayout()
        arrow = "↑" if trend >= 0 else "↓"
        trend_color = SECONDARY if trend >= 0 else TERTIARY
        self.trend_lbl = make_label(f"{arrow} {abs(trend)}% vs last period", 9, trend_color, bold=True)
        trend_lay.addWidget(self.trend_lbl)
        trend_lay.addStretch()
        lay.addLayout(trend_lay)

# ─── REPORTS SCREEN ───────────────────────────────────────────────────────────

class ReportsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.service = ReportService()
        self._build()
        self.refresh_data()

    def _build(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(24)

        # 1. Header Area
        header = QHBoxLayout()
        title_v = QVBoxLayout()
        title_v.addWidget(make_label("Performance Reports", 22, ON_SURFACE, bold=True))
        title_v.addWidget(make_label("Analyze your business performance and make data-driven decisions", 11, ON_SURF_VAR))
        header.addLayout(title_v)
        header.addStretch()
        
        # Search Placeholder
        search = QLineEdit()
        search.setPlaceholderText("Search reports...")
        search.setFixedWidth(240)
        header.addWidget(search)
        self.layout.addLayout(header)

        # 2. Controls Area
        controls = QHBoxLayout()
        
        # Date Picker Group
        date_group = QFrame()
        date_group.setStyleSheet(f"background: {SURF_CARD}; border-radius: 8px; padding: 5px;")
        dg_lay = QHBoxLayout(date_group)
        self.start_date = QDateEdit(datetime.now() - timedelta(days=30))
        self.end_date = QDateEdit(datetime.now())
        dg_lay.addWidget(make_label("📅", 11))
        dg_lay.addWidget(self.start_date)
        dg_lay.addWidget(make_label("-", 11))
        dg_lay.addWidget(self.end_date)
        controls.addWidget(date_group)
        
        self.compare_box = QComboBox()
        self.compare_box.addItems(["Previous Period", "Previous Year", "None"])
        self.compare_box.setFixedWidth(180)
        controls.addWidget(self.compare_box)
        
        controls.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(GHOST_BTN)
        refresh_btn.clicked.connect(self.refresh_data)
        controls.addWidget(refresh_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(SECONDARY_BTN)
        export_btn.clicked.connect(self.on_export)
        controls.addWidget(export_btn)
        
        self.layout.addLayout(controls)

        # Main Scroll Area for dashboard content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        self.content_lay = QVBoxLayout(content)
        self.content_lay.setSpacing(24)
        
        # 3. KPI Grid
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(20)
        self.content_lay.addLayout(self.kpi_grid)
        
        # 4. Charts Row 1
        charts_row1 = QHBoxLayout()
        self.sales_overview = LineChart("Sales Overview")
        self.cat_breakdown = DonutChart("Sales by Category")
        self.pay_breakdown = DonutChart("Payment Method Breakdown")
        charts_row1.addWidget(self.sales_overview, 2)
        charts_row1.addWidget(self.cat_breakdown, 1)
        charts_row1.addWidget(self.pay_breakdown, 1)
        self.content_lay.addLayout(charts_row1)
        
        # 5. Tables Row
        tables_row = QHBoxLayout()
        self.top_products_card, self.top_products_table = self._create_table_card("Top Selling Products")
        self.top_customers_card, self.top_customers_table = self._create_table_card("Top Customers")
        self.low_stock_card, self.low_stock_table = self._create_table_card("Low Stock Alerts")
        
        tables_row.addWidget(self.top_products_card)
        tables_row.addWidget(self.top_customers_card)
        tables_row.addWidget(self.low_stock_card)
        self.content_lay.addLayout(tables_row)
        
        # 6. Advanced Charts Row
        charts_row2 = QHBoxLayout()
        self.dow_chart = BarChart("Sales by Day of Week")
        self.slot_chart = BarChart("Sales by Time Slot")
        self.trend_chart = LineChart("Monthly Trend (Last 6 Months)")
        charts_row2.addWidget(self.dow_chart)
        charts_row2.addWidget(self.slot_chart)
        charts_row2.addWidget(self.trend_chart)
        self.content_lay.addLayout(charts_row2)
        
        scroll.setWidget(content)
        
        # Layout integration: Main Dashboard + Right Panel
        main_h = QHBoxLayout()
        main_h.addWidget(scroll, 4)
        
        # Right Panel
        right_panel_container = QWidget()
        right_panel_container.setFixedWidth(280)
        right_panel = QVBoxLayout(right_panel_container)
        right_panel.setContentsMargins(0, 0, 0, 0)
        
        cat_card = card()
        ccl = QVBoxLayout(cat_card)
        ccl.addWidget(make_label("Report Categories", 13, ON_SURFACE, bold=True))
        cats = ["Sales Reports", "Inventory Reports", "Customer Reports", "Profitability Reports", "Tax Reports"]
        for cname in cats:
            btn = QPushButton(cname)
            btn.setStyleSheet(f"text-align: left; padding: 10px; border: none; color: {ON_SURF_VAR}; font-weight: 500;")
            ccl.addWidget(btn)
        right_panel.addWidget(cat_card)
        
        insight_card = card()
        icl = QVBoxLayout(insight_card)
        icl.addWidget(make_label("Quick Insights", 13, ON_SURFACE, bold=True))
        self.insight_v = QVBoxLayout()
        icl.addLayout(self.insight_v)
        right_panel.addWidget(insight_card)
        right_panel.addStretch()
        
        main_h.addWidget(right_panel_container)
        self.layout.addLayout(main_h)

    def _create_table_card(self, title):
        f = QFrame()
        f.setStyleSheet(CARD_STYLE)
        lay = QVBoxLayout(f)
        lay.addWidget(make_label(title, 10, ON_SURFACE, bold=True))
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setStyleSheet("background: transparent; font-size: 11px;")
        lay.addWidget(table)
        
        link = QPushButton(f"View All {title.split()[-1]} →")
        link.setStyleSheet(f"text-align: left; color: {SECONDARY}; border: none; font-size: 10px; font-weight: bold;")
        lay.addWidget(link)
        return f, table

    def refresh_data(self):
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        
        # Comparison logic
        delta = end_dt - start_dt
        prev_start = start_dt - delta
        prev_end = start_dt - timedelta(seconds=1)
        
        # Fetch stats
        stats = self.service.get_dashboard_stats(start_dt, end_dt, prev_start, prev_end)
        self._render_kpis(stats)
        
        # Fetch chart data
        self.sales_overview.set_data(self.service.get_sales_overview(start_dt, end_dt))
        self.cat_breakdown.set_data(self.service.get_categorical_breakdown(start_dt, end_dt))
        self.pay_breakdown.set_data(self.service.get_payment_breakdown(start_dt, end_dt))
        self.dow_chart.set_data(self.service.get_day_of_week_analytics(start_dt, end_dt))
        self.slot_chart.set_data(self.service.get_time_slot_analytics(start_dt, end_dt))
        
        # Render Tables
        self._render_top_products(start_dt, end_dt)
        self._render_top_customers(start_dt, end_dt)
        self._render_low_stock()
        
        self._render_insights(stats)

    def _render_kpis(self, stats):
        # Clear grid
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        kpi_defs = [
            ("Total Sales", f"₹{stats['sales']['value']:,.0f}", stats['sales']['trend'], "\ue149"),
            ("Total Orders", str(stats['orders']['value']), stats['orders']['trend'], "\ue188"),
            ("Total Profit", f"₹{stats['profit']['value']:,.0f}", stats['profit']['trend'], "\ue12a"),
            ("Avg. Order Value", f"₹{stats['avg_order']['value']:,.0f}", stats['avg_order']['trend'], "\ue19d"),
            ("Total Customers", str(stats['customers']['value']), stats['customers']['trend'], "\ue125"),
            ("Items Sold", str(stats['items_sold']['value']), stats['items_sold']['trend'], "\ue115")
        ]
        
        for i, (t, v, tr, icon) in enumerate(kpi_defs):
            self.kpi_grid.addWidget(KPICard(t, v, tr, icon), i // 3, i % 3)

    def _render_top_products(self, start, end):
        data = self.service.get_top_products(start, end)
        self.top_products_table.setRowCount(len(data))
        for i, d in enumerate(data):
            self.top_products_table.setItem(i, 0, QTableWidgetItem(d['name']))
            self.top_products_table.setItem(i, 1, QTableWidgetItem(str(d['qty'])))
            self.top_products_table.setItem(i, 2, QTableWidgetItem(f"₹{d['revenue']:,.0f}"))

    def _render_top_customers(self, start, end):
        data = self.service.get_top_customers(start, end)
        self.top_customers_table.setRowCount(len(data))
        for i, d in enumerate(data):
            self.top_customers_table.setItem(i, 0, QTableWidgetItem(d['name']))
            self.top_customers_table.setItem(i, 1, QTableWidgetItem(str(d['orders'])))
            self.top_customers_table.setItem(i, 2, QTableWidgetItem(f"₹{d['spend']:,.0f}"))

    def _render_low_stock(self):
        data = self.service.get_low_stock_alerts()
        self.low_stock_table.setRowCount(len(data))
        for i, d in enumerate(data):
            self.low_stock_table.setItem(i, 0, QTableWidgetItem(d['product']))
            self.low_stock_table.setItem(i, 1, QTableWidgetItem(str(d['stock'])))
            status_item = QTableWidgetItem(d['status'])
            status_item.setForeground(QColor(TERTIARY if d['status'] == "Critical" else "#ffb300"))
            self.low_stock_table.setItem(i, 2, status_item)

    def _render_insights(self, stats):
        while self.insight_v.count():
            item = self.insight_v.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        points = [
            (f"Best selling day: Friday", SECONDARY),
            (f"Peak sales time: 6PM - 9PM", PRIMARY),
            (f"Growth this month: {stats['sales']['trend']}%", SECONDARY if stats['sales']['trend'] >= 0 else TERTIARY)
        ]
        for text, color in points:
            lbl = make_label(f"• {text}", 10, color, bold=True)
            self.insight_v.addWidget(lbl)

    def on_export(self):
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        
        # Export dashboard summary
        # In a real app, you'd open a file dialog, but here we just trigger the service
        delta = end_dt - start_dt
        prev_start = start_dt - delta
        prev_end = start_dt - timedelta(seconds=1)
        
        stats = self.service.get_dashboard_stats(start_dt, end_dt, prev_start, prev_end)
        path = ExportService.export_dashboard_summary(stats, [])
        if path:
            QMessageBox.information(self, "Export Success", f"Report exported successfully to:\n{path}")
