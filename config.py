import os

# App Info
APP_NAME = "Fabric POS"
VERSION = "1.0.0"

# Database
DB_NAME = "fabricpos.db"
# Use absolute path relative to this file to ensure it's found regardless of CWD
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

# Shop Details
SHOP_NAME = "My Clothing Store"
GSTIN = "22AAAAA0000A1Z5"
ADDRESS = "123, Fashion Street, Mumbai"
PHONE = "+91 98765 43210"

# Settings
DEFAULT_GST = 12.0  # Percentage
CURRENCY = "₹"

# UI Settings
THEME_COLOR = "#2c3e50"
ACCENT_COLOR = "#3498db"
DARK_MODE = True
