"""
Supabase Authentication Plugin for Radicale
Authenticates users against Supabase Auth API and stores JWT for storage plugin
"""

import os
import sys
import requests
import threading
from radicale.auth import BaseAuth

# Thread-local storage for JWT tokens
_jwt_storage = threading.local()


def get_user_jwt(username: str):
    """Get JWT token for a user from thread-local storage"""
    if not hasattr(_jwt_storage, 'tokens'):
        return None
    return _jwt_storage.tokens.get(username)


def set_user_jwt(username: str, jwt: str):
    """Store JWT token for a user in thread-local storage"""
    if not hasattr(_jwt_storage, 'tokens'):
        _jwt_storage.tokens = {}
    _jwt_storage.tokens[username] = jwt


class SupabaseAuth(BaseAuth):
    """Authentication using Supabase Auth API"""
    
    def __init__(self, configuration):
        super().__init__(configuration)
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY required")
    
    def login(self, login: str, password: str) -> str:
        """
        Authenticate user with Supabase Auth
        Returns username if successful, empty string if failed
        """
        try:
            # Authenticate with Supabase Auth
            url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
            headers = {
                'apikey': self.supabase_key,
                'Content-Type': 'application/json'
            }
            data = {
                'email': login,
                'password': password
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                # Authentication successful - store JWT
                jwt_data = response.json()
                access_token = jwt_data.get('access_token')
                if access_token:
                    print(f"[DEBUG AUTH] Storing JWT for {login}: {access_token[:50]}...", file=sys.stderr, flush=True)
                    set_user_jwt(login, access_token)
                return login
            else:
                # Auth failed
                return ""
                
        except Exception as e:
            print(f"Auth error: {e}")
            return ""

# Radicale expects a class named 'Auth'
Auth = SupabaseAuth
