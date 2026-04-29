FROM python:3.11

WORKDIR /app

COPY requirements/ ./requirements/

RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "settings.asgi:application"]