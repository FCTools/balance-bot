import logging

import requests
from services import requests_manager


class Sender:
    def __init__(self, telegram_access_token):
        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"
        self._logger = logging.getLogger("WorkingLoop.Sender")

        self._logger.info("Sender initialized.")

    def send_message(self, to, text):
        method = "sendMessage"

        response = requests_manager.post(
            requests.Session(), self._requests_url + method, params={"chat_id": to, "text": text, "parse_mode": "HTML"}
        )

        if not isinstance(response, requests.Response):
            self._logger.error(f"Error occurred while trying to send message: {response}")
