import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from auth import generate_api_key, hash_api_key, verify_api_key, extract_key_from_header, extract_key_prefix

def test_generate_api_key():
    key = generate_api_key()
    assert key.startswith("ek_")
    assert len(key) == 35  # "ek_" + 32 chars

def test_hash_and_verify():
    key = generate_api_key()
    hashed = hash_api_key(key)
    assert verify_api_key(key, hashed)
    assert not verify_api_key("wrong_key", hashed)

def test_extract_key_from_header():
    assert extract_key_from_header("Bearer ek_abc123") == "ek_abc123"
    assert extract_key_from_header("Basic abc") is None

def test_extract_key_prefix():
    key = generate_api_key()
    prefix = extract_key_prefix(key)
    assert prefix == key[:10]
    assert prefix.startswith("ek_")
    assert len(prefix) == 10
