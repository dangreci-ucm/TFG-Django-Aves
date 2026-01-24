# Base compatible con las dependencias (Django 2.2, sklearn 0.24, numpy 1.20)
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Paquetes de sistema mínimos
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala las dependencias
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt \
 && pip install gunicorn whitenoise

# Copia el código
COPY . /app/

# Usuario no root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Puerto de la app
EXPOSE 8000

# Arranque con gunicorn
CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--log-level", "info"]
