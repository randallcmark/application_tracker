import base64
import hashlib
import hmac
import secrets

from app.core.config import settings

_VERSION = "v1"


class SecretEnvelopeError(ValueError):
    pass


def _master_key() -> bytes:
    return settings.session_secret_key.encode("utf-8")


def _derive_key(label: bytes) -> bytes:
    return hmac.new(_master_key(), label, hashlib.sha256).digest()


def _xor_stream(key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(plaintext):
        block = hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        output.extend(block)
        counter += 1
    return bytes(a ^ b for a, b in zip(plaintext, output, strict=False))


def seal_secret(value: str) -> str:
    raw = value.encode("utf-8")
    nonce = secrets.token_bytes(16)
    ciphertext = _xor_stream(_derive_key(b"ai-secret-enc"), nonce, raw)
    payload = nonce + ciphertext
    tag = hmac.new(_derive_key(b"ai-secret-mac"), payload, hashlib.sha256).digest()
    return ".".join(
        (
            _VERSION,
            base64.urlsafe_b64encode(nonce).decode("ascii"),
            base64.urlsafe_b64encode(ciphertext).decode("ascii"),
            base64.urlsafe_b64encode(tag).decode("ascii"),
        )
    )


def open_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        version, nonce_b64, ciphertext_b64, tag_b64 = value.split(".", 3)
    except ValueError as exc:
        raise SecretEnvelopeError("Stored secret envelope is invalid") from exc
    if version != _VERSION:
        raise SecretEnvelopeError("Stored secret envelope version is not supported")
    nonce = base64.urlsafe_b64decode(nonce_b64.encode("ascii"))
    ciphertext = base64.urlsafe_b64decode(ciphertext_b64.encode("ascii"))
    tag = base64.urlsafe_b64decode(tag_b64.encode("ascii"))
    payload = nonce + ciphertext
    expected = hmac.new(_derive_key(b"ai-secret-mac"), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, tag):
        raise SecretEnvelopeError("Stored secret envelope failed verification")
    plaintext = _xor_stream(_derive_key(b"ai-secret-enc"), nonce, ciphertext)
    return plaintext.decode("utf-8")


def key_hint(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) <= 8:
        return cleaned
    return f"{cleaned[:4]}...{cleaned[-4:]}"
