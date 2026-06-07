from typing import Optional, List
from slugify import slugify 
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.entity.models import User, Post, Role
from src.schemas.post import PostResponse, PostUpdateSchema
from src.services.cloudinary_service import CloudinaryService

cloudinary_service = CloudinaryService()


async def get_posts(db: AsyncSession) -> List[PostResponse]:
    stmt = select(Post)
    result = await db.execute(stmt)
    posts = result.scalars().all()
    return [PostResponse.model_validate(p) for p in posts]


async def get_post(photo_id: int, db: AsyncSession) -> Optional[PostResponse]:
    stmt = select(Post).filter_by(id=photo_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    return PostResponse.model_validate(post) if post else None


async def create_photo(
    title: str,
    file: UploadFile,
    content: str,
    db: AsyncSession,
    user: User
) -> PostResponse:
   
    url, _ = await cloudinary_service.upload_image(file)

    base_slug = slugify(title)
    slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

    new_photo = Post(
        title=title,
        content=content,
        url=url,
        slug=slug,
        user_id=user.id
    )
    
    db.add(new_photo)
    await db.commit()
    await db.refresh(new_photo)
    return PostResponse.model_validate(new_photo)


async def update_post_description(photo_id: int, body: PostUpdateSchema, db: AsyncSession, user: User) -> PostResponse:
    stmt = select(Post).filter_by(id=photo_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id and user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions to update this post")


    if body.title is not None and body.title != post.title:
        post.title = body.title
        post.slug = f"{slugify(body.title)}-{uuid.uuid4().hex[:6]}"  # Перегенеруємо slug тільки для НОВОГО заголовка

    if body.content is not None and body.content != post.content:
        post.content = body.content

  
    if body.url is not None and body.url != post.url:
        post.url = body.url

    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


async def delete_photo(photo_id: int, db: AsyncSession, user: User):
    stmt = select(Post).filter_by(id=photo_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id and user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions to delete this post")

   
    await db.delete(post)
    await db.commit()

    return {"detail": "Post deleted successfully"}


# --------------- Admin methods -----------------

async def get_all_photos_admin(db: AsyncSession) -> List[PostResponse]:
    result = await db.execute(select(Post))
    posts = result.scalars().all()
    return [PostResponse.model_validate(p) for p in posts]


async def admin_delete_photo(photo_id: int, db: AsyncSession) -> bool:
    result = await db.execute(select(Post).where(Post.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        return False
        
    await db.delete(photo)
    await db.commit()
    return True


async def admin_update_photo_description(photo_id: int, body: PostUpdateSchema, db: AsyncSession) -> Optional[PostResponse]:
    result = await db.execute(select(Post).where(Post.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        return None
        
    if body.title is not None:
        photo.title = body.title
        photo.slug = f"{slugify(body.title)}-{uuid.uuid4().hex[:6]}"
    if body.content is not None:
        photo.content = body.content
        
    await db.commit()
    await db.refresh(photo)
    return PostResponse.model_validate(photo)