FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Instala dependencias Python
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# Copia el código de la aplicación
COPY . /app/

# Usuario no root
#RUN useradd -m appuser && chown -R appuser /app
#USER appuser

EXPOSE 8000

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "120", "--log-level", "info"]