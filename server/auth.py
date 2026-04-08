import bcrypt
import secrets
import base64
from config import API_KEY_LENGTH, API_KEY_PREFIX, KEY_PREFIX_LEN

def generate_api_key() -> str:
    """Generate a new API key: ek_ + 32 char Base64 URL-safe."""
    random_bytes = secrets.token_bytes(24)  # 24 bytes = 32 Base64 chars
    key_body = base64.urlsafe_b64encode(random_bytes).decode()[:API_KEY_LENGTH]
    return f"{API_KEY_PREFIX}{key_body}"

def hash_api_key(api_key: str) -> str:
    """Hash API key using bcrypt."""
    return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify API key against hash."""
    return bcrypt.checkpw(api_key.encode(), api_key_hash.encode())

def extract_key_from_header(authorization: str) -> str:
    """Extract API key from 'Bearer <key>' header."""
    if not authorization.startswith("Bearer "):
        return None
    return authorization[7:]

def extract_key_prefix(api_key: str) -> str:
    """Extract prefix from API key for fast DB lookup."""
    return api_key[:KEY_PREFIX_LEN]
