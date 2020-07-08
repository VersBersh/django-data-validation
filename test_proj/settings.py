from pathlib import Path

BASE_DIR = Path(__file__).absolute().parent.resolve(strict=True)

DEBUG = True

ALLOWED_HOSTS = ["django-dev"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "datavalidation.apps.DataValidationConfig",
    "animalconference.apps.AnimalConferenceConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": (BASE_DIR.parent / "db.sqlite3").as_posix(),
    },
}

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

STATIC_URL = "/static/"
STATIC_ROOT = (BASE_DIR / "static").as_posix()

WSGI_APPLICATION = "test_proj.wsgi.application"

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Australia/Melbourne"

USE_I18N = False

USE_L10N = False

try:
    # .gitignored overrides
    exec((BASE_DIR / "local_settings.py").read_text())
except FileNotFoundError:
    pass
