from pathlib import Path


BASE_DIR = Path(__file__).absolute().parent.resolve(strict=True)

SECRET_KEY = "***REMOVED***"

DEBUG = True

ALLOWED_HOSTS = ["django-dev"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "datavalidation.apps.DataValidationConfig",
    "test_app.apps.TestAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "test_proj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "test_proj.wsgi.application"

DATABASES = {
    "sqlite3": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": (BASE_DIR.parent / "db.sqlite3").as_posix(),
    },

    "postgres": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "ddv",
        "USER": "***REMOVED***",
        "PASSWORD": "***REMOVED***",
        "HOST": "",
        "PORT": "",
    }
}

DATABASES["default"] = DATABASES["postgres"]


# # Password validation
# # https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
#
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
#     },
#     {
#         "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
#     },
# ]
#
#
# # Internationalization
# # https://docs.djangoproject.com/en/2.2/topics/i18n/
#
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Australia/Melbourne"

USE_I18N = False

USE_L10N = False

#USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"
