import string
import secrets

def generate_secure_password(length=30, min_digits=3):
    alphabet = string.ascii_letters + string.digits
    password_chars = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        *[secrets.choice(string.digits) for _ in range(min_digits)]
    ]
    password_chars += [secrets.choice(alphabet) for _ in range(length - len(password_chars))]
    secrets.SystemRandom().shuffle(password_chars)
    return ''.join(password_chars)
