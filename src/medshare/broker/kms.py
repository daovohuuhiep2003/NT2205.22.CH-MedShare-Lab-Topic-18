"""
Software KMS Client module for MedShare-Lab.
Integrates with HashiCorp Vault Transit Engine in Zone Z1.
Provides authenticated key wrapping, unwrapping, rotation, and rewrapping.
"""

from abc import ABC, abstractmethod
import base64
import os
import secrets
from typing import Any, Optional
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class KmsError(Exception):
    """Base exception for KMS operations."""
    pass


class KmsConnectionError(KmsError):
    """Raised when KMS service cannot be reached."""
    pass


class KmsKeyNotFoundError(KmsError):
    """Raised when the specified key is not found in KMS."""
    pass


class KmsDecryptionFailedError(KmsError):
    """Raised when unwrapping/decryption fails in KMS."""
    pass


class KmsContextMismatchError(KmsDecryptionFailedError):
    """Raised when authenticated context does not match during unwrap."""
    pass


class KmsClientBase(ABC):
    """Abstract base class for Software KMS clients."""

    @abstractmethod
    def ensure_key(self, key_name: str, key_type: str = "aes256-gcm96") -> bool:
        """Ensure a key exists in KMS, creating it if necessary."""
        pass

    @abstractmethod
    def wrap_dek(self, key_name: str, plaintext_dek: bytes, context: Optional[bytes] = None) -> tuple[str, int]:
        """
        Wrap (encrypt) a data encryption key (DEK) under the specified KEK.
        Returns: (wrapped_ciphertext, kek_version)
        """
        pass

    @abstractmethod
    def unwrap_dek(self, key_name: str, wrapped_dek: str, context: Optional[bytes] = None) -> bytes:
        """
        Unwrap (decrypt) a data encryption key under the specified KEK and context.
        Returns: plaintext_dek bytes
        """
        pass

    @abstractmethod
    def rotate_key(self, key_name: str) -> int:
        """Rotate the KEK to a new version. Returns the new version number."""
        pass

    @abstractmethod
    def rewrap_dek(self, key_name: str, wrapped_dek: str, context: Optional[bytes] = None) -> tuple[str, int]:
        """
        Rewrap ciphertext under the latest KEK version without exposing plaintext.
        Returns: (new_wrapped_ciphertext, new_version)
        """
        pass


