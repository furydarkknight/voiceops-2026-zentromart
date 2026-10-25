"""Domain and business logic calculations for ZentroMart."""
from datetime import date, timedelta
from typing import Optional, Tuple, Dict, Any
from src.config import REFERENCE_DATE, HOLIDAYS

def is_business_day(d: date) -> bool:
    """A business day is Monday to Saturday (weekday 0-5), excluding warehouse holidays."""
    if d.weekday() == 6:  # Sunday
        return False
    if d in HOLIDAYS:
        return False
    return True

def add_business_days(start_date: date, num_days: int) -> date:
    """Adds num_days business days starting from the day after start_date."""
    current = start_date
    added = 0
    while added < num_days:
        current += timedelta(days=1)
        if is_business_day(current):
            added += 1
    return current

def count_business_days_between(start_date: date, end_date: date) -> int:
    """Counts business days strictly between start_date and end_date (start_date exclusive, end_date inclusive)."""
    current = start_date
    count = 0
    while current < end_date:
        current += timedelta(days=1)
        if is_business_day(current):
            count += 1
    return count

def get_refund_timeline_days(payment_method: str) -> Optional[Tuple[int, int]]:
    """Returns (min_days, max_days) in business days for a payment method."""
    method = (payment_method or "").lower().strip()
    if "wallet" in method:
        return (0, 0)  # Instant, within 2 hours
    if "upi" in method:
        return (1, 3)
    if "net_banking" in method or "netbanking" in method or "net banking" in method:
        return (3, 5)
    if "card" in method or "credit" in method or "debit" in method:
        return (5, 7)
    if "cod" in method or "cash" in method or "neft" in method or "transfer" in method:
        return (5, 7)
    return None

def calculate_refund_expected_dates(initiation_date: date, payment_method: str) -> Optional[Tuple[date, date]]:
    """Calculates min and max expected delivery dates for a refund."""
    timeline = get_refund_timeline_days(payment_method)
    if not timeline:
        return None
    min_d, max_d = timeline
    if min_d == 0 and max_d == 0:
        return (initiation_date, initiation_date)
    min_date = add_business_days(initiation_date, min_d)
    max_date = add_business_days(initiation_date, max_d)
    return (min_date, max_date)

def get_return_window_days(category: str, delivery_date: Optional[date] = None, order_date: Optional[date] = None) -> int:
    """Calculates return window in calendar days based on category, delivery date, and order date."""
    cat = (category or "").lower().strip()
    
    # Festive sale rule (RET-8): Fashion orders placed between 1 and 15 Oct 2026 get 30 days
    if cat in ("fashion", "clothing", "footwear", "bags") and order_date:
        if date(2026, 10, 1) <= order_date <= date(2026, 10, 15):
            return 30
        return 15
    elif cat in ("fashion", "clothing", "footwear", "bags"):
        return 15
        
    if cat in ("electronics", "elec"):
        # RET-3: Delivered before 1 August 2026 kept 10 days, otherwise 7 days
        if delivery_date and delivery_date < date(2026, 8, 1):
            return 10
        return 7
        
    if cat in ("home_kitchen", "home"):
        return 10
    if cat in ("beauty_sealed", "beauty"):
        return 7
    if cat in ("books_media", "books"):
        return 10
    if cat in ("grocery", "innerwear", "digital"):
        return 0
    return 7  # default fallback

def is_refund_overdue(initiation_date: date, payment_method: str, as_of: date = REFERENCE_DATE) -> Tuple[bool, int]:
    """Checks if refund is more than 3 business days past maximum timeline (ESC-1 rule 5)."""
    timeline = get_refund_timeline_days(payment_method)
    if not timeline:
        return False, 0
    _, max_days = timeline
    expected_max_date = add_business_days(initiation_date, max_days)
    if as_of > expected_max_date:
        overdue_business_days = count_business_days_between(expected_max_date, as_of)
        if overdue_business_days > 3:
            return True, overdue_business_days
    return False, 0

def format_spoken_date(d: date) -> str:
    """Formats date for voice output: e.g. '24th of October 2026'."""
    day = d.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    month_name = d.strftime("%B")
    return f"the {day}{suffix} of {month_name} {d.year}"

def format_written_date(d: date) -> str:
    """Formats date for written reply: e.g. '24 October 2026'."""
    return f"{d.day} {d.strftime('%B')} {d.year}"

def format_spoken_order_id(order_id: str) -> str:
    """Spaces out order id digits in groups of four for natural TTS rendering."""
    digits = "".join(ch for ch in str(order_id) if ch.isdigit())
    if len(digits) == 8:
        return f"{digits[:4]} {digits[4:]}"
    return " ".join(digits)
