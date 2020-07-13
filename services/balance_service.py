import os
import time
from datetime import datetime, timedelta

import requests

from services.database_cursor import Database
from services.sender import Sender


class BalanceService:
    def __init__(self, telegram_access_token):
        self._sender = Sender(telegram_access_token)
        self._database_cursor = Database()

        self._networks = {
            "PropellerAds": {
                "login": os.environ.get("PROPELLER_LOGIN"),
                "password": os.environ.get("PROPELLER_PASSWORD"),
                "last_sent_status": None,
                "last_status_message_time": None,
            }
        }

    def get_propeller_balance(self):
        user_agent_val = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/75.0.3770.142 Safari/537.36"
        )

        login = self._networks["PropellerAds"]["login"]
        password = self._networks["PropellerAds"]["password"]

        session = requests.Session()
        session.headers.update({"User-Agent": user_agent_val})

        post_request = session.post(
            "https://partners.propellerads.com/v1.0/login_check",
            {
                "username": login,
                "password": password,
                "fingerprint": "df9baa6341c7a67c40bcc3df469cf017",
                "type": "ROLE_ADVERTISER",
            },
        ).json()

        access_token = post_request["result"]["accessToken"]

        balance = requests.get(
            "https://partners.propellerads.com/v1.0/advertiser/dashboard/",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()["result"]["balance"]

        return balance

    def check_propeller_balance(self):
        propeller_balance = self.get_propeller_balance()

        notification_levels = self._database_cursor.get_notification_levels()

        notification_level = notification_levels[0]["level"]
        last_balance = notification_levels[0]["balance"]

        for level in notification_levels:
            if last_balance > level["balance"] > propeller_balance:
                last_balance = level["balance"]
                notification_level = level["level"]

        if not notification_level:
            return

        if not self._networks["PropellerAds"]["last_status_message_time"] or (
            notification_level != self._networks["PropellerAds"]["last_sent_status"]
            and datetime.utcnow() - self._networks["PropellerAds"]["last_status_message_time"] < timedelta(hours=2)
        ):
            self.send_status_message("PropellerAds", propeller_balance, notification_level)

    def send_status_message(self, network, balance, level):
        message = f"{level}: {network} balance is {balance}"
        users_list = self._database_cursor.get_users()

        for user in users_list:
            self._sender.send_message(user["chat_id"], message)

        self._networks[network]["last_sent_status"] = level
        self._networks[network]["last_status_message_time"] = datetime.utcnow()

    def check_balances(self):
        while True:
            self.check_propeller_balance()

            time.sleep(120)
