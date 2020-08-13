"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import json
import logging

import requests
from services import requests_manager


def _button(text):
    return {"text": text}


class Sender:
    def __init__(self, telegram_access_token):
        self._logger = logging.getLogger("WorkingLoop.Sender")
        
        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"
        self._basic_keyboard = json.dumps(
            {
                "keyboard": [
                    [_button("/get_balance")],
                    [_button("/get_balance prop"), _button("/get_balance eva")],
                    [_button("/get_balance pushhouse"), _button("/get_balance dao")],
                    [_button("/help")],
                ],
                "resize_keyboard": True,
            }
        )

        self._logger.info("Sender initialized.")

    def send_message(self, to, text, parse_mode="HTML"):
        method = "sendMessage"

        response = requests_manager.post(
            requests.Session(),
            self._requests_url + method,
            params={"chat_id": to, "text": text, "parse_mode": parse_mode, "reply_markup": self._basic_keyboard},
        )

        if not isinstance(response, requests.Response):
            self._logger.error(f"Error occurred while trying to send message: {response}")
