from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC # Ensure cryptography is installed
import base64
import os
import hashlib

class DataEncryptionService:
    """
    Handles encryption of personal data before it leaves the safe environment.
    """
    
    def __init__(self):
        self.master_key = os.getenv("MASTER_ENCRYPTION_KEY", "dev_master_key")
    
    def get_user_key(self, user_id: int, password: str) -> bytes:
        """
        Derive user-specific encryption key from master key and user password.
        """
        salt = hashlib.sha256(f"{user_id}:{self.master_key}".encode()).digest()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_personal_data(self, data: str, user_id: int, password: str) -> str:
        """
        Encrypt personal data before it leaves the safe environment.
        """
        if not data: return ""
        key = self.get_user_key(user_id, password)
        cipher = Fernet(key)
        encrypted = cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt_personal_data(self, encrypted_data: str, user_id: int, password: str) -> str:
        """
        Decrypt personal data when it returns to the safe environment.
        """
        if not encrypted_data: return ""
        key = self.get_user_key(user_id, password)
        cipher = Fernet(key)
        try:
            return cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return "[Decryption Failed]"