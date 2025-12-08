from pathlib import Path

import os
from decouple import config
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# DEBUG ONLY — remove after verifying
print("DID_API_KEY present in environment?", bool(os.environ.get("DID_API_KEY")))
print("AWS_STORAGE_BUCKET_NAME present?", bool(os.environ.get("AWS_STORAGE_BUCKET_NAME")))

import datetime
print("SERVER UTC TIME:", datetime.datetime.utcnow().isoformat())

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------
# SECURITY
# -------------------------------------------------
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,.onrender.com'
).split(',')

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]


# -------------------------------------------------
# APPS
# -------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'learning',
    'corsheaders',
]

AUTH_USER_MODEL = 'learning.User'


# -------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be here for Render!

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    "utils.middleware.refresh_presigned.RefreshPresignedURLMiddleware",
]


ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


CORS_ALLOW_ALL_ORIGINS = True

# -------------------------------------------------
# TEMPLATES
# -------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]


# -------------------------------------------------
# DATABASE (Supabase)
# -------------------------------------------------
DATABASE_URL = config("DATABASE_URL")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}


# -------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# -------------------------------------------------
# STATIC & MEDIA (Render)
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# -------------------------------------------------
# LOGIN SETTINGS
# -------------------------------------------------
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'student-dashboard'
LOGOUT_REDIRECT_URL = 'home'


# -------------------------------------------------
# API KEYS
# -------------------------------------------------
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
DID_API_KEY = config("DID_API_KEY", default="")
SUPABASE_URL = config("DATABASE_URL", default="")


# -----------------------------
# AWS S3 Storage settings
# -----------------------------
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")