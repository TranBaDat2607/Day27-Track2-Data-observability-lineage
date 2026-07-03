"""Fernet encrypt/decrypt of phase schedules (spec §9). The plaintext schedule
(events + ground_truth + labels) never touches disk or git history — only the
ciphertext + a per-phase key file do."""
import json
from cryptography.fernet import Fernet


def generate_key():
    return Fernet.generate_key()


def encrypt_schedule(schedule_dict, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(json.dumps(schedule_dict).encode("utf-8"))


def decrypt_schedule(ciphertext: bytes, key: bytes) -> dict:
    f = Fernet(key)
    return json.loads(f.decrypt(ciphertext).decode("utf-8"))
