"""
Security management for Stressor.
"""

import os
import hashlib
import hmac
import base64
import time
import secrets
import re
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import logging
from .config import settings
from .logger import get_logger, log_security_event

logger = get_logger(__name__)

# Define valid permission scopes
VALID_PERMISSIONS = {
    'stress_tests:read', 'stress_tests:write', 'stress_tests:delete',
    'results:read', 'results:write', 'results:delete',
    'config:read', 'config:write',
    'users:read', 'users:write', 'users:delete',
    'admin:all'
}

# Key prefix for better identification and security
API_KEY_PREFIX = "sk_stressor_"


class SecurityManager:
    """Manages security aspects of the Stressor framework."""
    
    def __init__(self):
        """Initialize the security manager."""
        self.encryption_key = settings.encryption_key.encode()
        self.secret_key = settings.secret_key.encode()
        self.fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(self.encryption_key).digest()))
        
        # Rate limiting storage
        self.rate_limits: Dict[str, List[float]] = {}
        
        # API key metadata storage (key hashes -> encrypted metadata)
        # Store by hash to avoid plaintext keys in memory
        self._api_key_metadata: Dict[str, bytes] = {}
        
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
            iterations=600000,  # Increased from 100,000 to current OWASP recommendation
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
                iterations=600000,  # Updated to match hash_password
            )
            kdf.verify(password.encode(), key)
            return True
        except Exception:
            return False
    
    def validate_permissions(self, permissions: List[str]) -> List[str]:
        """
        Validate and sanitize permission list.
        
        Args:
            permissions: List of permissions to validate
            
        Returns:
            List of valid permissions
            
        Raises:
            ValueError: If invalid permissions are provided
        """
        if not permissions:
            return ['stress_tests:read']  # More restrictive default
        
        invalid_permissions = set(permissions) - VALID_PERMISSIONS
        if invalid_permissions:
            raise ValueError(f"Invalid permissions: {invalid_permissions}")
        
        return list(set(permissions))  # Remove duplicates
    
    def generate_api_key_with_checksum(self) -> str:
        """
        Generate API key with prefix and checksum for validation.
        
        Returns:
            API key with prefix and checksum
        """
        # Generate 24 bytes of random data
        key_data = secrets.token_bytes(24)
        key_b64 = base64.urlsafe_b64encode(key_data).decode().rstrip('=')
        
        # Create checksum of the key
        checksum = hashlib.sha256(key_data).hexdigest()[:8]
        
        return f"{API_KEY_PREFIX}{key_b64}_{checksum}"
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Create a secure hash of the API key for storage indexing.
        
        Args:
            api_key: API key to hash
            
        Returns:
            Hashed API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_api_key(self, user_id: str, permissions: List[str] = None, 
                        expires_days: int = 90, description: str = None) -> str:
        """
        Generate a secure API key for a user.
        
        Args:
            user_id: User identifier (validated)
            permissions: List of permissions (validated against whitelist)
            expires_days: Number of days until expiration (default: 90, max: 365)
            description: Optional description for the key
            
        Returns:
            Generated API key
            
        Raises:
            ValueError: If invalid parameters are provided
        """
        # Input validation
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            raise ValueError("user_id contains invalid characters")
        
        if expires_days <= 0 or expires_days > 365:
            raise ValueError("expires_days must be between 1 and 365")
        
        # Validate permissions
        validated_permissions = self.validate_permissions(permissions)
        
        # Generate structured API key
        api_key = self.generate_api_key_with_checksum()
        key_hash = self.hash_api_key(api_key)
        
        # Create key metadata
        metadata = {
            'user_id': user_id,
            'permissions': validated_permissions,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=expires_days)).isoformat(),
            'description': description,
            'last_used': None,
            'usage_count': 0,
            'is_active': True
        }
        
        # Store encrypted metadata indexed by key hash
        self._api_key_metadata[key_hash] = self.encrypt_data(json.dumps(metadata)).encode()
        
        # Log key generation with minimal data
        log_security_event(
            'api_key_generated',
            {
                'user_id': user_id, 
                'permissions': validated_permissions,
                'expires_days': expires_days,
                'key_prefix': api_key[:16] + '...'  # Only log prefix for debugging
            },
            user_id
        )
        
        return api_key
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """
        Validate API key format and checksum.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not api_key.startswith(API_KEY_PREFIX):
            return False
        
        try:
            # Extract key and checksum
            key_part = api_key[len(API_KEY_PREFIX):]
            if '_' not in key_part:
                return False
            
            key_b64, checksum = key_part.rsplit('_', 1)
            
            # Validate checksum length
            if len(checksum) != 8:
                return False
            
            # Recreate key data and verify checksum
            key_data = base64.urlsafe_b64decode(key_b64 + '==')
            expected_checksum = hashlib.sha256(key_data).hexdigest()[:8]
            
            return hmac.compare_digest(checksum, expected_checksum)
        except Exception:
            return False
    
    def validate_api_key(self, api_key: str, required_permissions: Set[str] = None) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return user info.
        
        Args:
            api_key: API key to validate
            required_permissions: Set of required permissions for this operation
            
        Returns:
            User information if valid, None otherwise
        """
        try:
            # Basic format validation
            if not self.validate_api_key_format(api_key):
                log_security_event('api_key_invalid_format', {'key_prefix': api_key[:16] + '...'})
                return None
            
            key_hash = self.hash_api_key(api_key)
            
            if key_hash not in self._api_key_metadata:
                log_security_event('api_key_not_found', {'key_prefix': api_key[:16] + '...'})
                return None
            
            encrypted_data = self._api_key_metadata[key_hash].decode()
            metadata = json.loads(self.decrypt_data(encrypted_data))
            
            # Check if key is active
            if not metadata.get('is_active', True):
                log_security_event('api_key_inactive', {'user_id': metadata['user_id']})
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(metadata['expires_at'])
            if datetime.utcnow() > expires_at:
                log_security_event('api_key_expired', {
                    'user_id': metadata['user_id'],
                    'expired_at': metadata['expires_at']
                })
                return None
            
            # Check permissions if required
            if required_permissions:
                user_permissions = set(metadata['permissions'])
                if 'admin:all' not in user_permissions and not required_permissions.issubset(user_permissions):
                    log_security_event('api_key_insufficient_permissions', {
                        'user_id': metadata['user_id'],
                        'required': list(required_permissions),
                        'available': metadata['permissions']
                    })
                    return None
            
            # Update usage statistics
            metadata['last_used'] = datetime.utcnow().isoformat()
            metadata['usage_count'] = metadata.get('usage_count', 0) + 1
            
            # Save updated metadata
            self._api_key_metadata[key_hash] = self.encrypt_data(json.dumps(metadata)).encode()
            
            return metadata
        
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    def revoke_api_key(self, api_key: str, user_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            api_key: API key to revoke
            user_id: User ID (for authorization check)
            
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            key_hash = self.hash_api_key(api_key)
            
            if key_hash not in self._api_key_metadata:
                return False
            
            encrypted_data = self._api_key_metadata[key_hash].decode()
            metadata = json.loads(self.decrypt_data(encrypted_data))
            
            # Verify user owns this key
            if metadata['user_id'] != user_id:
                log_security_event('api_key_revoke_unauthorized', {
                    'requesting_user': user_id,
                    'key_owner': metadata['user_id']
                })
                return False
            
            # Mark as inactive instead of deleting for audit trail
            metadata['is_active'] = False
            metadata['revoked_at'] = datetime.utcnow().isoformat()
            
            self._api_key_metadata[key_hash] = self.encrypt_data(json.dumps(metadata)).encode()
            
            log_security_event('api_key_revoked', {'user_id': user_id})
            return True
        
        except Exception as e:
            logger.error(f"API key revocation failed: {e}")
            return False
    
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
            # Remove null bytes and control characters except common whitespace
            sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)
            # Limit length to prevent DoS
            if len(sanitized) > 10000:
                sanitized = sanitized[:10000]
            return sanitized
        elif isinstance(data, dict):
            return {self.sanitize_input(k): self.sanitize_input(v) for k, v in data.items()}
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
        
        payload = payload.copy()  # Don't modify original
        payload['iat'] = int(time.time())
        payload['exp'] = int(time.time()) + expires_in
        payload['jti'] = secrets.token_hex(16)  # Add unique token ID
        
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
    
    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired API keys from memory.
        
        Returns:
            Number of keys cleaned up
        """
        cleaned_count = 0
        current_time = datetime.utcnow()
        keys_to_remove = []
        
        for key_hash, encrypted_data in self._api_key_metadata.items():
            try:
                metadata = json.loads(self.decrypt_data(encrypted_data.decode()))
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                
                # Remove keys expired more than 30 days ago
                if current_time > expires_at + timedelta(days=30):
                    keys_to_remove.append(key_hash)
                    cleaned_count += 1
            except Exception:
                # Remove corrupted entries
                keys_to_remove.append(key_hash)
                cleaned_count += 1
        
        for key_hash in keys_to_remove:
            del self._api_key_metadata[key_hash]
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired API keys")
        
        return cleaned_count