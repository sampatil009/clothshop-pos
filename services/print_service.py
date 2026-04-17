from reportlab.lib.pagesizes import A5, portrait
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from fabricpos.models.data_models import Invoice
from fabricpos.config import SHOP_NAME, ADDRESS, PHONE, GSTIN
import os

class PrintService:
    @staticmethod
    def generate_invoice_pdf(invoice: Invoice, output_path: str):
        c = canvas.Canvas(output_path, pagesize=A5)
        width, height = A5
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 40, SHOP_NAME)
        
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height - 55, ADDRESS)
        c.drawCentredString(width/2, height - 70, f"Phone: {PHONE} | GSTIN: {GSTIN}")
        
        c.line(30, height - 80, width - 30, height - 80)
        
        # Invoice Info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, height - 100, f"Invoice: {invoice.invoice_number}")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 40, height - 100, f"Date: {invoice.date.strftime('%d-%m-%Y')}")
        
        c.drawString(40, height - 115, f"Customer: {invoice.party_name}")
        
        # Table Header
        y = height - 140
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Item")
        c.drawRightString(width - 160, y, "Qty")
        c.drawRightString(width - 110, y, "Price")
        c.drawRightString(width - 40, y, "Total")
        
        c.line(30, y - 5, width - 30, y - 5)
        
        # Items
        y -= 25
        c.setFont("Helvetica", 9)
        for item in invoice.items:
            c.drawString(40, y, item.product_name)
            c.drawRightString(width - 160, y, str(item.quantity))
            c.drawRightString(width - 110, y, f"{item.unit_price:.2f}")
            c.drawRightString(width - 40, y, f"{item.total:.2f}")
            y -= 15
            
            if y < 60: # Pagination check (very simple)
                c.showPage()
                y = height - 40
        
        c.line(30, y - 5, width - 30, y - 5)
        y -= 25
        
        # Totals
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(width - 100, y, "Subtotal:")
        c.drawRightString(width - 40, y, f"₹{invoice.subtotal:.2f}")
        
        y -= 15
        c.drawRightString(width - 100, y, "GST:")
        c.drawRightString(width - 40, y, f"₹{invoice.gst_total:.2f}")
        
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(width - 100, y, "GRAND TOTAL:")
        c.drawRightString(width - 40, y, f"₹{invoice.grand_total:.2f}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width/2, 30, "Thank you for shopping with us!")
        
        c.save()
        return output_path
