from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    id: str
    username: str
    email: EmailStr
