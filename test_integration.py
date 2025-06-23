#!/usr/bin/env python3
"""
Test script to verify the Voice AI integration is working
"""
import requests
import base64
import json

def test_integration():
    base_url = "http://localhost:5001"
    
    # Test credentials
    credentials = base64.b64encode(b"admin:password").decode('ascii')
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    print("🧪 Testing Voice AI Integration...")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Dashboard metrics (with auth)
    print("\n2. Testing dashboard metrics...")
    try:
        response = requests.get(f"{base_url}/api/dashboard/metrics", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard metrics passed")
            data = response.json()
            print(f"   Metrics: {data}")
        else:
            print(f"❌ Dashboard metrics failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Dashboard metrics error: {e}")
    
    # Test 3: Frontend serving
    print("\n3. Testing frontend serving...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200 and "html" in response.headers.get('content-type', ''):
            print("✅ Frontend serving passed")
            print(f"   Content length: {len(response.text)} bytes")
        else:
            print(f"❌ Frontend serving failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend serving error: {e}")
    
    # Test 4: System status
    print("\n4. Testing system status...")
    try:
        response = requests.get(f"{base_url}/api/dashboard/system-status", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ System status passed")
            data = response.json()
            print(f"   Status: {data}")
        else:
            print(f"❌ System status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ System status error: {e}")
    
    print("\n🎯 Integration Test Complete!")
    print("\nIf all tests passed, you can:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Login with: admin / password")
    print("3. Explore your Voice AI dashboard!")

if __name__ == "__main__":
    test_integration()