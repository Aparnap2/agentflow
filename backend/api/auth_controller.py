"""
Authentication API Controller
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from auth.supabase_auth import supabase_auth

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class SignUpRequest(BaseModel):
    email: str
    password: str
    name: str

class SignInRequest(BaseModel):
    email: str
    password: str

@router.post("/signup")
async def sign_up(request: SignUpRequest) -> Dict[str, Any]:
    """Sign up new user"""
    result = await supabase_auth.sign_up(
        email=request.email,
        password=request.password,
        metadata={"name": request.name}
    )
    
    if result["success"]:
        # Add name and avatar to user data
        user_data = result["user"]
        user_data["name"] = request.name
        user_data["avatar"] = f"https://ui-avatars.com/api/?name={request.name}&background=3b82f6&color=fff"
        result["user"] = user_data
    
    return result

@router.post("/signin")
async def sign_in(request: SignInRequest) -> Dict[str, Any]:
    """Sign in user"""
    result = await supabase_auth.sign_in(
        email=request.email,
        password=request.password
    )
    
    if result["success"]:
        # Add name and avatar to user data
        user_data = result["user"]
        user_data["name"] = request.email.split('@')[0]
        user_data["avatar"] = f"https://ui-avatars.com/api/?name={user_data['name']}&background=3b82f6&color=fff"
        result["user"] = user_data
    
    return result

@router.get("/user")
async def get_current_user(user: Dict[str, Any] = Depends(supabase_auth.verify_token)) -> Dict[str, Any]:
    """Get current user info"""
    # Add name and avatar if missing
    if "name" not in user:
        user["name"] = user["email"].split('@')[0]
    if "avatar" not in user:
        user["avatar"] = f"https://ui-avatars.com/api/?name={user['name']}&background=3b82f6&color=fff"
    
    return {"success": True, "user": user}

@router.post("/signout")
async def sign_out() -> Dict[str, Any]:
    """Sign out user (client-side token removal)"""
    return {"success": True, "message": "Signed out successfully"}