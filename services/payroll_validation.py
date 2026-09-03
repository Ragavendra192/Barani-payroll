def validate_working_days(val, max_days=31.0):
    try:
        days = float(val)
        if days < 0:
            return False, "Working days cannot be negative"
        if days > max_days:
            return False, f"Working days cannot exceed {max_days}"
        return True, days
    except Exception:
        return False, "Invalid working days value"

def validate_ot_hours(val):
    try:
        hours = float(val)
        if hours < 0:
            return False, "OT Hours cannot be negative"
        return True, hours
    except Exception:
        return False, "Invalid OT hours value"

def validate_deduction(val):
    try:
        ded = float(val)
        if ded < 0:
            return False, "Deduction cannot be negative"
        return True, ded
    except Exception:
        return False, "Invalid deduction value"

def validate_year_month(year, month):
    try:
        y = int(year)
        m = int(month)
        if y < 2000 or y > 2100:
            return False, "Invalid year"
        if m < 1 or m > 12:
            return False, "Invalid month"
        return True, (y, m)
    except Exception:
        return False, "Invalid year or month"
