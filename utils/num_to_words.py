def amount_in_words(num):
    """
    Convert a numeric amount into Indian Currency Words.
    Example: 53718.00 -> Rupees Fifty-Three Thousand Seven Hundred Eighteen Only
    """
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "Rupees Zero Only"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _convert_below_thousand(n):
        res = ""
        if n >= 100:
            res += units[n // 100] + " Hundred "
            n %= 100
        if n >= 20:
            res += tens[n // 10] + ("-" + units[n % 10] if n % 10 != 0 else "") + " "
        elif n > 0:
            res += units[n] + " "
        return res

    rupees = int(num)
    paise = int(round((num - rupees) * 100))

    if rupees == 0:
        words = "Zero"
    else:
        parts = []
        crores = rupees // 10000000
        rupees %= 10000000
        if crores > 0:
            parts.append(_convert_below_thousand(crores).strip() + " Crore")

        lakhs = rupees // 100000
        rupees %= 100000
        if lakhs > 0:
            parts.append(_convert_below_thousand(lakhs).strip() + " Lakh")

        thousands = rupees // 1000
        rupees %= 1000
        if thousands > 0:
            parts.append(_convert_below_thousand(thousands).strip() + " Thousand")

        if rupees > 0:
            parts.append(_convert_below_thousand(rupees).strip())

        words = " ".join(parts).strip()

    res_str = f"Rupees {words}"
    if paise > 0:
        paise_words = _convert_below_thousand(paise).strip()
        res_str += f" and {paise_words} Paise"
    
    res_str += " Only"
    return res_str
