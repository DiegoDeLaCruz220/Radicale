import requests

# Replace these with your actual values
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key-here"

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json'
}

try:
    print("Testing Supabase API connection...")
    
    # Test query
    url = f"{SUPABASE_URL}/rest/v1/contacts"
    params = {'select': 'count', 'limit': 1}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    contacts = response.json()
    count = len(contacts) if isinstance(contacts, list) else 0
    
    print(f"✅ Connection successful!")
    print(f"✅ Found {count}+ contacts in database")
    print(f"✅ API key is valid!")
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("❌ INVALID API KEY - Check your SUPABASE_SERVICE_ROLE_KEY")
    elif e.response.status_code == 404:
        print("❌ WRONG URL - Check your SUPABASE_URL")
    else:
        print(f"❌ HTTP Error {e.response.status_code}: {e.response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
