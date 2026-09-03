import re

def normalize_indian_phone(phone_str):
    """
    Normalizes Indian mobile numbers into standard E.164 format (+919876543210).
    Accepts:
    - 9876543210 -> +919876543210
    - 09876543210 -> +919876543210
    - 919876543210 -> +919876543210
    - +919876543210 -> +919876543210
    Returns normalized string or None if invalid.
    """
    if not phone_str:
        return None

    # Remove spaces, dashes, brackets
    cleaned = re.sub(r'[\s\-\(\)\.]', '', str(phone_str).strip())
    if not cleaned:
        return None

    # Standard E.164 already
    if re.match(r'^\+91[6-9]\d{9}$', cleaned):
        return cleaned

    # 91 prefix without plus
    if re.match(r'^91[6-9]\d{9}$', cleaned):
        return f"+{cleaned}"

    # 0 prefix
    if re.match(r'^0[6-9]\d{9}$', cleaned):
        return f"+91{cleaned[1:]}"

    # 10 digit Indian mobile number (starts with 6, 7, 8, 9)
    if re.match(r'^[6-9]\d{9}$', cleaned):
        return f"+91{cleaned}"

    return None

def mask_phone_number(phone_str):
    """
    Masks phone numbers for UI display & logging privacy.
    Example: +919876543210 -> XXXXXX3210, 9876543210 -> XXXXXX3210
    """
    if not phone_str:
        return ""

    s = str(phone_str).strip()
    # Extract digits
    digits = re.sub(r'\D', '', s)
    if len(digits) >= 4:
        last4 = digits[-4:]
        return f"XXXXXX{last4}"
    return "XXXXXX"

def validate_email_address(email_str):
    """Validates email format using regex."""
    if not email_str:
        return True # Optional email unless provided
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email_str).strip()))
