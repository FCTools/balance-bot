"""
Copyright © 2020 FC Tools. All rights reserved.
Author: German Yakimov
"""

import json
import logging

import requests
from services import requests_manager


def _button(text):
    """
    Create button-object with given text.

    :param text: text
    :type text: str

    :return: button-object
    :rtype: Dict[str, str]
    """

    return {"text": text}


class Sender:
    """
    Service for messages sending.
    """

    def __init__(self, telegram_access_token):
        self._logger = logging.getLogger("WorkingLoop.Sender")

        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"
        self._basic_keyboard = json.dumps(
            {
                "keyboard": [
                    [_button("/get_balance")],
                    [_button("/get_balance prop"), _button("/get_balance eva")],
                    [_button("/get_balance pushhouse"), _button("/get_balance dao")],
                    [_button("/get_balance zero"), _button("/get_balance mgid")],
                    [_button("/help")],
                ],
                "resize_keyboard": True,
            }
        )

        self._logger.info("Sender initialized.")

    def send_message(self, to, text, parse_mode="HTML"):
        """
        Send message with given text to given user.

        :param to: message receiver chat id
        :type to: int

        :param text: message text
        :type text: str

        :param parse_mode: parse mode for telegram formatting
        :type parse_mode: str

        :return: None
        """

        method = "sendMessage"

        response = requests_manager.post(
            requests.Session(),
            self._requests_url + method,
            params={"chat_id": to, "text": text, "parse_mode": parse_mode, "reply_markup": self._basic_keyboard},
        )

        if not isinstance(response, requests.Response):
            self._logger.error(f"Error occurred while trying to send message: {response}")
