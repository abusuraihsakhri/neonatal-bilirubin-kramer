"""
Pytest configuration for neonatal-bilirubin-kramer.
Sets required environment variables for testing.
"""
import os

# Set a deterministic test key for HMAC audit trail
# This is only for unit tests - production must use a strong random key
os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-key-for-unit-tests-only-32chars")
