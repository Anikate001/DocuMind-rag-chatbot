import os
import sys
from database import supabase
from config import GROQ_API_KEY
from groq import Groq
import traceback

def test_supabase():
    print("Testing Supabase connection...")
    sys.stdout.flush()
    try:
        # Check documents table
        docs = supabase.table("documents").select("id").limit(1).execute()
        print("✅ Supabase 'documents' table exists and is accessible. Docs data:", docs.data)
        
        # Check chunks table
        chunks = supabase.table("chunks").select("id").limit(1).execute()
        print("✅ Supabase 'chunks' table exists and is accessible. Chunks data:", chunks.data)
        
    except Exception as e:
        print("❌ Supabase table error:", traceback.format_exc())

def test_groq():
    print("\nTesting Groq connection...")
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
            max_tokens=10
        )
        print("✅ Groq is accessible. Response:", response.choices[0].message.content)
    except Exception as e:
        print("❌ Groq error:", traceback.format_exc())

if __name__ == "__main__":
    test_supabase()
    test_groq()
