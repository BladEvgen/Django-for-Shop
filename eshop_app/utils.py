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

    company_name = "ElectroHub"
    current_year = datetime.datetime.now().year

    subject = f"Сброс пароля для вашего аккаунта на {company_name}"
    html_message = format_html(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f8f9fa; color: #333333;">
            <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%; background-color: #f8f9fa; margin: 0; padding: 20px;">
                <tr>
                    <td align="center">
                        <table role="presentation" cellpadding="0" cellspacing="0" style="max-width: 600px; min-width: 320px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1); background-color: #ffffff; border: 1px solid #e9ecef; margin: 20px auto;">
                            <!-- Header with Logo -->
                            <tr>
                                <td style="padding: 30px 0; text-align: center; background: linear-gradient(135deg, #28a745, #218838); color: white;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%;">
                                        <tr>
                                            <td style="text-align: center; padding: 0 20px;">
                                                <!-- Logo placeholder - replace with your actual logo -->
                                                <div style="width: 70px; height: 70px; background-color: white; border-radius: 50%; margin: 0 auto 15px; padding: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block;">
                                                    <svg viewBox="0 0 24 24" style="width: 100%; height: 100%;">
                                                        <path d="M13 5H11V11H5V13H11V19H13V13H19V11H13V5Z" fill="#28a745"/>
                                                        <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#28a745" stroke-width="2"/>
                                                    </svg>
                                                </div>
                                                <h1 style="margin: 10px 0; font-size: 24px; font-weight: 600;">{company_name}</h1>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Main Content -->
                            <tr>
                                <td style="padding: 40px 30px; background-color: #ffffff;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%;">
                                        <!-- Icon and Title -->
                                        <tr>
                                            <td style="text-align: center; padding-bottom: 30px;">
                                                <div style="width: 60px; height: 60px; background-color: #f0f7f1; border-radius: 50%; margin: 0 auto 20px; padding: 15px; display: inline-block;">
                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width: 100%; height: 100%;">
                                                        <path d="M12 1C8.676 1 6 3.676 6 7v3H4v13h16V10h-2V7c0-3.324-2.676-6-6-6zm0 2c2.276 0 4 1.724 4 4v3H8V7c0-2.276 1.724-4 4-4zm-6 9h12v9H6v-9z" fill="#28a745"/>
                                                    </svg>
                                                </div>
                                                <h2 style="margin: 0; color: #28a745; font-size: 22px; font-weight: 600;">Восстановление доступа</h2>
                                            </td>
                                        </tr>
                                        
                                        <!-- Personal Greeting -->
                                        <tr>
                                            <td style="padding-bottom: 20px;">
                                                <p style="margin: 0; font-size: 16px; line-height: 1.6;">Здравствуйте, <span style="font-weight: 600;">{username}</span>!</p>
                                            </td>
                                        </tr>
                                        
                                        <!-- Message -->
                                        <tr>
                                            <td style="padding-bottom: 30px;">
                                                <p style="margin: 0 0 15px 0; font-size: 16px; line-height: 1.6;">Мы получили запрос на сброс пароля для вашего аккаунта на {company_name}. Для создания нового пароля, пожалуйста, нажмите на кнопку ниже.</p>
                                                <p style="margin: 0; font-size: 16px; line-height: 1.6; color: #6c757d;">Если вы не запрашивали сброс пароля, пожалуйста, проигнорируйте это письмо или свяжитесь с нашей службой поддержки.</p>
                                            </td>
                                        </tr>
                                        
                                        <!-- Button -->
                                        <tr>
                                            <td style="padding-bottom: 30px; text-align: center;">
                                                <div>
                                                    <a href="{reset_link}" style="display: inline-block; min-width: 180px; padding: 14px 24px; background: linear-gradient(135deg, #28a745, #218838); color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center; box-shadow: 0 4px 6px rgba(40, 167, 69, 0.2);">
                                                        Сбросить пароль
                                                    </a>
                                                </div>
                                            </td>
                                        </tr>
                                        
                                        <!-- Time Warning -->
                                        <tr>
                                            <td style="text-align: center; padding-bottom: 30px;">
                                                <table role="presentation" cellpadding="0" cellspacing="0" style="width: 100%; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 6px; padding: 15px; margin: 0 auto;">
                                                    <tr>
                                                        <td style="width: 24px; vertical-align: top;">
                                                            <div style="color: #856404; margin-right: 10px;">
                                                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                                    <circle cx="12" cy="12" r="10"></circle>
                                                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                                                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                                                </svg>
                                                            </div>
                                                        </td>
                                                        <td style="color: #856404; text-align: left; font-size: 14px;">
                                                            Ссылка действительна <strong>только 1 час</strong> с момента получения этого письма.
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        
                                        <!-- Fallback Link -->
                                        <tr>
                                            <td style="padding-bottom: 20px;">
                                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #6c757d; text-align: center;">Если кнопка не работает, скопируйте и вставьте следующую ссылку в ваш браузер:</p>
                                                <p style="margin: 0; font-size: 14px; word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px; color: #495057; text-align: center;">{reset_link}</p>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            
                            <!-- Security tips -->
                            <tr>
                                <td style="padding: 20px 30px; background-color: #f8f9fa; border-top: 1px solid #e9ecef;">
                                    <h3 style="margin: 0 0 15px 0; font-size: 16px; color: #495057;">Рекомендации по безопасности:</h3>
                                    <ul style="margin: 0; padding-left: 20px; color: #6c757d; font-size: 14px; line-height: 1.6;">
                                        <li>Никогда не сообщайте свой пароль другим людям</li>
                                        <li>Используйте уникальный и надежный пароль для каждого сервиса</li>
                                        <li>Регулярно меняйте свои пароли для повышения безопасности</li>
                                    </ul>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px 30px; background-color: #f1f3f5; color: #6c757d; font-size: 12px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="margin: 0 0 10px 0;">Это автоматическое письмо, пожалуйста, не отвечайте на него.</p>
                                    <p style="margin: 0 0 10px 0;">Если вам нужна помощь, обратитесь в нашу <a href="#" style="color: #28a745; text-decoration: none;">службу поддержки</a>.</p>
                                    <p style="margin: 0;">&copy; {current_year} {company_name}. Все права защищены.</p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """,
        username=user.username,
        reset_link=reset_link,
        company_name=company_name,
        current_year=current_year,
    )

    plain_message = (
        f"Здравствуйте, {user.username}!\n\n"
        f"Мы получили запрос на сброс пароля для вашего аккаунта на {company_name}.\n\n"
        f"Для сброса пароля перейдите по следующей ссылке: {reset_link}\n\n"
        "Эта ссылка будет действительна в течение 1 часа. Для вашей безопасности не передавайте эту ссылку другим лицам.\n\n"
        "Рекомендации по безопасности:\n"
        "- Никогда не сообщайте свой пароль другим людям\n"
        "- Используйте уникальный и надежный пароль для каждого сервиса\n"
        "- Регулярно меняйте свои пароли для повышения безопасности\n\n"
        "Если вы не запрашивали сброс пароля, проигнорируйте это письмо или свяжитесь с нашей службой поддержки.\n\n"
        f"© {current_year} {company_name}. Все права защищены."
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
