"""
Supabase Authentication Plugin for Radicale
Authenticates users against Supabase Auth API
"""

import os
import requests
from radicale.auth import BaseAuth

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
                # Authentication successful
                return login
            else:
                # Auth failed
                return ""
                
        except Exception as e:
            print(f"Auth error: {e}")
            return ""

# Radicale expects a class named 'Auth'
Auth = SupabaseAuth
