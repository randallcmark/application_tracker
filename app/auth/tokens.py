from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe


def create_secret_token(prefix: str, nbytes: int = 32) -> str:
    return f"{prefix}_{token_urlsafe(nbytes)}"


def hash_secret(secret: str) -> str:
    return sha256(secret.encode("utf-8")).hexdigest()


def verify_secret(secret: str, secret_hash: str) -> bool:
    return compare_digest(hash_secret(secret), secret_hash)


def create_session_token() -> str:
    return create_secret_token("ats_session")


def create_api_token() -> str:
    return create_secret_token("ats")

