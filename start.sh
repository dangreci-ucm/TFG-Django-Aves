#!/bin/sh
set -e

echo "Esperando a PostgreSQL..."
until python -c "import os, psycopg2; psycopg2.connect(
    host=os.environ['DATABASE_HOST'],
    dbname=os.environ['DATABASE_NAME'],
    user=os.environ['DATABASE_USER'],
    password=os.environ['DATABASE_PASSWORD'],
    port=os.environ.get('DATABASE_PORT', '5432')
)"; do
    sleep 2
done

echo "Aplicando migraciones..."
python manage.py migrate

echo "Recogiendo estáticos..."
python manage.py collectstatic --noinput

# Opcional, si luego implementas el comando
# python manage.py init_model_artifacts || true

echo "Arrancando Gunicorn..."
gunicorn mysite.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --log-level info &

echo "Generando config de Nginx..."
envsubst '${PORT}' < /etc/nginx/templates/render.conf.template > /etc/nginx/conf.d/default.conf

echo "Arrancando Nginx..."
exec nginx -g 'daemon off;'