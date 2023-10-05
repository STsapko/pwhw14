from fastapi import APIRouter, Depends, Query, status
from fastapi_limiter.depends import RateLimiter

from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.db import get_db
from src.DB.models import User
from src.repository.contacts_repo import (
    repo_get_contacts,
    repo_get_contact_by_id,
    repo_create_new_contact,
    repo_update_contact_db,
    repo_delete_contact_db,
    repo_get_contacts_query,
    repo_get_upcoming_birthday_contacts,
)
from src.schemas.Contacts_Schemas import ContactCreate, ContactResponse, ContactUpdate
from src.services.authservice import authservice as auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


# CRUD block
# OK
@router.get("/", tags=["contacts"], response_model=list[ContactResponse])
async def get_contacts_db(
    user: User = Depends(auth_service.get_current_user),
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    return await repo_get_contacts(user=user, limit=limit, offset=offset, db=db)


# OK
@router.get("/{id}", tags=["contacts"], response_model=ContactResponse)
async def get_contact_by_id(
    id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await repo_get_contact_by_id(id=id, user=user, db=db)


# OK
@router.post(
    "/",
    tags=["contacts"],
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(RateLimiter(times=2, seconds=5))]
)
async def create_new_contact(
    body: ContactCreate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await repo_create_new_contact(user=user, body=body, db=db)


# OK
@router.put("/{id}", tags=["contacts"], response_model=ContactResponse)
async def update_contact_db(
    id: int,
    body: ContactUpdate,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await repo_update_contact_db(id=id, user=user, body=body, db=db)


# OK
@router.delete("/{id}", tags=["contacts"])
async def delete_contact_db(
    id: int,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await repo_delete_contact_db(id=id, user=user, db=db)


# end of CRUD block

"""Additional block
Контакты должны быть доступны для поиска по имени, фамилии или адресу электронной почты (Query)."""


# OK
@router.get("/query/", tags=["contacts"], response_model=list[ContactResponse])
async def get_contacts_query(
    user: User = Depends(auth_service.get_current_user),
    query: str = Query(min_length=2, max_length=100),
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    return await repo_get_contacts_query(
        user=user, query=query, limit=limit, offset=offset, db=db
    )


"""API должен получить список контактов с днями рождения на ближайшие 7 дней."""


# OK
@router.get(
    "/upcoming_birthdays/", tags=["contacts"], response_model=list[ContactResponse]
)
async def get_upcoming_birthday_contacts(
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await repo_get_upcoming_birthday_contacts(user=user, db=db)
