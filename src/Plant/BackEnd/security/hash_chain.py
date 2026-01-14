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


def validate_chain(data_list: List[Any], hashes: List[str]) -> Dict[str, Any]:
    """
    Validate hash chain integrity (detect tampering).
    
    Args:
        data_list: List of original amendment data (dicts)
        hashes: List of hashes in chain
        
    Returns:
        Dict with:
            - intact: bool (True if chain is valid)
            - broken_at_index: Optional[int] (index where tampering detected, None if intact)
        
    Example:
        >>> result = validate_chain(amendments, entity.hash_chain_sha256)
        >>> if result["intact"]:
        ...     print("Chain integrity verified")
    """
    
    if len(hashes) != len(data_list):
        return {"intact": False, "broken_at_index": 0}  # Length mismatch
    
    for i in range(len(hashes)):
        # Reconstruct hash for this position
        if i == 0:
            # First hash: just hash the data
            expected_hash = calculate_sha256(str(data_list[i]))
        else:
            # Subsequent hashes: link to previous
            expected_hash = create_hash_link(hashes[i-1], str(data_list[i]))
        
        if expected_hash != hashes[i]:
            return {"intact": False, "broken_at_index": i}
    
    return {"intact": True, "broken_at_index": None}
