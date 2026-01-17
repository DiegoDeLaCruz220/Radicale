"""
Supabase Storage Plugin for Radicale
Reads contacts from Supabase contacts table and serves via CardDAV
"""

import os
import json
from typing import Iterable, Optional
from radicale.storage import BaseCollection, BaseStorage
from radicale import pathutils, types
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

class SupabaseCollection(BaseCollection):
    """Collection backed by Supabase contacts table"""
    
    def __init__(self, storage, path, connection):
        super().__init__(storage, path)
        self.connection = connection
        self._items = {}
        self._load_contacts()
    
    def _load_contacts(self):
        """Load contacts from Supabase"""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT id, uid, display_name, first_name, last_name, 
                       email, email_work, email_home,
                       phone, phone_work, phone_mobile, phone_home,
                       company, job_title, department,
                       addresses, website, notes, birthday, anniversary,
                       updated_at, etag
                FROM contacts
                ORDER BY display_name
            """)
            
            for row in cursor.fetchall():
                vcard = self._generate_vcard(row)
                self._items[row['uid']] = {
                    'uid': row['uid'],
                    'etag': row['etag'] or str(hash(vcard)),
                    'text': vcard,
                    'last-modified': row['updated_at'].isoformat()
                }
    
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
        if contact['birthday']:
            lines.append(f'BDAY:{contact["birthday"].strftime("%Y%m%d")}')
        
        # Revision timestamp
        if contact['updated_at']:
            rev = contact['updated_at'].strftime('%Y%m%dT%H%M%SZ')
            lines.append(f'REV:{rev}')
        
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
    
    def upload(self, href, item):
        """Upload not supported (read-only from Supabase)"""
        raise PermissionError("Contacts are synced from Supabase and cannot be modified via CardDAV")
    
    def delete(self, href):
        """Delete not supported (read-only from Supabase)"""
        raise PermissionError("Contacts are synced from Supabase and cannot be deleted via CardDAV")


class SupabaseStorage(BaseStorage):
    """Storage plugin that reads from Supabase"""
    
    def __init__(self, configuration):
        super().__init__(configuration)
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Test connection
        self.connection = psycopg2.connect(self.database_url)
    
    def discover(self, path: str, depth: str = "0"):
        """Discover collections"""
        if path == "/":
            # Return the main contacts collection
            yield types.CollectionOrItem(
                path="/contacts.vcf/",
                etag="collection",
                item=None,
                collection=SupabaseCollection(self, "/contacts.vcf/", self.connection)
            )
        elif path == "/contacts.vcf/":
            # Return all contacts
            collection = SupabaseCollection(self, path, self.connection)
            for item in collection.get_all():
                yield types.CollectionOrItem(
                    path=f"/contacts.vcf/{item['uid']}.vcf",
                    etag=item['etag'],
                    item=item,
                    collection=None
                )
    
    def move(self, item, to_collection, to_href):
        """Move not supported"""
        raise PermissionError("Moving contacts not supported")
    
    def create_collection(self, href, props=None):
        """Creating collections not supported"""
        raise PermissionError("Creating collections not supported")
