# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of balance-bot project.
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import logging
import os
import sqlite3
import threading

from services.helpers.singleton import Singleton


def catch_database_error(method):
    """
    Catch sqlite3 errors.
    """

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
    """
    Singleton database client.
    """

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
        """
        Create database and all required tables.

        :return: status (True if success, else False) and message
        :rtype: Tuple[Union[bool, str]]
        """

        connection = sqlite3.connect(self._database_name)
        cursor = connection.cursor()

        cursor.execute("CREATE table users (chat_id integer, login text, first_name text, last_name text)")
        cursor.execute("CREATE table networks (name text, info_level real, warning_level real, critical_level real, "
                       "status integer)")

        connection.commit()

        return True, "OK"

    @catch_database_error
    def get_users(self):
        """
        Select all users from database.

        :return: status (True if success, else False) and users list
        :rtype: Tuple[Union[bool, List[Dict[str, Union[int, str]]]]]
        """

        with sqlite3.connect(self._database_name) as connection:
            users_query = connection.execute("SELECT * from users")

            users_list = [
                {"chat_id": query[0], "login": query[1], "first_name": query[2], "last_name": query[3]}
                for query in users_query.fetchall()
            ]

        return True, users_list

    @catch_database_error
    def is_authorized(self, chat_id):
        """
        Check that user with given chat_id exists in database.

        :param chat_id: user chat_id
        :type chat_id: int

        :return: bool-status and result (True if exists, else False)
        :rtype: Tuple[bool]
        """

        with sqlite3.connect(self._database_name) as connection:
            users_query = connection.execute(f"SELECT * from users WHERE chat_id={chat_id}")

            if len(users_query.fetchall()) > 0:
                return True, True
            return True, False

        return True, users_list

    @catch_database_error
    def get_notification_levels(self, network):
        """
        Select notification levels from database for given network.

        :param network: network
        :type network: str

        :return: status (True if success, else False) and notification levels list
        :rtype: Tuple[Union[bool, List[Dict[str, float]]]]
        """

        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                notification_levels_query = connection.execute(f"SELECT * from networks WHERE name='{network}'")
                levels = notification_levels_query.fetchone()

                notification_levels = {"info": levels[1], "warning": levels[2], "critical": levels[3]}

            return True, notification_levels

    @catch_database_error
    def set_notification_level_balance(self, network, level, balance):
        """
        Set border for some notification level.

        :param network: network alias
        :type network: str

        :param level: notification level
        :type level: str

        :param balance: border
        :type balance: float

        :return: status (True if success, else False) and message
        :rtype: Tuple[Union[bool, str]]
        """

        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                connection.execute(f"UPDATE networks SET {level}_level={balance} WHERE name='{network}'")

        return True, "OK"

    @catch_database_error
    def set_network_status(self, status, network):
        """
        Set status (enabled/disabled) for given network.

        :param network: network alias
        :type network: str

        :return: status (True if success, else False) and message
        :rtype: Tuple[Union[bool, str]]
        """

        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                connection.execute(f"UPDATE networks SET status='{status}' WHERE name='{network}'")

        return True, "OK"

    @catch_database_error
    def get_network_status(self, network):
        """
        Return status (enabled/disabled) for given network.

        :param network: network alias
        :type network: str

        :return: network status
        """

        with self._lock:
            with sqlite3.connect(self._database_name) as connection:
                status_query = connection.execute(f"SELECT * from networks WHERE name='{network}'")

                return status_query.fetchone()[4]
