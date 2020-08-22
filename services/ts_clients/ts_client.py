"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import logging
import os
from datetime import timedelta, datetime
from random import choice

from services.database_cursor import Database
from services.sender import Sender


class TrafficSourceClient:
    def __init__(self, telegram_access_token, network_fullname, network_alias, interface, **kwargs):
        self._logger = logging.getLogger(f"WorkingLoop.BalanceService.{network_fullname}Client")
        self._sender = Sender(telegram_access_token)

        self._last_notification_level = None
        self._last_notification_sending_time = None
        self._database = Database()
        self.network_fullname = network_fullname
        self.network_alias = network_alias
        self.interface = interface

        self.notifications_interval = float(os.getenv("NOTIFICATIONS_INTERVAL", 2))  # hours

        if interface == "api":
            if "access_token" in kwargs:
                self._access_token = kwargs["access_token"]
            else:
                self._logger.error(f"Interface for network {network_fullname} is "
                                   "api, but can't find access token in kwargs.")
                exit(-1)

        elif interface == "web":
            self._session_lifetime = float(os.getenv("SESSION_LIFETIME", 2))  # hours
            self._session = None
            self._session_ctime = None

            if "login" in kwargs:
                self._login = kwargs["login"]
            else:
                self._logger.error(f"Interface for network {network_fullname} is "
                                   "web, but can't find login in kwargs.")
                exit(-1)

            if "password" in kwargs:
                self._password = kwargs["password"]
            else:
                self._logger.error(f"Interface for network {network_fullname} is "
                                   "web, but can't find password in kwargs.")
                exit(-1)

            self._read_user_agents()
        else:
            self._logger.error(f"Incorrect network interface: {interface}")
            exit(-1)

    def _read_user_agents(self):
        with open("user_agents.csv", "r", encoding="utf-8") as user_agents_file:
            self._user_agents_list = user_agents_file.read().split("\n")

    def _update_user_agent(self):
        """
        Select random user agent from list and save it to self._user_agent.

        :return: None
        """

        self._user_agent = choice(self._user_agents_list)

    def _authorize(self):
        pass

    def _session_is_active(self):
        """
        Checks that session is alive (age less than session lifetime).

        :return: True if alive, else False
        :rtype: bool
        """

        if self.interface == "web":
            return self._session and datetime.utcnow() - self._session_ctime < timedelta(hours=self._session_lifetime)

    def get_balance(self):
        pass

    def send_status_message(self, balance, level):
        """
        Sends notification about balance.

        :param balance: balance
        :type balance: float

        :param level: notification level
        :type level: str

        :return: None
        """

        message = f"<b>{level.upper()}</b>: {self.network_fullname} balance is {balance}$"
        success, users_list = self._database.get_users()

        if not success:
            self._logger.error(f"Database error occurred while trying to get users: {users_list}")
            return

        if not self._last_notification_sending_time or \
           datetime.utcnow() - self._last_notification_sending_time >= timedelta(hours=self.notifications_interval):

            for user in users_list:
                self._sender.send_message(user["chat_id"], message)

            self._last_notification_level = level
            self._last_notification_sending_time = datetime.utcnow()

    def check_balance(self):
        """
        Check balance and send notification if necessary.

        :return: None
        """

        balance = self.get_balance()

        if balance is None:
            self._logger.error("Can't get balance.")
            return

        if isinstance(balance, str):
            return

        success, notification_levels = self._database.get_notification_levels(self.network_fullname)

        if not success:
            self._logger.error(f"Can't get notification levels from database: {notification_levels}")
            return

        notification_level = None
        last_balance = 10 ** 9  # just very big number

        for level in notification_levels:
            if last_balance > notification_levels[level] > balance:
                last_balance = notification_levels[level]
                notification_level = level

        if not notification_level:
            return

        if (
                not self._last_notification_sending_time
                or notification_level != self._last_notification_level
                or datetime.utcnow() - self._last_notification_sending_time
                > timedelta(hours=self.notifications_interval)
        ):
            self.send_status_message(balance, notification_level)
