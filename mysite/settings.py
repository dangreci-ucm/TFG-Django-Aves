import os
from pathlib import Path

# -------------------------------------------------------------------
# BASE
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# SECURITY
# -------------------------------------------------------------------

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "web", "nginx", "django_backend"]

# -------------------------------------------------------------------
# APPLICATIONS
# -------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apptfg.apps.ApptfgConfig',
]

# -------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

# -------------------------------------------------------------------
# TEMPLATES (solo backend: login, admin, etc.)
# -------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # SOLO backend templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# -------------------------------------------------------------------
# DATABASE (PostgreSQL Docker)
# -------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'tfg_db'),
        'USER': os.getenv('DATABASE_USER', 'tfg_user'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', '123'),
        'HOST': os.getenv('DATABASE_HOST', 'database'),
        'PORT': '5432',
    }
}

# -------------------------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# -------------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------------

LANGUAGE_CODE = 'es-es'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# STATIC FILES
# -------------------------------------------------------------------
# Django solo necesita estáticos para admin.
# El frontend público lo sirve Nginx directamente.

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "static"

# -------------------------------------------------------------------
# AUTH SETTINGS
# -------------------------------------------------------------------

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# -------------------------------------------------------------------
# DEFAULT FIELD TYPE
# -------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8000",
]


EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@tfg.local")