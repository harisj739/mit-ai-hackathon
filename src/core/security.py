"""
Security management for Stressor.
"""

import os
import hashlib
import hmac
import base64
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import logging
from .config import settings
from .logger import get_logger, log_security_event

logger = get_logger(__name__)


class SecurityManager:
    """Manages security aspects of the Stressor framework."""
    
    def __init__(self):
        """Initialize the security manager."""
        self.encryption_key = settings.encryption_key.encode()
        self.secret_key = settings.secret_key.encode()
        self.fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(self.encryption_key).digest()))
        
        # Rate limiting storage
        self.rate_limits: Dict[str, List[float]] = {}
        
        # API key cache (encrypted in memory)
        self._api_keys: Dict[str, bytes] = {}
        
        logger.info("Security manager initialized")
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using PBKDF2.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return f"{base64.urlsafe_b64encode(salt).decode()}:{key.decode()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            salt_b64, key_b64 = hashed_password.split(':')
            salt = base64.urlsafe_b64decode(salt_b64.encode())
            key = base64.urlsafe_b64decode(key_b64.encode())
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            kdf.verify(password.encode(), key)
            return True
        except Exception:
            return False
    
    def generate_api_key(self, user_id: str, permissions: List[str] = None) -> str:
        """
        Generate a secure API key for a user.
        
        Args:
            user_id: User identifier
            permissions: List of permissions
            
        Returns:
            Generated API key
        """
        if permissions is None:
            permissions = ['read', 'write']
        
        # Generate random key
        key_data = os.urandom(32)
        key_b64 = base64.urlsafe_b64encode(key_data).decode()
        
        # Create key metadata
        metadata = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat()
        }
        
        # Store encrypted key with metadata
        key_info = {
            'key': key_b64,
            'metadata': metadata
        }
        
        self._api_keys[key_b64] = self.encrypt_data(json.dumps(key_info)).encode()
        
        # Log key generation
        log_security_event(
            'api_key_generated',
            {'user_id': user_id, 'permissions': permissions},
            user_id
        )
        
        return key_b64
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return user info.
        
        Args:
            api_key: API key to validate
            
        Returns:
            User information if valid, None otherwise
        """
        try:
            if api_key not in self._api_keys:
                return None
            
            encrypted_data = self._api_keys[api_key].decode()
            key_info = json.loads(self.decrypt_data(encrypted_data))
            
            # Check expiration
            expires_at = datetime.fromisoformat(key_info['metadata']['expires_at'])
            if datetime.utcnow() > expires_at:
                log_security_event('api_key_expired', {'api_key': api_key[:8] + '...'})
                return None
            
            return key_info['metadata']
        
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    def check_rate_limit(self, identifier: str, limit_per_minute: int = None, limit_per_hour: int = None) -> bool:
        """
        Check if a request is within rate limits.
        
        Args:
            identifier: Request identifier (IP, user_id, etc.)
            limit_per_minute: Requests per minute limit
            limit_per_hour: Requests per hour limit
            
        Returns:
            True if within limits, False otherwise
        """
        if limit_per_minute is None:
            limit_per_minute = settings.max_requests_per_minute
        if limit_per_hour is None:
            limit_per_hour = settings.max_requests_per_hour
        
        now = time.time()
        
        # Initialize rate limit tracking for this identifier
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # Clean old entries
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self.rate_limits[identifier] = [
            timestamp for timestamp in self.rate_limits[identifier]
            if timestamp > hour_ago
        ]
        
        # Check minute limit
        recent_requests = [
            timestamp for timestamp in self.rate_limits[identifier]
            if timestamp > minute_ago
        ]
        
        if len(recent_requests) >= limit_per_minute:
            log_security_event('rate_limit_exceeded', {
                'identifier': identifier,
                'limit': limit_per_minute,
                'period': 'minute'
            })
            return False
        
        # Check hour limit
        if len(self.rate_limits[identifier]) >= limit_per_hour:
            log_security_event('rate_limit_exceeded', {
                'identifier': identifier,
                'limit': limit_per_hour,
                'period': 'hour'
            })
            return False
        
        # Add current request
        self.rate_limits[identifier].append(now)
        return True
    
    def sanitize_input(self, data: Any) -> Any:
        """
        Sanitize input data to prevent injection attacks.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, str):
            # Remove potentially dangerous characters and patterns
            sanitized = data.strip()
            # Add more sanitization as needed
            return sanitized
        elif isinstance(data, dict):
            return {k: self.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data
    
    def generate_secure_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """
        Generate a secure JWT-like token.
        
        Args:
            payload: Token payload
            expires_in: Token expiration time in seconds
            
        Returns:
            Generated token
        """
        header = {
            'alg': 'HS256',
            'typ': 'JWT'
        }
        
        payload['iat'] = int(time.time())
        payload['exp'] = int(time.time()) + expires_in
        
        # Encode header and payload
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
        
        # Create signature
        message = f"{header_b64}.{payload_b64}".encode()
        signature = hmac.new(self.secret_key, message, hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a secure token.
        
        Args:
            token: Token to verify
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}".encode()
            expected_signature = hmac.new(self.secret_key, message, hashlib.sha256).digest()
            expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).rstrip(b'=').decode()
            
            if not hmac.compare_digest(signature_b64, expected_signature_b64):
                return None
            
            # Decode payload
            payload_bytes = base64.urlsafe_b64decode(payload_b64 + '==')
            payload = json.loads(payload_bytes.decode())
            
            # Check expiration
            if 'exp' in payload and payload['exp'] < time.time():
                return None
            
            return payload
        
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None 