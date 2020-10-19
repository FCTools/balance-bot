"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from services import requests_manager
from services.captcha_solver import CaptchaSolver
from services.ts_clients.ts_client import TrafficSourceClient


class PushHouseClient(TrafficSourceClient):
    def __init__(self, telegram_access_token):
        self._captcha_solver = CaptchaSolver()
        self._now_authorizing = False

        super().__init__(
            telegram_access_token=telegram_access_token,
            network_fullname="Push.house",
            network_alias="pushhouse",
            interface="web",
            login=os.getenv("PUSHHOUSE_EMAIL"),
            password=os.getenv("PUSHHOUSE_PASSWORD"))

    def _authorize(self):
        """
        Authorize on Push.house and update session.

        :return: True if success, else False
        :rtype: bool
        """

        if self._now_authorizing:
            return "Now authorizing."

        self._now_authorizing = True
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

        if auth_page.status_code != 200:
            self._logger.error(f"Get pushhouse auth-page with non-success status code: {auth_page.status_code}."
                               f"Response: {auth_page.text}")
            return False

        soup = BeautifulSoup(auth_page.text, "lxml")

        try:
            data_sitekey = str(soup.select("#mainBlock > div > form > div:nth-child(4) > div")[0]).split('"')[3]
        except IndexError:
            self._logger.error("Can't get data-sitekey (captcha key) from pushhouse auth page.")
            return False

        g_recaptcha_response = self._captcha_solver.solve(data_sitekey, "https://push.house/auth/login")

        if g_recaptcha_response == 0:
            self._logger.error("Captcha solving error.")
            self._now_authorizing = False
            return False

        auth_data = {
            "email": self._login,
            "pass": self._password,
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
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "push.house",
                "Origin": "https://push.house",
            },
            cookies=auth_page.cookies
        )

        if not isinstance(auth_response, requests.Response):
            self._logger.error(f"Error occurred while trying to authorize on pushhouse: {auth_response}")
            return False
        if auth_response.status_code != 200:
            self._logger.error(
                f"Can't authorize on pushhouse: get auth-response with status code {auth_response.status_code}."
                f"Response: {auth_response.text}"
            )
            return False

        self._session = session
        self._session_ctime = datetime.utcnow()
        self._now_authorizing = False

        super()._authorize()
        return True

    def get_balance(self):
        """
        Get Push.house balance.

        :return: balance or None
        :rtype: Union[None, float]
        """

        if not self._session_is_active():
            authorization_status = self._authorize()
            if not authorization_status:
                return
            elif authorization_status == "Now authorizing.":
                return authorization_status

        dashboard_response = requests_manager.get(
            self._session, "https://push.house/dashboard"
        )

        if not isinstance(dashboard_response, requests.Response):
            self._logger.error(f"Error occurred while trying to get pushhouse dashboard: {dashboard_response}")
            return
        if dashboard_response.status_code != 200:
            self._logger.error(
                f"Can't get pushhouse balance: get dashboard response with status code {dashboard_response.status_code}."
                f"Response: {dashboard_response.text}"
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
            self._logger.error("Can't get balance from dashboard-page.")
            return

        return balance
