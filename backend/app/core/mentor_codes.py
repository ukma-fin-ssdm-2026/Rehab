"""Permanent, unpredictable sharing codes; never authentication credentials."""

import secrets

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_mentor_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(12))
