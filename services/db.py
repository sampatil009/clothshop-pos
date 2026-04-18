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

# Database initialization
engine = create_engine(f'sqlite:///{DB_PATH}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    return SessionLocal()
