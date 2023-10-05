import datetime

import pytest
from unittest.mock import MagicMock

from libgravatar import Gravatar

from src.DB.models import User
from src.schemas.User_Schemas import UserCreationResponse, UserDBScheme


# @pytest.mark.usefixtures("db")
@pytest.mark.asyncio
async def test_register_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/auth/register", json=user)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["email"] == user.get("email")


@pytest.mark.asyncio
async def test_register_user_successful(client, user, monkeypatch):
    # Мокиваем функции для имитации успешной регистрации
    async def mock_repo_user_authentication_by_email(email, db):
        return None

    async def mock_repo_create_user(body, db):
        g = Gravatar(email=user["email"])
        avatar_img_url = g.get_image()
        return User(
            **user,
            created_at=datetime.datetime.utcnow(),
            avatar=avatar_img_url,
            refresh_token="refresh.token"
        )

    monkeypatch.setattr(
        "src.repository.users_repo.repo_user_authentication_by_email",
        mock_repo_user_authentication_by_email,
    )
    monkeypatch.setattr(
        "src.repository.users_repo.repo_create_user", mock_repo_create_user
    )

    response = client.post("/auth/register", json=user)

    assert response.status_code == 201
    assert (
        response.json()["message"]
        == "Your account created successfully. Check your email to activate it."
    )
    assert response.json()["email"] == user["email"]
    assert response.json()["username"] == user["username"]
    # Проверка вызова функции send_email
    # assert len(client.background_tasks) == 1


@pytest.mark.asyncio
async def test_register_user_existing_email(client, user, monkeypatch):
    # Мокируtv функцию, возвращающую существующего пользователя
    async def mock_repo_user_authentication_by_email(email, db):
        return True

    monkeypatch.setattr(
        "src.repository.users_repo.repo_user_authentication_by_email",
        mock_repo_user_authentication_by_email,
    )

    response = client.post("/auth/register", json=user)

    assert response.status_code == 409
    assert "Email already exists. Try to log in." in response.json()["detail"]
