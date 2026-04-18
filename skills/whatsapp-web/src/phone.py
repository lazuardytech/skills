"""Phone number formatting utilities for WhatsApp Web."""

import re


def extract_digits(phone: str) -> str:
    """Strip all non-digit characters from a phone string."""
    return re.sub(r"[^\d]", "", phone)


def normalize_phone(phone: str, country_code: str = "62") -> str:
    """Strip non-digits and prepend country code if needed.

    - Leading '0' is replaced with the country code
    - If no country code prefix, it's prepended
    """
    p = extract_digits(phone)
    if p.startswith("0"):
        p = country_code + p[1:]
    elif not p.startswith(country_code):
        p = country_code + p
    return p


def format_phone_wa(phone: str, country_code: str = "62") -> str:
    """Convert a phone number to WhatsApp Web display format.

    Examples (country_code="62"):
        "81246564246"  -> "+62 812-4656-4246"
        "081246564246" -> "+62 812-4656-4246"
        "811289848"    -> "+62 811-289-848"
    """
    p = normalize_phone(phone, country_code)
    digits = p[len(country_code) :]
    prefix = f"+{country_code} "
    if len(digits) >= 9:
        # 3-3-rest grouping (default WA display for most Indonesian numbers)
        return f"{prefix}{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return f"{prefix}{digits}"


def format_phone_wa_variants(phone: str, country_code: str = "62") -> list[str]:
    """Return all plausible WhatsApp Web display formats for a phone number.

    WA Web uses different digit groupings depending on number length:
        9 digits:  3-3-3 or 3-4-2
        10 digits: 3-3-4 or 3-4-3
        11 digits: 3-3-5 or 3-4-4
    """
    p = normalize_phone(phone, country_code)
    digits = p[len(country_code) :]
    prefix = f"+{country_code} "

    if len(digits) < 9:
        return [f"{prefix}{digits}"]

    variants = {
        f"{prefix}{digits[:3]}-{digits[3:6]}-{digits[6:]}",  # 3-3-rest
        f"{prefix}{digits[:3]}-{digits[3:7]}-{digits[7:]}",  # 3-4-rest
    }
    return list(variants)
