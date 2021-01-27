# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of balance-bot project.
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

import json
import logging

import requests

from services.helpers import requests_manager


class Updater:
    """
    Service for telegram updates getting.
    """

    def __init__(self, telegram_access_token):
        self._requests_url = f"https://api.telegram.org/bot{telegram_access_token}/"
        self._logger = logging.getLogger(__name__)

        self._logger.info("Updater was successfully initialized.")

    def get_updates(self, offset=None, timeout=10):
        """
        Get updates list from telegram.

        :param offset: offset (last update id)
        :type offset: int

        :param timeout: timeout
        :type timeout: int

        :return: updates list
        :rtype: list
        """

        method = "getUpdates"
        response = requests_manager.get(requests.Session(), self._requests_url + method,
                                        params={"offset": offset, "timeout": timeout})

        if not isinstance(response, requests.Response):
            self._logger.error(f"Network error occurred while trying to get updates from telegram: {response}")
            return []
        if response.status_code != 200:
            self._logger.error(
                f"Get response with non-success status code (while trying to get updates from telegram)."
                f" Response: {response.text}")
            return []

        try:
            response_json = response.json()
        except json.JSONDecodeError as decode_error:
            self._logger.error(f"Can't decode response from telegram with updates, doc: {decode_error.doc}")
            return []

        if "result" in response_json:
            return response_json["result"]
        else:
            self._logger.error(f"Get response with incorrect structure (telegram updates): {response_json}")
            return []
