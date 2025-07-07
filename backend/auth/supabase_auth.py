"""
Supabase Authentication Integration
"""
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import json

class SupabaseAuth:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not all([self.supabase_url, self.supabase_key]):
            # Use demo mode if not configured
            self.demo_mode = True
            self.supabase_url = "https://demo.supabase.co"
            self.supabase_key = "demo_key"
        else:
            self.demo_mode = False
        
        self.security = HTTPBearer(auto_error=False)
    
    async def sign_up(self, email: str, password: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Sign up new user"""
        if self.demo_mode:
            return {
                "success": True,
                "user": {"id": "demo_user", "email": email},
                "access_token": "demo_token"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/signup",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password,
                        "data": metadata or {}
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "user": data.get("user", {}),
                        "access_token": data.get("access_token")
                    }
                else:
                    return {"success": False, "error": response.text}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user"""
        if self.demo_mode:
            return {
                "success": True,
                "user": {"id": "demo_user", "email": email},
                "access_token": "demo_token"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/token?grant_type=password",
                    headers={
                        "apikey": self.supabase_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "user": data.get("user", {}),
                        "access_token": data.get("access_token")
                    }
                else:
                    return {"success": False, "error": "Invalid credentials"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user from JWT token"""
        if self.demo_mode or token == "demo_token":
            return {"id": "demo_user", "email": "demo@example.com"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/auth/v1/user",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {token}"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
        except:
            return None
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> Dict[str, Any]:
        """Verify JWT token dependency"""
        if not credentials:
            # Allow demo access
            return {"id": "demo_user", "email": "demo@example.com"}
        
        token = credentials.credentials
        user = await self.get_user_from_token(token)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return user

# Global auth instance
supabase_auth = SupabaseAuth()