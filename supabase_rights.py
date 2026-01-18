"""
Custom rights plugin for Radicale that allows all authenticated users.
Security is enforced by Supabase RLS policies.
"""
from radicale import rights


class Rights(rights.BaseRights):
    """Rights class that allows all authenticated users to access everything."""
    
    def authorization(self, user: str, path: str) -> bool:
        """
        Allow access if user is authenticated.
        
        Args:
            user: Username (email) of authenticated user, or empty string for anonymous
            path: Path being accessed
            
        Returns:
            True if user is authenticated (not empty), False otherwise
        """
        # Allow any authenticated user to access any path
        # Security is enforced by Supabase RLS at the data layer
        return bool(user)
