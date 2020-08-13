from services.ts_clients.ts_client import TrafficSourceClient
from services import requests_manager
import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime


class DaoPushCient(TrafficSourceClient):
    def __init__(self):
        super().__init__(
            network_fullname="DaoPush",
            network_alias="dao",
            interface="web",
            login=os.getenv("DAO_EMAIL"),
            password=os.getenv("DAO_PASSWORD"))

    def _authorize(self):
        """
        Authorize on DaoPush and update session.

        :return: status - True if success, else False
        :rtype: bool
        """

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
                "LoginForm[email]": self._login,
                "LoginForm[password]": self._password,
                "LoginForm[anotherPc]": 0,
            },
        )

        if not isinstance(login_response, requests.Response):
            self._logger.error(f"Error occurred while trying to authorize on dao.ad: {login_response}")
            return False

        self._session = session
        self._session_ctime = datetime.utcnow()
        super()._authorize()

        return True

    def get_balance(self):
        """
        Gets DaoPush balance.

        :return: balance or None
        :rtype: Union[None, float]
        """

        if not self._session_is_active():
            if not self._authorize():
                return

        statistics_page = requests_manager.get(
            self._session, "https://dao.ad/manage/statistic"
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