class VaultKmsClient(KmsClientBase):
    """
    HashiCorp Vault Transit Secret Engine Client.
    Connects to Vault in Zone Z1 via REST API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8200",
        token: str = "dev-root-token-topic18",
        mount_path: str = "transit",
        timeout: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.mount_path = mount_path.strip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-Vault-Token": self.token,
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        return f"{self.base_url}/v1/{self.mount_path}/{path.lstrip('/')}"

    def ensure_key(self, key_name: str, key_type: str = "aes256-gcm96", derived: bool = True) -> bool:
        """Ensure transit key exists; create if not found."""
        check_url = self._url(f"keys/{key_name}")
        try:
            resp = self._session.get(check_url, timeout=self.timeout)
            if resp.status_code == 200:
                return True
            if resp.status_code == 404:
                # Key does not exist; create it with context derivation enabled
                create_resp = self._session.post(
                    check_url,
                    json={"type": key_type, "derived": derived, "convergent_encryption": False},
                    timeout=self.timeout,
                )
                if create_resp.status_code in (200, 204):
                    return True
                raise KmsError(f"Failed to create Vault key '{key_name}': {create_resp.text}")
            raise KmsError(f"Unexpected response checking key '{key_name}': {resp.status_code} - {resp.text}")
        except requests.exceptions.ConnectionError as ex:
            raise KmsConnectionError(f"Cannot connect to Vault at {self.base_url}: {ex}") from ex

    def wrap_dek(self, key_name: str, plaintext_dek: bytes, context: Optional[bytes] = None) -> tuple[str, int]:
        """
        Wrap DEK via POST /v1/transit/encrypt/<key_name>.
        """
        if not plaintext_dek:
            raise ValueError("Plaintext DEK cannot be empty")
        self.ensure_key(key_name)
        
        payload: dict[str, Any] = {
            "plaintext": base64.b64encode(plaintext_dek).decode("ascii"),
        }
        if context:
            payload["context"] = base64.b64encode(context).decode("ascii")

        url = self._url(f"encrypt/{key_name}")
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                raise KmsError(f"Vault encrypt failed for key '{key_name}': {resp.status_code} - {resp.text}")
            data = resp.json().get("data", {})
            ciphertext = data.get("ciphertext")
            if not ciphertext:
                raise KmsError(f"Vault response missing ciphertext: {resp.text}")
            
            # Vault format: vault:v<version>:<base64>
            version = 1
            parts = ciphertext.split(":")
            if len(parts) >= 2 and parts[1].startswith("v"):
                try:
                    version = int(parts[1][1:])
                except ValueError:
                    version = 1
            return ciphertext, version
        except requests.exceptions.ConnectionError as ex:
            raise KmsConnectionError(f"Cannot connect to Vault: {ex}") from ex

    def unwrap_dek(self, key_name: str, wrapped_dek: str, context: Optional[bytes] = None) -> bytes:
        """
        Unwrap DEK via POST /v1/transit/decrypt/<key_name>.
        """
        if not wrapped_dek:
            raise ValueError("Wrapped DEK ciphertext cannot be empty")

        payload: dict[str, Any] = {
            "ciphertext": wrapped_dek,
        }
        if context:
            payload["context"] = base64.b64encode(context).decode("ascii")

        url = self._url(f"decrypt/{key_name}")
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 400:
                error_msg = resp.text.lower()
                if "context" in error_msg or "message authentication failed" in error_msg or "decryption failed" in error_msg:
                    raise KmsContextMismatchError(f"Context mismatch or corrupted ciphertext in Vault: {resp.text}")
                raise KmsDecryptionFailedError(f"Vault decryption failed: {resp.text}")
            if resp.status_code != 200:
                raise KmsError(f"Vault decrypt request failed: {resp.status_code} - {resp.text}")
            
            data = resp.json().get("data", {})
            plaintext_b64 = data.get("plaintext")
            if not plaintext_b64:
                raise KmsError(f"Vault response missing plaintext: {resp.text}")
            return base64.b64decode(plaintext_b64)
        except requests.exceptions.ConnectionError as ex:
            raise KmsConnectionError(f"Cannot connect to Vault: {ex}") from ex

    def rotate_key(self, key_name: str) -> int:
        """
        Rotate KEK via POST /v1/transit/keys/<key_name>/rotate.
        """
        self.ensure_key(key_name)
        url = self._url(f"keys/{key_name}/rotate")
        try:
            resp = self._session.post(url, timeout=self.timeout)
            if resp.status_code not in (200, 204):
                raise KmsError(f"Vault rotate failed for key '{key_name}': {resp.status_code} - {resp.text}")
            
            # Read new version
            read_url = self._url(f"keys/{key_name}")
            read_resp = self._session.get(read_url, timeout=self.timeout)
            if read_resp.status_code == 200:
                latest_version = read_resp.json().get("data", {}).get("latest_version", 1)
                return int(latest_version)
            return 2
        except requests.exceptions.ConnectionError as ex:
            raise KmsConnectionError(f"Cannot connect to Vault: {ex}") from ex

    def rewrap_dek(self, key_name: str, wrapped_dek: str, context: Optional[bytes] = None) -> tuple[str, int]:
        """
        Rewrap ciphertext under latest KEK version via POST /v1/transit/rewrap/<key_name>.
        """
        payload: dict[str, Any] = {
            "ciphertext": wrapped_dek,
        }
        if context:
            payload["context"] = base64.b64encode(context).decode("ascii")

        url = self._url(f"rewrap/{key_name}")
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                raise KmsError(f"Vault rewrap failed for key '{key_name}': {resp.status_code} - {resp.text}")
            data = resp.json().get("data", {})
            new_ciphertext = data.get("ciphertext")
            if not new_ciphertext:
                raise KmsError(f"Vault response missing rewrapped ciphertext: {resp.text}")
            
            version = 1
            parts = new_ciphertext.split(":")
            if len(parts) >= 2 and parts[1].startswith("v"):
                try:
                    version = int(parts[1][1:])
                except ValueError:
                    version = 1
            return new_ciphertext, version
        except requests.exceptions.ConnectionError as ex:
            raise KmsConnectionError(f"Cannot connect to Vault: {ex}") from ex


class MockKmsClient(KmsClientBase):
    """
    In-memory software KMS simulation using local AES-256-GCM.
    Used for unit testing and offline development where Vault daemon is unavailable.
    Faithfully replicates Vault Transit context binding and versioning.
    """

    def __init__(self):
        # Maps key_name -> list of versions: [(version_num, 32-byte-aes-key), ...]
        self._keys: dict[str, list[bytes]] = {}

    def ensure_key(self, key_name: str, key_type: str = "aes256-gcm96") -> bool:
        if key_name not in self._keys:
            self._keys[key_name] = [secrets.token_bytes(32)]
        return True

    def wrap_dek(self, key_name: str, plaintext_dek: bytes, context: Optional[bytes] = None) -> tuple[str, int]:
        self.ensure_key(key_name)
        versions = self._keys[key_name]
        latest_ver = len(versions)
        aes_key = versions[-1]
        
        nonce = secrets.token_bytes(12)
        aad = context if context else b""
        cipher = AESGCM(aes_key)
        ct = cipher.encrypt(nonce, plaintext_dek, aad)
        
        # Format similar to Vault: vault:v<version>:<nonce_b64>.<ct_b64>
        encoded = f"{base64.b64encode(nonce).decode('ascii')}.{base64.b64encode(ct).decode('ascii')}"
        wrapped_str = f"vault:v{latest_ver}:{encoded}"
        return wrapped_str, latest_ver

    def unwrap_dek(self, key_name: str, wrapped_dek: str, context: Optional[bytes] = None) -> bytes:
        if key_name not in self._keys:
            raise KmsKeyNotFoundError(f"Key '{key_name}' not found in mock KMS")
        
        if not wrapped_dek.startswith("vault:v"):
            raise KmsDecryptionFailedError("Malformed mock vault ciphertext format")
        
        try:
            parts = wrapped_dek.split(":")
            version_str = parts[1]
            ver_num = int(version_str[1:])
            encoded = parts[2]
            nonce_b64, ct_b64 = encoded.split(".")
            nonce = base64.b64decode(nonce_b64)
            ct = base64.b64decode(ct_b64)
        except Exception as ex:
            raise KmsDecryptionFailedError(f"Cannot parse mock ciphertext: {ex}") from ex

        versions = self._keys[key_name]
        if ver_num < 1 or ver_num > len(versions):
            raise KmsDecryptionFailedError(f"Version {ver_num} not found for key '{key_name}'")
        
        aes_key = versions[ver_num - 1]
        aad = context if context else b""
        cipher = AESGCM(aes_key)
        try:
            plaintext = cipher.decrypt(nonce, ct, aad)
            return plaintext
        except Exception as ex:
            raise KmsContextMismatchError(f"Mock KMS decryption failed (context mismatch or corrupted tag): {ex}") from ex

    def rotate_key(self, key_name: str) -> int:
        self.ensure_key(key_name)
        new_key = secrets.token_bytes(32)
        self._keys[key_name].append(new_key)
        return len(self._keys[key_name])

    def rewrap_dek(self, key_name: str, wrapped_dek: str, context: Optional[bytes] = None) -> tuple[str, int]:
        # Decrypt with old version, encrypt with latest
        plaintext = self.unwrap_dek(key_name, wrapped_dek, context)
        return self.wrap_dek(key_name, plaintext, context)
