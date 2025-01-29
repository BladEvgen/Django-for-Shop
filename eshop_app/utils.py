import re
import pytz
import sqlite3
import logging
import datetime
from pathlib import Path
from eshop_app import models
from time import perf_counter
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.core.mail import send_mail
from django.utils.html import format_html


logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "database.db"
LOGS_PATH = Path(__file__).resolve().parent.parent / "log"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOGS_PATH.mkdir(parents=True, exist_ok=True)


class Database:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def query(
        self,
        query_str: str,
        args: tuple = (),
        many: bool = True,
        commit: bool = False,
    ) -> list | None:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute(query_str, args)
            try:
                if many:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                if commit:
                    connection.commit()
                return result
            except Exception as error:
                logging.error(f"Error executing query {str(error)} ")
                return None


def create_tables():
    db = Database(DB_PATH)

    query_str = """
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_description TEXT,
            datetime TEXT,
            route TEXT
        )
    """
    db.query(query_str, commit=True)
    logger.info("Creating table error_log")
    
    query_str = """
        CREATE TABLE IF NOT EXISTS performance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            route TEXT,
            datetime TEXT,
            elapsed_time REAL
        )
    """
    db.query(query_str, commit=True)
    logger.info("Creating table performance_log")
    
    query_str = """
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            price REAL,
            is_active BOOLEAN DEFAULT 1
        )
    """
    db.query(query_str, commit=True)
    logger.info("Creating table price_data")


def decorator_error_handler(view_func):
    create_tables()

    def wrapper(request, *args, **kwargs):
        start_time = perf_counter()
        db = Database(DB_PATH)
        current_time = datetime.datetime.now()
        formatted_datetime = current_time.strftime("%H:%M:%S %d-%m-%Y")
        try:
            response = view_func(request, *args, **kwargs)
        except Exception as error:
            error = str(error)
            route = request.path

            with open(f"{LOGS_PATH}/logs.log", "a", encoding="utf-8") as log_file:
                log_file.write(f"{formatted_datetime} ERROR {request.path}: {error}\n")

            query_str = "INSERT INTO error_log (error_description, datetime, route) VALUES (?, ?, ?)"
            db.query(query_str, (error, current_time, route), commit=True)

            return render(request, "error.html", {"error": error}, status=500)
        else:
            return response
        finally:
            end_time = perf_counter()
            elapsed_time = end_time - start_time

            username = (
                request.user.username
                if request.user.is_authenticated
                else "Anonymous_user"
            )

            with open(f"{LOGS_PATH}/click.txt", "a", encoding="utf-8") as click_file:
                click_file.write(
                    f'{formatted_datetime} Username: "{username}" clicked on "{request.path}" (elapsed time: {round(elapsed_time, 5)} seconds)\n'
                )

            query_str = "INSERT INTO performance_log (username, route, datetime, elapsed_time) VALUES (?, ?, ?, ?)"
            db.query(
                query_str,
                (username, request.path, formatted_datetime, elapsed_time),
                commit=True,
            )

    return wrapper


def password_check(password: str) -> bool:
    return (
        True
        if re.match(
            r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$", password
        )
        is not None
        else False
    )


def transliterate(name):
    slovar = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        " ": " ",
        "-": "-",
        ".": ".",
        ",": ",",
        "!": "!",
        "?": "?",
        ":": ":",
    }

    name = name.lower()
    translit = []
    for letter in name:
        translit.append(slovar.get(letter, letter))

    return "".join(translit)

def send_password_reset_email(user, request):
    reset_link = f"{request.scheme}://{request.get_host()}{reverse('password_reset_confirm', args=[models.PasswordResetToken.generate_token(user)])}"

    subject = "Инструкция по сбросу пароля"
    html_message = format_html(
        """
        <div style="font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ececec; border-radius: 10px; background-color: #ffffff;">
            <h2 style="color: #007bff; text-align: center; margin-bottom: 20px;">Сброс пароля</h2>
            <p style="color: #333; line-height: 1.6; margin-bottom: 20px; text-align: center;">
                Здравствуйте, {username}. Вы запросили сброс пароля для своего аккаунта. 
                Пожалуйста, нажмите кнопку ниже, чтобы сбросить пароль.
            </p>
            <div style="text-align: center; margin-bottom: 30px;">
                <a href="{reset_link}" style="display: inline-block; padding: 15px 30px; color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold;">
                    Сбросить пароль
                </a>
            </div>
            <p style="color: #555; line-height: 1.6; margin-bottom: 20px; text-align: center;">
                Ссылка для сброса пароля действительна в течение <strong>1 часа</strong>. Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.
            </p>
            <hr style="border: none; border-top: 1px solid #ececec; margin: 30px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">
                Мы рады помочь вам сохранить безопасность вашего аккаунта. 
            </p>
        </div>
        """,
        username=user.username,
        reset_link=reset_link,
    )

    plain_message = (
        f"Здравствуйте, {user.username}!\n\n"
        "Вы получили это письмо, потому что был запрошен сброс пароля для вашего аккаунта.\n\n"
        f"Для сброса пароля перейдите по следующей ссылке: {reset_link}\n\n"
        "Эта ссылка будет действительна в течение 1 часа. Для вашей безопасности не передавайте эту ссылку другим лицам.\n\n"
        "Если вы не запрашивали сброс пароля, проигнорируйте это письмо, и ваш пароль останется неизменным.\n\n"
        "С уважением,\n"
        "Команда поддержки."
    )

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )


def get_client_ip(request):
    """Get the client IP address from the request, considering proxy setups."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip



def get_user_timezone(request):
    user_timezone = request.session.get("timezone")
    if not user_timezone:
        user_timezone = settings.TIME_ZONE
    return pytz.timezone(user_timezone)
