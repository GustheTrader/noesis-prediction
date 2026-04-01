"""
Sovereign OS — Encrypted API Gateway

All API traffic encrypted end-to-end.
Your data. Your encryption. Your sovereignty.
"""

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


@dataclass
class EncryptedPayload:
    """An encrypted API payload."""
    ciphertext: bytes
    iv: bytes
    timestamp: float
    signature: str
    sender_id: str


class SovereignEncryption:
    """
    End-to-end encryption for Sovereign OS API traffic.
    
    Uses Fernet (AES-128-CBC with HMAC) for symmetric encryption.
    For production, upgrade to X25519 key exchange + AES-256-GCM.
    """

    def __init__(self, secret_key: str):
        """Initialize with a secret key (derived from passphrase or generated)."""
        self.key = self._derive_key(secret_key)
        self.cipher = Fernet(self.key)

    def _derive_key(self, secret: str) -> bytes:
        """Derive encryption key from passphrase using PBKDF2."""
        salt = b"sovereign_os_salt_v1"  # In production, use random salt per instance
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key

    def encrypt(self, data: str, sender_id: str = "") -> EncryptedPayload:
        """Encrypt data for transmission."""
        timestamp = time.time()

        # Create payload with metadata
        payload = json.dumps({
            "data": data,
            "timestamp": timestamp,
            "sender": sender_id,
        })

        # Encrypt
        ciphertext = self.cipher.encrypt(payload.encode())

        # Sign (HMAC for integrity)
        signature = hmac.new(
            self.key,
            ciphertext,
            hashlib.sha256,
        ).hexdigest()

        return EncryptedPayload(
            ciphertext=ciphertext,
            iv=b"",  # Fernet handles IV internally
            timestamp=timestamp,
            signature=signature,
            sender_id=sender_id,
        )

    def decrypt(self, payload: EncryptedPayload) -> Optional[str]:
        """Decrypt and verify a received payload."""
        # Verify signature
        expected_sig = hmac.new(
            self.key,
            payload.ciphertext,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(payload.signature, expected_sig):
            return None  # Tampered

        # Check timestamp (reject if > 5 minutes old)
        if time.time() - payload.timestamp > 300:
            return None  # Replay attack protection

        # Decrypt
        try:
            decrypted = self.cipher.decrypt(payload.ciphertext)
            data = json.loads(decrypted)
            return data.get("data")
        except Exception:
            return None

    def to_wire(self, payload: EncryptedPayload) -> str:
        """Serialize encrypted payload for transmission."""
        return json.dumps({
            "ciphertext": base64.b64encode(payload.ciphertext).decode(),
            "timestamp": payload.timestamp,
            "signature": payload.signature,
            "sender": payload.sender_id,
        })

    def from_wire(self, wire: str) -> Optional[EncryptedPayload]:
        """Deserialize encrypted payload from wire format."""
        try:
            data = json.loads(wire)
            return EncryptedPayload(
                ciphertext=base64.b64decode(data["ciphertext"]),
                iv=b"",
                timestamp=data["timestamp"],
                signature=data["signature"],
                sender_id=data.get("sender", ""),
            )
        except Exception:
            return None


class SovereignAPIGateway:
    """
    Encrypted API gateway for Sovereign OS.
    
    All traffic between instances is encrypted.
    No plaintext leaves your instance.
    """

    def __init__(self, instance_id: str, secret_key: str):
        self.instance_id = instance_id
        self.encryption = SovereignEncryption(secret_key)
        self.trusted_instances: dict[str, SovereignEncryption] = {}

    def register_trusted(self, instance_id: str, shared_secret: str):
        """Register a trusted instance with shared encryption."""
        self.trusted_instances[instance_id] = SovereignEncryption(shared_secret)

    def send(self, data: str, to_instance: str) -> Optional[str]:
        """Encrypt and prepare data for sending to another instance."""
        enc = self.trusted_instances.get(to_instance, self.encryption)
        payload = enc.encrypt(data, sender_id=self.instance_id)
        return enc.to_wire(payload)

    def receive(self, wire: str, from_instance: str = "") -> Optional[str]:
        """Decrypt and verify received data."""
        if from_instance and from_instance in self.trusted_instances:
            enc = self.trusted_instances[from_instance]
        else:
            enc = self.encryption

        payload = enc.from_wire(wire)
        if not payload:
            return None

        return enc.decrypt(payload)

    def broadcast(self, data: str) -> dict[str, str]:
        """Encrypt and send to all trusted instances."""
        results = {}
        for instance_id in self.trusted_instances:
            wire = self.send(data, instance_id)
            if wire:
                results[instance_id] = wire
        return results


class SovereignAuth:
    """
    Simple sovereign authentication.
    
    No OAuth. No third-party auth. Just cryptographic proof of identity.
    """

    def __init__(self, instance_id: str, secret_key: str):
        self.instance_id = instance_id
        self.secret_key = secret_key

    def create_token(self, expires_in: int = 3600) -> str:
        """Create a sovereign auth token."""
        payload = {
            "instance": self.instance_id,
            "issued": time.time(),
            "expires": time.time() + expires_in,
        }
        # Sign with HMAC
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        token = base64.urlsafe_b64encode(
            json.dumps({"payload": payload, "sig": signature}).encode()
        ).decode()
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify a sovereign auth token."""
        try:
            data = json.loads(base64.urlsafe_b64decode(token))
            payload = data["payload"]
            signature = data["sig"]

            # Check expiry
            if time.time() > payload.get("expires", 0):
                return None

            # Verify signature
            message = json.dumps(payload, sort_keys=True)
            expected = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256,
            ).hexdigest()

            if hmac.compare_digest(signature, expected):
                return payload
            return None
        except Exception:
            return None
