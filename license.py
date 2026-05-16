import os
import hashlib
from config import APP_DIR, LICENSE_FILE


# --- Validate key format and authenticity ---
def validate_key(key):
    try:
        parts = key.strip().upper().split("-")

        if len(parts) != 4 or parts[0] != "GITINVO":
            return False

        SECRET = "GitInvo2026SecretSalt"
        raw = f"{SECRET}-{parts[1]}-{parts[2]}"  # ← only seg1 and seg2
        expected = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

        return expected == parts[3]  # ← now compares correctly

    except Exception:
        return False


def generate_key(seg1, seg2):
    SECRET = "GitInvo2026SecretSalt"
    raw = f"{SECRET}-{seg1}-{seg2}"  # ← must match validate_key exactly
    checksum = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()
    return f"GITINVO-{seg1}-{seg2}-{checksum}"


if __name__ == "__main__":
    key = generate_key("AB12", "CD34")
    print(f"Generated key: {key}")


# --- Check if already activated ---
def is_activated():
    if not os.path.exists(LICENSE_FILE):
        return False

    with open(LICENSE_FILE, "r") as f:
        key = f.read().strip()

    return validate_key(key)


# --- Save key after activation ---
def activate(key):
    if not validate_key(key):
        return False, "Invalid license key."

    if os.path.exists(LICENSE_FILE):
        return False, "This app is already activated."

    os.makedirs(APP_DIR, exist_ok=True)
    with open(LICENSE_FILE, "w") as f:
        f.write(key.strip().upper())

    return True, "Activation successful!"


if __name__ == "__main__":
    # Run this file directly to generate a key
    # python license.py
    key = generate_key("AB12", "CD34")
    print(f"Generated key: {key}")