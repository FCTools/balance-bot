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
        cursor.execute("CREATE table notification_levels (level text, balance real)")

        connection.commit()

    def get_users(self):
        with sqlite3.connect(self._database_name) as connection:
            users_query = connection.execute("SELECT * from users")

            users_list = [
                {"chat_id": query[0], "login": query[1], "first_name": query[2], "last_name": query[3]}
                for query in users_query.fetchall()
            ]

        return users_list

    def get_notification_levels(self):
        with sqlite3.connect(self._database_name) as connection:
            notifications_query = connection.execute("SELECT * from notification_levels")

            notifications_list = [{"level": query[0], "balance": query[1]} for query in notifications_query.fetchall()]

        return notifications_list
