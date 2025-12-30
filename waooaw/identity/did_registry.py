"""
DID Registry - In-memory storage and retrieval of DID documents.

In production, this would be backed by a database (PostgreSQL, DynamoDB, etc.)
For now, provides in-memory registry for all Platform CoE agents.
"""

import copy
from typing import Dict, List, Optional
from datetime import datetime, UTC
from waooaw.identity.did_service import DIDDocument


class DIDRegistry:
    """
    Registry for storing and querying DID documents.
    
    Responsibilities:
    - Store DID documents
    - Query by DID
    - List all DIDs
    - Update DID documents
    - Track DID history
    """
    
    def __init__(self):
        """Initialize DID registry."""
        self._documents: Dict[str, DIDDocument] = {}
        self._history: Dict[str, List[DIDDocument]] = {}
        
    def register(self, did_document: DIDDocument) -> None:
        """
        Register DID document in registry.
        
        Args:
            did_document: DID document to register
        """
        did = did_document.id
        
        # Store current version (deep copy to prevent mutations)
        self._documents[did] = copy.deepcopy(did_document)
        
        # Append to history (deep copy)
        if did not in self._history:
            self._history[did] = []
        self._history[did].append(copy.deepcopy(did_document))
        
    def get(self, did: str) -> Optional[DIDDocument]:
        """
        Get DID document by DID.
        
        Args:
            did: DID to lookup
            
        Returns:
            DID document if found, None otherwise
        """
        return self._documents.get(did)
    
    def list_all(self) -> List[DIDDocument]:
        """
        List all registered DID documents.
        
        Returns:
            List of all DID documents
        """
        return list(self._documents.values())
    
    def list_dids(self) -> List[str]:
        """
        List all registered DIDs.
        
        Returns:
            List of DID strings
        """
        return list(self._documents.keys())
    
    def update(self, did_document: DIDDocument) -> None:
        """
        Update existing DID document.
        
        Args:
            did_document: Updated DID document
        """
        did = did_document.id
        
        # Verify DID exists
        if did not in self._documents:
            raise ValueError(f"DID {did} not registered")
        
        # Update timestamp
        did_document.updated = datetime.now(UTC).isoformat()
        
        # Store updated version (deep copy)
        self._documents[did] = copy.deepcopy(did_document)
        self._history[did].append(copy.deepcopy(did_document))
        
    def get_history(self, did: str) -> List[DIDDocument]:
        """
        Get version history of DID document.
        
        Args:
            did: DID to get history for
            
        Returns:
            List of DID document versions (oldest first)
        """
        return self._history.get(did, [])
    
    def delete(self, did: str) -> bool:
        """
        Delete DID document from registry.
        
        Args:
            did: DID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if did in self._documents:
            del self._documents[did]
            # Keep history for audit trail
            return True
        return False
    
    def exists(self, did: str) -> bool:
        """
        Check if DID exists in registry.
        
        Args:
            did: DID to check
            
        Returns:
            True if exists, False otherwise
        """
        return did in self._documents
    
    def count(self) -> int:
        """
        Get count of registered DIDs.
        
        Returns:
            Number of DIDs in registry
        """
        return len(self._documents)
    
    def search_by_controller(self, controller_did: str) -> List[DIDDocument]:
        """
        Search for DID documents by controller.
        
        Args:
            controller_did: Controller DID to search for
            
        Returns:
            List of DID documents with matching controller
        """
        return [
            doc for doc in self._documents.values()
            if doc.controller == controller_did
        ]
    
    def get_statistics(self) -> Dict:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry stats
        """
        docs = self._documents.values()
        
        # Count by controller
        controllers = {}
        for doc in docs:
            controller = doc.controller
            controllers[controller] = controllers.get(controller, 0) + 1
        
        return {
            "total_dids": len(self._documents),
            "total_history_entries": sum(len(h) for h in self._history.values()),
            "by_controller": controllers,
            "dids": list(self._documents.keys())
        }


# Singleton instance
_did_registry = None

def get_did_registry() -> DIDRegistry:
    """Get singleton DID registry instance."""
    global _did_registry
    if _did_registry is None:
        _did_registry = DIDRegistry()
    return _did_registry
