from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import sys

# Add the parent directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

Base = declarative_base()

class ProductModel(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True)
    hsn = Column(String(20))
    category = Column(String(100))
    price = Column(Float, default=0.0)
    cost_price = Column(Float, default=0.0)
    gst_rate = Column(Float, default=12.0)
    stock_quantity = Column(Integer, default=0)
    unit = Column(String(20), default="Pcs")

class PartyModel(Base):
    __tablename__ = 'parties'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(200))
    phone = Column(String(20))
    gstin = Column(String(20))
    address = Column(Text)
    party_type = Column(String(50), default="Customer") # Customer, Supplier
    balance = Column(Float, default=0.0)

class InvoiceModel(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True)
    date = Column(DateTime, default=datetime.now)
    due_date = Column(DateTime)
    party_id = Column(Integer, ForeignKey('parties.id'))
    party_name = Column(String(200))
    party_phone = Column(String(20))
    customer_address = Column(Text)
    customer_notes = Column(Text)
    subtotal = Column(Float, default=0.0)
    gst_total = Column(Float, default=0.0)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    payment_mode = Column(String(50), default="Cash")
    status = Column(String(50), default="Paid")
    
    items = relationship("InvoiceItemModel", back_populates="invoice")

class WhatsAppLogModel(Base):
    __tablename__ = 'whatsapp_logs'
    id = Column(Integer, primary_key=True)
    sent_at = Column(DateTime, default=datetime.now)
    phone = Column(String(20), nullable=False)
    party_name = Column(String(200))
    message_type = Column(String(50)) # invoice, reminder, custom
    invoice_no = Column(String(50))
    message_body = Column(Text)
    status = Column(String(50)) # sent, failed
    error_msg = Column(Text)

class InvoiceItemModel(Base):
    __tablename__ = 'invoice_items'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    product_name = Column(String(200))
    hsn_code = Column(String(20))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    gst_rate = Column(Float, default=12.0)
    total = Column(Float, default=0.0)
    
    invoice = relationship("InvoiceModel", back_populates="items")

class BusinessProfileModel(Base):
    __tablename__ = 'business_profile'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), default="FabricPOS Boutique")
    phone = Column(String(20))
    email = Column(String(200))
    website = Column(String(200))
    address = Column(Text)
    gstin = Column(String(20))

class UserModel(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False) # In production, use hashing
    role_id = Column(Integer, ForeignKey('roles.id'))
    last_login = Column(DateTime)
    
    role = relationship("RoleModel", back_populates="users")

class RoleModel(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(Text) # JSON string or comma-separated
    
    users = relationship("UserModel", back_populates="role")

class PrinterSettingsModel(Base):
    __tablename__ = 'printer_settings'
    id = Column(Integer, primary_key=True)
    printer_name = Column(String(200))
    paper_size = Column(String(50), default="80mm") # 80mm, 58mm, A4

class InvoiceSettingsModel(Base):
    __tablename__ = 'invoice_settings'
    id = Column(Integer, primary_key=True)
    header_text = Column(Text)
    footer_text = Column(Text)
    font_size = Column(String(20), default="Normal (10pt)")

# Database initialization
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed default data if empty
    session = SessionLocal()
    try:
        # Business Profile
        if not session.query(BusinessProfileModel).first():
            profile = BusinessProfileModel(
                name="Atrium Boutique",
                phone="+91 98765 43210",
                email="contact@atrium.com",
                website="www.atriumboutique.com",
                address="Shop No. 12, Main Market, City Center",
                gstin="22AAAAA0000A1Z5"
            )
            session.add(profile)
        
        # Roles
        if not session.query(RoleModel).first():
            admin_role = RoleModel(name="Administrator", permissions="all")
            staff_role = RoleModel(name="Staff", permissions="pos,inventory")
            session.add(admin_role)
            session.add(staff_role)
            session.commit() # Commit to get IDs
        
        # Users
        if not session.query(UserModel).first():
            admin_role = session.query(RoleModel).filter_by(name="Administrator").first()
            admin_user = UserModel(
                username="admin",
                password="admin",
                role_id=admin_role.id
            )
            session.add(admin_user)
            
        # Printer Settings
        if not session.query(PrinterSettingsModel).first():
            printer = PrinterSettingsModel(
                printer_name="Microsoft Print to PDF",
                paper_size="80mm Thermal"
            )
            session.add(printer)
            
        # Invoice Settings
        if not session.query(InvoiceSettingsModel).first():
            invoice = InvoiceSettingsModel(
                header_text="GSTIN: 22AAAAA0000A1Z5\nThank you for shopping!",
                footer_text="Terms & Conditions: Goods once sold will not be taken back.",
                font_size="Normal (10pt)"
            )
            session.add(invoice)
            
        session.commit()
    except Exception as e:
        print(f"Error seeding database: {e}")
        session.rollback()
    finally:
        session.close()

def get_db():
    return SessionLocal()
