"""
services/whatsapp_service.py
─────────────────────────────
WhatsApp messaging service for FabricPOS.
Supports two backends:
  • pywhatkit  — free, uses WhatsApp Web (needs browser open)
  • twilio     — paid API, fully automated, no browser needed

Usage:
    svc = WhatsAppService()
    svc.send_invoice_message(phone="9876543210", invoice_no="INV-001",
                             customer="Priya Sharma", amount=1250.00)
    svc.send_due_reminder(phone="9876543210", name="Priya Sharma", due=2500.00)
"""

import os, sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    WHATSAPP_BACKEND, SHOP_NAME,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
)
from services.db import get_db, WhatsAppLogModel, PartyModel, InvoiceModel


class WhatsAppService:

    # ── Message Templates ──────────────────────────────────────────────────
    INVOICE_MSG = (
        "Dear {customer},\n\n"
        "Your invoice *{invoice_no}* from *{shop}* has been generated.\n"
        "Amount: *₹{amount:,.2f}*\n"
        "Date: {date}\n\n"
        "Thank you for shopping with us! 🙏\n"
        "— {shop}"
    )

    INVOICE_MSG_MARATHI = (
        "प्रिय {customer},\n\n"
        "*{shop}* कडून तुमचे इनव्हॉइस *{invoice_no}* तयार झाले आहे.\n"
        "रक्कम: *₹{amount:,.2f}*\n"
        "दिनांक: {date}\n\n"
        "आमच्याकडे खरेदी केल्याबद्दल धन्यवाद! 🙏\n"
        "— {shop}"
    )

    REMINDER_MSG = (
        "Dear {name},\n\n"
        "This is a gentle reminder that you have an outstanding balance of "
        "*₹{due:,.2f}* with *{shop}*.\n\n"
        "Please contact us to clear your dues at your earliest convenience.\n"
        "📞 {phone}\n\n"
        "— {shop}"
    )

    CUSTOM_MSG = "{body}"

    # ── Public API ─────────────────────────────────────────────────────────

    def send_invoice_message(self, phone: str, invoice_no: str,
                             customer: str, amount: float,
                             pdf_path: str = None) -> dict:
        """Send invoice notification after billing. Returns {success, message}."""
        from config import PHONE as SHOP_PHONE
        body = self.INVOICE_MSG.format(
            customer=customer,
            invoice_no=invoice_no,
            shop=SHOP_NAME,
            amount=amount,
            date=datetime.now().strftime("%d %b %Y"),
        )
        return self._send(
            phone=phone,
            body=body,
            msg_type="invoice",
            invoice_no=invoice_no,
            party_name=customer,
            pdf_path=pdf_path,
        )

    def send_due_reminder(self, phone: str, name: str, due: float) -> dict:
        """Send payment due reminder to a customer/supplier."""
        from config import PHONE as SHOP_PHONE
        body = self.REMINDER_MSG.format(
            name=name,
            due=due,
            shop=SHOP_NAME,
            phone=SHOP_PHONE,
        )
        return self._send(
            phone=phone,
            body=body,
            msg_type="reminder",
            party_name=name,
        )

    def send_custom(self, phone: str, body: str, party_name: str = "") -> dict:
        """Send a fully custom message."""
        return self._send(
            phone=phone,
            body=body,
            msg_type="custom",
            party_name=party_name,
        )

    def get_history(self, limit: int = 50) -> list:
        """Return recent WhatsApp send history from DB."""
        db = get_db()
        try:
            return db.query(WhatsAppLogModel)\
                     .order_by(WhatsAppLogModel.sent_at.desc())\
                     .limit(limit).all()
        finally:
            db.close()

    def get_contact_list(self) -> list:
        """
        Aggregate unique contacts from Parties, Invoices, and WhatsApp logs.
        Returns list of dicts: {"name": str, "phone": str, "source": str}
        """
        db = get_db()
        all_contacts = {} # phone -> (name, source)

        try:
            # 1. CRM Parties
            parties = db.query(PartyModel).all()
            for p in parties:
                if p.phone:
                    all_contacts[p.phone] = (p.name, "CRM Contact")

            # 2. Invoices (One-time walk-in customers)
            invoices = db.query(InvoiceModel).filter(InvoiceModel.party_phone != None).all()
            for i in invoices:
                if i.party_phone and i.party_phone not in all_contacts:
                    all_contacts[i.party_phone] = (i.party_name or "Walk-in Customer", "Invoice History")

            # 3. WhatsApp History
            logs = db.query(WhatsAppLogModel).all()
            for l in logs:
                if l.phone and l.phone not in all_contacts:
                    all_contacts[l.phone] = (l.party_name or "Unknown", "Message Log")

            # Convert to sorted list
            result = []
            for phone, (name, source) in all_contacts.items():
                result.append({"name": name, "phone": phone, "source": source})
            
            return sorted(result, key=lambda x: x['name'].lower())
        finally:
            db.close()

    # ── Internal ───────────────────────────────────────────────────────────

    def _send(self, phone: str, body: str, msg_type: str,
              invoice_no: str = None, party_name: str = "",
              pdf_path: str = None) -> dict:
        """Route to the configured backend and log the result."""
        # Normalise phone: strip spaces/dashes, ensure +91 prefix
        phone_clean = self._normalise_phone(phone)

        status, error = "sent", None
        try:
            if WHATSAPP_BACKEND == "twilio":
                self._send_via_twilio(phone_clean, body, pdf_path)
            else:
                self._send_via_pywhatkit(phone_clean, body)
        except Exception as e:
            status = "failed"
            error  = str(e)

        self._log(phone_clean, party_name, msg_type,
                  invoice_no, body, status, error)

        if status == "sent":
            return {"success": True,  "message": "Message sent successfully"}
        return  {"success": False, "message": f"Failed: {error}"}

    def _send_via_pywhatkit(self, phone: str, body: str):
        """
        Send using pywhatkit — opens WhatsApp Web in browser.
        Requires WhatsApp Web to be logged in on this PC.
        """
        try:
            import pywhatkit
        except ImportError:
            raise ImportError("pywhatkit not installed. Run: pip install pywhatkit")

        # sendwhatmsg_instantly opens browser and sends after wait_time seconds
        pywhatkit.sendwhatmsg_instantly(
            phone_no=phone,       # must include country code: +919876543210
            message=body,
            wait_time=12,         # seconds to wait for WhatsApp Web to load
            tab_close=True,       # close the tab after sending
            close_time=3,
        )

    def _send_via_twilio(self, phone: str, body: str, pdf_url: str = None):
        """
        Send via Twilio WhatsApp API — fully automated, no browser needed.
        Requires: pip install twilio
        Requires a Twilio account with WhatsApp sandbox or approved sender.
        """
        try:
            from twilio.rest import Client
        except ImportError:
            raise ImportError("twilio not installed. Run: pip install twilio")

        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise ValueError("Twilio credentials not set in config.py")

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        msg_kwargs = {
            "from_": TWILIO_FROM_NUMBER,
            "to":    f"whatsapp:{phone}",
            "body":  body,
        }
        if pdf_url:
            msg_kwargs["media_url"] = [pdf_url]

        client.messages.create(**msg_kwargs)

    def _normalise_phone(self, phone: str) -> str:
        """Ensure phone has +91 prefix and no spaces/dashes."""
        digits = "".join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f"+91{digits}"
        if digits.startswith("91") and len(digits) == 12:
            return f"+{digits}"
        if digits.startswith("0") and len(digits) == 11:
            return f"+91{digits[1:]}"
        return f"+{digits}"   # already has country code

    def _log(self, phone: str, party_name: str, msg_type: str,
             invoice_no: str, body: str, status: str, error: str):
        """Persist send attempt to whatsapp_log table."""
        db = get_db()
        try:
            log = WhatsAppLogModel(
                phone=phone,
                party_name=party_name,
                message_type=msg_type,
                invoice_no=invoice_no,
                message_body=body,
                status=status,
                error_msg=error,
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
