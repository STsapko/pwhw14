import asyncio
import random
import timeit

from faker import Faker
from src.DB.models import Contact
from src.DB.db import async_session, engine


async def generate_contacts(num_contacts: int):
    fake = Faker("ru-RU")

    contacts = []
    async with async_session() as session:
        for _ in range(num_contacts):
            contact = Contact(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number(),
                user_id=random.randint(1, 2),
                # user_id=int(1),
                b_day=fake.date_between(start_date="-90y", end_date="now"),
                rest_data=random.choice([fake.text(max_nb_chars=300), None]),
            )

            contacts.append(contact)

    return contacts


async def seed_contacts():
    async with engine.begin() as connection:
        await connection.run_sync(Contact.metadata.drop_all)
        await connection.run_sync(Contact.metadata.create_all)

    contacts = await generate_contacts(400)
    async with async_session() as session:
        async with session.begin():
            for contact in contacts:
                session.add(contact)
            await session.commit()
    print(f"Contacts seeded")


if __name__ == "__main__":
    start_time = timeit.default_timer()
    asyncio.run(seed_contacts())
    print(f"Contacts seeded in {timeit.default_timer() - start_time}")
