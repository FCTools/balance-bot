import os
import sqlite3
import threading

from services.singleton import Singleton


class Database(metaclass=Singleton):
    def __init__(self):
        self._database_name = "info.sqlite3"

        if not os.path.exists(self._database_name):
            self._create_database()

        self._lock = threading.Lock()

    def _create_database(self):
        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        cursor.execute("CREATE table users (chat_id integer, login text, first_name text, last_name text)")
        cursor.execute("CREATE table networks (name text, info_level real, warning_level real, critical_level real)")

        connection.commit()

    def get_users(self):
        with sqlite3.connect(self._database_name) as connection:
            users_query = connection.execute("SELECT * from users")

            users_list = [
                {"chat_id": query[0], "login": query[1], "first_name": query[2], "last_name": query[3]}
                for query in users_query.fetchall()
            ]

        return users_list

    def get_notification_levels(self, network):
        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                notification_levels_query = connection.execute(f"SELECT * from networks WHERE name='{network}'")
                levels = notification_levels_query.fetchone()

                notification_levels = {"info": levels[1], "warning": levels[2], "critical": levels[3]}

            return notification_levels

    def set_notification_level_balance(self, network, level, balance):
        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                connection.execute(f"UPDATE networks SET {level}_level={balance} WHERE name='{network}'")
