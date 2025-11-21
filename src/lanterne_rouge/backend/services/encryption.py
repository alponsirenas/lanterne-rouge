"""Encryption service for secure credential storage."""
import json

from cryptography.fernet import Fernet

from lanterne_rouge.backend.core.config import get_settings

settings = get_settings()


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        """Initialize encryption service with a key."""
        # Use SECRET_KEY to derive an encryption key
        # In production, this should be a separate encryption key
        key = self._derive_key_from_secret(settings.secret_key)
        self.cipher = Fernet(key)

    @staticmethod
    def _derive_key_from_secret(secret: str) -> bytes:
        """
        Derive a Fernet-compatible key from the secret key.

        Fernet requires a 32-byte base64-encoded key.
        We'll use the first 32 bytes of the secret key, padded if necessary.
        """
        import base64
        import hashlib

        # Hash the secret to get consistent 32 bytes
        key_bytes = hashlib.sha256(secret.encode()).digest()
        # Encode to base64 for Fernet
        return base64.urlsafe_b64encode(key_bytes)

    def encrypt_credentials(self, credentials: dict) -> str:
        """
        Encrypt a credentials dictionary.

        Args:
            credentials: Dictionary containing credential data

        Returns:
            Encrypted string (base64 encoded)
        """
        # Convert dict to JSON string
        json_str = json.dumps(credentials)
        # Encrypt
        encrypted = self.cipher.encrypt(json_str.encode())
        # Return as string
        return encrypted.decode()

    def decrypt_credentials(self, encrypted_data: str) -> dict:
        """
        Decrypt credentials string back to dictionary.

        Args:
            encrypted_data: Encrypted credentials string

        Returns:
            Decrypted credentials dictionary
        """
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        # Parse JSON
        return json.loads(decrypted.decode())

    def redact_for_logging(self, credentials: dict) -> dict:
        """
        Create a redacted version of credentials safe for logging.

        Args:
            credentials: Original credentials dictionary

        Returns:
            Redacted dictionary with sensitive values masked
        """
        redacted = {}
        for key, value in credentials.items():
            if any(sensitive in key.lower() for sensitive in [
                'token', 'secret', 'password', 'key', 'pat'
            ]):
                # Show only first and last 4 characters
                if isinstance(value, str) and len(value) > 8:
                    redacted[key] = f"{value[:4]}...{value[-4:]}"
                else:
                    redacted[key] = "***REDACTED***"
            else:
                redacted[key] = value
        return redacted


# Global instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get or create the encryption service singleton."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
