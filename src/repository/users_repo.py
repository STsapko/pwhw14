from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.DB.models import User
from src.schemas.User_Schemas import UserCreate
from src.services import authservice as auth_service


async def repo_create_user(body: UserCreate, db: AsyncSession):
    """
    Создать нового пользователя.

    Эта функция создает нового пользователя с данными и сохраняет его в базе данных.
    Для присвоения аватара используется libgravatar, автоматически присваивающий аватар пользователю,
    в соответствии с пользовательским имейлом.

    Args:
        body (UserCreate): Объект `UserCreate`, содержащий данные для создания нового пользователя.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        User: Объект созданного пользователя из базы данных.

    Raises:
        HTTPException(409): Если пользователь с указанным электронным адресом уже существует.
    """
    g = Gravatar(email=body.email)
    avatar_img_url = g.get_image()
    refresh_token = await auth_service.authservice.create_refresh_token(
        {"sub": body.email}
    )
    user = User(
        **body.dict(),
        created_at=datetime.utcnow(),
        avatar=avatar_img_url,
        refresh_token=refresh_token
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def repo_user_authentication_by_email(email: str, db: AsyncSession) -> User:
    """
    Проводит аутентификацию пользователя по электронной почте.

    Эта функция ищет пользователя в базе данных по его электронной почте
    и возвращает пользовательский объект, если такой пользователь существует.

    Args:
        email (str): Электронная почта пользователя, которого нужно найти.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        User: Объект пользователя, если пользователь с указанным электронным адресом существует.
            Если пользователь с такой электронной почтой не найден, возвращается None.
    """
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    existing_user = result.scalar()
    return existing_user


async def repo_update_refresh_token(
    user: User, new_refresh_token: str, db: AsyncSession
):
    """
    Обновляет токен обновления (refresh token) для пользователя.

    Эта функция обновляет токен обновления для указанного пользователя в базе данных.
    Она сохраняет новый токен обновления и сохраняет изменения в базе данных.

    Args:
        user (User): Объект пользователя, для которого необходимо обновить токен обновления.
        new_refresh_token (str): Новый токен обновления, который необходимо сохранить.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        None
    """
    user.refresh_token = new_refresh_token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession):
    """
    Подтверждает электронную почту пользователя.

    Эта функция подтверждает электронную почту пользователя, обновляя статус активации.
    Она устанавливает значение поля `is_activated` пользователя на True, указывая, что
    электронная почта была успешно подтверждена.

    Args:
        email (str): Электронная почта пользователя, которую нужно подтвердить.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        None
    """

    user = await repo_user_authentication_by_email(email=email, db=db)
    user.is_activated = True
    await db.commit()


async def update_avatar(email, src_url, db: AsyncSession):
    """
    Обновляет аватар пользователя.

    Эта функция обновляет аватар (URL изображения) пользователя в базе данных по указанной электронной почте.
    Она находит пользователя по его электронной почте, обновляет поле `avatar` на новый URL аватара
    и сохраняет изменения в базе данных.

    Args:
        email (str): Электронная почта пользователя, чей аватар нужно обновить.
        src_url(str): URL нового аватара, который нужно сохранить.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        User: Объект пользователя с обновленным аватаром.
    """

    user = await repo_user_authentication_by_email(email=email, db=db)
    user.avatar = src_url
    await db.commit()
    return user


async def add_reset_token_to_db(user, reset_token, db: AsyncSession):
    """
    Добавляет токен сброс пароля (reset token) к пользователю.

    Эта функция добавляет токен сброса пароля (reset token) к указанному пользователю в базе данных.
    Она сохраняет новый токен сброса пароля в поле `reset_token` пользователя и сохраняет изменения в базе данных.

    Args:
        user: Объект пользователя, для которого нужно добавить токен сброса пароля.
        reset_token (str): Токен сброса пароля, который нужно сохранить.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.
    Returns:
        None
    """

    user.reset_token = reset_token
    await db.commit()
