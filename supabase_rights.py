"""
Custom rights plugin for Radicale that allows all authenticated users.
Security is enforced by Supabase RLS policies.
"""
from radicale import rights


class Rights(rights.BaseRights):
    """Rights class that allows all authenticated users to access everything."""
    
    def authorization(self, user: str, path: str) -> str:
        """
        Return access rights for user on path.
        
        Args:
            user: Username (email) of authenticated user, or empty string for anonymous
            path: Path being accessed
            
        Returns:
            "RrWw" for full access if authenticated, "" for no access if anonymous
        """
        # Allow full read/write access to any authenticated user
        # Security is enforced by Supabase RLS at the data layer
        if user:
            return "RrWw"  # Read collections, read items, write collections, write items
        return ""  # No access for anonymous users
