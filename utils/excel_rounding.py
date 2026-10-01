"""
utils/excel_rounding.py
Authoritative Excel-compatible rounding and display formatting utilities.

Provides exact equivalents for Excel functions:
- excel_round(value, digits=0)     <-> Excel =ROUND(val, digits)
- excel_roundup(value, digits=0)   <-> Excel =ROUNDUP(val, digits)
- excel_rounddown(value, digits=0) <-> Excel =ROUNDDOWN(val, digits)
- display_currency(value, ...)     <-> Visual presentation formatting (cell formatting)
- display_decimal(value, ...)      <-> 2-decimal presentation formatting

Guarantees:
- Decouples mathematical calculation from presentation/display.
- Preserves full Decimal precision without lossy float casting during calculations.
"""

from decimal import Decimal, ROUND_HALF_UP, ROUND_UP, ROUND_DOWN
import math

def to_decimal(val, default='0.0'):
    """Safe conversion to Decimal without losing fractional precision."""
    if val is None or str(val).strip() == '':
        return Decimal(str(default))
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal(str(default))

def excel_round(value, digits=0):
    """
    Replicates Excel's =ROUND(value, digits) function:
    Uses standard symmetric arithmetic rounding (half away from zero / ROUND_HALF_UP).
    """
    if value is None or str(value).strip() == '':
        return Decimal('0') if digits == 0 else Decimal('0.' + '0' * digits)
    d = to_decimal(value)
    q = Decimal('1') if digits == 0 else Decimal('1e-' + str(digits))
    return d.quantize(q, rounding=ROUND_HALF_UP)

def excel_roundup(value, digits=0):
    """
    Replicates Excel's =ROUNDUP(value, digits) function:
    Rounds away from zero (equivalent to math.ceil for positive values).
    """
    if value is None or str(value).strip() == '':
        return Decimal('0') if digits == 0 else Decimal('0.' + '0' * digits)
    d = to_decimal(value)
    q = Decimal('1') if digits == 0 else Decimal('1e-' + str(digits))
    return d.quantize(q, rounding=ROUND_UP)

def excel_rounddown(value, digits=0):
    """
    Replicates Excel's =ROUNDDOWN(value, digits) function:
    Rounds towards zero (equivalent to math.floor for positive values).
    """
    if value is None or str(value).strip() == '':
        return Decimal('0') if digits == 0 else Decimal('0.' + '0' * digits)
    d = to_decimal(value)
    q = Decimal('1') if digits == 0 else Decimal('1e-' + str(digits))
    return d.quantize(q, rounding=ROUND_DOWN)

def display_currency(value, symbol='', decimals=0):
    """
    Formats an unrounded internal calculation value for visual presentation only.
    DOES NOT modify the underlying numeric value.
    Example: 8332.50 -> '8,333' (if decimals=0) or '8,332.50' (if decimals=2).
    Uses symmetric arithmetic rounding (ROUND_HALF_UP) matching Excel's #,##0 format.
    """
    if value is None or str(value).strip() == '':
        return f"{symbol}0" if decimals == 0 else f"{symbol}0.00"
    try:
        if decimals == 0:
            rounded = int(excel_round(value, 0))
            formatted = f"{rounded:,}"
        else:
            rounded = excel_round(value, decimals)
            formatted = f"{rounded:,.{decimals}f}"
        return f"{symbol}{formatted}" if symbol else formatted
    except Exception:
        return f"{symbol}0"

def display_decimal(value, decimals=2):
    """Formats number to standard 2-decimal string for table views."""
    return display_currency(value, symbol='', decimals=decimals)

def format_excel_display(value, number_format='General'):
    """
    Simulates how Excel visually displays a cell value according to its number_format.
    Preserves the underlying calculation value while generating the display string.
    """
    if value is None or str(value).strip() == '':
        return ''
    try:
        fmt = str(number_format).strip()
        if fmt in ('#,##0', '0'):
            # Integer with or without commas
            rounded = int(excel_round(value, 0))
            return f"{rounded:,}" if '#,##0' in fmt else str(rounded)
        elif fmt == '#,##0.00':
            rounded = excel_round(value, 2)
            return f"{rounded:,.2f}"
        elif fmt == '0.00':
            rounded = excel_round(value, 2)
            return f"{rounded:.2f}"
        elif fmt == '0.0':
            rounded = excel_round(value, 1)
            return f"{rounded:.1f}"
        elif '0' in fmt and '.' in fmt:
            # e.g. custom decimal places
            dec_places = len(fmt.split('.')[1].replace(';', '').replace('@', ''))
            rounded = excel_round(value, dec_places)
            return f"{rounded:,.{dec_places}f}" if ',' in fmt else f"{rounded:.{dec_places}f}"
        else:
            # General or text
            try:
                f_val = float(value)
                if f_val.is_integer():
                    return str(int(f_val))
                return f"{f_val:g}"
            except Exception:
                return str(value)
    except Exception:
        return str(value)

