"""StepBite-ის კონფიგურაცია — Django + SQLite.

ეს სასწავლო პროექტია; runserver გამოიყენება ლოკალურად და არა საჯარო ჰოსტინგზე.
"""
# საწყისი პარამეტრები: პროექტის საქაღალდე, საიდუმლო გასაღები და ლოკალური მისამართები.
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-dev-only-stepbite-not-for-public-use-2026")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

# Django-ის მზა ნაწილები და ჩვენი restaurant აპლიკაცია.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "restaurant.apps.RestaurantConfig",
]

# შემომავალი მოთხოვნის შემოწმება: სესია, მომხმარებლის შესვლა, CSRF დაცვა და სხვა.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # ფორმებსა და კალათის ცვლილებებს იცავს
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# მთავარი URL ფაილი და HTML შაბლონების საძებნი პარამეტრები.
ROOT_URLCONF = "stepbite.urls"
TEMPLATES = [{
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
}]
WSGI_APPLICATION = "stepbite.wsgi.application"
ASGI_APPLICATION = "stepbite.asgi.application"

# SQLite ქმნის ფაილს db.sqlite3, როცა გავუშვებთ python manage.py migrate.
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
# პაროლზე მოთხოვნები: სიგრძე, სიმარტივე და სხვა წესები.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
# ენა, დროის სარტყელი, CSS/JS ფაილები და შესვლის შემდეგ მისამართები.
LANGUAGE_CODE = "ka"
TIME_ZONE = "Asia/Tbilisi"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
# სესიისა და CSRF cookie-ების საბაზისო უსაფრთხოების წესები.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# რეალური API ჩვეულებრივ გამოიყენება; მხოლოდ ლოკალურ ტესტში STEPBITE_DEMO=1.
# ეს სერვერის მისამართია, საიდანაც კერძებსა და კატეგორიებს ვიღებთ.
STEPBITE_DEMO = os.environ.get("STEPBITE_DEMO", "0") == "1"
RESTAURANT_API_ORIGIN = "https://restaurant.stepprojects.ge"
