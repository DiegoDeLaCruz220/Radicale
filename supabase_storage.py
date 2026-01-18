"""
Supabase Storage Plugin for Radicale
Reads contacts from Supabase contacts table via REST API and serves via CardDAV
"""

import os
import sys
import json
import requests
from typing import Iterable, Optional
from contextlib import contextmanager
from radicale.storage import BaseCollection, BaseStorage
from radicale import pathutils, types
from datetime import datetime

def debug_log(msg):
    """Log debug messages to stderr with flush"""
    print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)

class SupabaseCollection(BaseCollection):
    """Collection backed by Supabase contacts table via REST API"""
    
    def __init__(self, storage, path, supabase_url, supabase_key):
        super().__init__()
        self._storage = storage
        self._path = path.strip("/")
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        self._items = {}
        self._tag = "VADDRESSBOOK"
        self._load_contacts()
    
    @property
    def path(self):
        """Return the collection path"""
        return self._path
    
    @property
    def tag(self):
        """Return the collection tag"""
        return self._tag
    
    def _load_contacts(self):
        """Load contacts from Supabase via REST API"""
        try:
            # Query contacts table via Supabase REST API
            url = f"{self.supabase_url}/rest/v1/contacts"
            params = {
                'select': '*',
                'order': 'display_name.asc'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            contacts = response.json()
            
            for contact in contacts:
                vcard = self._generate_vcard(contact)
                self._items[contact['uid']] = {
                    'uid': contact['uid'],
                    'etag': contact.get('etag') or str(hash(vcard)),
                    'text': vcard,
                    'last-modified': contact['updated_at']
                }
        except Exception as e:
            print(f"Error loading contacts from Supabase: {e}")
            raise
    
    def _generate_vcard(self, contact):
        """Generate vCard 3.0 format from contact data"""
        lines = [
            'BEGIN:VCARD',
            'VERSION:3.0',
            f'UID:{contact["uid"]}'
        ]
        
        # Display name (required)
        lines.append(f'FN:{contact["display_name"]}')
        
        # Structured name
        if contact['first_name'] or contact['last_name']:
            last = contact['last_name'] or ''
            first = contact['first_name'] or ''
            lines.append(f'N:{last};{first};;;')
        
        # Email addresses
        if contact['email']:
            lines.append(f'EMAIL;TYPE=INTERNET:{contact["email"]}')
        if contact['email_work']:
            lines.append(f'EMAIL;TYPE=WORK:{contact["email_work"]}')
        if contact['email_home']:
            lines.append(f'EMAIL;TYPE=HOME:{contact["email_home"]}')
        
        # Phone numbers
        if contact['phone']:
            lines.append(f'TEL;TYPE=VOICE:{contact["phone"]}')
        if contact['phone_work']:
            lines.append(f'TEL;TYPE=WORK,VOICE:{contact["phone_work"]}')
        if contact['phone_mobile']:
            lines.append(f'TEL;TYPE=CELL:{contact["phone_mobile"]}')
        if contact['phone_home']:
            lines.append(f'TEL;TYPE=HOME,VOICE:{contact["phone_home"]}')
        
        # Organization
        if contact['company']:
            lines.append(f'ORG:{contact["company"]}')
        if contact['job_title']:
            lines.append(f'TITLE:{contact["job_title"]}')
        
        # Address (if stored in JSONB)
        if contact['addresses']:
            try:
                addresses = json.loads(contact['addresses']) if isinstance(contact['addresses'], str) else contact['addresses']
                for addr in addresses:
                    if addr.get('street') or addr.get('city'):
                        adr_line = f'ADR;TYPE={addr.get("type", "WORK").upper()}:;;'
                        adr_line += f'{addr.get("street", "")};{addr.get("city", "")};'
                        adr_line += f'{addr.get("state", "")};{addr.get("zip", "")};{addr.get("country", "")}'
                        lines.append(adr_line)
            except:
                pass
        
        # Website
        if contact['website']:
            lines.append(f'URL:{contact["website"]}')
        
        # Notes
        if contact['notes']:
            # Escape special chars in notes
            notes = contact['notes'].replace('\n', '\\n').replace(',', '\\,')
            lines.append(f'NOTE:{notes}')
        
        # Birthday
        if contact.get('birthday'):
            try:
                bday = datetime.fromisoformat(contact['birthday'].replace('Z', '+00:00'))
                lines.append(f'BDAY:{bday.strftime("%Y%m%d")}')
            except:
                pass
        
        # Revision timestamp
        if contact.get('updated_at'):
            try:
                rev = datetime.fromisoformat(contact['updated_at'].replace('Z', '+00:00'))
                lines.append(f'REV:{rev.strftime("%Y%m%dT%H%M%SZ")}')
            except:
                pass
        
        lines.append('END:VCARD')
        return '\r\n'.join(lines) + '\r\n'
    
    def get_multi(self, hrefs: Iterable[str]):
        """Get multiple items"""
        for href in hrefs:
            uid = href.rstrip('.vcf')
            if uid in self._items:
                yield self._items[uid]
    
    def get_all(self):
        """Get all items"""
        return list(self._items.values())
    
    def get_meta(self, key=None):
        """Get collection metadata"""
        if key:
            return {
                "tag": "VADDRESSBOOK",
                "D:displayname": "Contacts"
            }.get(key)
        return {
            "tag": "VADDRESSBOOK",
            "D:displayname": "Contacts"
        }
    
    def set_meta(self, props):
        """Setting metadata not supported"""
        pass
    
    @property
    def last_modified(self):
        """Return last modified time"""
        return datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    def upload(self, href, item):
        """Upload not supported (read-only from Supabase)"""
        raise PermissionError("Contacts are synced from Supabase and cannot be modified via CardDAV")
    
    def delete(self, href):
        """Delete not supported (read-only from Supabase)"""
        raise PermissionError("Contacts are synced from Supabase and cannot be deleted via CardDAV")


class SupabaseStorage(BaseStorage):
    """Storage plugin that reads from Supabase via REST API"""
    
    def __init__(self, configuration):
        debug_log("SupabaseStorage.__init__ called")
        super().__init__(configuration)
        self.supabase_url = os.getenv('SUPABASE_URL')
        # Use service role key to bypass RLS - authentication is handled by Radicale
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        debug_log(f"SUPABASE_URL={self.supabase_url}")
        debug_log(f"Using key type: {'SERVICE_ROLE' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'ANON'}")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) environment variables are required")
        
        debug_log("SupabaseStorage initialized successfully")
    
    @staticmethod
    @contextmanager
    def acquire_lock(mode, user=""):
        """Lock not needed for read-only storage"""
        debug_log(f"acquire_lock called with mode='{mode}', user='{user}'")
        yield  # No actual locking for read-only
    
    def _get_collection(self, path):
        """Get a single collection by path"""
        debug_log(f"_get_collection called with path='{path}'")
        if path == "/" or path == "/contacts.vcf/":
            return SupabaseCollection(self, "/contacts.vcf/", self.supabase_url, self.supabase_key)
        return None
    
    def discover(self, path: str, depth: str = "0"):
        """Discover collections"""
        debug_log(f"discover called with path='{path}', depth='{depth}'")
        try:
            # Strip leading/trailing slashes for comparison
            clean_path = path.strip("/")
            
            if path == "/" or not clean_path:
                # Root - return contacts collection
                debug_log("Returning root collection")
                collection = SupabaseCollection(self, "/contacts.vcf/", self.supabase_url, self.supabase_key)
                yield collection
            elif "/" not in clean_path:
                # User principal (e.g., /diego@adlcrm.com/)
                debug_log(f"Returning user principal: {clean_path}")
                # Return the contacts collection under this principal
                collection = SupabaseCollection(self, f"/{clean_path}/contacts.vcf/", self.supabase_url, self.supabase_key)
                yield collection
            elif path == "/contacts.vcf/" or clean_path.endswith("/contacts.vcf"):
                # Return the collection itself, not items
                debug_log("Returning contacts collection")
                collection = SupabaseCollection(self, path, self.supabase_url, self.supabase_key)
                yield collection
                # If depth > 0, also return items
                if depth != "0":
                    debug_log("Returning contacts collection items")
                    for item in collection.get_all():
                        yield item
        except Exception as e:
            debug_log(f"Exception in discover: {e}")
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise
    
    def verify(self):
        """Verify storage - always returns True for read-only storage"""
        return True
    
    def move(self, item, to_collection, to_href):
        """Move not supported"""
        raise PermissionError("Moving contacts not supported")
    
    def create_collection(self, href, items=None, props=None):
        """Creating collections not supported, but return success for principals"""
        debug_log(f"create_collection called with href='{href}'")
        # If it's a principal path (user/), just return empty - principals are virtual
        clean_href = href.strip("/")
        if "/" not in clean_href:
            debug_log(f"Allowing principal creation: {href}")
            # Return empty collection for principal
            return (SupabaseCollection(self, f"/{clean_href}/contacts.vcf/", self.supabase_url, self.supabase_key), {}, [])
        raise PermissionError("Creating collections not supported")

# Radicale expects a class named 'Storage'
Storage = SupabaseStorage
