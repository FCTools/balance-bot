"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""
import os
import time

from services.sender import Sender
from services.singleton import Singleton
from services.ts_clients.clients import *
import logging


class BalanceService(metaclass=Singleton):
    def __init__(self, telegram_access_token):
        self._logger = logging.getLogger("WorkingLoop.BalanceService")
        self._sender = Sender(telegram_access_token)

        self._clients = [
            DaoPushClient(telegram_access_token),
            EvadavClient(telegram_access_token),
            PropellerClient(telegram_access_token),
            ZeroParkClient(telegram_access_token),
            MgidClient(telegram_access_token),
            PushHouseClient(telegram_access_token),
        ]

        self._balances_checking_interval = float(os.getenv("BALANCES_CHECKING_INTERVAL", 900))  # seconds

        self._logger.info("Balance service was successfully initialized.")

    def set_notifications_interval(self, chat_id, interval):
        """
        Set given interval between balance notifications.

        :param chat_id: chat id
        :type chat_id: int

        :param interval: notifications interval to set (in hours)
        :type interval: float

        :return: None
        """

        for client in self._clients:
            client.notifications_interval = interval

        self._sender.send_message(chat_id, "Success.")
        self._logger.info(f"Change notifications interval to {interval}")

    def get_balance(self, network):
        for client in self._clients:
            if client.network_alias == network or client.network_fullname == network:
                return client.get_balance()

    def check_balances(self):
        """
        Checks balances and send notifications in infinite loop.

        :return: None
        """

        while True:
            for client in self._clients:
                client.check_balance()

            time.sleep(self._balances_checking_interval)
