from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import posts as repository_posts
from src.entity.models import User, Role

from src.schemas.post import PostResponse, PostUpdateSchema
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(tags=["posts"])


@router.get("/", response_model=List[PostResponse], status_code=status.HTTP_200_OK)
async def get_posts(
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(auth_service.get_current_user)
):
    return await repository_posts.get_posts(db)


@router.get("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def get_post(
    post_id: int, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    photo = await repository_posts.get_post(post_id, db)
    if not photo:
        raise HTTPException(status_code=404, detail="Post not found")
    return photo


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    return await repository_posts.create_photo(
        title=title, 
        file=file, 
        content=content, 
        db=db, 
        user=user
    )


@router.put("/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def update_photo_description(
    post_id: int, 
    body: PostUpdateSchema, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    photo = await repository_posts.update_post_description(post_id, body, db, user)
    if not photo:
        raise HTTPException(status_code=404, detail="Post not found")
    return photo


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    post_id: int, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
):
    await repository_posts.delete_photo(post_id, db, user)
    return None


@router.post("/{post_id}/transform", response_model=PostResponse, status_code=status.HTTP_200_OK)
async def transform_photo(
    post_id: int,
    transformation: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    if not hasattr(repository_posts, "transform_photo"):
        raise HTTPException(status_code=501, detail="Transformation feature not implemented yet")
    return await repository_posts.transform_photo(post_id, transformation, db, user)




# --------------- Admin routes -----------------
admin_required = RoleAccess([Role.ADMIN])


@router.get("/admin/all", response_model=List[PostResponse], dependencies=[Depends(admin_required)])
async def admin_get_all_photos(db: AsyncSession = Depends(get_db)):
    return await repository_posts.get_all_photos_admin(db)


@router.delete("/admin/{post_id}", dependencies=[Depends(admin_required)], status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_photo(post_id: int, db: AsyncSession = Depends(get_db)):
    success = await repository_posts.admin_delete_photo(post_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return None


@router.put("/admin/{post_id}", response_model=PostResponse, dependencies=[Depends(admin_required)])
async def admin_update_photo(
    post_id: int, 
    body: PostUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    photo = await repository_posts.admin_update_photo_description(post_id, body, db)
    if not photo:
        raise HTTPException(status_code=404, detail="Post not found")
    return photo