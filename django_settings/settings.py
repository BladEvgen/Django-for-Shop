import os
import socket
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Host names and DEBUG setting
HOST_NAMES = ["RogStrix", "MacBook-Pro.local", "MacbookPro"]
DEBUG = socket.gethostname() in HOST_NAMES

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Secret keys and API configurations
SECRET_KEY = os.getenv("SECRET_KEY")
DB_TYPE = os.getenv("DB_TYPE", "sqlite3").lower()

# Email configurations
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")


# Function to get the local IP address
def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip_address = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting local IP: {e}")
        ip_address = "127.0.0.1"
    return ip_address


LOCAL_IP = get_local_ip()


# Function to get the external IP address
def get_external_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            external_ip = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting external IP: {e}")
        external_ip = "127.0.0.1"
    return external_ip


EXTERNAL_IP = get_external_ip()

# Allowed hosts and CSRF trusted origins
ALLOWED_HOSTS: list[str] = ["*"] + (
    [LOCAL_IP, EXTERNAL_IP] if DEBUG else ["example.domain.com"]
)


INSTALLED_APPS = [
    "daphne",
    "channels",
    "grappelli",
    # Standart
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "eshop_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "eshop_app.middleware.ClickLoggingMiddleware",
]

ROOT_URLCONF = "django_settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "eshop_app.context_processors.current_year",
            ],
        },
    },
]


ASGI_APPLICATION = "django_settings.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": (
            "channels.layers.InMemoryChannelLayer"
            if DEBUG
            else "channels_redis.core.RedisChannelLayer"
        ),
        "CONFIG": {} if DEBUG else {"hosts": [("127.0.0.1", 6379)]},
    },
}

# Cache configurations
if DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": "redis://127.0.0.1:6379",
        }
    }
# Database configurations

DATABASES = {"default": {}}

if DB_TYPE == "sqlite3":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
elif DB_TYPE == "postgresql":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "forum_app"),
        "USER": os.getenv("DB_USER", "django-admin"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
elif DB_TYPE == "mysql":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "3306"),
    }
else:
    raise ValueError(f"Unsupported database type: {DB_TYPE}")


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "ru"

TIME_ZONE = "Asia/Almaty"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = Path(BASE_DIR / "staticroot")

STATICFILES_DIRS = [
    Path(BASE_DIR, "static"),
]


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/" 
MEDIA_ROOT = BASE_DIR / "static/media"

LOG_DIR = BASE_DIR / "log"
LOG_DIR.mkdir(exist_ok=True)


# Custom function to generate log filenames
def get_log_filename(log_name):
    return LOG_DIR / f'{log_name}_{datetime.now().strftime("%Y-%m-%d_%H")}.log'


# Function to remove old logs
def clean_old_logs(log_directory, days_to_keep=7):
    now = datetime.now()
    for filename in os.listdir(log_directory):
        if filename.endswith(".log"):
            file_path = log_directory / filename
            file_modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if (now - file_modified_time).days > days_to_keep:
                file_path.unlink()


# Clean old logs
clean_old_logs(LOG_DIR, days_to_keep=7)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{levelname} {asctime} {name} {module} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO" if DEBUG else "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": get_log_filename("log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 24,  # Keep logs for 24 hours
            "encoding": "utf-8",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": True,
        },
        "django": {
            "handlers": ["file"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": True,
        },
    },
}
