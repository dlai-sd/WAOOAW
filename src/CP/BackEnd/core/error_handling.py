"""
Standardized error handling utilities
"""

from fastapi import HTTPException, status

def raise_http_exception(detail: str, code: int = status.HTTP_400_BAD_REQUEST):
    """
    Raise an HTTP exception with standardized format.
    
    Args:
        detail: Error message
        code: HTTP status code
        
    Raises:
        HTTPException
    """
    raise HTTPException(status_code=code, detail=detail)
