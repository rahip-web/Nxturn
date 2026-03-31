import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

# ============================================================
# USERNAME VALIDATION
# ============================================================

USERNAME_ALLOWED_RE = re.compile(r"^[A-Za-z0-9._]+$")
ASCII_ONLY_RE = re.compile(r"^[\x00-\x7F]+$")

RESERVED_USERNAMES = {
    "admin",
    "administrator",
    "root",
    "support",
    "help",
    "instagram",
    "facebook",
    "meta",
    "api",
    "www",
    "mail",
    "email",
    "login",
    "logout",
    "signup",
    "register",
}


def validate_registration_username(username: str) -> str:
    if not username:
        raise serializers.ValidationError("Username is required.")

    username = username.strip()

    # Length check
    if not 3 <= len(username) <= 30:
        raise serializers.ValidationError(
            "Username must be between 3 and 30 characters."
        )

    # ASCII only (no emoji, no unicode)
    if not ASCII_ONLY_RE.fullmatch(username):
        raise serializers.ValidationError(
            "Username must contain only lowercase English letters, numbers, and underscores."
        )

    # Only lowercase letters and numbers
    if not re.fullmatch(r"[a-z0-9_]+", username):
        raise serializers.ValidationError(
            "Use only lowercase letters and numbers. No spaces or symbols."
        )

    # Cannot be entirely numeric
    if username.isdigit():
        raise serializers.ValidationError("Username cannot be entirely numeric.")

    # Must contain at least one letter
    if not re.search(r"[a-z]", username):
        raise serializers.ValidationError("Username must contain at least one letter.")

    # Reserved usernames
    if username.lower() in RESERVED_USERNAMES:
        raise serializers.ValidationError("This username is not available.")

    # Case-insensitive uniqueness
    if User.objects.filter(username__iexact=username).exists():
        raise serializers.ValidationError("A user with that username already exists.")

    return username


def validate_login_username(username: str) -> str:
    if not username:
        raise serializers.ValidationError("Username is required.")

    username = username.strip()

    if not username:
        raise serializers.ValidationError("Username is required.")

    if username != username.lower():
        raise serializers.ValidationError("Username must be lowercase.")

    if not re.fullmatch(r"[a-z0-9_]+", username):
        raise serializers.ValidationError(
            "Use only lowercase letters and numbers. No spaces or symbols."
        )

    return username


# ============================================================
# EMAIL VALIDATION
# ============================================================

EMAIL_LOCAL_ALLOWED_RE = re.compile(r"^[A-Za-z0-9._%+-]+$")

EMAIL_DOMAIN_ALLOWED_RE = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}$"
)


VALID_TLDS = {
    "com",
    "in",
    "org",
    "net",
    "co",
    "io",
    "edu",
    "gov",
    "me",
    "info",
    "biz",
    "app",
}


def validate_registration_email(email: str) -> str:
    if not email:
        raise serializers.ValidationError("Email is required.")

    email = email.strip()
    if email != email.lower():
        raise serializers.ValidationError("Email must contain only lowercase letters.")
    if any(ch.isspace() for ch in email):
        raise serializers.ValidationError("Email cannot contain spaces.")

    if not len(email) <= 50:
        raise serializers.ValidationError("Email must be between 3 and 50 characters.")

    if not email.isascii():
        raise serializers.ValidationError("Email must contain only English characters.")

    if email.count("@") != 1:
        raise serializers.ValidationError("Enter a valid email address.")

    local_part, domain = email.split("@", 1)

    if not local_part:
        raise serializers.ValidationError("Email username (before @) cannot be empty.")

    if not domain:
        raise serializers.ValidationError("Email domain (after @) cannot be empty.")

    if not re.fullmatch(r"[a-z0-9._]+", local_part):
        raise serializers.ValidationError(
            "Email username may contain only lowercase letters, numbers, dots, and underscores."
        )

    if local_part.startswith(".") or local_part.endswith(".") or ".." in local_part:
        raise serializers.ValidationError(
            "Email username cannot start/end with dot or contain consecutive dots."
        )

    if not EMAIL_DOMAIN_ALLOWED_RE.fullmatch(domain):
        raise serializers.ValidationError("Email domain is invalid.")

    labels = domain.split(".")

    # TLD check
    tld = labels[-1]
    if tld not in VALID_TLDS:
        raise serializers.ValidationError("Email domain is not supported.")

    # Block repeated patterns like gmailgmailgmail (2+ char segments)
    first_label = labels[0]

    if re.search(r"(.{2,})\1{1,}", first_label):
        raise serializers.ValidationError("Email domain is invalid.")

    # Optional: limit first label length (real providers are usually shorter)
    if len(first_label) > 30:
        raise serializers.ValidationError("Email domain is invalid.")

    if User.objects.filter(email__iexact=email).exists():
        raise serializers.ValidationError("This field must be unique.")

    return email


# ============================================================
# PASSWORD VALIDATION
# ============================================================


PASSWORD_ALLOWED_RE = re.compile(
    r"^(?=.*[a-z])"
    r"(?=.*[A-Z])"
    r"(?=.*\d)"
    r'(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/])'
    r'[A-Za-z\d !@#$%^&*()_+\-=\[\]{};:\'",.<>?/]{8,30}$'
)


def validate_registration_password(password: str) -> str:
    if not password:
        raise serializers.ValidationError("Password is required.")

    #  Block Hindi, Marathi, Emoji, any Unicode
    if not password.isascii():
        raise serializers.ValidationError(
            "Password must contain only English letters, numbers, and standard special characters."
        )

    if len(password) > 128:
        raise serializers.ValidationError("Password cannot exceed 128 characters.")

    if not PASSWORD_ALLOWED_RE.fullmatch(password):
        raise serializers.ValidationError(
            "Password must be 8 characters long and include at least "
            "1 uppercase, 1 lowercase, 1 number, and 1 special character."
        )

    try:
        validate_password(password)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages))

    return password
