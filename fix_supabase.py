import os
from database import supabase
import traceback

print("--- Checking and creating Buckets ---")
try:
    buckets = supabase.storage.list_buckets()
    bucket_ids = [b.id for b in buckets]
    print("Existing buckets:", bucket_ids)
    if "documents" not in bucket_ids:
        print("Bucket 'documents' not found. Attempting to create...")
        res = supabase.storage.create_bucket("documents", public=True)
        print("Bucket created:", res)
    else:
        print("Bucket 'documents' already exists.")

except Exception as e:
    print("Bucket error:")
    traceback.print_exc()

print("\n--- Checking match_chunks RPC ---")
test_emb = [0.0] * 384
try:
    res = supabase.rpc("match_chunks", {
        "query_embedding": test_emb,
        "match_count": 1,
        "match_threshold": 0.0
    }).execute()
    print("RPC match_chunks exists and returned:", res.data)
except Exception as e:
    print("RPC error:")
    traceback.print_exc()
