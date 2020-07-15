import os
import sqlite3


class Database:
    def __init__(self):
        self._database_name = "info.sqlite3"

        if not os.path.exists(self._database_name):
            self._create_database()

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
        with sqlite3.connect(self._database_name) as connection:
            notification_levels_query = connection.execute(f"SELECT * from networks WHERE name='{network}'")
            levels = notification_levels_query.fetchone()

            notification_levels = [
                {"level": "info", "balance": levels[1]},
                {"level": "warning", "balance": levels[2]},
                {"level": "critical", "balance": levels[3]},
            ]

        return notification_levels
