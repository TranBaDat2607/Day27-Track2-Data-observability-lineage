"""HMAC-SHA256 signing of result logs — a tamper-evidence tripwire, not a
cryptographic guarantee (spec §9: this module ships as readable source, so a
motivated reader could forge a signature; the real backstop is the spot-check
re-run, which recomputes independently rather than trusting the submitted
JSON's own contents)."""
import hmac
import hashlib
import json


def sign(result_dict, secret: bytes) -> str:
    canonical = json.dumps(result_dict, sort_keys=True).encode("utf-8")
    return hmac.new(secret, canonical, hashlib.sha256).hexdigest()


def verify(result_dict, signature: str, secret: bytes) -> bool:
    return hmac.compare_digest(sign(result_dict, secret), signature)
