from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, func, MetaData, Boolean
from sqlalchemy.orm import declarative_base, relationship

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    b_day = Column(Date, nullable=False)
    rest_data = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=True)
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    is_activated = Column(Boolean, default=False, nullable=False)
    contacts = relationship('Contact', backref='user', lazy='dynamic')
