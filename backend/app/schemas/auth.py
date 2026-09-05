from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.enums import UserRole


class UserRegister(BaseModel):
    """
    WHY a separate schema from the User model: clients must NEVER be able
    to set fields like `id` or arbitrary roles beyond what we allow by
    directly posting JSON. This schema is an intentional whitelist of what
    a client is allowed to send when registering.
    """

    email: EmailStr
    password: str
    name: str
    role: UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: UserRole
    access_token: str | None = None

    model_config = ConfigDict(from_attributes=True)
