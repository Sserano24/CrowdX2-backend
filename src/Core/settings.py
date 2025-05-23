"""
Django settings for Core project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import datetime
from pathlib import Path
from corsheaders.defaults import default_headers

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kix2_v+ymut21s!ky@r(1$#9iat(&cwzjs9dylhvj(*8li57^5'
STRIPE_WEBHOOK_SECRET = "whsec_7667f715dd78e87b0d8127fe4c75a9b1d36a1edcd5aa094bdd4de7348505309d"
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'daphne',
    'django.contrib.staticfiles',
    'channels',
    #third party
    'corsheaders',
    'ninja_extra',
    'ninja_jwt',
    #internal
    'campaigns',
    'accounts',
    'payments',

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Core.urls'

CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [

    "http://localhost:3000",#next.js
    "http://127.0.0.1:3000",#next.js
]
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
    "content-type",
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

ASGI_APPLICATION = 'Core.asgi.application'

STRIPE_PUBLISHABLE_KEY = "pk_test_51Qwj0jJQi9P7510EUj7bfyvwKCfFmlhsRojN1WVDFIiBDVOr6dtgMwAszEa4vIbRjsGEpNsNJIBXqoihGzxNz6E3007Aq3n59B"
STRIPE_SECRET_KEY = "sk_test_51Qwj0jJQi9P7510Eto6reuvr9srlwS9qKmlnoBdFg8pTGCTjw8hOxBt5J5iWRUGVVJfFBfN13qbh591iwznHwsIb00XzJngar5"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

NNIJA_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(hours= 12),
}

AUTH_USER_MODEL = 'accounts.User'
