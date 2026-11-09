from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)
    # Required to change the email or password.
    current_password: Optional[str] = Field(None, max_length=128)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    email_verified: bool = False
    # False for accounts made with Google that haven't set a password yet.
    has_password: bool = True

    class Config:
        from_attributes = True


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmail(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class GoogleLogin(BaseModel):
    # The ID token (JWT) that Google's sign-in button hands the browser.
    credential: str = Field(min_length=20, max_length=4096)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class GoogleTokenOut(TokenOut):
    # True when this sign-in created the account.
    created: bool = False