import unittest
from unittest.mock import AsyncMock


from sqlalchemy.ext.asyncio import AsyncSession
from src.DB.models import Contact, User
from src.repository.users_repo import repo_create_user, repo_user_authentication_by_email, repo_update_refresh_token, \
    confirmed_email, update_avatar, add_reset_token_to_db
from src.schemas.User_Schemas import UserCreate
from src.services.authservice import authservice as auth_service


class TestUserRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1, username="test_user", email="user@example.com", password="qwerty")
        self.async_session = AsyncMock(AsyncSession)

    async def test_repo_create_user(self):
        body = UserCreate(
            username=self.user.username,
            email=self.user.email,
            password=self.user.password
        )
        avatar_url_pattern = r"https://www.gravatar.com/avatar/[a-zA-Z0-9]{32}"
        result = await repo_create_user(body=body, db=self.async_session)
        self.assertTrue(hasattr(result, "id"))
        self.assertEqual(result.email, body.email)
        self.assertTrue(hasattr(result, 'avatar'))
        self.assertRegex(result.avatar, avatar_url_pattern)

    async def test_repo_user_authentication_by_email(self):
        email_to_find = self.user.email
        expected_user = self.user
        self.async_session.execute.return_value.scalar.return_value = expected_user
        result_coroutine = await repo_user_authentication_by_email(email=email_to_find, db=self.async_session)
        result = await result_coroutine
        self.assertEqual(result, expected_user)
        self.assertTrue(email_to_find.lower() == expected_user.email.lower())

    async def test_repo_update_refresh_token(self):
        refresh_token_ = await auth_service.create_refresh_token(data={"sub": self.user.email})
        self.assertNotEqual(self.user.refresh_token, refresh_token_)
        await repo_update_refresh_token(user=self.user, new_refresh_token=refresh_token_,
                                        db=self.async_session)
        self.assertTrue(hasattr(self.user, "refresh_token"))
        self.assertEqual(self.user.refresh_token, refresh_token_)

    async def test_confirmed_email(self):
        expected_user = self.user
        self.assertFalse(self.user.is_activated, True)
        with unittest.mock.patch('src.repository.users_repo.repo_user_authentication_by_email',
                                 return_value=expected_user):
            await confirmed_email(email=self.user.email, db=self.async_session)
        self.assertTrue(self.user.is_activated, True)

    async def test_update_avatar(self):
        expected_user = self.user
        new_avatar = "https://avatar.com/example_avatar.jpg"
        self.assertNotEqual(self.user.avatar, new_avatar)
        with unittest.mock.patch('src.repository.users_repo.repo_user_authentication_by_email',
                                 return_value=expected_user):
            await update_avatar(email=self.user.email, src_url=new_avatar, db=self.async_session)
        self.assertEqual(self.user.avatar, new_avatar)

    async def test_add_reset_token_to_db(self):
        reset_token = auth_service.create_reset_token({"sub": self.user.email})
        self.assertNotEqual(self.user.refresh_token, reset_token)
        await add_reset_token_to_db(user=self.user, reset_token=reset_token, db=self.async_session)
        self.assertTrue(hasattr(self.user, "reset_token"))
        self.assertEqual(self.user.reset_token, reset_token)

