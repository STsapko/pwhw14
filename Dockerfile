# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.11

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

COPY Pipfile $APP_HOME/Pipfile
COPY Pipfile.lock $APP_HOME/Pipfile.lock

# Встановимо залежності всередині контейнера
RUN pip install pipenv
RUN pipenv install --deploy --ignore-pipfile

# Скопіюємо інші файли в робочу директорію контейнера
COPY . .

# Позначимо порт, де працює програма всередині контейнера
EXPOSE 8000

# Запустимо нашу програму всередині контейнера
CMD ["pipenv", "run", "python", "instagram/manage.py", "runserver", "0.0.0.0:8000"]
