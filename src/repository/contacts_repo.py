import datetime

from fastapi import HTTPException
from sqlalchemy import select, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.models import Contact, User
from src.schemas.Contacts_Schemas import ContactCreate, ContactUpdate


async def get_specific_contact_belongs_to_user(id: int, user: User, db: AsyncSession):
    """
    Эта функция получает конкретный контакт из базы данных, принадлежащий пользователю,
    с указанным идентификатором.

    Args:
        id (int): Идентификатор контакта, который необходимо получить.
        user (User): Объект пользователя, которому принадлежит контакт.
        db(AsyncSession): Сессия базы данных для взаимодействия с ней.

    Returns:
        Contact: Объект контакта, принадлежащий пользователю, или None, если контакт не найден.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ к данному контакту.
        HTTPException(404): Если контакт с указанным идентификатором не найден.
    """

    stmt = select(Contact).where(Contact.user_id == user.id).filter(Contact.id == id)
    contact_data = await db.execute(stmt)
    contact = contact_data.scalar()
    return contact


# OK
async def repo_get_contacts(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[Contact]:
    """
    Получить список контактов пользователя.

    Эта функция получает список контактов из базы данных, принадлежащих пользователю.

    Args:
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.
        user(User): Объект пользователя, для которого получаем контакты.
        limit (int): Максимальное количество полученных контактов.
        offset (int): Количество контактов, пропущенных с начала результатов.

    Returns:
        List[Contact]: Список объектов контактов, принадлежащих пользователю.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ к контактам.
    """

    contacts_data = (
        select(Contact)
        .where(Contact.user_id == user.id)
        .offset(offset)
        .limit(limit)
        .order_by(asc(Contact.id))
    )
    result = await db.execute(contacts_data)
    return result.scalars().all()


# OK
async def repo_get_contact_by_id(id: int, user: User, db: AsyncSession):
    """
    Получить контакт по идентификатору, который принадлежит пользователю.

    Эта функция использует в качестве основы функцию get_specific_contact_belongs_to_user(), и дополняет ее необходимыми
    расширениями.

    Args:
        id (int): Идентификатор контакта, который необходимо получить.
        user(User): Объект пользователя, для которого получаем контакт.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        Contact: Объект контакта, принадлежащий пользователю.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ к контактам.
        HTTPException(404): Если контакт с указанным идентификатором не найден.
    """

    contact = await get_specific_contact_belongs_to_user(id, user, db)

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


# OK
async def repo_create_new_contact(user: User, body: ContactCreate, db: AsyncSession):
    """
    Создать новый пользовательский контакт.

    Эта функция создает новый контакт в пользовательской базе данных с указанными данными.

    Args:
        user(User): Объект пользователя, для которого создаем контакт.
        body (ContactCreate): Объект ContactCreate, содержащий данные для создания контакта.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        Contact: Созданный объект контакта.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступа для создания контакта.
        ValueError: При попытке создания контакта с не валидным форматом даты. Или будущей датой рождения.
    """

    contact = Contact(**body.dict(), user_id=user.id)
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    await db.commit()
    return contact


# OK
async def repo_update_contact_db(
    id: int, user: User, body: ContactUpdate, db: AsyncSession
):
    """
    Обновить существующий контакт для пользователя.

    Эта функция обновляет контакт существующего в пользовательской базе данных с указанным идентификатором.
    В ней используется функция для нахождения конкретного контакта get_specific_contact_belongs_to_user(),
    с расширенными возможностями для данного случая – (обновление информации о контакте).

    Args:
        id (int): Идентификатор контакта, который необходимо обновить.
        user (User): Объект пользователя, для которого принадлежит контакт.
        body (ContactUpdate): Объект ContactUpdate, содержащий данные для обновления контакта.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        Contact: Объект обновленного контакта.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ для обновления контакта.
        HTTPException(404): Если контакт с указанным идентификатором не найден.
    """

    contact = await get_specific_contact_belongs_to_user(id, user, db)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in body.dict(exclude_unset=True).items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


# OK
async def repo_delete_contact_db(id: int, user: User, db: AsyncSession):
    """
    Удалить существующий контакт пользователя.

    Эта функция удаляет существующий контакт из пользовательской базы данных с указанным идентификатором.
    В ней используется вспомогательная функция get_specific_contact_belongs_to_user(), с расширенными возможностями
    для данного случая – (удаление конкретного контакта)

    Args:
        id (int): Идентификатор контакта, который необходимо удалить.
        user (User): Объект пользователя, для которого принадлежит контакт.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        dict: Объект с уведомлением об успешном удалении контакта.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ для удаления контакта.
        HTTPException(404): Если контакт с указанным идентификатором не найден.

    Example response:
        {
            "message": "Contact 'John Doe' successfully deleted"
        }
    """

    contact = await get_specific_contact_belongs_to_user(id, user, db)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_name = f"{contact.first_name} {contact.last_name}"

    await db.delete(contact)
    await db.commit()

    return {"message": f"Contact '{contact_name}' successfully deleted"}


# OK
async def repo_get_contacts_query(
    user: User, query: str, limit: int, offset: int, db: AsyncSession
):
    """
    Получите список контактов пользователя по запросу поиска.

    Эта функция получает список контактов из базы данных, принадлежащих пользователю,
    и соответствуют заданному поисковому запросу.
    Поиск происходит в полях `first_name`, `last_name`, `email`.

    Args:
        user(User): Объект пользователя, для которого получаем контакты.
        query (str): Поисковый запрос для фильтрации контактов.
        limit (int): Максимальное количество полученных контактов.
        offset (int): Количество контактов, пропущенных с начала результатов.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        List[Contact]: Список объектов контактов, принадлежащих пользователю и соответствующих запросу.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ к контактам.
    """

    search_query = f"%{query}%"
    lower_search_query = search_query.lower()

    stmt = (
        select(Contact)
        .where(
            (Contact.user_id == user.id)
            & (
                (func.lower(Contact.first_name).like(lower_search_query))
                | (func.lower(Contact.last_name).like(lower_search_query))
                | (func.lower(Contact.email).like(lower_search_query))
            )
        )
        .offset(offset)
        .limit(limit)
        .order_by(asc(Contact.id))
    )

    contacts_data = await db.execute(stmt)
    return contacts_data.scalars().all()


# OK


async def repo_get_upcoming_birthday_contacts(user: User, db: AsyncSession):
    """
    Получить список контактов с приближающимися днями рождения пользователя.

    Эта функция возвращает список контактов, имеющих день рождения в ближайшие 7 дней.

    Args:
        user(User): Объект пользователя, для которого получаем контакты с ближайшими днями рождения.
        db(AsyncSession): Асинхронная сессия базы данных для взаимодействия с ней.

    Returns:
        List[Contact]: Список объектов контактов, в которых приближаются дни рождения.

    Raises:
        HTTPException(401): Возникает, если у пользователя нет действительной аутентификации
                            или доступ к контактам.
    """

    today = datetime.datetime.now().date()
    end_date = today + datetime.timedelta(days=7)

    answer_contacts = []
    results = await db.execute(select(Contact).filter(Contact.user_id == user.id))
    contacts: list[Contact] = results.scalars().all()

    for contact in contacts:
        b_day = contact.b_day
        today_year_b_day = datetime.datetime(today.year, b_day.month, b_day.day).date()

        if today <= today_year_b_day <= end_date:
            answer_contacts.append(contact)

    return answer_contacts
