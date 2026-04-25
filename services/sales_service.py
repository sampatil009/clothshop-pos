from sqlalchemy import func
from services.db import get_db, InvoiceModel, InvoiceItemModel, ProductModel, PartyModel
from models.data_models import Invoice, InvoiceItem
from datetime import datetime

class SalesService:
    @staticmethod
    def get_next_invoice_number():
        db = get_db()
        try:
            today = datetime.now().date()
            # Count invoices created today
            count = db.query(func.count(InvoiceModel.id)).filter(
                func.date(InvoiceModel.date) == today
            ).scalar() or 0
            
            # Format: INV-YYMMDD-XXX
            date_str = datetime.now().strftime("%y%m%d")
            next_num = count + 1
            return f"INV-{date_str}-{next_num:03d}"
        finally:
            db.close()

    @staticmethod
    def create_invoice(invoice_data: Invoice):
        db = get_db()
        try:
            # 1. Handle Party (Auto-save if new)
            party_id = invoice_data.party_id
            if not party_id and invoice_data.party_phone:
                # Check if party with this phone exists
                existing = db.query(PartyModel).filter(PartyModel.phone == invoice_data.party_phone).first()
                if existing:
                    party_id = existing.id
                else:
                    # Create new party
                    new_party = PartyModel(
                        name=invoice_data.party_name or "Walk-in Customer",
                        phone=invoice_data.party_phone,
                        party_type="Customer"
                    )
                    db.add(new_party)
                    db.flush()
                    party_id = new_party.id

            # 2. Create Invoice Record
            db_invoice = InvoiceModel(
                invoice_number=invoice_data.invoice_number or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                party_id=invoice_data.party_id,
                party_name=invoice_data.party_name,
                party_phone=invoice_data.party_phone or "",
                subtotal=invoice_data.subtotal,
                gst_total=invoice_data.gst_total,
                cgst=invoice_data.cgst,
                sgst=invoice_data.sgst,
                discount=invoice_data.discount,
                grand_total=invoice_data.grand_total,
                payment_mode=invoice_data.payment_mode,
                status=invoice_data.status
            )
            db.add(db_invoice)
            db.flush()
            
            # 3. Add Items and Update Stock
            for item in invoice_data.items:
                db_item = InvoiceItemModel(
                    invoice_id=db_invoice.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    hsn_code=item.hsn_code,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    gst_rate=item.gst_rate,
                    total=item.total
                )
                db.add(db_item)
                
                # Update Stock
                product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
                if product:
                    product.stock_quantity -= item.quantity
            
            db.commit()
            return db_invoice.id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
