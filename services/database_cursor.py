import logging
import os
import sqlite3
import threading

from services.singleton import Singleton


def catch_database_error(method):
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except (
            sqlite3.ProgrammingError,
            sqlite3.OperationalError,
            sqlite3.DatabaseError,
            sqlite3.Error,
            Exception,
        ) as database_error:
            return False, database_error

    return wrapper


class Database(metaclass=Singleton):
    def __init__(self):
        self._logger = logging.getLogger("WorkingLoop.Database")
        self._database_name = "info.sqlite3"

        self._logger.info(f"Database name: {self._database_name}")

        if not os.path.exists(self._database_name):
            self._logger.warning("Database doesn't exist, start to creating new one...")
            success, message = self._create_database()

            if success:
                self._logger.info("Database created. Please fill users and networks and then restart the program.")
                exit(0)
            else:
                self._logger.critical(f"Can't create database. Error: {message}")
                exit(-1)

        self._lock = threading.Lock()
        self._logger.info("Database initialized.")

    @catch_database_error
    def _create_database(self):
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        cursor.execute("CREATE table users (chat_id integer, login text, first_name text, last_name text)")
        cursor.execute("CREATE table networks (name text, info_level real, warning_level real, critical_level real)")

        connection.commit()

        return True, "OK"

    @catch_database_error
    def get_users(self):
        with sqlite3.connect(self._database_name) as connection:
            users_query = connection.execute("SELECT * from users")

            users_list = [
                {"chat_id": query[0], "login": query[1], "first_name": query[2], "last_name": query[3]}
                for query in users_query.fetchall()
            ]

        return True, users_list

    @catch_database_error
    def get_notification_levels(self, network):
        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                notification_levels_query = connection.execute(f"SELECT * from networks WHERE name='{network}'")
                levels = notification_levels_query.fetchone()

                notification_levels = {"info": levels[1], "warning": levels[2], "critical": levels[3]}

            return True, notification_levels

    @catch_database_error
    def set_notification_level_balance(self, network, level, balance):
        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                connection.execute(f"UPDATE networks SET {level}_level={balance} WHERE name='{network}'")

        return True, "OK"
