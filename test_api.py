#!/usr/bin/env python3
import requests
import time
import json

API_URL = "http://localhost:8000"

def test_health():
    """Test if API is running"""
    try:
        response = requests.get(f"{API_URL}/health")
        print("✅ Health check:", response.json())
        return True
    except Exception as e:
        print("❌ API is not running:", str(e))
        return False

def test_sync_query():
    """Test synchronous query endpoint"""
    print("\n🔍 Testing synchronous query...")
    try:
        start = time.time()
        response = requests.post(
            f"{API_URL}/query",
            json={"query": "What beers cost less than £6?"},
            timeout=300  # 5 minute timeout
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query completed in {elapsed:.2f} seconds")
            print(f"Response preview: {result['response'][:200]}...")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(response.text)
    except requests.exceptions.Timeout:
        print("❌ Query timed out after 5 minutes!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_async_query():
    """Test asynchronous query endpoint"""
    print("\n🔍 Testing asynchronous query...")
    try:
        # Submit job
        response = requests.post(
            f"{API_URL}/query/async",
            json={"query": "What pizzas are under £12?"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to submit job: {response.status_code}")
            return
            
        job_id = response.json()["job_id"]
        print(f"📋 Job ID: {job_id}")
        
        # Poll for results
        start = time.time()
        while True:
            status_response = requests.get(f"{API_URL}/jobs/{job_id}")
            job_status = status_response.json()
            
            elapsed = time.time() - start
            print(f"\r⏳ Status: {job_status['status']} ({elapsed:.1f}s)", end="", flush=True)
            
            if job_status['status'] == 'completed':
                print(f"\n✅ Query completed in {elapsed:.2f} seconds")
                print(f"Response preview: {job_status['result']['response'][:200]}...")
                break
            elif job_status['status'] == 'failed':
                print(f"\n❌ Query failed: {job_status.get('error', 'Unknown error')}")
                break
            
            if elapsed > 300:  # 5 minute timeout
                print("\n❌ Query timed out after 5 minutes!")
                break
                
            time.sleep(1)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🧪 Testing CAG API...")
    
    if test_health():
        test_sync_query()
        test_async_query()
    else:
        print("\nPlease ensure the API is running with: ./run_api.sh")