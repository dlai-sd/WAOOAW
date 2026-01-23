"""
Standardized error handling utilities
"""

from fastapi import HTTPException, status
from typing import Dict

def raise_http_exception(detail: str, code: int = status.HTTP_400_BAD_REQUEST) -> None:
    """
    Raise an HTTP exception with standardized format.
    
    Args:
        detail: Error message
        code: HTTP status code
        
    Raises:
        HTTPException
    """
    raise HTTPException(status_code=code, detail=detail)

def create_problem_details(type: str, title: str, status: int, detail: str) -> Dict[str, str]:
    """
    Create a standardized problem details response.
    
    Args:
        type: URI reference that identifies the problem type
        title: Short, human-readable summary of the problem
        status: HTTP status code
        detail: Specific error message
    
    Returns:
        A dictionary representing the problem details
    """
    return {
        "type": type,
        "title": title,
        "status": str(status),
        "detail": detail
    }
