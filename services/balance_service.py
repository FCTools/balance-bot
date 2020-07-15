import os
from datetime import timedelta
from urllib.parse import urlencode

from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from bs4 import BeautifulSoup

import requests
from datetime import datetime
import time

from services.database_cursor import Database
from services.sender import Sender


class BalanceService:
    def __init__(self, telegram_access_token):
        self._sender = Sender(telegram_access_token)
        self._database_cursor = Database()
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/83.0.4103.116 Safari/537.36"
        )

        self._networks = {
            "PropellerAds": {
                "login": os.environ.get("PROPELLER_LOGIN"),
                "password": os.environ.get("PROPELLER_PASSWORD"),
                "last_sent_status": None,
                "last_status_message_time": None,
                "session": {},
                "access_token": None,
            },
            "Evadav": {
                "last_sent_status": None,
                "last_status_message_time": None,
                "access_token": os.environ.get("EVADAV_ACCESS_TOKEN"),
            },
            "Push.house": {
                "email": os.environ.get("PUSHHOUSE_EMAIL"),
                "password": os.environ.get("PUSHHOUSE_PASSWORD"),
                "last_sent_status": None,
                "last_status_message_time": None,
                "session": {},
            },
        }

    def session_is_active(self, network):
        return self._networks[network]["session"] and datetime.utcnow() - self._networks[network]["session"][
            "creation_time"
        ] < timedelta(hours=1)

    def propeller_authorize(self):
        login = self._networks["PropellerAds"]["login"]
        password = self._networks["PropellerAds"]["password"]

        session = requests.Session()
        session.headers.update({"User-Agent": self._user_agent})

        post_request = session.post(
            "https://partners.propellerads.com/v1.0/login_check",
            {
                "username": login,
                "password": password,
                "fingerprint": "df9baa6341c7a67c40bcc3df469cf017",
                "type": "ROLE_ADVERTISER",
            },
        ).json()

        self._networks["PropellerAds"]["access_token"] = post_request["result"]["accessToken"]

        if self._networks["PropellerAds"]["session"]:
            self._networks["PropellerAds"]["session"]["instance"].delete()

        self._networks["PropellerAds"]["session"] = {"instance": session, "creation_time": datetime.utcnow()}

    def get_propeller_balance(self):
        if not self.session_is_active(network="PropellerAds"):
            self.propeller_authorize()

        balance = (
            self._networks["PropellerAds"]["session"]["instance"]
            .get(
                "https://partners.propellerads.com/v1.0/advertiser/dashboard/",
                headers={"Authorization": f"Bearer {self._networks['PropellerAds']['access_token']}"},
            )
            .json()["result"]["balance"]
        )

        return balance

    def check_propeller_balance(self):
        balance = self.get_propeller_balance()

        notification_levels = self._database_cursor.get_notification_levels("PropellerAds")

        notification_level = notification_levels[0]["level"]
        last_balance = notification_levels[0]["balance"]

        for level in notification_levels:
            if last_balance > level["balance"] > balance:
                last_balance = level["balance"]
                notification_level = level["level"]

        if not notification_level:
            return

        if not self._networks["PropellerAds"]["last_status_message_time"] or (
            notification_level != self._networks["PropellerAds"]["last_sent_status"]
            and datetime.utcnow() - self._networks["PropellerAds"]["last_status_message_time"] < timedelta(hours=2)
        ):
            self.send_status_message("PropellerAds", balance, notification_level)

    def pushhouse_authorize(self):
        session = requests.Session()
        session.headers.update({"User-Agent": self._user_agent})

        auth_page = session.get("https://push.house/auth/login")
        soup = BeautifulSoup(auth_page.text, "lxml")
        data_sitekey = str(soup.select("#mainBlock > div > form > div:nth-child(4) > div")[0]).split('"')[3]

        solver = recaptchaV2Proxyless()
        # solver.set_verbose(False) - you can do this for disable console logging
        solver.set_verbose(1)
        solver.set_key(os.environ.get("CAPTCHA_SERVICE_KEY"))
        solver.set_website_url("https://push.house/auth/login")
        solver.set_website_key(data_sitekey)

        g_response = solver.solve_and_return_solution()

        if g_response == 0:
            return

        auth_data = {
            "email": self._networks["Push.house"]["email"],
            "pass": self._networks["Push.house"]["password"],
            "formsended": 1,
            "g-recaptcha-response": g_response,
        }

        session.post(
            "https://push.house/auth/login",
            data=auth_data,
            headers={
                "UserAgent": self._user_agent,
                "Referer": "https://push.house/auth/login",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "push.house",
                "Origin": "https://push.house",
                "Content-Length": urlencode(auth_data),
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
        )

        if self._networks["Push.house"]["session"]:
            self._networks["Push.house"]["session"]["instance"].delete()

        self._networks["Push.house"]["session"] = {"instance": session, "creation_time": datetime.utcnow()}

    def get_pushhouse_balance(self):
        # Note: after captcha solving you can get balance without solving it (from same session)

        if not self.session_is_active("Push.house"):
            self.pushhouse_authorize()

        dashboard = self._networks["Push.house"]["session"]["instance"].get("https://push.house/dashboard")

        soup_page = BeautifulSoup(dashboard.text, "lxml")
        balance = float(
            str(
                soup_page.select(
                    "body > div.wrapper100.headerblock > div > div > " "div.col.flexible > div > div.amountBlock > span"
                )[0]
            )
            .split("$")[1]
            .split("<")[0]
            .strip()
        )

        return balance

    def check_pushhouse_balance(self):
        balance = self.get_pushhouse_balance()

        notification_levels = self._database_cursor.get_notification_levels("Push.house")

        notification_level = notification_levels[0]["level"]
        last_balance = notification_levels[0]["balance"]

        for level in notification_levels:
            if last_balance > level["balance"] > balance:
                last_balance = level["balance"]
                notification_level = level["level"]

        if not notification_level or balance > last_balance:
            return

        if not self._networks["Push.house"]["last_status_message_time"] or (
            notification_level != self._networks["Push.house"]["last_sent_status"]
            and datetime.utcnow() - self._networks["Push.house"]["last_status_message_time"] < timedelta(hours=2)
        ):
            self.send_status_message("Push.house", balance, notification_level)

    def get_evadav_balance(self):
        method = "account/balance"
        balance = requests.get(
            f"https://evadav.com/api/v2.0/{method}",
            params={"access-token": self._networks["Evadav"]["access_token"]},
            headers={"accept": "application/json"},
        ).json()["data"]["advertiser"]

        return balance

    def check_evadav_balance(self):
        balance = self.get_evadav_balance()

        notification_levels = self._database_cursor.get_notification_levels("Evadav")

        notification_level = notification_levels[0]["level"]
        last_balance = notification_levels[0]["balance"]

        for level in notification_levels:
            if last_balance > level["balance"] > balance:
                last_balance = level["balance"]
                notification_level = level["level"]

        if not notification_level or balance > last_balance:
            return

        if not self._networks["Evadav"]["last_status_message_time"] or (
            notification_level != self._networks["Evadav"]["last_sent_status"]
            and datetime.utcnow() - self._networks["Evadav"]["last_status_message_time"] < timedelta(hours=2)
        ):
            self.send_status_message("Evadav", balance, notification_level)

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
            self.check_pushhouse_balance()
            self.check_evadav_balance()

            time.sleep(30)
