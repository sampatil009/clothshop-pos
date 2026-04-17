from fabricpos.services.db import get_db, InvoiceModel, InvoiceItemModel, ProductModel
from fabricpos.models.data_models import Invoice, InvoiceItem
from datetime import datetime

class SalesService:
    @staticmethod
    def create_invoice(invoice_data: Invoice):
        db = get_db()
        try:
            # 1. Create Invoice Record
            db_invoice = InvoiceModel(
                invoice_number=invoice_data.invoice_number or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                party_id=invoice_data.party_id,
                party_name=invoice_data.party_name,
                subtotal=invoice_data.subtotal,
                gst_total=invoice_data.gst_total,
                grand_total=invoice_data.grand_total,
                payment_mode=invoice_data.payment_mode,
                status=invoice_data.status
            )
            db.add(db_invoice)
            db.flush() # Get ID
            
            # 2. Add Items and Update Stock
            for item in invoice_data.items:
                db_item = InvoiceItemModel(
                    invoice_id=db_invoice.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
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
