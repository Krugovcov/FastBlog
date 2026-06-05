from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserSchema
from src.database.db import get_db
from src.entity.models import User, RefreshToken


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter_by(email=email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_username(username: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter_by(username=username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter_by(id=id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(body: dict | UserSchema, db: AsyncSession = Depends(get_db)):
    data = body.model_dump() if isinstance(body, UserSchema) else dict(body)

    if "password" in data and "password_hash" not in data:
        data["password_hash"] = data.pop("password")

    new_user = User(**data)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token: str | None, db: AsyncSession = Depends(get_db)):
    if refresh_token is None:
        return None

    token_record = RefreshToken(token=refresh_token, user_id=user.id)
    db.add(token_record)
    await db.commit()
    return token_record