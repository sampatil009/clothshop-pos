from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Product:
    id: Optional[int] = None
    name: str = ""
    sku: str = ""  # Barcode
    hsn: str = ""
    category: str = ""
    price: float = 0.0
    cost_price: float = 0.0
    gst_rate: float = 12.0
    stock_quantity: int = 0
    unit: str = "Pcs"  # Pcs, Meters, etc.

@dataclass
class Party:
    id: Optional[int] = None
    name: str = ""
    contact_person: str = ""
    phone: str = ""
    gstin: str = ""
    address: str = ""
    party_type: str = "Customer"  # Customer or Supplier
    balance: float = 0.0

@dataclass
class InvoiceItem:
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    gst_rate: float
    total: float

@dataclass
class Invoice:
    id: Optional[int] = None
    invoice_number: str = ""
    date: datetime = field(default_factory=datetime.now)
    party_id: Optional[int] = None
    party_name: str = ""
    items: List[InvoiceItem] = field(default_factory=list)
    subtotal: float = 0.0
    gst_total: float = 0.0
    grand_total: float = 0.0
    payment_mode: str = "Cash"  # Cash, Card, UPI, Credit
    status: str = "Paid"  # Paid, Unpaid, Partial
