import hmac
import hashlib
import json

# Replace these with your actual values
secret = "string"
payload = {
    "event": "user.created",
    "data": {"id": 123, "name": "John Doe"}
}

# Encode the payload
body = json.dumps(payload, separators=(",", ":")).encode() # No whitespace, consistent with server
signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

# Format it for the header
x_hub_signature_256 = f"sha256={signature}"

print("X-Hub-Signature-256:", x_hub_signature_256)
