FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    nginx \
    gettext-base \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

COPY . /app/

RUN mkdir -p /app/staticfiles /var/cache/nginx /var/lib/nginx /var/log/nginx /etc/nginx/templates

COPY nginx/render.conf.template /etc/nginx/templates/render.conf.template
COPY frontend/ /usr/share/nginx/html/
COPY start.sh /start.sh

RUN chmod +x /start.sh

EXPOSE 10000

CMD ["/start.sh"]