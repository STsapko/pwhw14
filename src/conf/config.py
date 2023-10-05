import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

database_url = os.environ.get("SQLALCHEMY_DATABASE_URL")


class Settings(BaseSettings):
    sqlalchemy_database_url: str = "postgresql+asyncpg://user:password@$localhost:5432/postgres?async_fallback=True"
    secret_key: str = 'secret_key'
    algorithm: str = "HS256"
    mail_username: str = "example@email.com"
    mail_password: str = "password"
    mail_from: str = "example@email.com"
    mail_port: int = 465
    mail_server: str = "smtp.mail.com"
    cloudinary_cloud_name: str = "cloudinary"
    cloudinary_api_key: str = "123456879789"
    cloudinary_api_secret: str = "cloudinary_api_secret"

    redis_host: str = 'localhost'
    redis_port: int = 6379

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# if __name__ == "__main__":
#     print(database_url)
