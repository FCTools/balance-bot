import json
import logging
import os
from datetime import timedelta
from random import choice
from urllib.parse import urlencode

from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from bs4 import BeautifulSoup

import requests
from datetime import datetime
import time

from services.database_cursor import Database
from services import requests_manager
from services.sender import Sender
from services.singleton import Singleton


class BalanceService(metaclass=Singleton):
    def __init__(self, telegram_access_token):
        self._sender = Sender(telegram_access_token)
        self._database_cursor = Database()

        self._logger = logging.getLogger("WorkingLoop.BalanceService")

        self._user_agents_list = []
        self._user_agent = None
        self._read_user_agents()
        self._update_user_agent()

        self._networks = {
            "PropellerAds": {
                "login": os.getenv("PROPELLER_LOGIN"),
                "password": os.getenv("PROPELLER_PASSWORD"),
                "fingerprint": os.getenv("PROPELLER_FINGERPRINT"),
                "last_notification": None,
                "last_notification_sending_time": None,
                "session": {"instance": requests.Session(),
                "creation_time": datetime.utcnow()},
                "access_token": os.getenv("PROPELLER_ACCESS_TOKEN"),
            },
            "Evadav": {
                "last_notification": None,
                "last_notification_sending_time": None,
                "access_token": os.getenv("EVADAV_ACCESS_TOKEN"),
            },
            "Push.house": {
                "email": os.getenv("PUSHHOUSE_EMAIL"),
                "password": os.getenv("PUSHHOUSE_PASSWORD"),
                "last_notification": None,
                "last_notification_sending_time": None,
                "session": {},
            },
            "DaoPush": {
                "login": os.getenv("DAO_EMAIL"),
                "password": os.getenv("DAO_PASSWORD"),
                "last_notification": None,
                "last_notification_sending_time": None,
                "session": {},
            },
        }

        self._session_lifetime = float(os.getenv("SESSION_LIFETIME", 2))  # hours
        self._balances_checking_interval = float(os.getenv("BALANCES_CHECKING_INTERVAL", 900))  # seconds
        self._notifications_interval = float(os.getenv("NOTIFICATIONS_INTERVAL", 2))  # hours
        self._captcha_api_key = os.getenv("CAPTCHA_SERVICE_KEY")

        self._logger.info("Balance service initialized.")

    def set_notifications_interval(self, chat_id, interval):
        self._notifications_interval = interval
        self._sender.send_message(chat_id, "Success.")

    def _read_user_agents(self):
        with open("user_agents.csv", "r", encoding="utf-8") as user_agents_file:
            data = user_agents_file.readlines()
        self._user_agents_list += [user_agent.strip() for user_agent in data]

    def _update_user_agent(self):
        self._user_agent = choice(self._user_agents_list)

    def session_is_active(self, network):
        return self._networks[network]["session"] and datetime.utcnow() - self._networks[network]["session"][
            "creation_time"
        ] < timedelta(hours=self._session_lifetime)

    def check_balance(self, network, balance):
        success, notification_levels = self._database_cursor.get_notification_levels(network)

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
            not self._networks[network]["last_notification_sending_time"]
            or notification_level != self._networks[network]["last_notification"]
            or datetime.utcnow() - self._networks[network]["last_notification_sending_time"]
            > timedelta(hours=self._notifications_interval)
        ):
            self.send_status_message(network, balance, notification_level)

    def get_propeller_balance_with_token(self):
        balance_response = requests_manager.get(
            self._networks["PropellerAds"]["session"]["instance"],
            "https://partners.propellerads.com/v1.0/advertiser/dashboard/",
            headers={"Authorization": f"Bearer {self._networks['PropellerAds']['access_token']}"},
        )

        if not isinstance(balance_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get propeller balance: {balance_response}")
            return

        try:
            balance_json = balance_response.json()
            print(balance_json)
        except json.JSONDecodeError as decode_error:
            self._logger.error(
                f"Decode error occurred while trying to parse balance response for propeller, doc:"
                f"{decode_error.doc}"
            )
            return

        try:
            return balance_json["result"]["balance"]
        except KeyError:
            self._logger.error(
                f"KeyError while trying to get balance from balance response for propeller. JSON data: {balance_json}"
            )

    def pushhouse_authorize(self):
        self._update_user_agent()

        session = requests.Session()

        auth_page = requests_manager.get(
            session,
            "https://push.house/auth/login",
            headers={"User-Agent": self._user_agent,
                     "Referer": "https://www.google.com/"})

        if not isinstance(auth_page, requests.Response):
            self._logger.error(f"Error occurred while trying to get login page for pushhouse: {auth_page}")
            return False

        soup = BeautifulSoup(auth_page.text, "lxml")

        try:
            data_sitekey = str(soup.select("#mainBlock > div > form > div:nth-child(4) > div")[0]).split('"')[3]
        except IndexError:
            self._logger.error("Can't parse data-sitekey from auth page html-code.")
            return False

        solver = recaptchaV2Proxyless()
        # solver.set_verbose(False) - you can do this for disable console logging
        solver.set_verbose(1)
        solver.set_key(self._captcha_api_key)
        solver.set_website_url("https://push.house/auth/login")
        solver.set_website_key(data_sitekey)

        g_recaptcha_response = solver.solve_and_return_solution()

        if g_recaptcha_response == 0:
            self._logger.error("Captcha solving error.")
            return False

        auth_data = {
            "email": self._networks["Push.house"]["email"],
            "pass": self._networks["Push.house"]["password"],
            "formsended": 1,
            "g-recaptcha-response": g_recaptcha_response,
        }

        auth_response = requests_manager.post(
            session,
            "https://push.house/auth/login",
            data=auth_data,
            headers={
                "UserAgent": self._user_agent,
                "Referer": "https://push.house/auth/login",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                "application/signed-exchange;v=b3;q=0.9",
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
            cookies=auth_page.cookies
        )

        if not isinstance(auth_response, requests.Response):
            self._logger.error(f"Error occurred while trying to authorize on pushhouse: {auth_response}")
            return False
        if auth_response.status_code != 200:
            self._logger.error(
                f"Can't authorize on pushhouse: get auth-response with status code {auth_response.status_code}"
            )
            return False

        self._networks["Push.house"]["session"] = {"instance": session, "creation_time": datetime.utcnow()}
        return True

    def get_pushhouse_balance(self):
        if not self.session_is_active(network="Push.house"):
            if not self.pushhouse_authorize():
                return

        dashboard_response = requests_manager.get(
            self._networks["Push.house"]["session"]["instance"], "https://push.house/dashboard"
        )

        if not isinstance(dashboard_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get pushhouse dashboard: {dashboard_response}")
            return
        if dashboard_response.status_code != 200:
            self._logger.error(
                f"Can't get pushhouse balance: get dashboard response with status code {dashboard_response.status_code}"
            )
            return

        soup_page = BeautifulSoup(dashboard_response.text, "lxml")

        try:
            balance = float(
                str(
                    soup_page.select(
                        "body > div.wrapper100.headerblock > div > div > "
                        "div.col.flexible > div > div.amountBlock > span"
                    )[0]
                )
                .split("$")[1]
                .split("<")[0]
                .strip()
            )
        except IndexError:
            self._logger.error("Can't get pushhouse balance from dashboard-page.")
            return

        return balance

    def get_evadav_balance(self):
        method = "account/balance"

        balance_response = requests_manager.get(
            requests.Session(),
            f"https://evadav.com/api/v2.0/{method}",
            params={"access-token": self._networks["Evadav"]["access_token"]},
            headers={"accept": "application/json"},
        )

        if not isinstance(balance_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get balance from eva: {balance_response}")
            return
        if balance_response.status_code != 200:
            self._logger.error(f"Can't get eva balance: get response with status code {balance_response.status_code}")
            return

        try:
            balance_response_json = balance_response.json()
        except json.JSONDecodeError as decode_error:
            self._logger.error(
                f"Decode error occurred while trying to parse balance response for evadav, doc:" f"{decode_error.doc}"
            )
            return

        try:
            return balance_response_json["data"]["advertiser"]
        except KeyError:
            self._logger.error(
                f"KeyError occurred while trying to get eva balance from balance_response_json. "
                f"Value: {balance_response_json}"
            )

    def dao_authorize(self):
        self._update_user_agent()
        session = requests.Session()

        main_page = requests_manager.get(
            session,
            "https://dao.ad/",
            headers={"user-agent": self._user_agent,
                     "referer": "https://www.google.com/"})

        if not isinstance(main_page, requests.Response):
            self._logger.error(f"Error occurred while trying to get dao.ad main page: {main_page}")
            return False

        time.sleep(5)

        auth_page = requests_manager.get(
            session,
            "https://dao.ad/en/manage/main/login",
            headers={"user-agent": self._user_agent, "referer": "https://dao.ad/"},
            cookies=main_page.cookies,
        )

        if not isinstance(auth_page, requests.Response):
            self._logger.error(f"Error occurred while trying to get dao.ad login-page: {auth_page}")
            return False

        if auth_page.status_code != 200:
            self._logger.error(f"Get dao.ad auth-page with non-success status code: {auth_page.status_code}")
            return False

        soup = BeautifulSoup(auth_page.text, "lxml")

        try:
            csrf = str(soup.select("#login-form > input[type=hidden]")[0]).split('value="')[1].split('"')[0]
        except IndexError:
            self._logger.error("Error occurred while trying to get csrf-token from dao.ad login-page.")
            return False

        time.sleep(5)

        login_response = requests_manager.post(
            session,
            "https://dao.ad/en/manage/main/login",
            data={
                "_csrf": csrf,
                "LoginForm[message]": "",
                "LoginForm[email]": self._networks["DaoPush"]["login"],
                "LoginForm[password]": self._networks["DaoPush"]["password"],
                "LoginForm[anotherPc]": 0,
            },
        )

        if not isinstance(login_response, requests.Response):
            self._logger.error(f"Error occurred while trying to authorize on dao.ad: {login_response}")
            return False

        self._networks["DaoPush"]["session"] = {"instance": session, "creation_time": datetime.utcnow()}
        return True

    def get_dao_balance(self):
        if not self.session_is_active("DaoPush"):
            if not self.dao_authorize():
                return

        statistics_page = requests_manager.get(
            self._networks["DaoPush"]["session"]["instance"], "https://dao.ad/manage/statistic"
        )

        if not isinstance(statistics_page, requests.Response):
            self._logger.error(f"Error occurred while trying to get dao.ad statistics page: {statistics_page}")
            return
        elif statistics_page.status_code != 200:
            self._logger.error(f"Get statistics page with non-success status code: {statistics_page.status_code}")
            return

        soup = BeautifulSoup(statistics_page.text, "lxml")
        try:
            balance = float(
                str(
                    soup.select(
                        "#topnav > div.topbar-main > div > div.menu-extras > div.top-nav.pull-right.hidden-xs > ul > "
                        "li:nth-child(2) > a"
                    )[0]
                )
                .split(":")[1]
                .split("$")[0]
                .strip()
                .replace(",", ".")
            )
        except IndexError:
            self._logger.error("Can't get balance from dao.ad statistics page.")
            return

        return balance

    def send_status_message(self, network, balance, level):
        message = f"<b>{level.upper()}</b>: {network} balance is {balance}$"
        success, users_list = self._database_cursor.get_users()

        if not success:
            self._logger.error(f"Database error occurred while trying to get users: {users_list}")
            return

        for user in users_list:
            self._sender.send_message(user["chat_id"], message)

        self._networks[network]["last_notification"] = level
        self._networks[network]["last_notification_sending_time"] = datetime.utcnow()

    def check_balances(self):
        while True:
            dao_balance = self.get_dao_balance()

            if dao_balance is not None:
                self.check_balance("DaoPush", dao_balance)

            propeller_balance = self.get_propeller_balance_with_token()
            print(propeller_balance)

            if propeller_balance is not None:
                self.check_balance("PropellerAds", propeller_balance)

            pushhouse_balance = self.get_pushhouse_balance()

            if pushhouse_balance is not None:
                self.check_balance("Push.house", pushhouse_balance)
            else:
                self._networks["Push.house"]["session"] = None
                pushhouse_balance = self.get_pushhouse_balance()

                if pushhouse_balance is not None:
                    self.check_balance("Push.house", pushhouse_balance)

            evadav_balance = self.get_evadav_balance()

            if evadav_balance is not None:
                self.check_balance("Evadav", evadav_balance)

            time.sleep(self._balances_checking_interval)
