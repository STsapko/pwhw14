import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.DB.models import Contact, User
from src.repository.contacts_repo import repo_get_contacts, get_specific_contact_belongs_to_user, \
    repo_update_contact_db, repo_get_contact_by_id, repo_create_new_contact, repo_delete_contact_db, \
    repo_get_contacts_query, repo_get_upcoming_birthday_contacts
from src.schemas.Contacts_Schemas import ContactCreate, ContactUpdate


class TestContactRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1, email="user@example.com")
        self.async_session = AsyncMock(AsyncSession)

    async def test_get_specific_contact_belongs_to_user(self):
        expected_contact = Contact(id=1, first_name="John", last_name="Doe", email="test@example.com",
                                   user_id=self.user.id)
        self.async_session.execute.return_value.scalar.return_value = expected_contact
        result_coroutine = await get_specific_contact_belongs_to_user(1, self.user, self.async_session)
        result = await result_coroutine
        self.assertEqual(result, expected_contact)

    async def test_repo_get_contacts(self):
        expected_contacts = [
            Contact(id=1, first_name="John", last_name="Doe", email="test@example.com", user_id=self.user.id),
            Contact(id=2, first_name="Jane", last_name="Doe", email="test@example.com", user_id=self.user.id)
        ]
        # Mocking the result of the async execution
        async_result_mock = MagicMock()
        async_result_mock.scalars.return_value.all.return_value = expected_contacts
        self.async_session.execute.return_value = async_result_mock

        result = await repo_get_contacts(db=self.async_session, user=self.user, limit=10, offset=0)
        self.assertEqual(result, expected_contacts)

        # Additional check: Verify that the result is a list of contacts
        self.assertIsInstance(result, list)
        for contact in result:
            self.assertIsInstance(contact, Contact)

    async def test_repo_get_contact_by_id_contact_not_found(self):
        expected_contact = None
        with unittest.mock.patch('src.repository.contacts_repo.get_specific_contact_belongs_to_user',
                                 return_value=expected_contact):
            with self.assertRaises(HTTPException) as exc:
                await repo_get_contact_by_id(1, self.user, self.async_session)
            self.assertEqual(exc.exception.status_code, 404)
            self.assertEqual(exc.exception.detail, "Contact not found")

    async def test_repo_get_contact_by_id_contact_found(self):
        expected_contact = Contact(id=1, first_name="John", last_name="Doe", email="test@example.com",
                                   user_id=self.user.id)
        with unittest.mock.patch('src.repository.contacts_repo.get_specific_contact_belongs_to_user',
                                 return_value=expected_contact):
            result = await repo_get_contact_by_id(1, self.user, self.async_session)
            self.assertEqual(result.first_name, expected_contact.first_name)

    async def test_repo_create_new_contact(self):
        body = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="test@example.com",
            phone="0123456789",
            b_day="1999-07-10",
            rest_data="",
        )
        result = await repo_create_new_contact(user=self.user, body=body, db=self.async_session)
        print(result)
        self.assertEqual(result.first_name, body.first_name)
        self.assertTrue(hasattr(result, "id"))

    async def test_repo_update_contact_db(self):
        existing_contact = Contact(id=1, first_name="John", last_name="Doe", email="test@example.com",
                                   user_id=self.user.id)
        body = ContactUpdate(
            first_name="John",
            last_name="Doe",
            email="test@example.com",
            phone="0123456789",
            b_day="1999-07-10",
            rest_data="",
        )
        with unittest.mock.patch('src.repository.contacts_repo.get_specific_contact_belongs_to_user',
                                 return_value=existing_contact):
            result = await repo_update_contact_db(id=1, user=self.user, db=self.async_session, body=body)
            self.assertTrue(hasattr(result, "phone"))
            self.assertEqual(body.phone, existing_contact.phone)

    async def test_repo_update_contact_db_id_not_found(self):
        expected_contact = None
        body = ContactUpdate(
            first_name="John",
            last_name="Doe",
            email="test@example.com",
            phone="0123456789",
            b_day="1999-07-10",
            rest_data="",
        )
        with unittest.mock.patch('src.repository.contacts_repo.get_specific_contact_belongs_to_user',
                                 return_value=expected_contact):
            with self.assertRaises(HTTPException) as exc:
                await repo_update_contact_db(id=1, user=self.user, db=self.async_session, body=body)
            self.assertEqual(exc.exception.status_code, 404)
            self.assertEqual(exc.exception.detail, "Contact not found")

    async def test_repo_delete_contact_db_id_not_found(self):
        expected_contact = None
        with unittest.mock.patch('src.repository.contacts_repo.get_specific_contact_belongs_to_user',
                                 return_value=expected_contact):
            with self.assertRaises(HTTPException) as exc:
                await repo_delete_contact_db(id=1, user=self.user, db=self.async_session)
            self.assertEqual(exc.exception.status_code, 404)
            self.assertEqual(exc.exception.detail, "Contact not found")

    async def test_repo_delete_contact_db_success(self):
        existing_contact = Contact(id=1, first_name="John", last_name="Doe", email="test@example.com",
                                   user_id=self.user.id)
        contact_name = f'{existing_contact.first_name} {existing_contact.last_name}'
        with unittest.mock.patch('src.repository.contacts_repo.get_specific_contact_belongs_to_user',
                                 return_value=existing_contact):
            result = await repo_delete_contact_db(id=1, user=self.user, db=self.async_session)
            expected_msg = {"message": f"Contact '{contact_name}' successfully deleted"}
        self.assertEqual(result, expected_msg)
        self.assertIn(f'{contact_name}', result['message'])

    async def test_repo_get_contacts_query(self):
        contact1 = Contact(id=1, first_name="John", last_name="Doe", email="testJohn@example.com",
                           user_id=self.user.id)
        contact2 = Contact(id=2, first_name="Jane", last_name="Doe", email="testJohn@example.com",
                           user_id=self.user.id)
        # contact3 = Contact(id=3, first_name="Michael", last_name="Smith",
        #                    email="test@example.com", user_id=self.user.id)
        expected_contacts = [contact1, contact2]
        # Mocking the result of the async execution
        async_result_mock = MagicMock()
        async_result_mock.scalars.return_value.all.return_value = expected_contacts
        self.async_session.execute.return_value = async_result_mock

        # Test the function with a search query and other parameters
        query = "John"
        limit = 10
        offset = 0
        result = await repo_get_contacts_query(db=self.async_session, user=self.user, query=query, limit=limit,
                                               offset=offset)

        # Verify the returned result
        self.assertEqual(result, expected_contacts)

        # Additional checks: Verify the types and data returned
        self.assertIsInstance(result, list)
        for contact in result:
            self.assertIsInstance(contact, Contact)

        # Additional checks: Verify if the contacts match the search query
        for contact in result:
            print(query.lower(), contact.email.lower())
            self.assertTrue(
                query.lower() in contact.first_name.lower()
                or query.lower() in contact.last_name.lower()
                or query.lower() in contact.email.lower()
            )

    async def test_repo_get_upcoming_birthday_contacts(self):
        # Create contacts with upcoming birthdays
        contact_with_birthday_in_3_days = Contact(id=1, first_name="John", last_name="Doe", email="test@example.com",
                                                  user_id=self.user.id,
                                                  b_day=(datetime.datetime.now() + datetime.timedelta(days=3)).date())
        contact_with_birthday_in_5_days = Contact(id=2, first_name="Jane", last_name="Doe", email="test@example.com",
                                                  user_id=self.user.id,
                                                  b_day=(datetime.datetime.now() + datetime.timedelta(days=5)).date())
        contact_with_birthday_in_10_days = Contact(id=3, first_name="Michael", last_name="Smith",
                                                   email="test@example.com", user_id=self.user.id,
                                                   b_day=(datetime.datetime.now() + datetime.timedelta(days=10)).date())
        # Create contacts with birthdays outside the range of 7 days
        contact_with_birthday_in_20_days = Contact(id=4, first_name="Alex", last_name="Johnson",
                                                   email="test@example.com", user_id=self.user.id,
                                                   b_day=(datetime.datetime.now() + datetime.timedelta(days=20)).date())
        contact_with_birthday_in_1_day = Contact(id=5, first_name="Kate", last_name="Williams",
                                                 email="test@example.com", user_id=self.user.id,
                                                 b_day=(datetime.datetime.now() + datetime.timedelta(days=1)).date())

        expected_contacts = [contact_with_birthday_in_3_days, contact_with_birthday_in_5_days,
                             contact_with_birthday_in_1_day]

        # Mock the result of the async execution
        async_result_mock = MagicMock()
        async_result_mock.scalars.return_value.all.return_value = [contact_with_birthday_in_3_days,
                                                                   contact_with_birthday_in_5_days,
                                                                   contact_with_birthday_in_10_days,
                                                                   contact_with_birthday_in_20_days,
                                                                   contact_with_birthday_in_1_day]
        self.async_session.execute.return_value = async_result_mock

        # Test the function
        result = await repo_get_upcoming_birthday_contacts(db=self.async_session, user=self.user)

        # Verify the returned result
        self.assertEqual(result, expected_contacts)

        # Additional checks: Verify the types and data returned
        self.assertIsInstance(result, list)
        for contact in result:
            self.assertIsInstance(contact, Contact)
