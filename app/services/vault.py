import os
import logging
from cryptography.fernet import Fernet # Ensure cryptography is installed

logger = logging.getLogger(__name__)

class DataVault:
    """Cryptographic service for handling sensitive data."""
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY')
        app_env = os.getenv('APP_ENV', 'development')
        
        if not self.key:
            if app_env == 'production':
                logger.critical("FATAL: ENCRYPTION_KEY not set in production!")
                raise RuntimeError("ENCRYPTION_KEY is mandatory for production safety.")
            self.key = os.getenv('DEV_ENCRYPTION_KEY', Fernet.generate_key().decode())
            logger.warning("Using transient encryption key for development!")
            
        self.cipher = Fernet(self.key.encode())

    def encrypt(self, plaintext: str) -> str:
        if not plaintext: return ''
        try:
            return self.cipher.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return ''

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext: return ''
        try:
            return self.cipher.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ''

vault = DataVault()