"""
services/crm_service.py
────────────────────────
Service layer for CRM / Customer management.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

# Ensure fabricpos namespace works if needed, but local imports are safer here
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db import (
    get_db, CustomerModel, CustomerTagModel, LoyaltyModel,
    PreferenceModel, InteractionModel, CustomerNoteModel,
    InvoiceModel, get_customer_stats as db_get_stats
)

class CRMService:

    TAG_COLORS = {
        "VIP":       "#7b1fa2",
        "Regular":   "#43474e",
        "New":       "#1b6b51",
        "Bridal":    "#c0392b",
        "Wholesale": "#002045",
    }

    # ── Customer CRUD ──────────────────────────────────────────────────────
    
    def get_all_customers(self, search="", tag_filter="") -> list[CustomerModel]:
        db = get_db()
        try:
            query = db.query(CustomerModel).options(
                joinedload(CustomerModel.tags),
                joinedload(CustomerModel.loyalty)
            )
            
            if search:
                query = query.filter(or_(
                    CustomerModel.name.ilike(f"%{search}%"),
                    CustomerModel.phone.ilike(f"%{search}%"),
                    CustomerModel.email.ilike(f"%{search}%")
                ))
            
            if tag_filter:
                query = query.join(CustomerTagModel).filter(CustomerTagModel.name == tag_filter)
                
            return query.all()
        finally:
            db.close()

    def get_customer_by_id(self, customer_id: int) -> CustomerModel | None:
        db = get_db()
        try:
            return db.query(CustomerModel).options(
                joinedload(CustomerModel.tags),
                joinedload(CustomerModel.loyalty),
                joinedload(CustomerModel.preferences)
            ).filter(CustomerModel.id == customer_id).first()
        finally:
            db.close()

    def add_customer(self, name, phone, email="", address="",
                     dob="", gender="", notes="", tags: list[str] = []) -> CustomerModel:
        db = get_db()
        try:
            cust = CustomerModel(
                name=name, phone=phone, email=email, address=address,
                dob=dob, gender=gender, notes=notes
            )
            db.add(cust)
            db.flush() # get ID
            
            # Add Tags
            for tname in tags:
                tag = CustomerTagModel(customer_id=cust.id, name=tname, color=self.TAG_COLORS.get(tname, "#000000"))
                db.add(tag)
            
            # Init Loyalty
            loyalty = LoyaltyModel(customer_id=cust.id)
            db.add(loyalty)
            
            db.commit()
            return cust
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def update_customer(self, customer_id, **fields) -> bool:
        db = get_db()
        try:
            cust = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
            if not cust: return False
            
            if "tags" in fields:
                self.set_tags(customer_id, fields.pop("tags"))
            
            for key, val in fields.items():
                if hasattr(cust, key):
                    setattr(cust, key, val)
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def delete_customer(self, customer_id) -> bool:
        db = get_db()
        try:
            cust = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
            if not cust: return False
            db.delete(cust)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # ── Tags ───────────────────────────────────────────────────────────────
    
    def set_tags(self, customer_id, tag_names: list[str]) -> None:
        db = get_db()
        try:
            # Clear existing
            db.query(CustomerTagModel).filter(CustomerTagModel.customer_id == customer_id).delete()
            # Add new
            for tname in tag_names:
                tag = CustomerTagModel(customer_id=customer_id, name=tname, color=self.TAG_COLORS.get(tname, "#000000"))
                db.add(tag)
            db.commit()
        finally:
            db.close()

    # ── Loyalty ────────────────────────────────────────────────────────────
    
    def add_loyalty_points(self, customer_id, points: int) -> LoyaltyModel:
        db = get_db()
        try:
            loyalty = db.query(LoyaltyModel).filter(LoyaltyModel.customer_id == customer_id).first()
            if not loyalty:
                loyalty = LoyaltyModel(customer_id=customer_id)
                db.add(loyalty)
            
            loyalty.total_points += points
            loyalty.available_points += points
            
            # Log interaction
            self.log_interaction(customer_id, "Loyalty", "System", f"Added {points} points")
            
            db.commit()
            return loyalty
        finally:
            db.close()

    def redeem_points(self, customer_id, points: int) -> bool:
        db = get_db()
        try:
            loyalty = db.query(LoyaltyModel).filter(LoyaltyModel.customer_id == customer_id).first()
            if not loyalty or loyalty.available_points < points:
                return False
            
            loyalty.available_points -= points
            loyalty.total_redeemed += points
            
            # Log interaction
            self.log_interaction(customer_id, "Loyalty", "System", f"Redeemed {points} points")
            
            db.commit()
            return True
        finally:
            db.close()

    def get_loyalty(self, customer_id) -> LoyaltyModel | None:
        db = get_db()
        try:
            return db.query(LoyaltyModel).filter(LoyaltyModel.customer_id == customer_id).first()
        finally:
            db.close()

    # ── Preferences ────────────────────────────────────────────────────────
    
    def save_preferences(self, customer_id, category="", sub_category="",
                         brand="", budget_range="", color_preference="",
                         notes="") -> PreferenceModel:
        db = get_db()
        try:
            pref = db.query(PreferenceModel).filter(PreferenceModel.customer_id == customer_id).first()
            if not pref:
                pref = PreferenceModel(customer_id=customer_id)
                db.add(pref)
            
            pref.category = category
            pref.sub_category = sub_category
            pref.brand = brand
            pref.budget_range = budget_range
            pref.color_preference = color_preference
            pref.notes = notes
            
            db.commit()
            return pref
        finally:
            db.close()

    # ── Interactions ───────────────────────────────────────────────────────
    
    def log_interaction(self, customer_id, itype, platform, content) -> InteractionModel:
        db = get_db()
        try:
            inter = InteractionModel(
                customer_id=customer_id,
                type=itype,
                platform=platform,
                content=content
            )
            db.add(inter)
            db.commit()
            return inter
        finally:
            db.close()

    def get_interactions(self, customer_id, limit=20) -> list[InteractionModel]:
        db = get_db()
        try:
            return db.query(InteractionModel)\
                     .filter(InteractionModel.customer_id == customer_id)\
                     .order_by(InteractionModel.created_at.desc())\
                     .limit(limit).all()
        finally:
            db.close()

    # ── Notes ──────────────────────────────────────────────────────────────
    
    def add_note(self, customer_id, note, created_by="Admin") -> CustomerNoteModel:
        db = get_db()
        try:
            cnote = CustomerNoteModel(
                customer_id=customer_id,
                note=note,
                created_by=created_by
            )
            db.add(cnote)
            db.commit()
            return cnote
        finally:
            db.close()

    def get_notes(self, customer_id) -> list[CustomerNoteModel]:
        db = get_db()
        try:
            return db.query(CustomerNoteModel)\
                     .filter(CustomerNoteModel.customer_id == customer_id)\
                     .order_by(CustomerNoteModel.created_at.desc()).all()
        finally:
            db.close()

    # ── Analytics ──────────────────────────────────────────────────────────
    
    def get_customer_stats(self, customer_id) -> dict:
        return db_get_stats(customer_id)

    def get_overview_stats(self) -> dict:
        db = get_db()
        try:
            total_cust = db.query(func.count(CustomerModel.id)).scalar() or 0
            
            # Active this month (based on invoices)
            this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            active_this_month = db.query(func.count(func.distinct(InvoiceModel.party_id)))\
                                  .filter(InvoiceModel.date >= this_month_start).scalar() or 0
            
            # Total Sales
            total_sales = db.query(func.sum(InvoiceModel.grand_total)).scalar() or 0
            
            # Avg Spend
            avg_spend = 0
            if total_cust > 0:
                avg_spend = round(total_sales / total_cust, 2)
                
            return {
                "total_customers": total_cust,
                "active_this_month": active_this_month,
                "total_sales": total_sales,
                "avg_spend": avg_spend
            }
        finally:
            db.close()

    def get_segmented_customers(self) -> dict:
        db = get_db()
        try:
            # VIP
            vip = db.query(CustomerModel).options(joinedload(CustomerModel.tags))\
                    .join(CustomerTagModel).filter(CustomerTagModel.name == "VIP").all()
            # Regular
            regular = db.query(CustomerModel).options(joinedload(CustomerModel.tags))\
                        .join(CustomerTagModel).filter(CustomerTagModel.name == "Regular").all()
            # New (joined in last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            new_cust = db.query(CustomerModel).options(joinedload(CustomerModel.tags))\
                         .filter(CustomerModel.created_at >= thirty_days_ago).all()
            
            # Frequent Buyers (> 5 invoices)
            freq_ids = db.query(InvoiceModel.party_id)\
                         .group_by(InvoiceModel.party_id)\
                         .having(func.count(InvoiceModel.id) > 5).all()
            freq_ids = [r[0] for r in freq_ids if r[0]]
            freq_buyers = db.query(CustomerModel).options(joinedload(CustomerModel.tags))\
                            .filter(CustomerModel.id.in_(freq_ids)).all()
            
            # Inactive (no invoice in last 60 days)
            sixty_days_ago = datetime.now() - timedelta(days=60)
            active_ids = db.query(func.distinct(InvoiceModel.party_id))\
                           .filter(InvoiceModel.date >= sixty_days_ago).all()
            active_ids = [r[0] for r in active_ids if r[0]]
            inactive = db.query(CustomerModel).options(joinedload(CustomerModel.tags))\
                         .filter(~CustomerModel.id.in_(active_ids)).all()
            
            return {
                "VIP": vip,
                "Regular": regular,
                "New": new_cust,
                "Frequent Buyers": freq_buyers,
                "Inactive": inactive
            }
        finally:
            db.close()

def relative_time(dt: datetime) -> str:
    if dt is None:
        return "Never"
    delta = datetime.now() - dt
    days  = delta.days
    if days == 0:   return "Today"
    if days == 1:   return "Yesterday"
    if days < 7:    return f"{days} days ago"
    if days < 14:   return "1 week ago"
    if days < 30:   return f"{days // 7} weeks ago"
    if days < 60:   return "1 month ago"
    return f"{days // 30} months ago"
