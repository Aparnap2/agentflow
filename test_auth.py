#!/usr/bin/env python3
"""
Test script to verify auth system works
"""
import asyncio
import httpx

async def test_auth_system():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing AgentFlow Authentication System")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/api/health")
            if response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to backend: {e}")
            return
        
        # Test sign up
        print("\n2. Testing user signup...")
        signup_data = {
            "email": "test@example.com",
            "password": "test123",
            "name": "Test User"
        }
        
        try:
            response = await client.post(f"{base_url}/api/auth/signup", json=signup_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Signup successful")
                    token = data.get("access_token")
                    user = data.get("user")
                    print(f"   User: {user.get('name')} ({user.get('email')})")
                else:
                    print(f"❌ Signup failed: {data.get('error')}")
                    return
            else:
                print(f"❌ Signup request failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Signup error: {e}")
            return
        
        # Test sign in
        print("\n3. Testing user signin...")
        signin_data = {
            "email": "test@example.com",
            "password": "test123"
        }
        
        try:
            response = await client.post(f"{base_url}/api/auth/signin", json=signin_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Signin successful")
                    token = data.get("access_token")
                    user = data.get("user")
                    print(f"   Token: {token[:20]}...")
                else:
                    print(f"❌ Signin failed: {data.get('error')}")
                    return
            else:
                print(f"❌ Signin request failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Signin error: {e}")
            return
        
        # Test authenticated endpoint
        print("\n4. Testing authenticated user endpoint...")
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{base_url}/api/auth/user", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Authenticated request successful")
                    user = data.get("user")
                    print(f"   User info: {user.get('name')} ({user.get('email')})")
                else:
                    print(f"❌ User info failed: {data}")
            else:
                print(f"❌ User info request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ User info error: {e}")
        
        # Test demo login
        print("\n5. Testing demo login...")
        demo_data = {
            "email": "demo@agentflow.ai",
            "password": "demo123"
        }
        
        try:
            response = await client.post(f"{base_url}/api/auth/signin", json=demo_data)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print("✅ Demo login successful")
                    user = data.get("user")
                    print(f"   Demo user: {user.get('name')} ({user.get('email')})")
                else:
                    print(f"❌ Demo login failed: {data.get('error')}")
            else:
                print(f"❌ Demo login request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Demo login error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication system test completed!")
    print("\nTo start the full system:")
    print("./start_with_auth.sh")

if __name__ == "__main__":
    asyncio.run(test_auth_system())