def to_kobo(value):
    return int(float(value))  # no multiplication

def to_naira(value):
    return float(value)

def format_currency(value):
    return f"NGN {float(value):,.2f}"