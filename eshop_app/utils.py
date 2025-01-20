import re
import sqlite3
import datetime
from pathlib import Path
from time import perf_counter
from django.shortcuts import render

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
                print(f"Error executing query {str(error)} ")
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
