"""
Encrypted credential storage for service authentication.

Provides secure at-rest storage for credentials using Fernet symmetric encryption.
Supports multiple credential types: login_password, api_key, oauth_token.
"""

import base64
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
import structlog

from autoqa.exceptions import AuthError

logger = structlog.get_logger(__name__)


class CredentialStore:
    """
    Encrypted credential store for service authentication.

    Usage:
        store = CredentialStore(encryption_key="your-secret-key")

        # Store credentials
        store.store_credentials(
            service_id="k2think",
            credential_type="login_password",
            data={"email": "user@example.com", "password": "secret123"}
        )

        # Retrieve credentials
        creds = store.get_credentials("k2think")
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize credential store.

        Args:
            encryption_key: Fernet encryption key (32 bytes, base64 encoded).
                          If not provided, will load from environment or generate.
        """
        if encryption_key:
            self._key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            # Try to load from environment
            env_key = os.environ.get("CREDENTIAL_ENCRYPTION_KEY")
            if env_key:
                self._key = env_key.encode()
            else:
                # Generate new key (WARNING: will lose existing credentials!)
                logger.warning("No encryption key provided, generating new key")
                self._key = Fernet.generate_key()
                logger.info("Generated new encryption key", key=self._key.decode())

        try:
            self._cipher = Fernet(self._key)
        except Exception as e:
            raise AuthError(f"Invalid encryption key: {e}")

        self._log = logger.bind(component="credential_store")

    def store_credentials(
        self,
        service_id: str,
        credential_type: str,
        data: Dict[str, Any],
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Encrypt and store credentials for a service.

        Args:
            service_id: Service identifier
            credential_type: Type of credentials (login_password, api_key, oauth_token, etc.)
            data: Credential data (email, password, api_key, etc.)
            expires_at: Optional expiration date

        Returns:
            Reference string for stored credentials

        Raises:
            AuthError: If encryption fails
        """
        try:
            # Prepare credential payload
            payload = {
                "service_id": service_id,
                "type": credential_type,
                "data": data,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None
            }

            # Serialize and encrypt
            json_data = json.dumps(payload).encode("utf-8")
            encrypted_data = self._cipher.encrypt(json_data)

            # Encode as base64 for storage reference
            credential_ref = base64.b64encode(encrypted_data).decode("utf-8")

            self._log.info(
                "Credentials stored",
                service_id=service_id,
                credential_type=credential_type,
                expires_at=expires_at
            )

            return credential_ref

        except Exception as e:
            self._log.error("Failed to store credentials", service_id=service_id, error=str(e))
            raise AuthError(f"Failed to encrypt credentials: {e}")

    def get_credentials(self, credential_ref: str) -> Dict[str, Any]:
        """
        Retrieve and decrypt credentials.

        Args:
            credential_ref: Credential reference from store_credentials()

        Returns:
            Dict with credential data

        Raises:
            AuthError: If decryption fails or credentials expired
        """
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(credential_ref.encode("utf-8"))

            # Decrypt
            json_data = self._cipher.decrypt(encrypted_data)
            payload = json.loads(json_data.decode("utf-8"))

            # Check expiration
            if payload.get("expires_at"):
                expires_at = datetime.fromisoformat(payload["expires_at"])
                if datetime.utcnow() > expires_at:
                    raise AuthError(f"Credentials expired at {expires_at}")

            self._log.info(
                "Credentials retrieved",
                service_id=payload.get("service_id"),
                credential_type=payload.get("type")
            )

            return payload

        except AuthError:
            raise
        except Exception as e:
            self._log.error("Failed to retrieve credentials", error=str(e))
            raise AuthError(f"Failed to decrypt credentials: {e}")

    def rotate_credentials(
        self,
        service_id: str,
        credential_ref: str,
        new_data: Dict[str, Any]
    ) -> str:
        """
        Rotate credentials for a service.

        Args:
            service_id: Service identifier
            credential_ref: Existing credential reference
            new_data: New credential data

        Returns:
            New credential reference
        """
        # Get existing credentials to preserve metadata
        existing = self.get_credentials(credential_ref)

        # Store new credentials
        return self.store_credentials(
            service_id=service_id,
            credential_type=existing["type"],
            data=new_data,
            expires_at=datetime.fromisoformat(existing["expires_at"]) if existing.get("expires_at") else None
        )

    def validate_credentials(self, credential_ref: str) -> bool:
        """
        Validate credentials without exposing them.

        Args:
            credential_ref: Credential reference

        Returns:
            True if credentials are valid and not expired
        """
        try:
            payload = self.get_credentials(credential_ref)
            return True
        except AuthError:
            return False

    def get_credential_type(self, credential_ref: str) -> Optional[str]:
        """
        Get credential type without decrypting full payload.

        Args:
            credential_ref: Credential reference

        Returns:
            Credential type string or None
        """
        try:
            payload = self.get_credentials(credential_ref)
            return payload.get("type")
        except AuthError:
            return None

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key

        Example:
            key = CredentialStore.generate_key()
            store = CredentialStore(encryption_key=key)
        """
        return Fernet.generate_key().decode("utf-8")


# Convenience function for environment setup
def setup_credential_store() -> CredentialStore:
    """
    Setup credential store from environment variables.

    Environment Variables:
        CREDENTIAL_ENCRYPTION_KEY: Fernet encryption key (required)

    Returns:
        Configured CredentialStore instance

    Raises:
        AuthError: If key not found in environment
    """
    key = os.environ.get("CREDENTIAL_ENCRYPTION_KEY")

    if not key:
        raise AuthError(
            "CREDENTIAL_ENCRYPTION_KEY environment variable not set. "
            "Generate one with: CredentialStore.generate_key()"
        )

    return CredentialStore(encryption_key=key)
