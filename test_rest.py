import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
print(f"URL: {url}")
try:
    res = requests.get(f"{url}/rest/v1/documents?select=id&limit=1", headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=5)
    print("documents status code:", res.status_code)
    print("documents response:", res.text)
    
    res2 = requests.get(f"{url}/rest/v1/chunks?select=id&limit=1", headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=5)
    print("chunks status code:", res2.status_code)
    print("chunks response:", res2.text)
except Exception as e:
    print("Request failed:", e)
