from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from models.data_models import Invoice
from config import SHOP_NAME, ADDRESS, PHONE, GSTIN
from datetime import datetime
import os

class PrintService:
    @staticmethod
    def generate_invoice_pdf(invoice: Invoice, output_path: str):
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # ── Header Section ──
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor("#0f172a")) # Modern Navy
        c.drawString(20*mm, height - 25*mm, SHOP_NAME)
        
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.gray)
        c.drawString(20*mm, height - 32*mm, ADDRESS)
        c.drawString(20*mm, height - 37*mm, f"Phone: {PHONE} | GSTIN: {GSTIN}")
        
        c.setFont("Helvetica-Bold", 24)
        c.drawRightString(width - 20*mm, height - 25*mm, "INVOICE")
        
        c.setStrokeColor(colors.lightgrey)
        c.line(20*mm, height - 45*mm, width - 20*mm, height - 45*mm)
        
        # ── Bill To & Meta Info ──
        y = height - 60*mm
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(20*mm, y, "Bill To:")
        c.drawRightString(width - 60*mm, y, "Invoice No:")
        c.drawRightString(width - 20*mm, y, f"#{invoice.invoice_number}")
        
        y -= 6*mm
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, y, invoice.party_name)
        c.drawRightString(width - 60*mm, y, "Date:")
        c.drawRightString(width - 20*mm, y, invoice.date.strftime("%d-%b-%Y"))
        
        y -= 5*mm
        if invoice.party_phone:
            c.drawString(20*mm, y, f"Ph: {invoice.party_phone}")
        c.drawRightString(width - 60*mm, y, "Due Date:")
        due_str = invoice.due_date.strftime("%d-%b-%Y") if invoice.due_date else "-"
        c.drawRightString(width - 20*mm, y, due_str)
        
        if invoice.customer_address:
            y -= 5*mm
            # Simple address wrap (limit to 1 line for simplicity in basic tool)
            c.drawString(20*mm, y, invoice.customer_address[:80])
            
        # ── Item Table Header ──
        y -= 15*mm
        c.setFillColor(colors.HexColor("#f8fafc")) # Light background for header
        c.rect(20*mm, y, width - 40*mm, 10*mm, fill=1, stroke=0)
        
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor("#475569"))
        ty = y + 3.5*mm
        c.drawString(25*mm, ty, "Item Description")
        c.drawString(85*mm, ty, "HSN")
        c.drawRightString(120*mm, ty, "Qty")
        c.drawRightString(150*mm, ty, "Rate")
        c.drawRightString(width - 25*mm, ty, "Amount")
        
        # ── Items ──
        y -= 10*mm
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        for item in invoice.items:
            c.drawString(25*mm, y + 2*mm, item.product_name)
            c.drawString(85*mm, y + 2*mm, item.hsn_code or "-")
            c.drawRightString(120*mm, y + 2*mm, str(item.quantity))
            c.drawRightString(150*mm, y + 2*mm, f"{item.unit_price:,.2f}")
            c.drawRightString(width - 25*mm, y + 2*mm, f"{item.total:,.2f}")
            
            c.setStrokeColor(colors.whitesmoke)
            c.line(20*mm, y, width - 20*mm, y)
            y -= 8*mm
            
            if y < 40*mm: # Page break
                c.showPage()
                y = height - 30*mm
                c.setFont("Helvetica", 10)

        # ── Totals & Notes ──
        y -= 10*mm
        # Prevent totals from going off bottom
        if y < 60*mm:
            c.showPage()
            y = height - 30*mm

        # Notes
        ty = y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20*mm, ty, "Customer Notes:")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#64748b"))
        if invoice.customer_notes:
            c.drawString(20*mm, ty - 6*mm, invoice.customer_notes[:100])
        else:
            c.drawString(20*mm, ty - 6*mm, "Thank you for your business!")

        # Summary
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 60*mm, ty, "Sub Total:")
        c.drawRightString(width - 25*mm, ty, f"₹{invoice.subtotal:,.2f}")
        
        ty -= 6*mm
        c.drawRightString(width - 60*mm, ty, f"CGST (2.5%):")
        c.drawRightString(width - 25*mm, ty, f"₹{invoice.cgst:,.2f}")
        
        ty -= 6*mm
        c.drawRightString(width - 60*mm, ty, f"SGST (2.5%):")
        c.drawRightString(width - 25*mm, ty, f"₹{invoice.sgst:,.2f}")
        
        ty -= 10*mm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#ef4444")) # Grand Total in Red as per image
        c.drawRightString(width - 60*mm, ty, "Grand Total:")
        c.drawRightString(width - 25*mm, ty, f"₹{invoice.grand_total:,.2f}")
        
        c.save()
        return output_path
