import json
import hmac
import hashlib


def sign_payload(payload: dict, key: str) -> str:
    message = json.dumps(payload, sort_keys=True).encode()
    return hmac.new(key.encode(), message, hashlib.sha256).hexdigest()
