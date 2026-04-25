"""
services/report_service.py
──────────────────────────
Analytics and data aggregation service for Performance Reports.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import func, case, and_

# Namespace handling
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import (
    get_db, InvoiceModel, InvoiceItemModel, ProductModel, CustomerModel
)

class ReportService:

    def get_dashboard_stats(self, start_date: datetime, end_date: datetime, 
                            prev_start: datetime, prev_end: datetime) -> dict:
        """
        Calculate top KPIs for current vs previous period.
        """
        db = get_db()
        try:
            # 1. Current Period
            curr_stats = db.query(
                func.sum(InvoiceModel.grand_total).label("sales"),
                func.count(InvoiceModel.id).label("orders"),
                func.avg(InvoiceModel.grand_total).label("avg_order")
            ).filter(InvoiceModel.date.between(start_date, end_date)).first()

            # Items Sold (Current)
            curr_items = db.query(func.sum(InvoiceItemModel.quantity))\
                           .join(InvoiceModel)\
                           .filter(InvoiceModel.date.between(start_date, end_date)).scalar() or 0

            # Profit Calculation (Approximate using current cost_price)
            # Profit = sum(item.quantity * (item.unit_price - product.cost_price))
            curr_profit = db.query(func.sum(
                InvoiceItemModel.quantity * (InvoiceItemModel.unit_price - ProductModel.cost_price)
            )).join(ProductModel, InvoiceItemModel.product_id == ProductModel.id)\
              .join(InvoiceModel, InvoiceItemModel.invoice_id == InvoiceModel.id)\
              .filter(InvoiceModel.date.between(start_date, end_date)).scalar() or 0

            # 2. Previous Period (for trend calculation)
            prev_stats = db.query(
                func.sum(InvoiceModel.grand_total).label("sales"),
                func.count(InvoiceModel.id).label("orders")
            ).filter(InvoiceModel.date.between(prev_start, prev_end)).first()

            # 3. Customer Count (Lifetime)
            total_cust = db.query(func.count(CustomerModel.id)).scalar() or 0
            
            # Helper to calc % change
            def calc_trend(curr, prev):
                if not prev or prev == 0: return 0
                return round(((curr - prev) / prev) * 100, 1)

            return {
                "sales": {"value": curr_stats.sales or 0, "trend": calc_trend(curr_stats.sales or 0, prev_stats.sales or 0)},
                "orders": {"value": curr_stats.orders or 0, "trend": calc_trend(curr_stats.orders or 0, prev_stats.orders or 0)},
                "profit": {"value": curr_profit, "trend": 0}, # Profit comparison requires deep query
                "avg_order": {"value": curr_stats.avg_order or 0, "trend": 0},
                "customers": {"value": total_cust, "trend": 0},
                "items_sold": {"value": int(curr_items), "trend": 0}
            }
        finally:
            db.close()

    def get_sales_overview(self, start_date: datetime, end_date: datetime) -> list:
        """Data for Sales Overview Line Chart (Grouped by Day)."""
        db = get_db()
        try:
            # Group by date part (SQLite specific strftime)
            results = db.query(
                func.strftime('%Y-%m-%d', InvoiceModel.date).label("day"),
                func.sum(InvoiceModel.grand_total).label("total")
            ).filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by("day").order_by("day").all()
            
            return [{"label": r.day, "value": r.total} for r in results]
        finally:
            db.close()

    def get_categorical_breakdown(self, start_date: datetime, end_date: datetime) -> list:
        """Data for Category Donut Chart."""
        db = get_db()
        try:
            results = db.query(
                ProductModel.category,
                func.sum(InvoiceItemModel.total).label("revenue")
            ).join(InvoiceItemModel, ProductModel.id == InvoiceItemModel.product_id)\
             .join(InvoiceModel, InvoiceItemModel.invoice_id == InvoiceModel.id)\
             .filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by(ProductModel.category).all()
            
            total_rev = sum(r.revenue for r in results) or 1
            return [
                {"category": r.category or "Others", "value": r.revenue, "percent": round((r.revenue/total_rev)*100)}
                for r in results
            ]
        finally:
            db.close()

    def get_payment_breakdown(self, start_date: datetime, end_date: datetime) -> list:
        """Data for Payment Method Donut Chart."""
        db = get_db()
        try:
            results = db.query(
                InvoiceModel.payment_mode,
                func.sum(InvoiceModel.grand_total).label("revenue")
            ).filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by(InvoiceModel.payment_mode).all()
            
            return [{"mode": r.payment_mode, "value": r.revenue} for r in results]
        finally:
            db.close()

    def get_top_products(self, start_date, end_date, limit=5) -> list:
        db = get_db()
        try:
            results = db.query(
                InvoiceItemModel.product_name,
                ProductModel.category,
                func.sum(InvoiceItemModel.quantity).label("qty"),
                func.sum(InvoiceItemModel.total).label("revenue")
            ).join(ProductModel, InvoiceItemModel.product_id == ProductModel.id)\
             .join(InvoiceModel, InvoiceItemModel.invoice_id == InvoiceModel.id)\
             .filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by(InvoiceItemModel.product_name)\
             .order_by(func.sum(InvoiceItemModel.total).desc())\
             .limit(limit).all()
            
            return [
                {"name": r.product_name, "category": r.category, "qty": r.qty, "revenue": r.revenue}
                for r in results
            ]
        finally:
            db.close()

    def get_top_customers(self, start_date, end_date, limit=5) -> list:
        db = get_db()
        try:
            results = db.query(
                InvoiceModel.party_name,
                func.sum(InvoiceModel.grand_total).label("spend"),
                func.count(InvoiceModel.id).label("orders")
            ).filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by(InvoiceModel.party_name)\
             .order_by(func.sum(InvoiceModel.grand_total).desc())\
             .limit(limit).all()
            
            return [
                {"name": r.party_name or "Walk-in", "spend": r.spend, "orders": r.orders}
                for r in results
            ]
        finally:
            db.close()

    def get_low_stock_alerts(self) -> list:
        db = get_db()
        try:
            # Assume reorder level is 10 for critical, 25 for low
            results = db.query(ProductModel)\
                        .filter(ProductModel.stock_quantity <= 25)\
                        .order_by(ProductModel.stock_quantity.asc()).limit(10).all()
            
            alerts = []
            for p in results:
                status = "Critical" if p.stock_quantity <= 10 else "Low"
                alerts.append({
                    "product": p.name,
                    "stock": p.stock_quantity,
                    "reorder": 10 if status == "Critical" else 25,
                    "status": status
                })
            return alerts
        finally:
            db.close()

    def get_day_of_week_analytics(self, start_date, end_date) -> list:
        db = get_db()
        try:
            # 0=Sunday in SQLite strftime %w
            results = db.query(
                func.strftime('%w', InvoiceModel.date).label("dow"),
                func.sum(InvoiceModel.grand_total).label("total")
            ).filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by("dow").all()
            
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            data = {d: 0 for d in days}
            for r in results:
                data[days[int(r.dow)]] = r.total
            
            return [{"label": d, "value": data[d]} for d in days]
        finally:
            db.close()

    def get_time_slot_analytics(self, start_date, end_date) -> list:
        db = get_db()
        try:
            # Group into 3-hour chunks
            results = db.query(
                func.strftime('%H', InvoiceModel.date).label("hour"),
                func.sum(InvoiceModel.grand_total).label("total")
            ).filter(InvoiceModel.date.between(start_date, end_date))\
             .group_by("hour").all()
            
            slots = ["6AM-9AM", "9AM-12PM", "12PM-3PM", "3PM-6PM", "6PM-9PM", "9PM-12AM"]
            data = {s: 0 for s in slots}
            for r in results:
                h = int(r.hour)
                if 6 <= h < 9: data["6AM-9AM"] += r.total
                elif 9 <= h < 12: data["9AM-12PM"] += r.total
                elif 12 <= h < 15: data["12PM-3PM"] += r.total
                elif 15 <= h < 18: data["3PM-6PM"] += r.total
                elif 18 <= h < 21: data["6PM-9PM"] += r.total
                elif 21 <= h or h < 0: data["9PM-12AM"] += r.total
            
            return [{"label": s, "value": data[s]} for s in slots]
        finally:
            db.close()
