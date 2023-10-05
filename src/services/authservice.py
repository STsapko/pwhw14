from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.db import get_db
from src.repository import users_repo as user_repository
from src.conf.config import settings


class Auth:
    """
    Класс Auth предоставляет разные методы для генерации, проверки и работы с токенами.
    аутентификации, а также для получения аутентифицированного пользователя.

    Attributes:
        pwd_cxt (CryptContext): Объект для хеширования паролей с помощью bcrypt.
        SECRET_KEY(str): Секретный ключ для подписи JWT.
        ALGR(str): Алгоритм подписи JWT.
        oauth2_scheme (OAuth2PasswordBearer): Объект для получения токена из HTTP-запроса.
    """

    pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGR = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

    def generate_password_hash(self, password: str):
        """
        Генерирует хэш пароля с помощью bcrypt.

        Args:
            password (str): Пароль в открытом виде.

        Returns:
            str: Хэш пароля, созданный с помощью bcrypt.
        """
        return self.pwd_cxt.hash(password)

    def check_password_hash(self, hashed_password: str, password: str):
        """
        Проверяет, соответствует ли пароль сохраненному хешу.

        Args:
            hashed_password (str): Сохраненный хэш пароля, созданный с помощью bcrypt.
            password (str): Пароль в открытом виде для проверки.

        Returns:
            bool: True, если пароли соответствуют друг другу, False – в противном случае.
        """
        return self.pwd_cxt.verify(password, hashed_password)

    async def create_access_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Создает токен доступа.

        Args:
            data (dict): Данные для включения в пейлоад токена.
            expires_delta (float, optional): Срок действия токена в секундах. По умолчанию – 15 минут.

        Returns:
            str: Токен доступа в виде строки JWT.
        """
        to_encode = data.copy()

        if expires_delta:
            expires = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expires = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expires, "scope": "access_token"}
        )
        access_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return access_token

    async def create_refresh_token(
        self, data: dict, expires_delta: Optional[float] = None
    ):
        """
        Создает обновление токена.

        Args:
            data (dict): Данные для включения в пейлоад токена.
            expires_delta (float, optional): Срок действия токена в секундах. По умолчанию – 7 дней.

        Returns:
            str: Токен обновления в виде строки JWT.
        """
        to_encode = data.copy()

        if expires_delta:
            expires = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expires = datetime.utcnow() + timedelta(days=7)

        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expires, "scope": "access_token"}
        )
        refresh_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return refresh_token

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
    ):
        """
        Получить текущего аутентифицированного пользователя с помощью токена доступа.
        Args:
            token (str, optional): Токен доступа в формате Bearer. По умолчанию: Depends(oauth2_scheme).
            db(AsyncSession, optional): Асинхронный сеанс базы данных. По умолчанию Depends(get_db).

        Returns:
            User: Объект аутентифицированного пользователя.

        Raises:
            HTTPException(401): Если токен недействителен или пользователь не аутентифицирован.
        """

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") != "access_token":
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await user_repository.repo_user_authentication_by_email(email, db)
        if user is None:
            raise credentials_exception

        return user

    def create_email_token(self, data: dict):
        """
        Создать токен подтверждение электронной почты.

        Args:
            data(dict): Данные, которые будут включены в тело токена.

        Returns:
            str: Токен подтверждения электронной почты в формате JWT (JSON Web Token) в виде строки.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"}
        )
        token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Разкодировать токен обновления и извлечь электронную почту.

        Args:
            refresh_token (str): Токен обновления в формате JWT (JSON Web Token) в виде строки.

        Returns:
            str: Электронная почта, извлеченная из токена обновления.

        Raises:
            HTTPException(401): Если токен недействителен или имеет неправильный объем.
        """
        try:
            payload = jwt.decode(
                refresh_token, key=self.SECRET_KEY, algorithms=[self.ALGR]
            )
            if payload.get("scope") == "refresh_token":
                email = payload.get("sub")
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope"
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def get_email_from_token(self, token: str):
        """
        Получить электронную почту с токеном подтверждения электронной почты.

        Args:
            token (str): Токен подтверждения электронной почты в формате JWT (JSON Web Token) в виде строки.

        Returns:
            str: Электронная почта, извлеченная из токена.

        Raises:
            HTTPException(422): Если токен недействителен для подтверждения электронной почты.
        """
        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "email_token":
                email = payload.get("sub")
                return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email confirmation.",
            )

    def create_reset_token(self, data: dict, expire=1):
        """
        Создать токен для сброса пароля.

        Args:
            data(dict): Данные, которые будут включены в тело токена.
            expire(int, optional): Время действия токена в часах. По умолчанию: 1 час.

        Returns:
            str: Токен для сброса пароля в формате JWT (JSON Web Token) в виде строки.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=expire)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh"})
        reset_token = jwt.encode(to_encode, key=self.SECRET_KEY, algorithm=self.ALGR)
        return reset_token

    def get_email_from_reset_token(self, token: str):
        """
        Получить электронную почту из токена для сброса пароля.

        Args:
            token (str): Токен для сброса пароля в формате JWT (JSON Web Token) в виде строки.

        Returns:
            str: Электронная почта, извлеченная из токена.

        Raises:
            HTTPException(422): Если токен недействителен для сброса пароля.
        """
        try:
            payload = jwt.decode(token, key=self.SECRET_KEY, algorithms=[self.ALGR])
            if payload.get("scope") == "refresh":
                email = payload.get("sub")
                return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for password reset.",
            )


authservice = Auth()
