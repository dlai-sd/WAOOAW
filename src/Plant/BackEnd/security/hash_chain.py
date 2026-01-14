"""
Hash chain utilities - SHA-256 linking for audit trail integrity
"""

import hashlib
from typing import List, Dict, Any


def calculate_sha256(data: str) -> str:
    """
    Calculate SHA-256 hash of data.
    
    Args:
        data: Data to hash (typically JSON string)
        
    Returns:
        str: Hex-encoded SHA-256 hash
        
    Example:
        >>> hash_val = calculate_sha256(json.dumps(amendment))
    """
    return hashlib.sha256(data.encode()).hexdigest()


def create_hash_link(previous_hash: str, current_data: str) -> str:
    """
    Create hash link combining previous hash + current data.
    
    Args:
        previous_hash: Previous hash in chain (or empty string for first)
        current_data: Current amendment data (JSON string)
        
    Returns:
        str: New hash linking to previous
        
    Example:
        >>> new_hash = create_hash_link(previous_hash, json.dumps(current_amendment))
    """
    # Combine previous hash + current data
    chain_input = f"{previous_hash}{current_data}"
    return calculate_sha256(chain_input)


def validate_chain(hashes: List[str], data_list: List[str]) -> bool:
    """
    Validate hash chain integrity (detect tampering).
    
    Args:
        hashes: List of hashes in chain
        data_list: List of original amendment data (JSON strings)
        
    Returns:
        bool: True if chain is intact, False if tampering detected
        
    Example:
        >>> if validate_chain(entity.hash_chain_sha256, amendments):
        ...     print("Chain integrity verified")
    """
    
    if len(hashes) != len(data_list):
        return False  # Length mismatch indicates tampering
    
    previous_hash = ""
    for i, (stored_hash, data) in enumerate(zip(hashes, data_list)):
        computed_hash = create_hash_link(previous_hash, data)
        if computed_hash != stored_hash:
            return False  # Hash mismatch at index i indicates tampering
        previous_hash = stored_hash
    
    return True
