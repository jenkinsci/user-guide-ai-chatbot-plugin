from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import models
from database import get_database_session
from manage_env import get_env
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = get_env("JWT_SECRET_KEY")
ALGORITHM = get_env("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(get_env("ACCESS_TOKEN_EXPIRE_MINUTES"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication"])

User = models.UserEntity


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_database_session),
) -> User:
    """
    Validates the JWT token, extracts the user details, and fetches the user
    from PostgreSQL. If the user does not exist, it creates a new record automatically.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or user is deleted",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode the JWT to extract user claims
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError as e:
        raise credentials_exception

    # Query PostgreSQL to find the user (without filtering by deleted_at yet)
    query = select(models.UserEntity).where(models.UserEntity.id == user_id)

    execution_result = await db_session.execute(query)
    existing_user = execution_result.scalars().first()

    if existing_user:
        # If the user exists but was soft-deleted, deny access
        if existing_user.deleted_at is not None:
            raise credentials_exception

        # User exists and is active
        return existing_user

    else:
        # User does not exist at all, we create them Just-In-Time
        new_provisioned_user = models.UserEntity(
            id=user_id,
        )

        db_session.add(new_provisioned_user)
        await db_session.commit()
        await db_session.refresh(new_provisioned_user)

        return new_provisioned_user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire_time = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire_time})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
