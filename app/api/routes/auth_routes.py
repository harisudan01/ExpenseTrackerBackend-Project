from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models import User
from app.schemas.auth_schema import AuthResponse, LoginRequest, SignupRequest, UserResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)

service = AuthService()


# Create an account and log in
@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    return service.signup(db, data)


# Log in with email + password
@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return service.login(db, data)


# Currently logged-in user
@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
