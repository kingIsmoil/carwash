from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    fullname: str = Field(..., max_length=70)
    email: EmailStr
    phone_number: str
    password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    phone_number: str
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str